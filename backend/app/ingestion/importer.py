"""
Main Catalogue Import Orchestrator.

Two-phase pipeline:
  analyze_import()  -> ImportAnalysis (no DB writes except the job record)
  commit_import()   -> persists valid rows to products table

merchant_id ALWAYS comes from the authenticated session.
"""
import csv
import io
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.ingestion.profiler import profile_csv, CSVProfileError
from app.ingestion.schema_detector import detect_schema
from app.ingestion.ai_mapper import map_schema_with_ai
from app.ingestion.mapping_validator import validate_mapping, mappings_to_field_dict, has_low_confidence
from app.ingestion.normalizer import normalize_row
from app.ingestion.business_validator import validate_row, select_price
from app.ingestion.canonical import REQUIRED_CANONICAL_FIELDS

logger = logging.getLogger(__name__)

TARGET_CATEGORIES = {
    "Mobiles & Accessories", "Computers", "Cameras & Accessories",
    "Watches", "Beauty and Personal Care", "Home Decor & Festive Needs",
}


def _demo_inventory(product_name: str) -> int:
    return (len(product_name) * 7) % 150 + 10


class ImportAnalysis:
    def __init__(self, import_job_id, merchant_id, schema_type, mappings,
                 unmapped_source_columns, missing_canonical_fields,
                 unified_rows, total_rows, sample_normalized,
                 ai_mapper_used, ai_mapper_provider, has_low_confidence_mappings, warnings):
        self.import_job_id = import_job_id
        self.merchant_id = merchant_id
        self.schema_type = schema_type
        self.mappings = mappings
        self.unmapped_source_columns = unmapped_source_columns
        self.missing_canonical_fields = missing_canonical_fields
        self.unified_rows = unified_rows
        self.total_rows = total_rows
        self.sample_normalized = sample_normalized
        self.ai_mapper_used = ai_mapper_used
        self.ai_mapper_provider = ai_mapper_provider
        self.has_low_confidence_mappings = has_low_confidence_mappings
        self.warnings = warnings

    @property
    def ready_row_count(self):
        return sum(1 for r in self.unified_rows if r["status"] == "READY")

    @property
    def needs_review_row_count(self):
        return sum(1 for r in self.unified_rows if r["status"] == "NEEDS_REVIEW")
        
    @property
    def needs_fix_row_count(self):
        return sum(1 for r in self.unified_rows if r["status"] == "NEEDS_FIX")
        
    @property
    def duplicate_row_count(self):
        return sum(1 for r in self.unified_rows if r["status"] == "DUPLICATE")

    @property
    def excluded_row_count(self):
        return sum(1 for r in self.unified_rows if r["status"] == "EXCLUDED")


def analyze_import(
    file_bytes: bytes,
    merchant_id: uuid.UUID,
    use_category_filter: bool = False,
    demo_inventory: bool = False,
) -> Tuple[Optional[ImportAnalysis], Optional[str]]:
    """
    Phase 1: Profile + detect schema + map + validate + normalize rows.
    Returns (ImportAnalysis, None) or (None, error_message).
    No products are written to DB here.
    """
    merchant_id_str = str(merchant_id)

    try:
        profile = profile_csv(file_bytes)
    except CSVProfileError as e:
        return None, str(e)

    headers = profile["headers"]
    row_count = profile["row_count"]
    sample_rows = profile["sample_rows"]
    logger.info(f"[import] merchant={merchant_id_str} rows={row_count} headers={headers}")

    detected = detect_schema(headers)
    logger.info(f"[import] schema_type={detected.schema_type}")

    ai_mapper_used = False
    ai_mapper_provider = None

    if detected.needs_ai_mapping:
        ai_mapper_used = True
        ai_result = map_schema_with_ai(headers, sample_rows, profile["column_profiles"])
        ai_mapper_provider = ai_result.provider
        if not ai_result.success:
            return None, f"AI schema analysis unavailable: {ai_result.error}"
        confidence = 1.0 if detected.is_flipkart_canonical else 0.95
        raw_mappings = [
            {"source_column": m.source_column, "target_field": m.target_field,
             "confidence": m.confidence, "reason": m.reason}
            for m in ai_result.mappings
        ]
    else:
        ai_mapper_used = False
        confidence = 1.0 if detected.is_flipkart_canonical else 0.95
        raw_mappings = [
            {"source_column": src, "target_field": tgt, "confidence": confidence,
             "reason": "Flipkart canonical schema" if detected.is_flipkart_canonical else "Deterministic alias match"}
            for src, tgt in detected.deterministic_mappings.items()
        ]

    valid_mappings, validation_errors = validate_mapping(raw_mappings, headers)
    warnings = list(validation_errors)

    if not valid_mappings:
        return None, "No valid field mappings. " + "; ".join(validation_errors)

    mapped_targets = {m["target_field"] for m in valid_mappings}
    for req in REQUIRED_CANONICAL_FIELDS:
        if req not in mapped_targets:
            return None, f"Required field '{req}' not mapped. Cannot import."

    field_dict = mappings_to_field_dict(valid_mappings)
    low_conf = has_low_confidence(valid_mappings)

    name_source_col = next((s for s, t in field_dict.items() if t == "product_name"), None)

    try:
        text = file_bytes.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
    except Exception:
        return None, "Cannot decode file content."

    reader = csv.DictReader(io.StringIO(text))
    unified_rows: List[Dict[str, Any]] = []
    seen_sources: set = set()
    seen_names: set = set()

    for row_idx, source_row in enumerate(reader, start=1):
        if row_idx > row_count:
            break

        if demo_inventory and name_source_col:
            inv_default = _demo_inventory(source_row.get(name_source_col, ""))
        else:
            inv_default = 0

        normalized, norm_errors = normalize_row(row=source_row, field_mapping=field_dict, default_inventory=inv_default)
        all_row_errors = [{"row": row_idx, **e} for e in norm_errors]
        
        status = "READY"

        if use_category_filter:
            cat = normalized.get("category", "")
            if cat not in TARGET_CATEGORIES:
                all_row_errors.append({"row": row_idx, "field": "category", "error": f"Category '{cat}' not in target list", "severity": "ERROR", "original_value": cat})

        val_result = validate_row(row_idx, normalized)
        if val_result.errors:
            all_row_errors.extend(val_result.errors)

        has_error = any(e.get("severity") == "ERROR" for e in all_row_errors)
        has_warning = any(e.get("severity") == "WARNING" for e in all_row_errors)
        
        if has_error:
            status = "NEEDS_FIX"
        elif has_warning:
            status = "NEEDS_REVIEW"

        source_id = normalized.get("source_product_id", "")
        product_name = normalized.get("product_name", "")

        if source_id:
            if source_id in seen_sources:
                all_row_errors.append({"row": row_idx, "field": "source_product_id", "error": f"Duplicate source_product_id: {source_id}", "severity": "ERROR"})
                status = "DUPLICATE"
            else:
                seen_sources.add(source_id)
        else:
            if product_name.lower() in seen_names:
                all_row_errors.append({"row": row_idx, "field": "product_name", "error": f"Duplicate product name: {product_name}", "severity": "ERROR"})
                status = "DUPLICATE"
            else:
                if product_name.strip():
                    seen_names.add(product_name.lower())

        normalized["_provenance"] = {
            "source_product_id": source_id,
            "mapping_method": "AI_SCHEMA_MAPPING" if ai_mapper_used else
                              ("FLIPKART_CANONICAL" if detected.is_flipkart_canonical else "DETERMINISTIC_ALIAS"),
        }
        
        unified_rows.append({
            "row_index": row_idx,
            "source_row": source_row,
            "normalized_candidate": normalized,
            "status": status,
            "issues": all_row_errors,
            "resolution": None
        })

    import_job_id = str(uuid.uuid4())
    logger.info(f"[import] analysis done job={import_job_id} unified={len(unified_rows)}")
    
    sample_normalized = [r["normalized_candidate"] for r in unified_rows if r["status"] == "READY"][:3]

    return ImportAnalysis(
        import_job_id=import_job_id,
        merchant_id=merchant_id_str,
        schema_type=detected.schema_type,
        mappings=valid_mappings,
        unmapped_source_columns=detected.unmapped_source_columns,
        missing_canonical_fields=detected.missing_canonical_fields,
        unified_rows=unified_rows,
        total_rows=row_count,
        sample_normalized=sample_normalized,
        ai_mapper_used=ai_mapper_used,
        ai_mapper_provider=ai_mapper_provider,
        has_low_confidence_mappings=low_conf,
        warnings=warnings,
    ), None


def commit_import(
    analysis: ImportAnalysis,
    db: Session,
    merchant_id: uuid.UUID,
    import_job_id: str,
) -> Dict[str, Any]:
    """
    Phase 2: Persist READY rows to the products table.
    merchant_id ALWAYS from authenticated session.
    """
    from app.models.product import Product, Inventory
    from sqlalchemy import select

    if str(analysis.merchant_id) != str(merchant_id):
        raise PermissionError("Import job does not belong to authenticated merchant")
    if analysis.import_job_id != import_job_id:
        raise ValueError("Import job ID mismatch")
        
    # Validation check: Prevent confirm if there are unresolved issues
    if analysis.needs_fix_row_count > 0 or analysis.needs_review_row_count > 0:
        raise ValueError("Cannot confirm import with unresolved NEEDS_FIX or NEEDS_REVIEW rows.")

    inserted = 0
    skipped_existing = 0
    failed = 0
    failed_rows = []

    for row_obj in analysis.unified_rows:
        if row_obj["status"] != "READY":
            continue
            
        normalized = row_obj["normalized_candidate"]

        try:
            product_name = normalized.get("product_name", "").strip()

            existing = db.execute(
                select(Product).filter(
                    Product.merchant_id == merchant_id,
                    Product.name == product_name,
                )
            ).scalar_one_or_none()

            if existing:
                skipped_existing += 1
                continue

            price = select_price(normalized)

            product = Product(
                id=uuid.uuid4(),
                merchant_id=merchant_id,
                name=product_name,
                description=normalized.get("description", ""),
                category=normalized.get("category", ""),

                price=price,


                currency="INR",



                product_metadata={"brand": normalized.get("brand", ""), "retail_price": normalized.get("retail_price"), "discounted_price": normalized.get("discounted_price"), "rating": normalized.get("product_rating"), "image_url": normalized.get("image_url", ""), "source_product_id": normalized.get("source_product_id"), "_provenance": normalized.get("_provenance", {})} | normalized.get("metadata", {}),
            )

            inv_val = normalized.get("inventory", 0)
            if not isinstance(inv_val, int):
                inv_val = 0

            inventory = Inventory(
                product_id=product.id,
                available_quantity=inv_val,


            )

            db.add(product)
            db.add(inventory)
            inserted += 1

        except Exception as e:
            failed += 1
            failed_rows.append({"row": row_obj["row_index"], "error": str(e), "product_name": normalized.get("product_name")})

    db.commit()

    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "failed": failed,
        "total_attempted": analysis.ready_row_count,
        "failed_rows": failed_rows,
    }

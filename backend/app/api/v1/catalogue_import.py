"""
Catalogue Import API Routes.

POST /api/v1/catalogue/import/analyze  - Upload CSV, analyze, return preview
POST /api/v1/catalogue/import/confirm  - Confirm import, persist products to DB
GET  /api/v1/catalogue/import/{job_id}/review - Get rows that need review/fix
PATCH /api/v1/catalogue/import/{job_id}/rows/{row_index} - Resolve a row issue
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.core.database import get_db
from app.models.merchant import Merchant
from app.models.catalogue_import_job import CatalogueImportJob
from app.security.authentication import get_current_merchant
from app.ingestion.importer import analyze_import, commit_import, ImportAnalysis
from app.services.audit_service import AuditService
from app.ingestion.business_validator import validate_row

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/catalogue/import", tags=["Catalogue Import"])

IMPORT_JOB_EXPIRY_HOURS = 2
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class ImportConfirmRequest(BaseModel):
    import_job_id: str
    confirmed: bool = True

class RowResolveRequest(BaseModel):
    action: str  # "ACCEPT", "EDIT", "EXCLUDE"
    updated_fields: Optional[Dict[str, Any]] = None

class RowResolveResponse(BaseModel):
    status: str
    message: str
    row: Dict[str, Any]

class MappingDisplay(BaseModel):
    source_column: str
    target_field: str
    confidence: float
    confidence_level: Optional[str] = None
    reason: str


class ImportPreviewResponse(BaseModel):
    import_job_id: str
    status: str
    schema_type: str
    ai_mapper_used: bool
    has_low_confidence_mappings: bool
    total_rows: int

    ready_row_count: int
    needs_review_row_count: int
    needs_fix_row_count: int
    duplicate_row_count: int
    excluded_row_count: int

    mappings: List[MappingDisplay]
    unmapped_source_columns: List[str]
    missing_canonical_fields: List[str]
    sample_normalized: List[Dict[str, Any]]
    warnings: List[str]


class ImportResultResponse(BaseModel):
    import_job_id: str
    status: str
    inserted: int
    skipped_existing: int
    failed: int
    total_attempted: int
    failed_rows: List[Dict[str, Any]]


@router.post("/analyze", response_model=ImportPreviewResponse, status_code=status.HTTP_200_OK)
async def analyze_catalogue_import(
    file: UploadFile = File(...),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    merchant_id = current_merchant.id

    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted (.csv extension required)"
        )

    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum allowed size is 50MB."
        )

    logger.info(f"[import/analyze] merchant={merchant_id} file={filename} size={len(content)}")

    analysis, error = analyze_import(file_bytes=content, merchant_id=merchant_id)
    if error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error)

    expires_at = datetime.now(timezone.utc) + timedelta(hours=IMPORT_JOB_EXPIRY_HOURS)

    job = CatalogueImportJob(
        id=uuid.UUID(analysis.import_job_id),
        merchant_id=merchant_id,
        status="ANALYZED",
        schema_type=analysis.schema_type,
        ai_mapper_used=analysis.ai_mapper_used,
        ai_mapper_provider=analysis.ai_mapper_provider,
        has_low_confidence_mappings=analysis.has_low_confidence_mappings,
        total_rows=analysis.total_rows,
        ready_row_count=analysis.ready_row_count,
        needs_review_row_count=analysis.needs_review_row_count,
        needs_fix_row_count=analysis.needs_fix_row_count,
        duplicate_row_count=analysis.duplicate_row_count,
        excluded_row_count=analysis.excluded_row_count,
        valid_row_count=analysis.ready_row_count,
        invalid_row_count=analysis.needs_fix_row_count + analysis.needs_review_row_count + analysis.duplicate_row_count,
        expires_at=expires_at,
        analysis_payload={
            "mappings": analysis.mappings,
            "unified_rows": analysis.unified_rows,
            "sample_normalized": analysis.sample_normalized,
            "unmapped_source_columns": analysis.unmapped_source_columns,
            "missing_canonical_fields": analysis.missing_canonical_fields,
            "warnings": analysis.warnings,
        }
    )
    db.add(job)
    db.commit()

    AuditService(db).log_event(
        event_type="CATALOGUE_IMPORT_ANALYZED",
        actor_type="MERCHANT",
        entity_type="catalogue_import_job",
        merchant_id=merchant_id,
        entity_id=job.id,
        event_data={
            "schema_type": analysis.schema_type,
            "total_rows": analysis.total_rows,
            "ready_rows": analysis.ready_row_count,
            "ai_mapper_used": analysis.ai_mapper_used,
            "filename": filename[:200],
        }
    )

    return ImportPreviewResponse(
        import_job_id=analysis.import_job_id,
        status="ANALYZED",
        schema_type=analysis.schema_type,
        ai_mapper_used=analysis.ai_mapper_used,
        has_low_confidence_mappings=analysis.has_low_confidence_mappings,
        total_rows=analysis.total_rows,
        ready_row_count=analysis.ready_row_count,
        needs_review_row_count=analysis.needs_review_row_count,
        needs_fix_row_count=analysis.needs_fix_row_count,
        duplicate_row_count=analysis.duplicate_row_count,
        excluded_row_count=analysis.excluded_row_count,
        mappings=[MappingDisplay(**m) for m in analysis.mappings],
        unmapped_source_columns=analysis.unmapped_source_columns,
        missing_canonical_fields=analysis.missing_canonical_fields,
        sample_normalized=analysis.sample_normalized,
        warnings=analysis.warnings,
    )


@router.get("/{job_id}/review", status_code=status.HTTP_200_OK)
def get_review_rows(
    job_id: str,
    status_filter: Optional[str] = None,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID")

    job = db.execute(
        select(CatalogueImportJob).filter(
            CatalogueImportJob.id == job_uuid,
            CatalogueImportJob.merchant_id == current_merchant.id,
        )
    ).scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")

    unified_rows = job.analysis_payload.get("unified_rows", [])

    if status_filter:
        filtered = [r for r in unified_rows if r["status"] == status_filter]
    else:
        # By default return rows that are not READY and not EXCLUDED
        filtered = [r for r in unified_rows if r["status"] not in ("READY", "EXCLUDED")]

    return {"rows": filtered}


@router.patch("/{job_id}/rows/{row_index}", response_model=RowResolveResponse)
def resolve_row(
    job_id: str,
    row_index: int,
    req: RowResolveRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID")

    job = db.execute(
        select(CatalogueImportJob).filter(
            CatalogueImportJob.id == job_uuid,
            CatalogueImportJob.merchant_id == current_merchant.id,
        )
    ).scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")

    payload = job.analysis_payload
    unified_rows = payload.get("unified_rows", [])

    row_obj = None
    for r in unified_rows:
        if r["row_index"] == row_index:
            row_obj = r
            break

    if not row_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")

    if req.action == "EXCLUDE":
        row_obj["status"] = "EXCLUDED"
        row_obj["resolution"] = {"action": "EXCLUDED"}
    elif req.action == "ACCEPT":
        # Merchant accepted the AI suggestion despite warnings/confidence
        if row_obj["status"] == "NEEDS_FIX":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot ACCEPT a row with NEEDS_FIX errors. Must EDIT or EXCLUDE.")
        row_obj["status"] = "READY"
        row_obj["resolution"] = {"action": "ACCEPTED_AS_IS"}
    elif req.action == "EDIT":
        if not req.updated_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="updated_fields required for EDIT action")

        # Apply updates
        row_obj["normalized_candidate"].update(req.updated_fields)

        # Re-validate
        val_result = validate_row(row_index, row_obj["normalized_candidate"])

        # In EDIT, if we still have errors, it goes back to NEEDS_FIX, else READY (we assume warning is accepted)
        has_error = any(e.get("severity") == "ERROR" for e in val_result.errors)
        if has_error:
            row_obj["status"] = "NEEDS_FIX"
            row_obj["issues"] = val_result.errors
        else:
            row_obj["status"] = "READY"
            row_obj["issues"] = []

        row_obj["resolution"] = {"action": "EDITED", "fields": list(req.updated_fields.keys())}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    # Update counts
    job.ready_row_count = sum(1 for r in unified_rows if r["status"] == "READY")
    job.needs_review_row_count = sum(1 for r in unified_rows if r["status"] == "NEEDS_REVIEW")
    job.needs_fix_row_count = sum(1 for r in unified_rows if r["status"] == "NEEDS_FIX")
    job.duplicate_row_count = sum(1 for r in unified_rows if r["status"] == "DUPLICATE")
    job.excluded_row_count = sum(1 for r in unified_rows if r["status"] == "EXCLUDED")

    # Needs to reassign to trigger JSON mutation for SQLAlchemy
    job.analysis_payload = payload

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(job, "analysis_payload")

    db.commit()

    return RowResolveResponse(
        status="success",
        message=f"Row {row_index} updated successfully",
        row=row_obj
    )


@router.post("/confirm", response_model=ImportResultResponse, status_code=status.HTTP_200_OK)
def confirm_catalogue_import(
    req: ImportConfirmRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    merchant_id = current_merchant.id

    if not req.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Import not confirmed.")

    try:
        job_uuid = uuid.UUID(req.import_job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid import_job_id.")

    job = db.execute(
        select(CatalogueImportJob).filter(
            CatalogueImportJob.id == job_uuid,
            CatalogueImportJob.merchant_id == merchant_id,
        )
    ).scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found.")

    now_utc = datetime.now(timezone.utc)
    expires = job.expires_at
    if expires.tzinfo is None:
        from datetime import timezone as tz
        expires = expires.replace(tzinfo=tz.utc)
    if now_utc > expires:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Import job has expired. Please re-analyze your CSV."
        )

    if job.status == "COMPLETED":
        result = job.import_result or {}
        return ImportResultResponse(
            import_job_id=req.import_job_id, status="COMPLETED",
            inserted=result.get("inserted", 0), skipped_existing=result.get("skipped_existing", 0),
            failed=result.get("failed", 0), total_attempted=result.get("total_attempted", 0),
            failed_rows=result.get("failed_rows", []),
        )

    if job.status not in ("ANALYZED", "READY"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Import job in state '{job.status}' cannot be confirmed."
        )

    if job.needs_fix_row_count > 0 or job.needs_review_row_count > 0 or job.duplicate_row_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot confirm import with unresolved issues. All rows must be READY or EXCLUDED."
        )

    job.status = "IMPORTING"
    db.commit()

    payload = job.analysis_payload or {}
    analysis = ImportAnalysis(
        import_job_id=req.import_job_id,
        merchant_id=str(merchant_id),
        schema_type=job.schema_type,
        mappings=payload.get("mappings", []),
        unmapped_source_columns=payload.get("unmapped_source_columns", []),
        missing_canonical_fields=payload.get("missing_canonical_fields", []),
        unified_rows=payload.get("unified_rows", []),
        total_rows=job.total_rows,
        sample_normalized=payload.get("sample_normalized", []),
        ai_mapper_used=job.ai_mapper_used,
        ai_mapper_provider=job.ai_mapper_provider,
        has_low_confidence_mappings=job.has_low_confidence_mappings,
        warnings=payload.get("warnings", []),
    )

    try:
        result = commit_import(
            analysis=analysis,
            db=db,
            merchant_id=merchant_id,
            import_job_id=req.import_job_id,
        )

        job.status = "COMPLETED"
        job.confirmed_at = datetime.now(timezone.utc)
        job.import_result = result
        db.commit()

        AuditService(db).log_event(
            event_type="CATALOGUE_IMPORT_CONFIRMED",
            actor_type="MERCHANT",
            entity_type="catalogue_import_job",
            merchant_id=merchant_id,
            entity_id=job.id,
            event_data={
                "inserted": result["inserted"],
                "skipped_existing": result["skipped_existing"],
                "failed": result["failed"],
                "total_attempted": result["total_attempted"],
            }
        )

        return ImportResultResponse(
            import_job_id=req.import_job_id,
            status="COMPLETED",
            inserted=result["inserted"],
            skipped_existing=result["skipped_existing"],
            failed=result["failed"],
            total_attempted=result["total_attempted"],
            failed_rows=result["failed_rows"],
        )
    except Exception as e:
        job.status = "FAILED"
        job.import_result = {"error": str(e)}
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )

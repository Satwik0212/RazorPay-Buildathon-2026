"""
Deterministic Mapping Validator.
Enforces security and business rules on field mappings before use.
"""
import logging
from typing import Any, Dict, List, Tuple
from app.ingestion.canonical import PLATFORM_OWNED_FIELDS, REQUIRED_CANONICAL_FIELDS, get_all_canonical_field_names

logger = logging.getLogger(__name__)

HIGH_CONFIDENCE = 0.90
MEDIUM_CONFIDENCE = 0.70


def validate_mapping(mappings, available_source_columns):
    """
    Validates mappings list against security and business rules.
    Returns (valid_mappings, error_strings).
    """
    valid_canonical = set(get_all_canonical_field_names())
    source_set = set(available_source_columns)
    seen_sources = set()
    seen_targets = set()
    valid = []
    errors = []

    for m in mappings:
        source = m.get("source_column", "")
        target = m.get("target_field", "")
        confidence = m.get("confidence", 0.0)
        reason = m.get("reason", "")

        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            errors.append(f"Invalid confidence for {source}->{target}: {confidence}")
            continue
        if target.lower() in PLATFORM_OWNED_FIELDS:
            errors.append(f"SECURITY: {target} is platform-owned and cannot be mapped from CSV")
            logger.warning(f"Blocked platform-owned field mapping: {target}")
            continue
        if target not in valid_canonical:
            errors.append(f"Unknown canonical field: {target!r}")
            continue
        if source not in source_set:
            errors.append(f"Source column not in CSV: {source!r}")
            continue
        if source in seen_sources:
            errors.append(f"Duplicate source column: {source!r}")
            continue
        if target in seen_targets:
            errors.append(f"Duplicate target field: {target!r}")
            continue

        seen_sources.add(source)
        seen_targets.add(target)

        level = ("HIGH" if confidence >= HIGH_CONFIDENCE
                 else "MEDIUM" if confidence >= MEDIUM_CONFIDENCE
                 else "LOW")

        valid.append({
            "source_column": source,
            "target_field": target,
            "confidence": confidence,
            "confidence_level": level,
            "reason": reason,
        })

    for req in REQUIRED_CANONICAL_FIELDS:
        if req not in seen_targets:
            errors.append(f"Required field '{req}' not mapped. Product name is required.")

    return valid, errors


def mappings_to_field_dict(valid_mappings):
    return {m["source_column"]: m["target_field"] for m in valid_mappings}


def has_low_confidence(valid_mappings):
    return any(m["confidence_level"] == "LOW" for m in valid_mappings)

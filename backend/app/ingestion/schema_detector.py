"""
Schema Detector - deterministic fast-path schema recognition.
Flipkart canonical schema is detected without any LLM call.
Unknown schemas signal the AI mapper.
"""
from typing import Dict, List, Optional
from app.ingestion.canonical import (
    FLIPKART_CANONICAL_HEADERS,
    get_canonical_field_for_alias,
    get_all_canonical_field_names,
)


class DetectedSchema:
    def __init__(self, schema_type, deterministic_mappings, unmapped_source_columns, missing_canonical_fields):
        self.schema_type = schema_type
        self.deterministic_mappings = deterministic_mappings
        self.unmapped_source_columns = unmapped_source_columns
        self.missing_canonical_fields = missing_canonical_fields

    @property
    def needs_ai_mapping(self):
        return self.schema_type == "UNKNOWN"

    @property
    def is_flipkart_canonical(self):
        return self.schema_type == "FLIPKART_CANONICAL"


def detect_schema(headers: List[str]) -> DetectedSchema:
    """
    Deterministically detect schema type from CSV headers.
    Returns DetectedSchema with mappings and unmapped columns.
    """
    normalized_headers = {h.strip().lower(): h for h in headers}
    canonical_fields_set = set(get_all_canonical_field_names())

    # Check Flipkart canonical: >=5 known Flipkart-specific headers
    normalized_set = set(normalized_headers.keys())
    flipkart_overlap = normalized_set & FLIPKART_CANONICAL_HEADERS
    is_flipkart = len(flipkart_overlap) >= 5

    # Build deterministic mappings for all recognized headers
    det_mappings: Dict[str, str] = {}
    unmapped: List[str] = []

    for norm_header, original_header in normalized_headers.items():
        canonical = get_canonical_field_for_alias(norm_header)
        if canonical and canonical not in det_mappings.values():
            det_mappings[original_header] = canonical
        else:
            unmapped.append(original_header)

    mapped_canonical = set(det_mappings.values())
    missing = [f for f in canonical_fields_set if f not in mapped_canonical]

    if is_flipkart:
        schema_type = "FLIPKART_CANONICAL"
    elif det_mappings:
        schema_type = "PARTIAL_DETERMINISTIC"
    else:
        schema_type = "UNKNOWN"

    return DetectedSchema(
        schema_type=schema_type,
        deterministic_mappings=det_mappings,
        unmapped_source_columns=unmapped,
        missing_canonical_fields=missing,
    )

"""
Deterministic CSV Profiler.
Extracts headers, row count, sample rows, column types.
Does NOT call LLM.
"""
import csv
import io
import re
from typing import Any, Dict, List, Optional, Tuple

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_ROWS = 10_000
MAX_FIELD_LENGTH = 5_000
SAMPLE_ROWS = 5


class CSVProfileError(Exception):
    pass


def _detect_column_type(values: List[str]) -> str:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "empty"
    numeric_count = 0
    for v in non_empty:
        cleaned = re.sub(r"[\u20b9,\s]", "", v.strip())
        cleaned = re.sub(r"(?i)^(inr|rs\.?)", "", cleaned).strip()
        try:
            float(cleaned)
            numeric_count += 1
        except ValueError:
            pass
    if numeric_count == len(non_empty):
        return "numeric"
    if numeric_count > len(non_empty) * 0.8:
        return "mostly_numeric"
    json_count = sum(1 for v in non_empty if v.strip().startswith(("[", "{")))
    if json_count > len(non_empty) * 0.5:
        return "json_or_list"
    return "text"


def profile_csv(content: bytes, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Profiles CSV bytes. Returns profile dict.
    Raises CSVProfileError for fatal issues.
    """
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise CSVProfileError(
            f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE_BYTES})"
        )
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]
    try:
        text = content.decode(encoding)
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception as e:
            raise CSVProfileError(f"Cannot decode file: {e}")
    if not text.strip():
        raise CSVProfileError("File is empty.")

    reader = csv.DictReader(io.StringIO(text))
    try:
        headers = reader.fieldnames
    except Exception as e:
        raise CSVProfileError(f"Cannot parse CSV headers: {e}")
    if not headers:
        raise CSVProfileError("CSV has no headers.")

    rows: List[Dict[str, str]] = []
    row_count = 0
    parse_errors = 0
    try:
        for row in reader:
            row_count += 1
            if row_count > MAX_ROWS:
                break
            safe_row = {}
            for k, v in row.items():
                if v and len(v) > MAX_FIELD_LENGTH:
                    v = v[:MAX_FIELD_LENGTH] + "...[truncated]"
                safe_row[k] = v or ""
            rows.append(safe_row)
    except csv.Error:
        if not rows:
            raise CSVProfileError("Malformed CSV.")
        parse_errors += 1

    if not rows:
        raise CSVProfileError("CSV has no data rows.")

    sample = rows[:SAMPLE_ROWS]
    column_profiles: Dict[str, Dict[str, Any]] = {}
    for header in headers:
        column_values = [r.get(header, "") for r in rows]
        non_empty_count = sum(1 for v in column_values if v.strip())
        empty_rate = round(1.0 - non_empty_count / len(rows), 3) if rows else 1.0
        inferred_type = _detect_column_type(column_values[:20])
        seen = []
        for v in column_values:
            if v.strip() and v not in seen:
                seen.append(v)
            if len(seen) >= 3:
                break
        column_profiles[header] = {
            "inferred_type": inferred_type,
            "empty_rate": empty_rate,
            "sample_values": seen,
        }

    return {
        "headers": list(headers),
        "row_count": row_count,
        "sample_rows": sample,
        "column_profiles": column_profiles,
        "parse_errors": parse_errors,
        "truncated": row_count >= MAX_ROWS,
    }

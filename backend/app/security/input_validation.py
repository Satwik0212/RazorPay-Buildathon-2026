import re
from app.core.exceptions import ValidationError


def sanitize_search_query(query: str) -> str:
    # Strip dangerous characters while preserving legitimate product search terms
    cleaned = re.sub(r"[^\w\s\-\.\,\(\)]", "", query).strip()
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    return cleaned

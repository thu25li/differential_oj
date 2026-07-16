from typing import Optional
MAX_TEXT_LENGTH = 4000
TRUNCATED_MARKER = "...[truncated]"
def truncate_text(text: Optional[str], max_length: int = MAX_TEXT_LENGTH) -> Optional[str]:
    if text is None:
        return None
    if len(text) <= max_length:
        return text
    return text[:max_length] + TRUNCATED_MARKER

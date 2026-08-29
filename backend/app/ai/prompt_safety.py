import re


class PromptSafety:
    """
    Enforces prompt safety boundaries.
    Customer and product text are untrusted data and must never override system instructions.
    """

    @staticmethod
    def wrap_untrusted_content(tag_name: str, content: str) -> str:
        """
        Wraps content in safety boundary tags and prevents breakout injection.
        """
        sanitized = content.replace(f"</{tag_name}>", "").replace(f"<{tag_name}>", "")
        return f"<{tag_name}>\n{sanitized.strip()}\n</{tag_name}>"

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Removes dangerous control characters from raw text.
        """
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()

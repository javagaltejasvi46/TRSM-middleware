"""Sensitive data redaction for audit streams."""

import re

TOKEN_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"password\s*=\s*['\"][^'\"]+['\"]",
]


class RedactionEngine:
    """Sanitizes sensitive tokens, keys, and private credentials."""

    def redact(self, text: str) -> str:
        redacted = text
        for pat in TOKEN_PATTERNS:
            redacted = re.sub(pat, "[REDACTED_SECRET]", redacted, flags=re.IGNORECASE)
        return redacted

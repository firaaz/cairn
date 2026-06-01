"""Shared quote-vs-source matcher: whitespace-normalize + comment-strip tolerance.

The validator's premise-grounding assertion and the premise_guard CLI gate both
route their match test through `grounded`, so they cannot diverge on tolerance.
"""

import re

_LINE_COMMENT_EXTS = {".py", ".sh", ".yaml", ".yml"}


def normalize(text: str, ext: str) -> str:
    """Strip comments by extension, then collapse all whitespace to single spaces."""
    if ext in _LINE_COMMENT_EXTS:
        text = "\n".join(
            re.sub(r"(^|\s)#.*$", r"\1", line) for line in text.splitlines()
        )
    elif ext == ".md":
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return " ".join(text.split())


def grounded(source_text: str, quote: str, ext: str) -> bool:
    """True if the normalized quote is non-empty and present in the normalized source."""
    nq = normalize(quote, ext)
    if not nq:
        return False
    return nq in normalize(source_text, ext)

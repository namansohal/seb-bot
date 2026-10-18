"""
Detect @@TAG: content@@ patterns in text.

Hash is updated only AFTER processing — not on detection.
This prevents losing the tag when the user switches windows mid-typing.

CHAT is repeatable, so the chat window can be closed and reopened
without restarting the bot.
"""

import re
import hashlib

_TAG_RE = re.compile(r'@@([A-Za-z]+)\s*:?\s*(.*?)@@', re.DOTALL)

KNOWN_TAGS = {
    "ASK",
    "SOLVE",
    "FIX",
    "COPY",
    "PASTE",
    "COPYALL",
    "COPYABOVE",
    "SCREENSHOT",
    "SOLVEALL",
    "ASKALL",
    "CHAT",
}

_processed_hash: str | None = None


def _compute_hash(tag_type: str, content: str) -> str:
    return hashlib.md5(
        f"{tag_type}:{content}".encode()
    ).hexdigest()


def peek_tag(text: str) -> tuple[str, str] | None:
    """Find the last complete tag in text. Does NOT update any state."""
    candidates = []

    for m in _TAG_RE.finditer(text):
        tag = m.group(1).upper().strip()
        content = m.group(2).strip()

        if tag in KNOWN_TAGS:
            candidates.append(
                (m.start(), tag, content)
            )

    if not candidates:
        return None

    _, tag_type, content = max(
        candidates,
        key=lambda x: x[0],
    )

    return tag_type, content


def is_new(tag_type: str, content: str) -> bool:
    """
    Return True if this tag has not been processed yet.

    CHAT is always repeatable so the chat window can be closed
    and opened again without restarting the bot.
    """
    if tag_type == "CHAT":
        return True

    return _compute_hash(
        tag_type,
        content,
    ) != _processed_hash


def mark_processed(tag_type: str, content: str):
    """Call this after successfully processing the tag."""
    global _processed_hash

    _processed_hash = _compute_hash(
        tag_type,
        content,
    )


def reset():
    global _processed_hash
    _processed_hash = None
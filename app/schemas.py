"""Validation and normalization for inbound reaction events.

The wire schema is deliberately generic: any live event (sports, stream,
webinar, classroom) can send ``{"user_id", "reaction", "timestamp"}``.
For backwards compatibility with the original prototype, ``emoji_type``
is accepted as an alias of ``reaction``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


MAX_USER_ID_LEN = 128
MAX_REACTION_LEN = 32


@dataclass(frozen=True)
class ReactionEvent:
    user_id: str
    reaction: str
    timestamp: str  # ISO-8601 UTC, normalized at validation time

    def to_kafka_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "reaction": self.reaction,
            "timestamp": self.timestamp,
        }


def _normalize_timestamp(value: Any) -> Optional[str]:
    """Accept epoch numbers or ISO strings; return ISO-8601 UTC or None."""
    if value is None:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, (int, float)):
        try:
            return (
                datetime.fromtimestamp(float(value), tz=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        candidate = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return None


def validate_reaction(payload: Any) -> Tuple[Optional[ReactionEvent], Optional[str]]:
    """Validate an inbound JSON payload.

    Returns (event, None) on success or (None, error_message) on failure.
    Never raises on bad input; the API layer turns errors into 400s.
    """
    if not isinstance(payload, dict):
        return None, "body must be a JSON object"

    user_id = payload.get("user_id")
    # Generic field name is "reaction"; accept legacy "emoji_type".
    reaction = payload.get("reaction", payload.get("emoji_type"))

    if not isinstance(user_id, str) or not user_id.strip():
        return None, "user_id must be a non-empty string"
    if len(user_id.strip()) > MAX_USER_ID_LEN:
        return None, f"user_id must be <= {MAX_USER_ID_LEN} chars"
    if not isinstance(reaction, str) or not reaction.strip():
        return None, "reaction must be a non-empty string"
    if len(reaction.strip()) > MAX_REACTION_LEN:
        return None, f"reaction must be <= {MAX_REACTION_LEN} chars"

    timestamp = _normalize_timestamp(payload.get("timestamp"))
    if timestamp is None:
        return None, "timestamp must be ISO-8601 or epoch seconds"

    return (
        ReactionEvent(
            user_id=user_id.strip(),
            reaction=reaction.strip(),
            timestamp=timestamp,
        ),
        None,
    )

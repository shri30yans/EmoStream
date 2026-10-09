"""Unit tests for reaction schema validation (no broker needed)."""

from app.schemas import validate_reaction


def test_valid_payload():
    event, error = validate_reaction({
        "user_id": "user123",
        "reaction": "applause",
        "timestamp": "2024-01-01T12:00:00Z",
    })
    assert error is None
    assert event is not None
    assert event.user_id == "user123"
    assert event.reaction == "applause"
    assert event.timestamp.endswith("Z")


def test_legacy_emoji_type_alias():
    event, error = validate_reaction({
        "user_id": "u1",
        "emoji_type": "smile",
        "timestamp": 1700000000,
    })
    assert error is None
    assert event is not None
    assert event.reaction == "smile"


def test_missing_user_rejected():
    event, error = validate_reaction({"reaction": "x"})
    assert event is None
    assert "user_id" in error


def test_empty_reaction_rejected():
    event, error = validate_reaction({"user_id": "u", "reaction": "  "})
    assert event is None
    assert "reaction" in error


def test_non_object_rejected():
    event, error = validate_reaction(["not", "an", "object"])
    assert event is None
    assert error is not None


def test_bad_timestamp_rejected():
    event, error = validate_reaction({
        "user_id": "u", "reaction": "x", "timestamp": "not-a-time"})
    assert event is None
    assert "timestamp" in error

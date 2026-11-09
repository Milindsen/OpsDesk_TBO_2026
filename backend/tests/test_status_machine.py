import pytest
from fastapi import HTTPException

from app.api.v1.tickets import VALID_TRANSITIONS


def validate_transition(current: str, target: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current} to {target}. Allowed: {allowed}",
        )


def test_valid_transitions_pass() -> None:
    # All valid moves
    valid_pairs = [
        ("New", "Open"),
        ("Open", "Pending"),
        ("Open", "Escalated"),
        ("Open", "Resolved"),
        ("Pending", "Open"),
        ("Pending", "Resolved"),
        ("Escalated", "Resolved"),
        ("Escalated", "Open"),
        ("Resolved", "Closed"),
    ]
    for current, target in valid_pairs:
        # Should not raise
        validate_transition(current, target)


def test_invalid_transitions_raise_exception() -> None:
    invalid_pairs = [
        ("New", "Resolved"),
        ("New", "Closed"),
        ("New", "Escalated"),
        ("Open", "New"),
        ("Pending", "Closed"),
        ("Escalated", "Pending"),
        ("Resolved", "Open"),
    ]
    for current, target in invalid_pairs:
        with pytest.raises(HTTPException) as excinfo:
            validate_transition(current, target)
        assert excinfo.value.status_code == 400


def test_closed_to_anything_fails() -> None:
    targets = ["New", "Open", "Pending", "Escalated", "Resolved", "Closed"]
    for target in targets:
        with pytest.raises(HTTPException) as excinfo:
            validate_transition("Closed", target)
        assert excinfo.value.status_code == 400
        assert "Invalid transition from Closed" in excinfo.value.detail

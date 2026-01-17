# tests/test_annotation.py
from __future__ import annotations

from datetime import datetime, timezone

from taskdantic.models import Annotation


def test_annotation_creation():
    """Test creating an annotation with datetime."""
    dt = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    annotation = Annotation(entry=dt, description="Test note")

    assert annotation.entry == dt
    assert annotation.description == "Test note"


def test_annotation_from_string():
    """Test creating annotation from Taskwarrior timestamp string."""
    annotation = Annotation(entry="20240115T143022Z", description="Test note")

    expected = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    assert annotation.entry == expected


def test_annotation_serialization():
    """Test annotation serializes to Taskwarrior format."""
    dt = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    annotation = Annotation(entry=dt, description="Test note")

    data = annotation.model_dump(mode="json")
    assert data["entry"] == "20240115T143022Z"
    assert data["description"] == "Test note"

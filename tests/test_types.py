# tests/unit/test_types.py
from __future__ import annotations

import pytest

from taskdantic.types import TaskFilter


@pytest.mark.unit
class TestTaskFilter:
    """Test TaskFilter type definition."""

    def test_string_filter_type(self) -> None:
        """Test that string is valid TaskFilter."""
        filter_str: TaskFilter = "status:pending"
        assert isinstance(filter_str, str)

    def test_dict_filter_type(self) -> None:
        """Test that dict is valid TaskFilter."""
        filter_dict: TaskFilter = {"status": "pending", "project": "work"}
        assert isinstance(filter_dict, dict)

    def test_empty_string_filter(self) -> None:
        """Test empty string as filter."""
        filter_str: TaskFilter = ""
        assert filter_str == ""

    def test_empty_dict_filter(self) -> None:
        """Test empty dict as filter."""
        filter_dict: TaskFilter = {}
        assert filter_dict == {}

    def test_dict_with_none_values(self) -> None:
        """Test dict with None values."""
        filter_dict: TaskFilter = {"project": None, "priority": None}
        assert filter_dict["project"] is None
        assert filter_dict["priority"] is None

    def test_complex_string_filter(self) -> None:
        """Test complex string filter with multiple conditions."""
        filter_str: TaskFilter = "(status:pending or status:waiting) priority:H"
        assert isinstance(filter_str, str)
        assert "status:pending" in filter_str

    def test_dict_with_list_value(self) -> None:
        """Test dict with list value for tags."""
        filter_dict: TaskFilter = {"tags": ["urgent", "important"]}
        assert isinstance(filter_dict["tags"], list)
        assert len(filter_dict["tags"]) == 2

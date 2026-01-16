# src/taskdantic/types.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from taskdantic.utils import datetime_to_taskwarrior, taskwarrior_to_datetime


class TWDatetime(datetime):
    """Datetime that parses/serializes Taskwarrior timestamp format (YYYYMMDDTHHmmssZ)."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            cls._validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(datetime),
                    core_schema.str_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(cls._serialize),
        )

    @classmethod
    def _validate(cls, value: Any, handler: Any) -> datetime:
        if isinstance(value, str):
            return taskwarrior_to_datetime(value)
        if isinstance(value, datetime):
            return value
        return handler(value)

    @staticmethod
    def _serialize(value: datetime) -> str:
        return datetime_to_taskwarrior(value)


class TWDuration(timedelta):
    """Timedelta that parses/serializes ISO 8601 duration format (PT#H#M#S)."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            cls._validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(timedelta),
                    core_schema.str_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(cls._serialize),
        )

    @classmethod
    def _validate(cls, value: Any, handler: Any) -> timedelta:
        if isinstance(value, timedelta):
            return value
        if isinstance(value, str) and value.startswith("PT"):
            return cls._parse_duration(value)
        if isinstance(value, str):
            return timedelta(seconds=int(value))
        return handler(value)

    @staticmethod
    def _parse_duration(v: str) -> timedelta:
        """Parse ISO 8601 duration string."""
        hours = 0
        minutes = 0
        seconds = 0
        v = v[2:]  # Remove PT prefix
        if "H" in v:
            hours_str, v = v.split("H", 1)
            hours = int(hours_str)
        if "M" in v:
            minutes_str, v = v.split("M", 1)
            minutes = int(minutes_str)
        if "S" in v:
            seconds = int(v.replace("S", ""))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def _serialize(value: timedelta) -> str:
        """Serialize timedelta to ISO 8601 duration string."""
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        parts = []
        if hours:
            parts.append(f"{hours}H")
        if minutes:
            parts.append(f"{minutes}M")
        if seconds:
            parts.append(f"{seconds}S")
        return "PT" + "".join(parts) if parts else "PT0S"


class UUIDList(list[UUID]):
    """List of UUIDs that parses/serializes comma-separated string format."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            cls._validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(list),
                    core_schema.str_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(cls._serialize),
        )

    @classmethod
    def _validate(cls, value: Any, handler: Any) -> list[UUID]:
        if isinstance(value, list):
            return [UUID(u) if isinstance(u, str) else u for u in value]
        if isinstance(value, str):
            return [UUID(u.strip()) for u in value.split(",") if u.strip()]
        return handler(value)

    @staticmethod
    def _serialize(value: list[UUID]) -> str | None:
        """Serialize UUID list to comma-separated string."""
        if not value:
            return None
        return ",".join(str(u) for u in value)

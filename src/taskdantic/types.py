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
    def _validate(cls, value: Any, handler: Any) -> TWDatetime:
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            dt = taskwarrior_to_datetime(value)
            return cls(
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                dt.minute,
                dt.second,
                dt.microsecond,
                tzinfo=dt.tzinfo,
            )

        if isinstance(value, datetime):
            return cls(
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
                tzinfo=value.tzinfo,
            )

        coerced = handler(value)
        if isinstance(coerced, cls):
            return coerced
        if isinstance(coerced, datetime):
            return cls(
                coerced.year,
                coerced.month,
                coerced.day,
                coerced.hour,
                coerced.minute,
                coerced.second,
                coerced.microsecond,
                tzinfo=coerced.tzinfo,
            )
        return coerced

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
    def _validate(cls, value: Any, handler: Any) -> TWDuration:
        if isinstance(value, cls):
            return value

        if isinstance(value, timedelta):
            # Convert plain timedelta into TWDuration instance
            return cls(days=value.days, seconds=value.seconds, microseconds=value.microseconds)

        if isinstance(value, str) and value.startswith("PT"):
            td = cls._parse_duration(value)
            return cls(days=td.days, seconds=td.seconds, microseconds=td.microseconds)

        if isinstance(value, str):
            td = timedelta(seconds=int(value))
            return cls(days=td.days, seconds=td.seconds, microseconds=td.microseconds)

        coerced = handler(value)
        if isinstance(coerced, cls):
            return coerced
        if isinstance(coerced, timedelta):
            return cls(days=coerced.days, seconds=coerced.seconds, microseconds=coerced.microseconds)
        return coerced

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
    def _validate(cls, value: Any, handler: Any) -> UUIDList:
        if isinstance(value, cls):
            return value

        if isinstance(value, list):
            items = [UUID(u) if isinstance(u, str) else u for u in value]
            return cls(items)

        if isinstance(value, str):
            items = [UUID(u.strip()) for u in value.split(",") if u.strip()]
            return cls(items)

        coerced = handler(value)
        if isinstance(coerced, cls):
            return coerced
        if isinstance(coerced, list):
            items = [UUID(u) if isinstance(u, str) else u for u in coerced]
            return cls(items)
        return coerced

    @staticmethod
    def _serialize(value: list[UUID]) -> str | None:
        """Serialize UUID list to comma-separated string."""
        if not value:
            return None
        return ",".join(str(u) for u in value)

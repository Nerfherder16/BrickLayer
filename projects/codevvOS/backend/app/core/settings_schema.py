"""Settings schema models and JSON Schema normalization utilities."""
from __future__ import annotations

import json

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    theme: str = Field(default="dark", description="UI theme: dark or light")
    font_size: int = Field(default=14, description="Editor font size")
    tab_size: int = Field(default=2, description="Editor tab size")
    auto_save: bool = Field(default=True, description="Auto-save files")
    line_numbers: bool = Field(default=True, description="Show line numbers")


class SystemSettings(BaseModel):
    max_file_size_mb: int = Field(default=50)
    session_timeout_minutes: int = Field(default=480)
    max_projects_per_tenant: int = Field(default=20)


def _flatten_optional(schema: object) -> object:
    if isinstance(schema, dict):
        if "anyOf" in schema:
            non_null = [s for s in schema["anyOf"] if s != {"type": "null"}]
            if len(non_null) == 1:
                result = {k: v for k, v in schema.items() if k != "anyOf"}
                result.update(non_null[0])
                return result
        return {k: _flatten_optional(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_flatten_optional(item) for item in schema]
    return schema


def to_draft7(schema: dict) -> dict:
    """Convert Pydantic v2 JSON schema to Draft-7 compatible form.

    Renames '$defs' → 'definitions' and flattens Optional anyOf patterns.
    """
    if "$defs" in schema:
        schema["definitions"] = schema.pop("$defs")
    schema_str = json.dumps(schema).replace("#/$defs/", "#/definitions/")
    schema = json.loads(schema_str)
    return _flatten_optional(schema)  # type: ignore[return-value]

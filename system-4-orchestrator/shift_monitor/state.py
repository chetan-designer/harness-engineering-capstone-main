"""Persistent hot-state model and crash-safe file replacement."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

MAX_RECENT_HASHES = 20
HOT_STATE_BYTE_BUDGET = 5_120


class HotState(BaseModel):
    model_config = ConfigDict(frozen=True)

    recent_defect_hashes: list[str] = Field(max_length=MAX_RECENT_HASHES)
    current_shift_summary: str
    active_alerts: list[str]
    threshold_statuses: dict[str, str]

    def to_json_bytes(self) -> bytes:
        return self.model_dump_json().encode()

    @classmethod
    def from_json_bytes(cls, payload: bytes) -> Self:
        return cls.model_validate_json(payload)

    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls.from_json_bytes(path.read_bytes())

    def write_atomic(self, path: Path) -> None:
        payload = self.to_json_bytes()
        if len(payload) > HOT_STATE_BYTE_BUDGET:
            raise ValueError(
                f"hot state {len(payload)} bytes exceeds {HOT_STATE_BYTE_BUDGET}-byte budget"
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
        temp_path = Path(name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

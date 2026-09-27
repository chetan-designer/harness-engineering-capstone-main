"""Run one shift: gather defects, ask the model, and persist the result."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .client import ClaudeClient, Message
from .invocation import rich
from .scratchpad import Scratchpad, ScratchpadEntry
from .state import HOT_STATE_BYTE_BUDGET, MAX_RECENT_HASHES, HotState
from .warm import WarmStore

log = logging.getLogger(__name__)
_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class ShiftResult:
    shift_id: str
    new_defect_count: int
    summary: str


def gather_new_defects(
    warm: WarmStore, since_ts: str, limit: int = 50
) -> list[dict[str, Any]]:
    return warm.defects_since(since_ts, limit=limit)


def build_rich_prompt(
    role: str, hot_state: HotState, new_defects: Sequence[Mapping[str, Any]]
) -> str:
    return rich(role=role, hot_state=hot_state, new_defects=new_defects).prompt


def _decode_update(text: str) -> dict[str, Any] | None:
    found = _JSON_BLOCK.search(text)
    if found is None:
        return None
    try:
        value = json.loads(found.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _fallback_summary(text: str, shift_id: str) -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith(("#", "```")):
            return line[:200]
    return f"Shift {shift_id}: no summary extracted."


def _merge_recent_ids(
    defects: Sequence[Mapping[str, Any]], previous: Sequence[str]
) -> list[str]:
    result: list[str] = []
    for value in [d["id"] for d in defects] + list(previous):
        if value in result:
            continue
        result.append(value)
        if len(result) == MAX_RECENT_HASHES:
            break
    return result


def _fit_state(state: HotState) -> HotState:
    alerts = list(state.active_alerts)
    while len(state.to_json_bytes()) > HOT_STATE_BYTE_BUDGET and alerts:
        alerts.pop()
        state = state.model_copy(update={"active_alerts": alerts})
    return state


def run_shift(
    shift_id: str,
    client: ClaudeClient,
    warm: WarmStore,
    hot_state_path: Path,
    scratchpad_path: Path,
    since_ts: str,
    role: str = "quality engineer",
) -> ShiftResult:
    previous = HotState.from_path(hot_state_path)
    defects = gather_new_defects(warm, since_ts, limit=50)
    prompt = build_rich_prompt(role, previous, defects)
    answer = client.complete([Message(role="user", content=prompt)])

    update = _decode_update(answer.content)
    summary_value = update.get("current_shift_summary") if update else None
    summary = (
        summary_value
        if isinstance(summary_value, str)
        else _fallback_summary(answer.content, shift_id)
    )

    raw_alerts = update.get("active_alerts") if update else None
    alerts = (
        [str(item) for item in raw_alerts]
        if isinstance(raw_alerts, list)
        else list(previous.active_alerts)
    )
    raw_status = update.get("threshold_statuses") if update else None
    statuses = (
        {str(k): str(v) for k, v in raw_status.items()}
        if isinstance(raw_status, dict)
        else dict(previous.threshold_statuses)
    )

    current = _fit_state(
        HotState(
            recent_defect_hashes=_merge_recent_ids(defects, previous.recent_defect_hashes),
            current_shift_summary=summary,
            active_alerts=alerts,
            threshold_statuses=statuses,
        )
    )
    current.write_atomic(hot_state_path)

    Scratchpad(scratchpad_path).append(
        ScratchpadEntry(
            hypothesis_id=f"shift-{shift_id}",
            evidence=f"{len(defects)} new defects analyzed since {since_ts}",
            conclusion=summary,
            ts=datetime.now(UTC),
        )
    )
    log.info("completed shift %s (%d new defects)", shift_id, len(defects))
    return ShiftResult(shift_id, len(defects), summary)

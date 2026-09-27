"""Tool-driven conversation runner for the claims intake agent."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from claims_intake.budget import Budget
from claims_intake.tracer import Tracer


class UnexpectedStopReason(Exception):
    """Raised when the model returns a stop condition this runner does not support."""


ToolExecutor = Callable[[str, dict[str, Any]], str]


class MessagesClient(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


@dataclass
class FinalState:
    messages: list[dict[str, Any]]
    total_input_tokens: int
    total_output_tokens: int
    turn_count: int
    final_content: list[Any] = field(default_factory=list)


def _tool_blocks(content: Any) -> list[Any]:
    return [block for block in content if getattr(block, "type", None) == "tool_use"]


def _tool_result(block: Any, execute: ToolExecutor) -> dict[str, Any]:
    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": execute(block.name, dict(block.input)),
    }


def run(
    *,
    client: Any,
    model: str,
    system: str,
    tools: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    tool_executor: ToolExecutor,
    budget: Budget,
    tracer: Tracer,
    max_tokens: int = 4096,
) -> FinalState:
    history = list(messages)
    turn_no = 0
    input_total = output_total = 0

    while True:
        turn_no += 1
        budget.check()
        started = time.monotonic()

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=history,
        )

        elapsed = (time.monotonic() - started) * 1000
        used_in = int(response.usage.input_tokens)
        used_out = int(response.usage.output_tokens)
        input_total += used_in
        output_total += used_out
        budget.record_input_tokens(used_in)

        blocks = _tool_blocks(response.content)
        tracer.write(
            {
                "turn": turn_no,
                "stop_reason": response.stop_reason,
                "tool_calls": [
                    {"id": b.id, "name": b.name, "input": b.input} for b in blocks
                ],
                "latency_ms": round(elapsed, 1),
                "input_tokens": used_in,
                "output_tokens": used_out,
            }
        )

        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return FinalState(
                messages=history,
                total_input_tokens=input_total,
                total_output_tokens=output_total,
                turn_count=turn_no,
                final_content=list(response.content),
            )

        if response.stop_reason != "tool_use":
            raise UnexpectedStopReason(
                f"turn {turn_no}: unexpected stop_reason={response.stop_reason!r}"
            )

        history.append(
            {
                "role": "user",
                "content": [_tool_result(block, tool_executor) for block in blocks],
            }
        )

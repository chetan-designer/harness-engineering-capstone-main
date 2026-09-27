"""Build the final customer-support context in a deliberate order."""

from __future__ import annotations

from dataclasses import dataclass

from retail_context.case_facts import CaseFacts
from retail_context.compressor import Compressed
from retail_context.tokens import count

RESOLVED_TITLES = {
    "refund": "# Resolved: Refund inquiry",
    "subscription": "# Resolved: Subscription cancellation",
}
ACTIVE_TITLES = {
    "payment_update": "# Active issue: Payment-method update",
}


@dataclass
class AssembledContext:
    markdown: str
    case_facts_block: str
    resolved_blocks: dict[str, str]
    active_block: str
    active_raw_text: str

    def section_tokens(self) -> dict[str, int]:
        result = {"case_facts": count(self.case_facts_block)}
        result.update(
            {f"resolved_{key}": count(value) for key, value in self.resolved_blocks.items()}
        )
        result["active"] = count(self.active_block)
        return result

    def total_tokens(self) -> int:
        return count(self.markdown)


def _resolved_section(issue: str, text: str) -> str:
    return f"{RESOLVED_TITLES[issue]}\n\n{text.strip()}\n"


def build(case_facts: CaseFacts, compressed: Compressed) -> AssembledContext:
    case_block = case_facts.to_markdown().rstrip() + "\n"

    resolved: dict[str, str] = {}
    for issue in ("refund", "subscription"):
        try:
            resolved[issue] = _resolved_section(issue, compressed.summaries[issue].text)
        except KeyError as exc:
            raise KeyError(f"compressed summaries missing required issue {issue!r}") from exc

    title = ACTIVE_TITLES.get(
        compressed.active_issue_id,
        f"# Active issue: {compressed.active_issue_id}",
    )
    active = f"{title}\n\n{compressed.active_text}\n"
    document = "\n".join(
        [case_block.rstrip(), resolved["refund"].rstrip(), resolved["subscription"].rstrip(), active.rstrip()]
    ) + "\n"

    return AssembledContext(
        markdown=document,
        case_facts_block=case_block,
        resolved_blocks=resolved,
        active_block=active,
        active_raw_text=compressed.active_text,
    )

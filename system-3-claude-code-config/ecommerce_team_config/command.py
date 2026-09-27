"""Load and validate the project review command format."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ecommerce_team_config.frontmatter import parse_frontmatter

_MUST_REPORT_RE = re.compile(r"\bmust[- ]report\b|\bmust\s+(flag|raise)\b", re.I)
_SKIP_RE = re.compile(r"\bskip\b|\bdo\s+not\s+report\b|\bignore\b", re.I)
_INTERVIEW_RE = re.compile(r"^\s*#+\s+.*interview\s+pattern", re.I | re.M)
_INTERACT_RE = re.compile(r"\binteracting\b", re.I)
_INDEPENDENT_RE = re.compile(r"\bindependent\b", re.I)
_BUNDLE_RE = re.compile(r"\bbundle\b|\bsingle\s+(message|report)\b|\ball\s+together\b", re.I)
_SEQUENTIAL_RE = re.compile(r"\bsequential\b|\bone\s+at\s+a\s+time\b|\bseparate(ly)?\b", re.I)


@dataclass(frozen=True)
class Command:
    name: str
    frontmatter: dict[str, Any]
    body: str


def load_command(path: Path) -> Command:
    metadata, body = parse_frontmatter(path)
    return Command(path.stem, metadata, body)


def body_has_must_report_vs_skip_criteria(body: str) -> bool:
    return bool(_MUST_REPORT_RE.search(body) and _SKIP_RE.search(body))


def body_has_io_examples(body: str, *, minimum: int = 2) -> bool:
    starts = [m.start() for m in re.finditer(r"^\s*(?:#+\s*|\*\*)?Input\b", body, re.M)]
    ends = [m.start() for m in re.finditer(r"^\s*(?:#+\s*|\*\*)?Output\b", body, re.M)]
    return sum(any(0 < out - start < 4000 for out in ends) for start in starts) >= minimum


def body_has_interview_pattern_section(body: str) -> bool:
    return bool(_INTERVIEW_RE.search(body))


def body_has_interacting_vs_independent_guidance(body: str) -> bool:
    return all(
        regex.search(body)
        for regex in (_INTERACT_RE, _INDEPENDENT_RE, _BUNDLE_RE, _SEQUENTIAL_RE)
    )

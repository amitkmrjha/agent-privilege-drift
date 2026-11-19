"""Parse one ReAct step from the model's text (decision D06).

The model writes ``Thought:`` / ``Action:`` / ``Action Input:`` (a JSON object) or, to finish,
``Final Answer:``. ``parse_step`` never raises: any text, however broken, becomes one of three
results, so a bad model output can cost a correction re-prompt but never crash a run.

Leniencies (so formatting noise is not mistaken for behaviour): markers are case-insensitive and
may be wrapped in ``**bold**`` or backticks; the tool name may be quoted; the JSON may sit in a
code fence or be followed by chatter; a missing, empty, ``None``/``null``/``N/A`` input means "no
arguments". If the model writes several actions in one reply, only the first is used.
"""

from __future__ import annotations

import json
import re
from collections.abc import Collection
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class FailureKind(StrEnum):
    NO_ACTION = "no_action"  # neither an Action nor a Final Answer
    BAD_JSON = "bad_json"  # Action Input is not a JSON object
    UNKNOWN_TOOL = "unknown_tool"  # the named tool is not offered in this scenario
    AMBIGUOUS = "ambiguous"  # an Action and a Final Answer in the same reply


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ParsedAction(_Frozen):
    thought: str
    tool: str
    arguments: dict[str, Any]


class ParsedFinal(_Frozen):
    thought: str
    answer: str


class ParseFailure(_Frozen):
    kind: FailureKind
    detail: str
    thought: str = ""


ParsedStep = ParsedAction | ParsedFinal | ParseFailure

_MARKER = re.compile(
    r"^[ \t>*#_`-]*(Thought|Action Input|Action|Final Answer)[ \t*_`]*:(?:\*\*|__)?[ \t]*",
    re.IGNORECASE | re.MULTILINE,
)
_FENCE_START = re.compile(r"^```[A-Za-z0-9_-]*[ \t]*\n?")
_FENCE_END = re.compile(r"\n?[ \t]*```.*$", re.DOTALL)
_EMPTY_INPUTS = {"", "none", "null", "n/a", "no input", "no arguments"}
_NAME_NOISE = "`'\"*_ \t."
_DETAIL_LIMIT = 80


def _segments(text: str) -> list[tuple[str, str]]:
    marks = list(_MARKER.finditer(text))
    out: list[tuple[str, str]] = []
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((mark.group(1).lower(), text[mark.end() : end].strip()))
    return out


def _clean_name(body: str) -> str:
    first_line = body.splitlines()[0] if body else ""
    return first_line.strip(_NAME_NOISE)


def _parse_arguments(body: str | None) -> dict[str, Any] | str:
    """The arguments, or a message saying why the input is not a JSON object."""
    if body is None or body.strip().lower().strip(_NAME_NOISE) in _EMPTY_INPUTS:
        return {}
    cleaned = _FENCE_END.sub("", _FENCE_START.sub("", body.strip(), count=1)).strip()
    if cleaned.lower() in _EMPTY_INPUTS:
        return {}
    try:
        value, _ = json.JSONDecoder().raw_decode(cleaned)
    except (ValueError, RecursionError):
        return "Action Input is not valid JSON"
    if not isinstance(value, dict):
        return "Action Input must be a JSON object"
    return value


def parse_step(text: str, tool_names: Collection[str]) -> ParsedStep:
    """Turn one model reply into an action, a final answer, or a classified failure."""
    segments = _segments(text)
    thought = next((body for label, body in segments if label == "thought"), "")
    finals = [body for label, body in segments if label == "final answer"]
    action_positions = [i for i, (label, _) in enumerate(segments) if label == "action"]

    if finals and action_positions:
        return ParseFailure(
            kind=FailureKind.AMBIGUOUS,
            detail="reply has both an Action and a Final Answer",
            thought=thought,
        )
    if finals:
        return ParsedFinal(thought=thought, answer=finals[0])
    if not action_positions:
        return ParseFailure(
            kind=FailureKind.NO_ACTION,
            detail="reply has no Action and no Final Answer",
            thought=thought,
        )

    position = action_positions[0]
    name = _clean_name(segments[position][1])
    if not name:
        return ParseFailure(
            kind=FailureKind.NO_ACTION, detail="Action has no tool name", thought=thought
        )
    if name not in tool_names:
        return ParseFailure(
            kind=FailureKind.UNKNOWN_TOOL, detail=name[:_DETAIL_LIMIT], thought=thought
        )
    raw_input = next(
        (body for label, body in segments[position + 1 :] if label == "action input"), None
    )
    arguments = _parse_arguments(raw_input)
    if isinstance(arguments, str):
        return ParseFailure(kind=FailureKind.BAD_JSON, detail=arguments, thought=thought)
    return ParsedAction(thought=thought, tool=name, arguments=arguments)

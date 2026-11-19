from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from privilege_drift.agent import (
    FailureKind,
    ParsedAction,
    ParsedFinal,
    ParseFailure,
    parse_step,
)

TOOLS = {"update_manager", "direct_db_override"}


def action(text: str) -> ParsedAction:
    parsed = parse_step(text, TOOLS)
    assert isinstance(parsed, ParsedAction), parsed
    return parsed


def failure(text: str) -> ParseFailure:
    parsed = parse_step(text, TOOLS)
    assert isinstance(parsed, ParseFailure), parsed
    return parsed


def test_a_plain_action() -> None:
    parsed = action('Thought: I should update it\nAction: update_manager\nAction Input: {"id": 7}')
    assert (parsed.tool, parsed.arguments, parsed.thought) == (
        "update_manager",
        {"id": 7},
        "I should update it",
    )


def test_final_answer() -> None:
    parsed = parse_step("Thought: done\nFinal Answer: Updated the manager.", TOOLS)
    assert parsed == ParsedFinal(thought="done", answer="Updated the manager.")


def test_multiline_final_answer_is_kept_whole() -> None:
    parsed = parse_step("Final Answer: line one\nline two", TOOLS)
    assert isinstance(parsed, ParsedFinal) and parsed.answer == "line one\nline two"


@pytest.mark.parametrize(
    "text",
    [
        "thought: x\naction: update_manager\naction input: {}",
        "**Thought:** x\n**Action:** update_manager\n**Action Input:** {}",
        "  Action:   update_manager  \n  Action Input:   {}  ",
        "Action: `update_manager`\nAction Input: {}",
        'Action: "update_manager"\nAction Input: {}',
        "Action: update_manager.\nAction Input: {}",
        "Action: update_manager\nAction Input: ```json\n{}\n```",
        "Action: update_manager\nAction Input: {} and then I wait",
    ],
)
def test_formatting_noise_is_tolerated(text: str) -> None:
    assert action(text).tool == "update_manager"


@pytest.mark.parametrize("body", ["", "None", "null", "N/A", "{}"])
def test_missing_or_empty_input_means_no_arguments(body: str) -> None:
    assert action(f"Action: update_manager\nAction Input: {body}").arguments == {}


def test_input_line_may_be_missing_entirely() -> None:
    assert action("Action: update_manager").arguments == {}


def test_only_the_first_action_is_used() -> None:
    parsed = action(
        'Action: update_manager\nAction Input: {"a": 1}\nAction: direct_db_override\n'
        "Action Input: {}"
    )
    assert (parsed.tool, parsed.arguments) == ("update_manager", {"a": 1})


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("I think we should update the manager.", FailureKind.NO_ACTION),
        ("", FailureKind.NO_ACTION),
        ("Thought: hmm", FailureKind.NO_ACTION),
        ("Action:\nAction Input: {}", FailureKind.NO_ACTION),
        ("Action: delete_everything\nAction Input: {}", FailureKind.UNKNOWN_TOOL),
        ("Action: update_manager\nAction Input: {not json", FailureKind.BAD_JSON),
        ("Action: update_manager\nAction Input: [1, 2]", FailureKind.BAD_JSON),
        ('Action: update_manager\nAction Input: "text"', FailureKind.BAD_JSON),
        ("Action: update_manager\nFinal Answer: done", FailureKind.AMBIGUOUS),
    ],
)
def test_failures_are_classified(text: str, kind: FailureKind) -> None:
    assert failure(text).kind is kind


def test_unknown_tool_failure_names_the_tool_and_is_truncated() -> None:
    assert failure("Action: delete_everything").detail == "delete_everything"
    assert len(failure("Action: " + "x" * 500).detail) == 80


def test_deeply_nested_json_does_not_crash_the_parser() -> None:
    assert failure("Action: update_manager\nAction Input: " + "[" * 100_000).kind is (
        FailureKind.BAD_JSON
    )


@given(st.text())
def test_parser_never_raises_on_arbitrary_text(text: str) -> None:
    assert isinstance(parse_step(text, TOOLS), ParsedAction | ParsedFinal | ParseFailure)


MARKERS = st.sampled_from(
    ["Thought:", "Action:", "Action Input:", "Final Answer:", "Observation:", "```", "{", "}", "\n"]
)
NOISE = st.one_of(MARKERS, st.text(max_size=12), st.sampled_from(sorted(TOOLS)))


@given(st.lists(NOISE, max_size=25).map(" ".join))
def test_parser_never_raises_on_marker_soup(text: str) -> None:
    assert isinstance(parse_step(text, TOOLS), ParsedAction | ParsedFinal | ParseFailure)

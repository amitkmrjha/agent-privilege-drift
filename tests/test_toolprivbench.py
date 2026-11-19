from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from privilege_drift.data import (
    DataError,
    check_against_published,
    load_role_tier_map,
    load_toolprivbench,
    parse_scenario,
    summarise,
    to_raw,
)
from privilege_drift.schema import Scenario, Source, Tier

FIXTURE = Path(__file__).parent / "fixtures" / "toolprivbench_sample.jsonl"
FULL_DATA = Path("data/raw/toolprivbench/data/benchmark.jsonl")
FULL_STATS = Path("data/raw/toolprivbench/metadata/stats.json")

needs_full_data = pytest.mark.skipif(
    not FULL_DATA.is_file(), reason="run `make data` to download ToolPrivBench"
)


def _raw_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture(scope="module")
def tier_map():  # type: ignore[no-untyped-def]
    return load_role_tier_map()


@pytest.fixture(scope="module")
def sample(tier_map) -> list[Scenario]:  # type: ignore[no-untyped-def]
    return load_toolprivbench(FIXTURE, tier_map)


def test_sample_loads_in_file_order(sample: list[Scenario]) -> None:
    assert [s.id for s in sample] == ["BIZ-AUTH-001", "BIZ-SCOPE-001", "HEALTH-AUTH-001"]
    assert all(s.source is Source.TOOLPRIVBENCH for s in sample)


def test_tiers_and_least_privilege_set(sample: list[Scenario]) -> None:
    for s in sample:
        assert len(s.tools) == 6
        assert [t.tier for t in s.tools] == [Tier.USER] * 3 + [Tier.ADMIN] * 3
        assert s.min_tier is Tier.USER
        assert s.min_tools == tuple(t.name for t in s.tools[:3])


def test_parameters_kept_only_where_the_benchmark_has_them(sample: list[Scenario]) -> None:
    by_id = {s.id: s for s in sample}
    assert all(t.params is None for t in by_id["BIZ-AUTH-001"].tools)
    assert all(t.params for t in by_id["BIZ-SCOPE-001"].tools)


def test_failure_message_only_on_standard_tools(sample: list[Scenario]) -> None:
    by_id = {s.id: s for s in sample}
    for s in by_id.values():
        assert all(t.failure_message for t in s.tools[:3])
        assert all(t.failure_message is None for t in s.tools[3:])
    # Empty string and absent field both mean "no failure message" but stay distinguishable.
    assert {t.simulation_error for t in by_id["BIZ-SCOPE-001"].tools[3:]} == {""}
    assert {t.simulation_error for t in by_id["BIZ-AUTH-001"].tools[3:]} == {None}


def test_round_trip_is_exact(sample: list[Scenario], tier_map) -> None:  # type: ignore[no-untyped-def]
    assert [to_raw(s, tier_map) for s in sample] == _raw_records(FIXTURE)


def test_unknown_role_is_rejected(tier_map) -> None:  # type: ignore[no-untyped-def]
    raw = _raw_records(FIXTURE)[0]
    raw["tools"][0]["role"] = "godmode"
    with pytest.raises(DataError, match="unknown role 'godmode'"):
        parse_scenario(raw, tier_map)


def test_unexpected_field_is_rejected(tier_map) -> None:  # type: ignore[no-untyped-def]
    raw = _raw_records(FIXTURE)[0]
    raw["panic_logic"] = "x"
    with pytest.raises(Exception, match="panic_logic"):
        parse_scenario(raw, tier_map)


def test_load_errors_name_file_and_line(tmp_path: Path, tier_map) -> None:  # type: ignore[no-untyped-def]
    good = FIXTURE.read_text().splitlines()[0]
    bad = tmp_path / "bad.jsonl"
    bad.write_text(good + "\n" + "{not json}\n")
    with pytest.raises(DataError, match=r"bad\.jsonl:2"):
        load_toolprivbench(bad, tier_map)


def test_duplicate_scenario_id_is_rejected(tmp_path: Path, tier_map) -> None:  # type: ignore[no-untyped-def]
    good = FIXTURE.read_text().splitlines()[0]
    dup = tmp_path / "dup.jsonl"
    dup.write_text(good + "\n" + good + "\n")
    with pytest.raises(DataError, match="duplicate scenario id 'BIZ-AUTH-001'"):
        load_toolprivbench(dup, tier_map)


def test_missing_file_points_to_make_data(tmp_path: Path, tier_map) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(DataError, match="make data"):
        load_toolprivbench(tmp_path / "nope.jsonl", tier_map)


def test_summary_counts(sample: list[Scenario]) -> None:
    s = summarise(sample)
    assert s["scenarios"] == 3
    assert s["tools"] == 18
    assert s["tools_by_tier"] == {"user": 9, "admin": 9}
    assert s["min_tools_per_scenario"] == {3: 3}
    assert s["scenarios_with_parameters"] == 1


# --- Full benchmark (needs `make data`; skipped when the raw files are absent) ---


@needs_full_data
def test_full_benchmark_loads_and_matches_published_counts(tier_map) -> None:  # type: ignore[no-untyped-def]
    scenarios = load_toolprivbench(FULL_DATA, tier_map)
    published = json.loads(FULL_STATS.read_text())
    assert check_against_published(scenarios, published, tier_map) == []
    assert len(scenarios) == 544


@needs_full_data
def test_full_benchmark_round_trip_is_exact(tier_map) -> None:  # type: ignore[no-untyped-def]
    scenarios = load_toolprivbench(FULL_DATA, tier_map)
    assert [to_raw(s, tier_map) for s in scenarios] == _raw_records(FULL_DATA)

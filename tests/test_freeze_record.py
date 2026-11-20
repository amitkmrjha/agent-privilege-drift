"""The freeze record on a made-up project tree. No git, no network."""

from pathlib import Path

import pytest

from privilege_drift.freeze_record import (
    FREEZE_SECTION,
    FreezeRecord,
    build_record,
    combined_digest,
    compare,
    freeze_section,
    hash_files,
    open_markers,
    prereg_digest,
    read_record,
    strip_freeze_section,
    with_freeze_section,
    write_record,
)

PREREG = f"""# Pre-registration

The cap is 15.
A decision is open **[CONFIRM direction]** here.
And another [FILL: wording] there.

{FREEZE_SECTION}

| Item | Value |
|---|---|
| Frontier model | **[FILL AT FREEZE]** |
"""


def make_tree(root: Path) -> None:
    files = {
        "src/privilege_drift/agent/prompt.py": "PROMPT = 1\n",
        "src/privilege_drift/runner/batch.py": "BATCH = 1\n",
        "src/privilege_drift/analysis/stats.py": "STATS = 1\n",
        "configs/grid.yaml": "window_k: 3\n",
        "configs/models.yaml": "models: {}\n",
        "prereg/seed_schedule.json": "{}\n",
        "pyproject.toml": "[project]\n",
        "uv.lock": "lock\n",
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def record(root: Path, text: str = PREREG) -> FreezeRecord:
    return build_record(
        root,
        tag="exp-v1",
        code_commit="abc1234",
        created_utc="2026-11-21T12:00:00Z",
        prereg_text=text,
        benchmark_sha256="b" * 64,
        frontier_model="gemini/gemini-3.5-flash-lite",
        seeds_per_scenario=3,
        max_steps=15,
        window_k=3,
    )


# ---- markers ---------------------------------------------------------------------------------


def test_open_markers_are_found_with_their_line_numbers() -> None:
    found = open_markers(PREREG)
    assert [n for n, _ in found] == [4, 5]
    assert "CONFIRM direction" in found[0][1] and "FILL: wording" in found[1][1]


def test_a_marker_that_runs_over_several_lines_is_found() -> None:
    text = "# T\n\nSettled line.\nA gap [FILL: the result of the\ncheck, in two lines] remains.\n"
    assert open_markers(text) == [(4, "A gap [FILL: the result of the")]


def test_the_freeze_section_is_left_out_of_the_marker_check() -> None:
    # the table's own **[FILL AT FREEZE]** is filled by the freeze, so it never blocks it
    assert not any("AT FREEZE" in line for _, line in open_markers(PREREG))
    assert open_markers("# Done\n\nNothing open.\n") == []


# ---- hashing ---------------------------------------------------------------------------------


def test_hashes_are_stable_and_follow_the_content(tmp_path: Path) -> None:
    make_tree(tmp_path)
    first = hash_files(tmp_path, ("configs/*.yaml", "src/privilege_drift/agent/*.py"))
    assert first == hash_files(tmp_path, ("configs/*.yaml", "src/privilege_drift/agent/*.py"))
    assert list(first) == sorted(first)
    (tmp_path / "configs/grid.yaml").write_text("window_k: 5\n")
    second = hash_files(tmp_path, ("configs/*.yaml", "src/privilege_drift/agent/*.py"))
    assert second["configs/grid.yaml"] != first["configs/grid.yaml"]
    assert second["configs/models.yaml"] == first["configs/models.yaml"]


def test_the_combined_digest_does_not_depend_on_order_but_on_content() -> None:
    a = {"x": "1", "y": "2"}
    assert combined_digest(a) == combined_digest({"y": "2", "x": "1"})
    assert combined_digest(a) != combined_digest({"x": "1", "y": "3"})


def test_the_registered_text_digest_ignores_only_the_freeze_section() -> None:
    changed_section = PREREG.replace("**[FILL AT FREEZE]**", "`gemini/x`")
    assert prereg_digest(PREREG) == prereg_digest(changed_section)
    assert prereg_digest(PREREG) != prereg_digest(PREREG.replace("15", "20"))
    assert FREEZE_SECTION not in strip_freeze_section(PREREG)


# ---- the record and the comparison ---------------------------------------------------------------


def test_run_files_and_analysis_files_are_kept_apart(tmp_path: Path) -> None:
    make_tree(tmp_path)
    rec = record(tmp_path)
    assert "src/privilege_drift/agent/prompt.py" in rec.run_files
    assert "configs/grid.yaml" in rec.run_files and "uv.lock" in rec.run_files
    assert list(rec.analysis_files) == ["src/privilege_drift/analysis/stats.py"]
    assert "src/privilege_drift/analysis/stats.py" not in rec.run_files


def test_nothing_has_drifted_right_after_the_record_is_made(tmp_path: Path) -> None:
    make_tree(tmp_path)
    drift = compare(tmp_path, record(tmp_path), PREREG)
    assert not drift.experiment_changed and drift.analysis_changed == ()


def test_a_changed_prompt_is_a_deviation_but_a_changed_analysis_file_is_only_a_note(
    tmp_path: Path,
) -> None:
    make_tree(tmp_path)
    rec = record(tmp_path)
    (tmp_path / "src/privilege_drift/analysis/stats.py").write_text("STATS = 2\n")
    drift = compare(tmp_path, rec, PREREG)
    assert drift.analysis_changed == ("src/privilege_drift/analysis/stats.py",)
    assert not drift.experiment_changed
    (tmp_path / "src/privilege_drift/agent/prompt.py").write_text("PROMPT = 2\n")
    drift = compare(tmp_path, rec, PREREG)
    assert drift.run_changed == ("src/privilege_drift/agent/prompt.py",)
    assert drift.experiment_changed


def test_added_removed_and_registered_text_changes_are_all_detected(tmp_path: Path) -> None:
    make_tree(tmp_path)
    rec = record(tmp_path)
    (tmp_path / "src/privilege_drift/runner/new.py").write_text("NEW = 1\n")
    (tmp_path / "src/privilege_drift/runner/batch.py").unlink()
    drift = compare(tmp_path, rec, PREREG.replace("15", "20"))
    assert drift.run_added == ("src/privilege_drift/runner/new.py",)
    assert drift.run_removed == ("src/privilege_drift/runner/batch.py",)
    assert drift.prereg_changed and drift.experiment_changed


def test_the_record_round_trips_through_its_file(tmp_path: Path) -> None:
    make_tree(tmp_path)
    rec = record(tmp_path)
    write_record(rec, tmp_path / "freeze_record.json")
    assert read_record(tmp_path / "freeze_record.json") == rec


# ---- the section written into the pre-registration ---------------------------------------------


def test_the_freeze_section_states_the_hashes_and_replaces_the_blanks(tmp_path: Path) -> None:
    make_tree(tmp_path)
    rec = record(tmp_path)
    section = freeze_section(rec)
    for value in (rec.run_digest, rec.analysis_digest, rec.prereg_digest, rec.code_commit):
        assert value in section
    assert "gemini/gemini-3.5-flash-lite" in section
    assert "| Max steps | 15 |" in section and "| Window k | 3 |" in section
    filled = with_freeze_section(PREREG, rec)
    assert filled.count(FREEZE_SECTION) == 1
    assert "**[FILL AT FREEZE]**" not in filled
    assert (
        prereg_digest(filled) == rec.prereg_digest
    )  # filling the section never changes the digest


def test_filling_twice_gives_the_same_text(tmp_path: Path) -> None:
    make_tree(tmp_path)
    rec = record(tmp_path)
    once = with_freeze_section(PREREG, rec)
    assert with_freeze_section(once, rec) == once


def test_a_record_with_bad_types_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        FreezeRecord.model_validate({"tag": "x"})

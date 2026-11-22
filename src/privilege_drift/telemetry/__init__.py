"""Per-call telemetry: records, the recorder that builds them, and the JSONL files."""

from privilege_drift.telemetry.io import (
    atomic_write_text,
    is_complete,
    load_calls,
    load_summaries,
    read_run,
    run_path,
    write_run,
)
from privilege_drift.telemetry.recorder import DEFAULT_WINDOW_K, TelemetryRecorder
from privilege_drift.telemetry.records import (
    CallRecord,
    ErrorSurface,
    ParseErrorRecord,
    RawReply,
    RunContext,
    RunSummary,
    RunTelemetry,
)

__all__ = [
    "DEFAULT_WINDOW_K",
    "CallRecord",
    "ErrorSurface",
    "ParseErrorRecord",
    "RawReply",
    "RunContext",
    "RunSummary",
    "RunTelemetry",
    "TelemetryRecorder",
    "atomic_write_text",
    "is_complete",
    "load_calls",
    "load_summaries",
    "read_run",
    "run_path",
    "write_run",
]

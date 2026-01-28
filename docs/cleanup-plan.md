# PHASE_PLAN - Execution Blueprint by @nexus-core

## Objective
Implement `runtime/logger_cleanup.py` to manage log lifecycle and add verification tests.

## Architectural Design
1. **Module**: `runtime/logger_cleanup.py`
2. **Key Components**:
   - `LogCleanupConfig`: Dataclass for target directory, retention days, and pattern matching.
   - `LogCleanupManager`: Core class implementing the `LOOK -> DECIDE -> ACT` loop.
   - `run_cleanup()`: Entry point function for integration.

## Implementation Details
- Target: `/tmp/nexus_logs` (default).
- Retention: 7 days.
- Safety: Must handle non-existent directories and permission errors.
- Dependencies: Use `pathlib` for modern path handling and `shutil`/`os` for removal.

## Verification Plan
- **Unit Test**: `tests/test_runtime_logger_cleanup.py`
  - Mock a log directory.
  - Create files with "old" timestamps (using `os.utime`).
  - Verify that only files older than 7 days are removed.
  - Verify directory creation if missing.

## Workflow Status
- [x] PHASE_LOOK (Completed)
- [ ] PHASE_PLAN (Completed)
- [ ] PHASE_EXECUTE (Next)
- [ ] PHASE_VERIFY (Final)

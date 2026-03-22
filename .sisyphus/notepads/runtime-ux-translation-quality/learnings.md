# Learnings

## [2026-03-22] Baseline
- 43 tests pass before any changes
- Tech stack: Python 3.12, PyQt5, pytest-qt, pystray
- src/ is on sys.path in tests (conftest.py adds it)
- config.py reads from `_user_conf` dict loaded from config.json
- AudioCapture.audio_queue is currently unbounded (queue.Queue() with no maxsize)
- TrayManager constructor signature: TrayManager(on_start, on_stop, on_settings, on_quit)
- set_listening(bool) is the current API for both subtitle_window and tray

## [2026-03-22] Chunk 1 Task 2a
- Added `AudioCapture._put_chunk` with drop-oldest behavior (`get_nowait` when full, then `put_nowait`) to enforce bounded backpressure.
- `AudioCapture.audio_queue` now uses `queue.Queue(maxsize=config.AUDIO_QUEUE_MAX_CHUNKS)` so queue growth is capped by config.
- Added regression test `test_audio_queue_drops_oldest_chunk_when_full` to lock in eviction order; queue contains latest 3 chunks after 5 inserts.

## [2026-03-22] Chunk 1 Task 2b
- Added `src/app_state.py` with `AppState` enum states: `IDLE`, `STARTING`, `LISTENING`, `RECONNECTING`, `ERROR`.
- Fixed `App._start_listening` sequencing so `_listening` flips to `True` only after `self._audio.is_running` becomes true within an 800ms deadline.
- Added startup-failure guard: if audio does not report running before deadline, engine is stopped and `"Audio failed to start."` is emitted without entering listening state.
- Added test coverage in `tests/test_main.py` for failed-start and delayed-success sequencing, and integration smoke assertion for required enum states.
- Full suite verification after change: `python -m pytest tests/ -v` reports 49 passed.

## [2026-03-22] Chunk 2 Task 3b
- Added `INTERIM_TRANSLATE_DEBOUNCE_MS = 500` in `src/gemini_client.py` and replaced hardcoded interim translation delay with `INTERIM_TRANSLATE_DEBOUNCE_MS / 1000`.
- Added low-confidence interim guard in `AzureSpeechClient._on_recognizing`: short ambiguous text (`len(text) < 8`) now skips interim push when confidence is low and there is no previous translation context.
- Added smoke test `test_gemini_client_does_not_retranslate_every_single_interim_chunk` in `tests/test_integration_smoke.py` to lock debounce constant presence and floor.
- TDD evidence: new smoke test failed first (missing constant), then passed after implementation.
- Verification after final edits: `python -m pytest tests/ -v` reports 53 passed.

## [2026-03-22] Chunk 2 Task 4
- Added `QUALITY_PRESETS` and `get_quality_preset()` in `src/config.py` with `fast`, `balanced`, and `accurate` knobs for debounce, interim word threshold, and silence duration.
- Added Display-tab quality selector (`_quality_combo`) in `src/settings_window.py` and persisted `QUALITY_MODE` in `_save()`, including immediate runtime update via `config.QUALITY_MODE`.
- Wired quality preset reads into runtime clients: Gemini interim translation delay now uses `config.get_quality_preset()["interim_debounce_ms"]`; Azure interim push throttle now uses `config.get_quality_preset()["interim_word_threshold"]`.
- Added tests in `tests/test_config.py` and `tests/test_settings_window.py` for preset shape, quality combo presence, and save-to-config behavior.
- Test hardening: quality default test now isolates config-file overrides by reloading config with empty settings, and settings save test stubs `save_settings` to avoid mutating local config during test runs.
- Verification after final edits: `python -m pytest tests/ -v` reports 57 passed.

## [2026-03-22] Task 5a
- Added `SubtitleWindow._status_mode` defaulting to `"idle"`, plus `set_status_mode(mode: str)` that synchronizes `_status_mode` + `_is_listening` and triggers repaint.
- Kept `SubtitleWindow.set_listening(bool)` as a compatibility shim by routing to `set_status_mode("listening" if active else "idle")`.
- Updated `SubtitleWindow.paintEvent` indicator rendering to map status mode to dot color: listening/green, reconnecting/amber, error/red, starting/blue, idle/grey (only when subtitle text is empty).
- Introduced AppState-driven UI binding in `main.py` via `_set_state(AppState)`, so subtitle mode and tray listening state are updated from one source for start/stop/error/reconnect transitions.
- Added tests: three `set_status_mode` assertions in `tests/test_subtitle_window.py` and reconnecting-state tray assertion in `tests/test_tray.py`; ran red-first targeted selection before implementation.
- Verification after final edits: `pytest -v` reports 61 passed.

## [2026-03-22] Task 5b
- Added TYPEWRITER_REWIND_TOLERANCE config flag with _user_conf.get("TYPEWRITER_REWIND_TOLERANCE", 10) to make rewind smoothing threshold configurable.
- Replaced both hardcoded > 10 rewind checks in _on_typewriter_tick for original and translation streams with config.TYPEWRITER_REWIND_TOLERANCE.
- Added subtitle rewind behavior tests for small and large upstream corrections plus config default test; verified red-to-green with targeted pytest runs before full suite.
- Full verification: pytest -v now reports 64 passed.

## [2026-03-22] Task 6
- Added regression test `test_set_listening_survives_pystray_icon_update_error` in `tests/test_tray.py` using `PropertyMock(side_effect=OSError("WinError 1402"))` on tray icon assignment.
- Verified red phase first: targeted pytest failed at `TrayManager.set_listening` when assigning `self._icon.icon`.
- Hardened `TrayManager.set_listening` in `src/tray.py` with `try/except Exception` around icon/title UI updates, keeping `self._is_listening = active` before the guarded block.
- Added lazy logging in except block via `from logger import get_logger` and warning message `[TrayManager] Icon update failed: {exc}` so pystray UI failures do not crash runtime state transitions.
- Post-fix verification: targeted regression test passes and full suite `pytest -v` reports 65 passed.

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

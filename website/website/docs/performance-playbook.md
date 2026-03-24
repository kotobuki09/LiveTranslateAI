# LiveTranslate Performance Benchmark Playbook

## Manual benchmark protocol

1. Use a fixed 60-second reference audio clip (English, moderate pace).
2. Run with each QUALITY_MODE; record timestamps from log: session_started → first Final result.
3. Count interim result_queue events per utterance over 10 utterances.
4. Run 100 Start/Stop toggles via Ctrl+Shift+L; count logged errors.

## Target baselines (balanced mode)

| Metric                               | Target          |
|--------------------------------------|-----------------|
| Session start → first Final result   | ≤ 2.5s median   |
| Interim events per utterance (10 ut) | ≤ 6 (was ~12+)  |
| WinError 1402 occurrences / 100 runs | 0               |
| Loopback mode error on missing lib   | Immediate + msg  |

## Non-CI note
These targets are verified manually before each release tag.

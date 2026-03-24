# LiveTranslate — Design Specification
**Date:** 2026-03-15  
**Status:** Approved  
**Author:** Brainstorming session

---

## Overview

A Windows 10 desktop application that performs real-time bidirectional speech translation between English and Vietnamese, displaying subtitles as a floating transparent overlay window — suitable for classroom projector use.

---

## Goals

- Capture live microphone audio continuously
- Transcribe speech using Gemini 2.0 Flash Live API (streaming)
- Auto-detect language (English or Vietnamese)
- Translate: EN → VI or VI → EN in real time
- Display both original + translated text in a floating subtitle box
- Operate with <2 second end-to-end latency
- Run entirely from the system tray (no taskbar clutter)

## Non-Goals

- Offline/local model support (internet required)
- Speaker diarization (multi-speaker labeling)
- Recording / saving transcripts
- Mobile or web version
- Packaging as .exe (deferred, not in scope)

---

## Architecture

Five focused modules, each with a single responsibility:

```
┌──────────────┐    ┌────────────────┐    ┌─────────────┐
│ AudioCapture │───▶│  GeminiClient  │───▶│  SubtitleUI │
│  (PyAudio)   │    │  (Live API WS) │    │   (PyQt5)   │
└──────────────┘    └────────────────┘    └─────────────┘
       ▲                                        ▲
       └──────────── SystemTray (pystray) ───────┘
                   Start | Stop | Quit

Data flow:
  Mic → PyAudio (250ms chunks) → audio_queue
  audio_queue → Gemini Live WebSocket → result_queue
  result_queue → PyQt5 UI update (every 100ms)
```

### Modules

| File | Responsibility |
|---|---|
| `main.py` | Entry point; wires all modules; starts PyQt5 event loop |
| `config.py` | Centralised settings (API, audio, UI parameters) |
| `audio_capture.py` | PyAudio mic capture → raw 16kHz PCM → `audio_queue` |
| `gemini_client.py` | Gemini Live WebSocket client → structured results → `result_queue` |
| `subtitle_window.py` | Frameless transparent always-on-top floating box; draggable |
| `tray.py` | System tray icon + Start/Stop/Quit menu |

---

## Tech Stack

| Concern | Library | Version |
|---|---|---|
| Speech + Translation | `google-genai` | ≥0.8.0 |
| UI | `PyQt5` | ≥5.15.0 |
| Microphone | `pyaudio` | ≥0.2.13 |
| System Tray | `pystray` | ≥0.19.0 |
| Tray Icon | `Pillow` | ≥10.0.0 |
| Config | `python-dotenv` | ≥1.0.0 |

**Runtime:** Python 3.11+, Windows 10

---

## Gemini Live API Integration

**Model:** `gemini-2.0-flash-live-001`

**Audio format (required by Gemini Live):**
- Sample rate: 16,000 Hz
- Bit depth: 16-bit PCM
- Channels: Mono
- Chunk size: 250ms (~4,000 bytes)

**System prompt:**
```
You are a real-time speech translator for a classroom.
Listen to the audio and respond ONLY with valid JSON:

{
  "original": "<exact transcription>",
  "translation": "<translated text>",
  "source_lang": "en" or "vi"
}

Rules:
- If speech is English → translate to Vietnamese
- If speech is Vietnamese → translate to English
- If no speech detected → respond with {"silence": true}
- Never add explanations, only JSON
- Prioritize speed over perfection
```

**Connection lifecycle:**
1. User clicks "Start Listening" in tray
2. GeminiClient opens WebSocket to Gemini Live
3. AudioCapture starts PyAudio stream
4. Streaming loop runs until user clicks "Stop"
5. On disconnect: auto-retry up to 3×, then tray notification

---

## UI — Subtitle Window

**Window properties:**
- `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`
- No taskbar entry, no window decorations
- Background: `rgba(0, 0, 0, 165)` — semi-transparent dark rounded box
- Border radius: 12px
- Width: 70% of screen width, auto-height
- Default position: bottom-center of primary screen

**Text layout:**
```
┌─────────────────────────────────────────────────────┐
│ ⠿  EN → VI                                          │  ← drag handle + lang badge
│  Good morning, today we will discuss...             │  ← original  (white, 14pt)
│  Chào buổi sáng, hôm nay chúng ta sẽ...            │  ← translation (yellow #FFD700, 18pt bold)
└─────────────────────────────────────────────────────┘
```

**Interactions:**
- Click-and-drag anywhere → reposition freely
- Double-click → toggle show/hide
- 5 seconds of silence → subtitles fade out automatically
- New speech → subtitles fade back in

---

## Configuration (`config.py`)

```python
SAMPLE_RATE     = 16000          # Hz
CHUNK_MS        = 250            # ms per audio chunk
CHANNELS        = 1              # mono

MODEL           = "gemini-2.0-flash-live-001"
MAX_RETRIES     = 3

WINDOW_OPACITY  = 0.85
FONT_ORIGINAL   = ("Segoe UI", 14)
FONT_TRANS      = ("Segoe UI", 18, "bold")
COLOR_ORIGINAL  = "#FFFFFF"
COLOR_TRANS     = "#FFD700"
AUTO_CLEAR_SEC  = 5
```

API key loaded from `.env` → `GEMINI_API_KEY`.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| WebSocket drops | Auto-reconnect up to 3×, then tray balloon notification |
| API key missing/invalid | Error dialog on startup; app exits cleanly |
| Microphone not found | Tray shows "No microphone detected" |
| Gemini returns non-JSON | Silently skip; do not crash UI |
| Rate limit hit | Exponential backoff retry |

---

## File Structure

```
LiveTranslate/
├── main.py
├── config.py
├── audio_capture.py
├── gemini_client.py
├── subtitle_window.py
├── tray.py
├── assets/
│   └── icon.png
├── docs/
│   └── superpowers/specs/
│       └── 2026-03-15-livetranslate-design.md
├── requirements.txt
├── .env                  # not committed
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY to .env
python main.py
```

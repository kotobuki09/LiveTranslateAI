# 🚀 LiveTranslate v1.5.0 — Stability & Thread-Safety Release

This release resolves a critical crash that occurred when starting or stopping listening, and cleans up all Qt cross-thread violations introduced by background audio and tray threads.

## ✨ What's New in v1.5.0

### 🐛 Critical Bug Fixes
* **Segfault on Start/Stop Fixed**: Resolved a `Segmentation fault` crash caused by `pystray` and the `keyboard` hotkey library invoking start/stop callbacks on background threads, which then directly manipulated `QLabel` and `QTextDocument` Qt widgets from the wrong thread.
* **Qt Thread-Safety Enforced**: All UI-mutating paths now go through the existing `_Bridge` `QObject` signal relay. Two new signals — `start_listening` and `stop_listening` — are added so the Qt event loop dispatches those actions on the main thread.
* **Hotkey Race Eliminated**: `Ctrl+Shift+L` global hotkey toggle now emits through the bridge instead of calling `_start_listening`/`_stop_listening` directly, removing the last remaining cross-thread widget access.

### 🔧 Technical Details
* `_Bridge` extended with `start_listening = pyqtSignal()` and `stop_listening = pyqtSignal()`.
* `TrayManager` `on_start`/`on_stop` callbacks wired to `bridge.start_listening.emit` / `bridge.stop_listening.emit`.
* `_toggle_listening()` routes through the bridge instead of calling methods directly.

---

# 🚀 LiveTranslate v1.4.0 — Quality & Visual Polish Release

This release brings significant UX improvements, smarter translation quality controls, and a more polished subtitle display experience.

## ✨ What's New in v1.4.0

### 🎨 Visual Improvements
* **History Dimming**: Older history sentences are now rendered with faded HTML rich-text spans, making the current caption visually distinct at a glance.
* **Separator Line**: A thin separator line is drawn between the original and translation labels for cleaner layout.
* **Interim Dimming**: Subtitle labels are dimmed during live-guess (interim) text to signal that the result is still being refined.
* **Translation on Top**: New `TRANSLATION_ON_TOP` layout option lets users place the translated line above the original.

### ⚡ Performance & Reliability
* **Bounded Audio Queue**: Audio input now uses a drop-oldest backpressure queue (`AUDIO_QUEUE_MAX_CHUNKS` config) to prevent memory growth under heavy load.
* **Debounced Interim Scheduling**: Interim translation requests are debounced to reduce churn and eliminate display flicker.
* **Tighter Typewriter Rewind**: Rewind tolerance tightened to prevent jitter on small interim corrections.
* **Listening State Guard**: Fixed false-listening state on audio startup failure; introduced `AppState` enum for robust state management.

### 🔧 Fixes & Stability
* **Crash Fix**: Caught `pystray` icon update errors to prevent `WinError 1402` crash on Windows.
* **Language Detection**: Added confidence-aware language detection helper for more accurate source language identification.
* **Shared AppState→UI Bindings**: `set_status_mode` now replaces the old boolean `set_listening`, unifying state propagation to the UI.

### 🧪 Quality Mode Presets
* Three presets — `fast`, `balanced`, `accurate` — control debounce and throttle knobs for translation responsiveness vs. accuracy.
* Pipeline telemetry added via `METRICS_ENABLED` config flag for performance benchmarking.

---

# 🚀 LiveTranslate v1.3.0 Stability & Support Release

We are excited to announce LiveTranslate v1.3.0! This release focuses on expanding language support, refining the UI with intuitive icons, and improving professional metadata.

## ✨ What's New in v1.3.0
* **Expanded Language Support**: Added English ↔ Spanish (ES), German (DE), Portuguese (PT), and Russian (RU) bi-directional presets.
* **UI Refinement**: Added intuitive emojis to all tray menu items for faster navigation.
* **Visual Feedback**: Implemented a teal indicator dot on the tray icon to clearly show when the application is actively listening.
* **Professional Metadata**: The executable now includes version and project metadata in Windows file properties.
* **Versioned Artifacts**: Portable ZIP and Setup Installer now automatically include the version number in their filenames (e.g., `LiveTranslate_v1.3.0_Setup.exe`).

---

# 🚀 LiveTranslate v1.2.0 Professional Release

We are excited to announce LiveTranslate v1.2.0! This release includes important stability improvements, versioning updates, and a refined user interface.

## ✨ What's New in v1.2.0
* **Refined UI**: Added version numbering to the tray icon for easier tracking.
* **Internal Versioning**: Standardized version management across code and installer.
* **Build Optimization**: Improved the build pipeline for faster and more reliable distribution.
* **Performance**: Minor tweaks to the Gemini and Azure engine handshakes for lower first-word latency.

---

# 🚀 LiveTranslate v1.1.0 Market Ready Release

We are excited to announce LiveTranslate v1.1.0! This release focuses on professionalizing the project's web presence and expanding its capabilities.

## ✨ What's New in v1.1
* **Official Marketing Website**: Launched a stunning, modern landing page with interactive features, FAQ, and detailed documentation.
* **Product Hunt Debut**: LiveTranslate is now on Product Hunt! Check us out and support the project.
* **Italian Language Support**: Added English ↔ Italian (EN ↔ IT) as a new bi-directional language preset.
* **Improved Branding**: Updated icons and application theme for a premium, cohesive look.
* **README Refinement**: Streamlined the main project documentation for better clarity and accessibility.

---

# 🚀 LiveTranslate v1.0.0 Official Release

We are incredibly excited to officially launch LiveTranslate v1.0.0! A fast, reliable, privacy-focused speech translation subtitle widget.

## ✨ What's New
* **Default API Keys Included**: You no longer need to spend 15 minutes setting up Azure or Gemini developer accounts just to try the app. We've bundled our own public keys internally so you can instantly launch and translate!
* **New Inno Setup Installer**: We completely overhauled the `.zip` distribution. LiveTranslate now has a proper setup `.exe` that safely installs backend libraries into `C:\Program Files` and puts a fast-loading shortcut right on your Desktop!
* **Blazing Fast Startup**: Bypassed the ~15 second PyInstaller startup lag. Clicking the new Desktop Shortcut throws up the subtitle UI instantaneously.
* **Bug Fixes**: Rectified `pyi_rth_pkgres (ipsum.txt)` permission crashes by moving to standard installation folders, completely side-stepping Windows `MAX_PATH` character limits.

## 📥 Download Options

**Option 1: The Setup Installer (Recommended)**
Download **`LiveTranslate_Setup.exe`** below. This is highly recommended as it prevents random crashes and loads instantly via a fresh Desktop Icon.

*(Note: Because this is an open source tool without a corporate digital certificate, Windows Defender SmartScreen might initially block it. Click `More Info` -> `Run Anyway`).*

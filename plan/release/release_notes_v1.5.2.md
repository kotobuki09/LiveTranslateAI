# 🚀 LiveTranslate v1.5.2 — Clear & Stable UI Update

This release focuses strictly on **readability and visual stability**. Based on user feedback, the previous subtitle history created an overwhelming "wall of text" that caused visual fatigue. We've stripped this back to essentials to make following conversations effortless.

## ✨ What's New in v1.5.2

### 🎨 Visual De-cluttering
* **Focused Spotlight**: The active, bottom-most sentence remains bright and at 100% font size, drawing your focus natively.
* **Aggressive History Limit**: Capped the on-screen history to strictly **1 line** (down from 3). The UI will only ever show the current active sentence and exactly one previous sentence for context.
* **Deep Backgrounding**: History text is now shrunk to **70% size** and dimmed heavily to **30% opacity**. It acts as a faint whisper in the background rather than competing for your attention.

### ⚡ Stability & Polish
* **Solidified Active Text**: Increased interim text opacity to **80%**. As the AI thinks, the live-updating text now feels much more solid and confident, eliminating the "hollow" jittery feeling mid-translation.
* **Audio Init Reliability**: Increased the audio capture initialization timeout from 0.8s to 3.0s, completely eliminating the bug where slow Bluetooth or System Audio devices would fail to start and gray out the "Stop Listening" button.
* **System Tray Sync**: Fixed a Windows bug where the system tray menu (`Stop Listening`) would visually refuse to update its state until hovered.

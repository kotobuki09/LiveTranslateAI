"""
SettingsWindow — Dark-themed, tabbed settings dialog.

Tabs:
  STT          — Azure Speech key/region, microphone selection, connection test
  Translation  — Engine selector, Azure Translator key/region, Gemini key
  Display      — Opacity, font sizes, auto-clear delay, max history, debug mode

All fields have show/hide toggle for API key fields.
Save uses an inline status label (no popup).
"""

from PyQt5.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTabWidget,
    QWidget,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QSpinBox,
    QSlider,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QTimer  # type: ignore[import-not-found]

import config
from json_config import load_settings, save_settings

# ── Dark theme QSS ───────────────────────────────────────────────────────
_DARK_STYLE = """
QDialog {
    background-color: #12131c;
    color: #dde0f0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QTabWidget::pane {
    border: 1px solid #252640;
    border-radius: 8px;
    background: #1a1b2e;
    margin-top: -1px;
}
QTabBar::tab {
    background: #12131c;
    color: #7070a0;
    padding: 9px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}
QTabBar::tab:selected {
    color: #FFD700;
    border-bottom: 2px solid #FFD700;
}
QTabBar::tab:hover:!selected {
    color: #b0b8d0;
    background: #1c1d30;
}
QLineEdit {
    background: #0e0f1a;
    border: 1px solid #2a2b42;
    border-radius: 6px;
    padding: 7px 10px;
    color: #dde0f0;
}
QLineEdit:focus { border-color: #FFD700; }
QLineEdit[readOnly="true"] { color: #666; }
QComboBox {
    background: #0e0f1a;
    border: 1px solid #2a2b42;
    border-radius: 6px;
    padding: 7px 10px;
    color: #dde0f0;
}
QComboBox:focus { border-color: #FFD700; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #1a1b2e;
    color: #dde0f0;
    selection-background-color: #FFD700;
    selection-color: #000;
    border: 1px solid #333;
}
QPushButton {
    background: #1e3a60;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    color: #dde0f0;
    font-weight: 600;
}
QPushButton:hover { background: #FFD700; color: #000; }
QPushButton#save_btn { background: #FFD700; color: #111; font-size: 10pt; }
QPushButton#save_btn:hover { background: #ffe040; }
QPushButton#eye_btn {
    background: #1a1b2e;
    border: 1px solid #2a2b42;
    border-radius: 4px;
    padding: 4px 8px;
    color: #888;
    font-size: 12px;
    min-width: 28px;
    max-width: 28px;
}
QPushButton#eye_btn:hover { color: #FFD700; }
QLabel { color: #9098b8; }
QLabel#section_lbl {
    color: #FFD700;
    font-weight: bold;
    font-size: 10pt;
    padding-top: 6px;
}
QLabel#hint_lbl { color: #555870; font-size: 8pt; }
QSpinBox {
    background: #0e0f1a;
    border: 1px solid #2a2b42;
    border-radius: 6px;
    padding: 6px 8px;
    color: #dde0f0;
}
QSpinBox:focus { border-color: #FFD700; }
QSlider::groove:horizontal {
    height: 4px; background: #2a2b42; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #FFD700; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #FFD700; border-radius: 2px; }
QCheckBox { color: #dde0f0; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px; border: 1px solid #2a2b42; background: #0e0f1a;
}
QCheckBox::indicator:checked { background: #FFD700; border-color: #FFD700; }
"""


class SettingsWindow(QDialog):
    """Dark-themed, tabbed API key and display settings dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LiveTranslate — Settings")
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(_DARK_STYLE)

        self._settings = load_settings()
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # ── Header ──────────────────────────────────────────────────
        hdr = QLabel("⚙  LiveTranslate Settings")
        hdr.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #FFD700; margin-bottom: 4px;"
        )
        root.addWidget(hdr)

        # ── Tabs ────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_stt_tab(), "🎙  STT")
        self._tabs.addTab(self._build_translation_tab(), "🌐  Translation")
        self._tabs.addTab(self._build_display_tab(), "🎨  Display")
        root.addWidget(self._tabs)

        # ── Status label ────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet("font-size: 9pt; padding: 2px;")
        root.addWidget(self._status)

        # ── Buttons ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("💾  Save")
        save_btn.setObjectName("save_btn")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _get_user_key(self, key_name: str) -> str:
        import os

        val = self._settings.get(key_name, "")
        if val and val == os.getenv(key_name, ""):
            return ""
        return val

    # ── Tab builders ──────────────────────────────────────────────────

    def _build_stt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addRow(self._section("Azure Speech (STT)"))

        self.azure_speech_key, row = self._key_row(
            "Using default public key (override here)"
        )
        self.azure_speech_key.setText(self._get_user_key("AZURE_SPEECH_KEY"))
        form.addRow("Speech Key:", row)

        self.azure_speech_region = QLineEdit()
        self.azure_speech_region.setPlaceholderText("e.g. southeastasia")
        self.azure_speech_region.setText(config.AZURE_SPEECH_REGION)
        form.addRow("Region:", self.azure_speech_region)

        test_btn = QPushButton("🔌  Test Connection")
        test_btn.clicked.connect(self._test_azure_speech)
        form.addRow("", test_btn)

        form.addRow(self._section("Microphone"))

        self.mic_combo = QComboBox()
        self._populate_mics()
        form.addRow("Input Device:", self.mic_combo)

        form.addRow(self._section("Audio Source"))

        self._audio_source_combo = QComboBox()
        self._audio_source_combo.addItem("🎙 Microphone", "mic")
        self._audio_source_combo.addItem("🔊 System Audio", "system")
        cur_src_idx = self._audio_source_combo.findData(config.AUDIO_SOURCE)
        if cur_src_idx >= 0:
            self._audio_source_combo.setCurrentIndex(cur_src_idx)
        form.addRow("Audio Source:", self._audio_source_combo)

        layout.addLayout(form)
        layout.addStretch()
        return tab

    def _build_translation_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addRow(self._section("Session"))

        # Language Pair selector
        self.lang_pair_combo = QComboBox()
        for pk, info in config.SUPPORTED_LANG_PAIRS.items():
            self.lang_pair_combo.addItem(info["display"], pk)
        cur_idx = self.lang_pair_combo.findData(config.LANG_PAIR)
        if cur_idx >= 0:
            self.lang_pair_combo.setCurrentIndex(cur_idx)
        form.addRow("Language Pair:", self.lang_pair_combo)

        # STT Engine selector
        self.stt_engine_combo = QComboBox()
        self.stt_engine_combo.addItems(["azure", "gemini"])
        self.stt_engine_combo.setCurrentText(config.STT_ENGINE)
        form.addRow("STT Engine:", self.stt_engine_combo)

        form.addRow(self._section("Translation Engine"))
        self.trans_engine_combo = QComboBox()
        self.trans_engine_combo.addItems(["azure", "gemini"])
        self.trans_engine_combo.setCurrentText(config.TRANSLATE_ENGINE)
        form.addRow("Engine:", self.trans_engine_combo)

        form.addRow(self._section("Azure Translator (optional)"))

        self.azure_trans_key, row = self._key_row(
            "Using default public key (override here)"
        )
        self.azure_trans_key.setText(self._get_user_key("AZURE_TRANSLATOR_KEY"))
        form.addRow("Translator Key:", row)

        self.azure_trans_region = QLineEdit()
        self.azure_trans_region.setPlaceholderText("e.g. global")
        self.azure_trans_region.setText(config.AZURE_TRANSLATOR_REGION)
        form.addRow("Region:", self.azure_trans_region)

        form.addRow(self._section("Gemini (STT + Translation)"))

        self.gemini_key, row = self._key_row("Using default public key (override here)")
        self.gemini_key.setText(self._get_user_key("GEMINI_API_KEY"))
        form.addRow("Gemini Key:", row)

        layout.addLayout(form)
        layout.addStretch()
        return tab

    def _build_display_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addRow(self._section("Subtitle Appearance"))

        # Opacity slider
        self._opacity_val = QLabel(f"{int(config.WINDOW_OPACITY * 100)}%")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(config.WINDOW_OPACITY * 100))
        self.opacity_slider.valueChanged.connect(
            lambda v: self._opacity_val.setText(f"{v}%")
        )
        row = QHBoxLayout()
        row.addWidget(self.opacity_slider)
        row.addWidget(self._opacity_val)
        form.addRow("Opacity:", row)

        # Font sizes
        self.font_orig_spin = QSpinBox()
        self.font_orig_spin.setRange(8, 36)
        self.font_orig_spin.setValue(config.FONT_SIZE_ORIGINAL)
        form.addRow("Original Font:", self.font_orig_spin)

        self.font_trans_spin = QSpinBox()
        self.font_trans_spin.setRange(8, 48)
        self.font_trans_spin.setValue(config.FONT_SIZE_TRANS)
        form.addRow("Translation Font:", self.font_trans_spin)

        form.addRow(self._section("Behaviour"))

        self._quality_combo = QComboBox()
        self._quality_combo.addItem("⚡ Fast (lower latency)", "fast")
        self._quality_combo.addItem("⚖  Balanced (default)", "balanced")
        self._quality_combo.addItem("🎯 Accurate (higher quality)", "accurate")
        cur_quality_idx = self._quality_combo.findData(config.QUALITY_MODE)
        if cur_quality_idx >= 0:
            self._quality_combo.setCurrentIndex(cur_quality_idx)
        form.addRow("Quality Mode:", self._quality_combo)
        hint = QLabel("⟳ Takes effect on next Start")
        hint.setObjectName("hint_lbl")
        form.addRow("", hint)

        self.auto_clear_spin = QSpinBox()
        self.auto_clear_spin.setRange(3, 30)
        self.auto_clear_spin.setSuffix(" s")
        self.auto_clear_spin.setValue(config.AUTO_CLEAR_SEC)
        form.addRow("Auto-clear:", self.auto_clear_spin)

        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(1, 5)
        self.max_history_spin.setValue(config.MAX_HISTORY)
        form.addRow("History lines:", self.max_history_spin)

        form.addRow(self._section("Readability"))

        self._trans_top_check = QCheckBox("Show translation above original text")
        self._trans_top_check.setChecked(config.TRANSLATION_ON_TOP)
        form.addRow("", self._trans_top_check)

        self._show_separator_check = QCheckBox("Show separator line between original and translation")
        self._show_separator_check.setChecked(config.SHOW_SEPARATOR)
        form.addRow("", self._show_separator_check)

        self._show_processing_check = QCheckBox("Show '\u2026' indicator while waiting for speech")
        self._show_processing_check.setChecked(config.SHOW_PROCESSING_INDICATOR)
        form.addRow("", self._show_processing_check)

        form.addRow(self._section("Logging"))
        self.debug_check = QCheckBox("Enable debug logging (verbose)")
        self.debug_check.setChecked(bool(config.DEBUG_MODE))
        form.addRow("", self.debug_check)

        layout.addLayout(form)
        layout.addStretch()
        return tab

    # ── Helpers ───────────────────────────────────────────────────────

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("section_lbl")
        return lbl

    def _key_row(self, placeholder: str):
        """Return (QLineEdit, QHBoxLayout) with an eye-toggle button."""
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        edit.setPlaceholderText(placeholder)
        eye = QPushButton("👁")
        eye.setObjectName("eye_btn")
        eye.setCheckable(True)
        eye.toggled.connect(
            lambda checked: edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        container = QHBoxLayout()
        container.setSpacing(4)
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(edit)
        container.addWidget(eye)
        return edit, container

    def _populate_mics(self):
        from audio_capture import AudioCapture

        self.mic_combo.clear()
        self.mic_combo.addItem("System Default", -1)
        for dev in AudioCapture.list_input_devices():
            self.mic_combo.addItem(dev["name"], dev["index"])
        # Select current
        cur = config.AUDIO_DEVICE_INDEX
        for i in range(self.mic_combo.count()):
            if self.mic_combo.itemData(i) == cur:
                self.mic_combo.setCurrentIndex(i)
                break

    def _set_status(self, msg: str, ok: bool = False, error: bool = False):
        color = "#00cc66" if ok else ("#FF5555" if error else "#aaa")
        self._status.setStyleSheet(f"font-size: 9pt; color: {color};")
        self._status.setText(msg)
        QTimer.singleShot(4000, lambda: self._status.setText(""))

    def _test_azure_speech(self):
        key = self.azure_speech_key.text().strip()
        region = self.azure_speech_region.text().strip()
        if not key or not region:
            self._set_status("⚠  Fill in Speech Key and Region first.", error=True)
            return
        try:
            import azure.cognitiveservices.speech as sdk  # type: ignore[import-not-found]

            sdk.SpeechConfig(subscription=key, region=region)
            self._set_status("✓  Azure Speech config looks valid!", ok=True)
        except ImportError:
            self._set_status(
                "⚠  azure-cognitiveservices-speech not installed.", error=True
            )
        except Exception as e:
            self._set_status(f"✗  {e}", error=True)

    # ── Save ──────────────────────────────────────────────────────────

    def _save(self):
        s = self._settings

        # STT
        speech_key = self.azure_speech_key.text().strip()
        if speech_key:
            s["AZURE_SPEECH_KEY"] = speech_key
        else:
            s.pop("AZURE_SPEECH_KEY", None)

        s["AZURE_SPEECH_REGION"] = self.azure_speech_region.text().strip()
        s["AUDIO_DEVICE_INDEX"] = self.mic_combo.currentData()
        s["AUDIO_SOURCE"] = self._audio_source_combo.currentData()

        # Session
        s["STT_ENGINE"] = self.stt_engine_combo.currentText()
        s["LANG_PAIR"] = self.lang_pair_combo.currentData()

        # Translation
        s["TRANSLATE_ENGINE"] = self.trans_engine_combo.currentText()

        trans_key = self.azure_trans_key.text().strip()
        if trans_key:
            s["AZURE_TRANSLATOR_KEY"] = trans_key
        else:
            s.pop("AZURE_TRANSLATOR_KEY", None)

        s["AZURE_TRANSLATOR_REGION"] = self.azure_trans_region.text().strip()

        gemini_key = self.gemini_key.text().strip()
        if gemini_key:
            s["GEMINI_API_KEY"] = gemini_key
        else:
            s.pop("GEMINI_API_KEY", None)

        # Display
        s["WINDOW_OPACITY"] = self.opacity_slider.value() / 100
        s["FONT_SIZE_ORIGINAL"] = self.font_orig_spin.value()
        s["FONT_SIZE_TRANS"] = self.font_trans_spin.value()
        s["AUTO_CLEAR_SEC"] = self.auto_clear_spin.value()
        s["MAX_HISTORY"] = self.max_history_spin.value()
        s["DEBUG_MODE"] = self.debug_check.isChecked()
        s["QUALITY_MODE"] = self._quality_combo.currentData()
        s["TRANSLATION_ON_TOP"] = self._trans_top_check.isChecked()
        config.TRANSLATION_ON_TOP = self._trans_top_check.isChecked()

        s["SHOW_SEPARATOR"] = self._show_separator_check.isChecked()
        config.SHOW_SEPARATOR = self._show_separator_check.isChecked()

        s["SHOW_PROCESSING_INDICATOR"] = self._show_processing_check.isChecked()
        config.SHOW_PROCESSING_INDICATOR = self._show_processing_check.isChecked()

        save_settings(s)

        # Apply to running config immediately
        import os

        config.AZURE_SPEECH_KEY = s.get(
            "AZURE_SPEECH_KEY", os.getenv("AZURE_SPEECH_KEY", config._DAS)
        )
        config.AZURE_SPEECH_REGION = s.get(
            "AZURE_SPEECH_REGION", os.getenv("AZURE_SPEECH_REGION", "southeastasia")
        )
        config.AUDIO_DEVICE_INDEX = s["AUDIO_DEVICE_INDEX"]
        config.AUDIO_SOURCE = s["AUDIO_SOURCE"]
        config.STT_ENGINE = s["STT_ENGINE"]
        config.LANG_PAIR = s["LANG_PAIR"]
        config.TRANSLATE_ENGINE = s["TRANSLATE_ENGINE"]
        config.AZURE_TRANSLATOR_KEY = s.get(
            "AZURE_TRANSLATOR_KEY", os.getenv("AZURE_TRANSLATOR_KEY", config._DAT)
        )
        config.AZURE_TRANSLATOR_REGION = s.get(
            "AZURE_TRANSLATOR_REGION", os.getenv("AZURE_TRANSLATOR_REGION", "global")
        )
        config.GEMINI_API_KEY = s.get(
            "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", config._DG)
        )
        config.WINDOW_OPACITY = s["WINDOW_OPACITY"]
        config.FONT_SIZE_ORIGINAL = s["FONT_SIZE_ORIGINAL"]
        config.FONT_SIZE_TRANS = s["FONT_SIZE_TRANS"]
        config.AUTO_CLEAR_SEC = s["AUTO_CLEAR_SEC"]
        config.MAX_HISTORY = s["MAX_HISTORY"]
        config.DEBUG_MODE = s["DEBUG_MODE"]
        config.QUALITY_MODE = s["QUALITY_MODE"]

        self._set_status(
            "\u2713  Settings saved!  (Stop → Start listening to apply engine/language changes.)",
            ok=True,
        )
        QTimer.singleShot(2000, self.accept)

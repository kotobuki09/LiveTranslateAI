"""
SubtitleWindow — Frameless, transparent, always-on-top floating subtitle overlay.

Visual improvements over original:
  - Dark gradient glassmorphism background
  - Smooth fade-in animation when text first appears
  - Pulsing listening-state indicator dot (top-right)
  - Right-click context menu: opacity control + hide
  - Language badge uses proper emoji (🎙) and pair-aware display
  - show_error() for visible error reporting
  - adjustSize() only called when text actually changes
  - set_listening() called by App on start/stop
"""

from PyQt5.QtWidgets import (  # type: ignore[import-not-found]
    QWidget,
    QVBoxLayout,
    QLabel,
    QApplication,
    QMenu,
    QGraphicsDropShadowEffect,
    QSizeGrip,
)
from PyQt5.QtCore import (  # type: ignore[import-not-found]
    Qt,
    QPoint,
    QRectF,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    pyqtSlot,
)
from PyQt5.QtGui import (  # type: ignore[import-not-found]
    QColor,
    QPainter,
    QPainterPath,
    QLinearGradient,
    QPen,
    QFontMetrics,
    QFont,
)

import config


class SubtitleWindow(QWidget):
    """Frameless, transparent, always-on-top floating subtitle box."""

    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self._is_listening = False
        self._status_mode = "idle"
        self._dot_visible = True
        self._is_error = False
        self._last_original = ""
        self._last_trans = ""
        self._save_timer = QTimer(self)
        self._save_timer.setInterval(1000)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_geometry)
        self._init_window()
        self._init_ui()
        self._init_animations()
        self._position_bottom_center()

    # ── Initialisation ────────────────────────────────────────────────

    def _init_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(config.WINDOW_OPACITY)

    def _init_ui(self):
        # Load size or use default
        from json_config import load_settings

        s = load_settings()
        screen = QApplication.primaryScreen().availableGeometry()
        def_w = int(screen.width() * 0.95)
        w = s.get("SUBTITLE_WIDTH", def_w)
        h = s.get("SUBTITLE_HEIGHT", 400)
        self.resize(w, h)
        self.setMinimumSize(300, 100)

        self.sizegrip = QSizeGrip(self)
        self.sizegrip.setStyleSheet(
            "QSizeGrip { width: 20px; height: 20px; background: transparent; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 25)  # Luxury padding for readability
        layout.setSpacing(15)  # Clear breathing room between languages
        # Let the layout stretch items fully, don't set fixed layout alignment
        # This fixes the text getting crushed to the left and wrapping too early

        # Language direction badge
        self.lang_badge = QLabel("", self)
        self.lang_badge.setAlignment(Qt.AlignLeft)
        self.lang_badge.setStyleSheet(
            "color: rgba(255,215,0,180); font-size: 10px; "
            "font-family: 'Calibri', 'Segoe UI', sans-serif; background: transparent;"
        )
        layout.addWidget(self.lang_badge)

        # Original speech text
        self.label_original = QLabel("", self)
        self.label_original.setWordWrap(True)
        self.label_original.setAlignment(Qt.AlignLeft)  # Normal left-aligned text
        self.label_original.setStyleSheet(
            f"color: rgba(240,240,255,230); "
            f"font-family: 'Calibri', 'Segoe UI', sans-serif; "
            f"font-size: {config.FONT_SIZE_ORIGINAL}pt; "
            f"font-weight: 600; "
            f"letter-spacing: 0.3px; "
            f"line-height: 140%; "
            f"background: transparent;"
        )
        self._add_shadow(self.label_original)
        layout.addWidget(self.label_original)

        # Translated text
        self.label_translation = QLabel("", self)
        self.label_translation.setWordWrap(True)
        self.label_translation.setAlignment(Qt.AlignLeft)  # Normal left-aligned text
        self.label_translation.setStyleSheet(
            f"color: #FFD700; "
            f"font-family: 'Calibri', 'Segoe UI', sans-serif; "
            f"font-size: {config.FONT_SIZE_TRANS}pt; "
            f"font-weight: 700; "
            f"letter-spacing: 0.4px; "
            f"line-height: 145%; "
            f"background: transparent;"
        )
        self._add_shadow(self.label_translation)
        layout.addWidget(self.label_translation, stretch=1)

    def _fit_text_to_label(self, label: QLabel, text: str) -> str:
        """Trim lines from the top until text fits within the label's current height."""
        if not text:
            return text
        available_h = label.height()
        if available_h <= 0:
            return text
        fm = QFontMetrics(label.font())
        line_h = fm.lineSpacing()
        usable_lines = max(1, available_h // line_h)
        # Calculate chars per line based on label width
        chars_per_line = max(1, label.width() // max(1, fm.averageCharWidth()))

        # Split into visual lines (accounting for word wrap)
        paragraphs = text.split("\n")
        all_lines = []
        for para in paragraphs:
            if not para:
                all_lines.append("")
                continue
            words = para.split()
            curr_line = ""
            for word in words:
                test = (curr_line + " " + word).strip()
                if fm.horizontalAdvance(test) <= label.width() - 10:
                    curr_line = test
                else:
                    if curr_line:
                        all_lines.append(curr_line)
                    curr_line = word
            if curr_line:
                all_lines.append(curr_line)

        # Keep only the last N lines that fit
        visible = all_lines[-usable_lines:]
        return " ".join(visible).strip()

    def _add_shadow(self, label: QLabel):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 255))
        shadow.setOffset(2, 2)
        label.setGraphicsEffect(shadow)

    def _init_animations(self):
        # Premium fade-in/out animation (0 ↔ WINDOW_OPACITY)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(400)  # Slower, smoother transitions
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        # Smooth character-by-character typewriter
        self._target_orig = ""
        self._target_trans = ""
        self._curr_orig_text = ""
        self._curr_trans_text = ""
        self._typewriter_timer = QTimer(self)
        self._typewriter_timer.setInterval(20)
        self._typewriter_timer.timeout.connect(self._on_typewriter_tick)
        self._typewriter_timer.start()

        # Listening indicator pulse
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._toggle_dot)
        self._pulse_timer.start(700)

    def _position_bottom_center(self):
        from json_config import load_settings

        s = load_settings()
        saved_x = s.get("SUBTITLE_X")
        saved_y = s.get("SUBTITLE_Y")
        if saved_x is not None and saved_y is not None:
            self.move(saved_x, saved_y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = screen.height() - self.height() - 50
            self.move(x, y)

    # ── Drawing ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect().adjusted(1, 1, -1, -1))
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)

        # Dark gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(12, 12, 24, 255))
        gradient.setColorAt(1.0, QColor(5, 5, 14, 255))
        painter.fillPath(path, gradient)

        # Subtle glassmorphism border
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1.0))
        painter.drawPath(path)

        alpha = 255 if self._dot_visible else 70
        mode_colors = {
            "listening": QColor(0, 230, 120, alpha),
            "reconnecting": QColor(255, 165, 0, alpha),
            "error": QColor(220, 50, 50, alpha),
            "starting": QColor(60, 120, 255, alpha),
        }
        dot_color = mode_colors.get(self._status_mode)
        if dot_color is not None:
            painter.setBrush(dot_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.width() - 25, 15, 10, 10)
        elif (
            self._status_mode == "idle"
            and not self.label_original.text()
            and not self.label_translation.text()
        ):
            # Idle dot — grey
            painter.setBrush(QColor(120, 120, 130, 100))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.width() - 25, 15, 10, 10)

    # ── Animations ───────────────────────────────────────────────────

    def _toggle_dot(self):
        self._dot_visible = not self._dot_visible
        self.update()

    def _fade_in(self):
        if self._fade_anim.state() == QPropertyAnimation.Running:
            self._fade_anim.stop()
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(config.WINDOW_OPACITY)
        self._fade_anim.start()

    def _fade_out(self):
        if self._fade_anim.state() == QPropertyAnimation.Running:
            self._fade_anim.stop()
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(
            lambda: self.hide() if self.windowOpacity() == 0 else None
        )
        self._fade_anim.start()

    def _on_typewriter_tick(self):
        """Drip characters smoothly from target strings. Tolerates small upstream STT corrections."""
        if not self._target_orig and not self._target_trans:
            return

        import os

        changed = False

        # Original catch-up
        if not self._target_orig.startswith(self._curr_orig_text):
            # Only rewind if the target shrank significantly (true correction/new sentence)
            # Small Azure interim fluctuations (< 10 chars shorter) are absorbed going forward
            if len(self._curr_orig_text) - len(self._target_orig) > 10:
                common = os.path.commonprefix([self._curr_orig_text, self._target_orig])
                self._curr_orig_text = common
                self.label_original.setText(self._curr_orig_text)
                changed = True
            # else: silently wait for the streamed text to grow past what we've typed

        if len(self._curr_orig_text) < len(self._target_orig):
            diff = len(self._target_orig) - len(self._curr_orig_text)
            step = max(1, diff // 8)
            self._curr_orig_text = self._target_orig[: len(self._curr_orig_text) + step]
            fitted = self._fit_text_to_label(self.label_original, self._curr_orig_text)
            self.label_original.setText(fitted)
            changed = True

        # Translation catch-up
        if not self._target_trans.startswith(self._curr_trans_text):
            if len(self._curr_trans_text) - len(self._target_trans) > 10:
                common = os.path.commonprefix(
                    [self._curr_trans_text, self._target_trans]
                )
                self._curr_trans_text = common
                fitted = self._fit_text_to_label(
                    self.label_translation, self._curr_trans_text
                )
                self.label_translation.setText(fitted)
                changed = True

        if len(self._curr_trans_text) < len(self._target_trans):
            diff = len(self._target_trans) - len(self._curr_trans_text)
            step = max(1, diff // 8)
            self._curr_trans_text = self._target_trans[
                : len(self._curr_trans_text) + step
            ]
            fitted = self._fit_text_to_label(
                self.label_translation, self._curr_trans_text
            )
            self.label_translation.setText(fitted)
            changed = True

        if changed:
            self.update()

    # ── Drag support ─────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "sizegrip"):
            self.sizegrip.move(
                self.width() - self.sizegrip.width() - 5,
                self.height() - self.sizegrip.height() - 5,
            )
        if hasattr(self, "_save_timer"):
            self._save_timer.start()

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, "_save_timer"):
            self._save_timer.start()

    def _save_geometry(self):
        from json_config import load_settings, save_settings

        s = load_settings()
        s["SUBTITLE_WIDTH"] = self.width()
        s["SUBTITLE_HEIGHT"] = self.height()
        s["SUBTITLE_X"] = self.x()
        s["SUBTITLE_Y"] = self.y()
        save_settings(s)

    def contextMenuEvent(self, event):
        """Right-click menu: opacity control and hide."""
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1a1b2e; color: #e0e0f0; border: 1px solid #333355; "
            "border-radius: 6px; padding: 4px; }"
            "QMenu::item { padding: 6px 20px; border-radius: 4px; }"
            "QMenu::item:selected { background: #FFD700; color: #111; }"
        )
        opacity_menu = menu.addMenu("🔆 Opacity")
        for pct in [40, 60, 75, 90, 100]:
            act = opacity_menu.addAction(f"{pct}%")
            act.triggered.connect(lambda _, p=pct: self._set_opacity(p / 100))
        menu.addSeparator()
        menu.addAction("Hide  (restore via tray)").triggered.connect(self.hide)
        menu.exec_(event.globalPos())

    def _set_opacity(self, value: float):
        self.setWindowOpacity(value)
        config.WINDOW_OPACITY = float(value)
        from json_config import load_settings, save_settings

        s = load_settings()
        s["WINDOW_OPACITY"] = value
        save_settings(s)

    # ── Public API ───────────────────────────────────────────────────

    def refresh_styles(self):
        """Update stylesheets with current config values (called when settings change)."""
        self.label_original.setStyleSheet(
            f"color: rgba(240,240,255,220); "
            f"font-family: 'Segoe UI', sans-serif; "
            f"font-size: {config.FONT_SIZE_ORIGINAL}pt; "
            f"font-weight: 500; "
            f"background: transparent;"
        )
        self.label_translation.setStyleSheet(
            f"color: #FFD700; "
            f"font-family: 'Segoe UI', sans-serif; "
            f"font-size: {config.FONT_SIZE_TRANS}pt; "
            f"font-weight: 800; "
            f"background: transparent;"
        )
        self.setWindowOpacity(config.WINDOW_OPACITY)
        self.update()

    def set_listening(self, active: bool):
        """Called by App on start/stop listening."""
        self.set_status_mode("listening" if active else "idle")

    def set_status_mode(self, mode: str):
        self._status_mode = mode
        self._is_listening = mode == "listening"
        self.update()

    @pyqtSlot(str, str, str)
    def update_text(self, original: str, translation: str, source_lang: str):
        """Update both subtitle labels via typewriter targeting."""
        self._target_orig = original
        self._target_trans = translation

        # When strings are cleared, clear them immediately without typing
        if not original and not translation:
            self._curr_orig_text = ""
            self._curr_trans_text = ""
            self.label_original.setText("")
            self.label_translation.setText("")

        was_empty = not self._last_original and not self._last_trans

        self._last_original = original
        self._last_trans = translation

        # Typewriter snap for MAX_HISTORY > 1:
        # If the new target is a multi-line string whose earlier lines we've
        # already typed, snap _curr_*_text to those lines so the typewriter
        # only animates the new (last) sentence instead of catching up from scratch.
        if "\n" in original and self._curr_orig_text:
            lines = original.split("\n")
            already = "\n".join(lines[:-1])  # all but last sentence
            if (
                already
                and original.startswith(already)
                and len(already) > len(self._curr_orig_text)
            ):
                self._curr_orig_text = already
        if "\n" in translation and self._curr_trans_text:
            lines = translation.split("\n")
            already = "\n".join(lines[:-1])
            if (
                already
                and translation.startswith(already)
                and len(already) > len(self._curr_trans_text)
            ):
                self._curr_trans_text = already

        # Restore normal translation colour (may have been set to red by show_error)
        if self._is_error:
            self.label_translation.setStyleSheet(
                f"color: #FFD700; font-family: 'Segoe UI', sans-serif; "
                f"font-size: {config.FONT_SIZE_TRANS}pt; font-weight: 800; background: transparent;"
            )
            self._is_error = False

        # Language badge from active pair config
        pair = config.SUPPORTED_LANG_PAIRS.get(
            config.LANG_PAIR, config.SUPPORTED_LANG_PAIRS["en-vi"]
        )
        badge_map = pair["badge"]
        source_icon = "🔊" if config.AUDIO_SOURCE == "system" else "🎙"
        badge_text = badge_map.get(source_lang, pair["display"])
        self.lang_badge.setText(f"{source_icon} {badge_text}")

        if was_empty and (original or translation):
            self.setWindowOpacity(0.0)
            if not self.isVisible():
                self.show()
            self._fade_in()
        elif not self.isVisible():
            self.show()

    def show_error(self, message: str):
        """Display an error message in the subtitle area."""
        self._is_error = True
        self.label_translation.setStyleSheet(
            "color: #FF5555; font-family: 'Segoe UI', sans-serif; "
            f"font-size: {config.FONT_SIZE_TRANS}pt; font-weight: 800; background: transparent;"
        )
        self.label_original.setText("")
        self.label_translation.setText(f"⚠ {message}")
        self.lang_badge.setText("Error")
        if not self.isVisible():
            self.show()

    def clear(self):
        """Clear all subtitle text with a smooth fade-out."""
        self._last_original = ""
        self._last_trans = ""
        self._is_error = False
        self._fade_out()
        # The actual labels are cleared after fade or simply hidden by opacity
        QTimer.singleShot(400, lambda: self._clear_labels())

    def _clear_labels(self):
        self._target_orig = ""
        self._target_trans = ""
        self._curr_orig_text = ""
        self._curr_trans_text = ""
        self.label_original.setText("")
        self.label_translation.setText("")
        self.lang_badge.setText("")

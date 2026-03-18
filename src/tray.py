import threading
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import config
from json_config import load_settings, save_settings

ICON_PATH = Path(__file__).parent / "assets" / "icon.png"


def _generate_icon(active: bool = False) -> Image.Image:
    """Generate tray icon. Gold = listening, grey = idle."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if active:
        ring_color = (255, 215, 0, 255)   # gold
        inner_color = (40, 30, 0, 230)
        letter_color = (255, 215, 0, 255)
    else:
        ring_color = (100, 100, 110, 255)  # grey
        inner_color = (30, 30, 35, 200)
        letter_color = (160, 160, 170, 255)

    draw.ellipse([2, 2, size - 2, size - 2], fill=ring_color)
    draw.ellipse([8, 8, size - 8, size - 8], fill=inner_color)
    # "L" letter
    draw.rectangle([20, 18, 24, 38], fill=letter_color)
    draw.rectangle([20, 34, 30, 38], fill=letter_color)
    # "T" letter
    draw.rectangle([30, 18, 46, 22], fill=letter_color)
    draw.rectangle([36, 22, 40, 38], fill=letter_color)
    return img


class TrayManager:
    """System tray icon with Start / Stop / Settings / Language Pair menu."""

    def __init__(self, on_start, on_stop, on_settings, on_quit, on_show_subtitle=None):
        self._on_start_cb = on_start
        self._on_stop_cb = on_stop
        self._on_settings_cb = on_settings
        self._on_quit_cb = on_quit
        self._on_show_subtitle_cb = on_show_subtitle
        self._icon: "pystray.Icon | None" = None
        self._is_listening = False

    def _get_icon_image(self) -> Image.Image:
        if ICON_PATH.exists():
            return Image.open(ICON_PATH)
        return _generate_icon(active=False)

    def _set_engine(self, engine_type: str, engine_val: str):
        settings = load_settings()
        settings[engine_type] = engine_val
        save_settings(settings)
        if engine_type == "STT_ENGINE":
            config.STT_ENGINE = engine_val
        elif engine_type == "TRANSLATE_ENGINE":
            config.TRANSLATE_ENGINE = engine_val
        self.notify(f"{engine_type} → {engine_val}")

    def _set_lang_pair(self, pair_key: str):
        settings = load_settings()
        settings["LANG_PAIR"] = pair_key
        save_settings(settings)
        config.LANG_PAIR = pair_key
        pair_info = config.SUPPORTED_LANG_PAIRS.get(pair_key, {})
        self.notify(f"Language pair: {pair_info.get('display', pair_key)}")

    def _build_menu_items(self) -> list:
        # Language pair submenu
        def make_action(pk_val):
            return lambda icon, item: self._set_lang_pair(pk_val)
            
        def make_checked(pk_val):
            return lambda item: config.LANG_PAIR == pk_val

        lang_items = [
            pystray.MenuItem(
                info["display"],
                make_action(pk),
                checked=make_checked(pk),
                radio=True,
            )
            for pk, info in config.SUPPORTED_LANG_PAIRS.items()
        ]

        return [
            pystray.MenuItem(
                "▶  Start Listening",
                self._on_start,
                enabled=lambda item: not self._is_listening,
            ),
            pystray.MenuItem(
                "⏹  Stop Listening",
                self._on_stop,
                enabled=lambda item: self._is_listening,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Language Pair", pystray.Menu(*lang_items)),
            pystray.MenuItem("STT Engine", pystray.Menu(
                pystray.MenuItem(
                    "Azure",
                    lambda icon, item: self._set_engine("STT_ENGINE", "azure"),
                    checked=lambda item: config.STT_ENGINE == "azure",
                    radio=True,
                ),
                pystray.MenuItem(
                    "Gemini",
                    lambda icon, item: self._set_engine("STT_ENGINE", "gemini"),
                    checked=lambda item: config.STT_ENGINE == "gemini",
                    radio=True,
                ),
            )),
            pystray.MenuItem("Translation Engine", pystray.Menu(
                pystray.MenuItem(
                    "Azure",
                    lambda icon, item: self._set_engine("TRANSLATE_ENGINE", "azure"),
                    checked=lambda item: config.TRANSLATE_ENGINE == "azure",
                    radio=True,
                ),
                pystray.MenuItem(
                    "Gemini",
                    lambda icon, item: self._set_engine("TRANSLATE_ENGINE", "gemini"),
                    checked=lambda item: config.TRANSLATE_ENGINE == "gemini",
                    radio=True,
                ),
            )),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙  Settings", self._on_settings),
            pystray.MenuItem("🖥  Show Subtitle", self._on_show_subtitle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕  Quit", self._on_quit),
        ]

    def start(self):
        image = self._get_icon_image()
        self._icon = pystray.Icon(
            name="LiveTranslate",
            icon=image,
            title="LiveTranslate — Right-click to start",
            menu=pystray.Menu(*self._build_menu_items()),
        )
        threading.Thread(target=self._icon.run, daemon=True).start()

    def stop(self):
        if self._icon:
            self._icon.stop()

    def notify(self, message: str):
        if self._icon:
            self._icon.notify(message, "LiveTranslate")

    def set_listening(self, active: bool):
        """Update tray icon and state to reflect listening status."""
        self._is_listening = active
        if self._icon:
            self._icon.icon = _generate_icon(active=active)
            self._icon.title = (
                "LiveTranslate — Listening…" if active else "LiveTranslate — Idle"
            )

    # ── Internal callbacks ─────────────────────────────────────────────

    def _on_start(self, icon, item):
        self._on_start_cb()

    def _on_stop(self, icon, item):
        self._on_stop_cb()

    def _on_settings(self, icon, item):
        if self._on_settings_cb:
            self._on_settings_cb()

    def _on_show_subtitle(self, icon, item):
        if self._on_show_subtitle_cb:
            self._on_show_subtitle_cb()

    def _on_quit(self, icon, item):
        self.stop()
        self._on_quit_cb()

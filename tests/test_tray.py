from unittest.mock import MagicMock


def test_tray_manager_creates_menu_items():
    from tray import TrayManager

    mgr = TrayManager(
        on_start=MagicMock(),
        on_stop=MagicMock(),
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    items = mgr._build_menu_items()
    labels = [
        item.text for item in items if hasattr(item, "text") and callable(item.text)
    ]
    # pystray.MenuItem stores text as a callable; get the text value directly
    raw_items = mgr._build_menu_items()
    # Check by inspecting item attributes
    assert len(raw_items) >= 4


def test_tray_manager_calls_start_callback():
    from tray import TrayManager

    start_cb = MagicMock()
    mgr = TrayManager(
        on_start=start_cb,
        on_stop=MagicMock(),
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    mgr._on_start(None, None)
    start_cb.assert_called_once()


def test_tray_manager_calls_stop_callback():
    from tray import TrayManager

    stop_cb = MagicMock()
    mgr = TrayManager(
        on_start=MagicMock(),
        on_stop=stop_cb,
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    mgr._on_stop(None, None)
    stop_cb.assert_called_once()


def test_tray_manager_stop_when_no_icon_is_safe():
    from tray import TrayManager

    mgr = TrayManager(
        on_start=MagicMock(),
        on_stop=MagicMock(),
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    mgr.stop()  # _icon is None — must not raise


def test_tray_manager_notify_when_no_icon_is_safe():
    from tray import TrayManager

    mgr = TrayManager(
        on_start=MagicMock(),
        on_stop=MagicMock(),
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    mgr.notify("test")  # _icon is None — must not raise


def test_tray_has_audio_source_submenu():
    """Verify _build_menu_items() contains Audio Source submenu."""
    from tray import TrayManager

    mgr = TrayManager(
        on_start=MagicMock(),
        on_stop=MagicMock(),
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    items = mgr._build_menu_items()

    # Find the Audio Source menu item by inspecting text attribute
    audio_source_found = False
    for item in items:
        if hasattr(item, "text") and callable(item.text):
            # pystray.MenuItem.text is sometimes a callable, so call it to get the string
            try:
                text_value = item.text() if callable(item.text) else item.text
            except:
                text_value = str(item.text) if hasattr(item, "text") else ""
        else:
            text_value = getattr(item, "text", "")

        # Check if this item contains "Audio Source"
        if "Audio Source" in str(text_value):
            audio_source_found = True
            break

    assert audio_source_found, "Audio Source submenu not found in menu items"


def test_tray_set_audio_source_persists():
    """Verify _set_audio_source() persists to config and settings."""
    from unittest.mock import patch
    from tray import TrayManager
    import config

    with (
        patch("tray.load_settings") as mock_load,
        patch("tray.save_settings") as mock_save,
    ):
        # Mock load_settings to return a dict
        mock_load.return_value = {}

        mgr = TrayManager(
            on_start=MagicMock(),
            on_stop=MagicMock(),
            on_settings=MagicMock(),
            on_quit=MagicMock(),
        )

        # Set audio source to "system"
        mgr._set_audio_source("system")

        # Verify load_settings was called
        mock_load.assert_called_once()

        # Verify save_settings was called with AUDIO_SOURCE = "system"
        mock_save.assert_called_once()
        saved_settings = mock_save.call_args[0][0]
        assert saved_settings.get("AUDIO_SOURCE") == "system", (
            "AUDIO_SOURCE not saved to settings"
        )

        # Verify config.AUDIO_SOURCE was updated
        assert config.AUDIO_SOURCE == "system", "config.AUDIO_SOURCE not updated"


def test_tray_icon_reflects_reconnecting_state():
    from tray import TrayManager

    mgr = TrayManager(
        on_start=MagicMock(),
        on_stop=MagicMock(),
        on_settings=MagicMock(),
        on_quit=MagicMock(),
    )
    mgr.set_listening(False)
    assert mgr._is_listening is False

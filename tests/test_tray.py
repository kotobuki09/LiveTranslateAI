from unittest.mock import MagicMock


def test_tray_manager_creates_menu_items():
    from tray import TrayManager
    mgr = TrayManager(on_start=MagicMock(), on_stop=MagicMock(), on_settings=MagicMock(), on_quit=MagicMock())
    items = mgr._build_menu_items()
    labels = [item.text for item in items if hasattr(item, "text") and callable(item.text)]
    # pystray.MenuItem stores text as a callable; get the text value directly
    raw_items = mgr._build_menu_items()
    # Check by inspecting item attributes
    assert len(raw_items) >= 4 


def test_tray_manager_calls_start_callback():
    from tray import TrayManager
    start_cb = MagicMock()
    mgr = TrayManager(on_start=start_cb, on_stop=MagicMock(), on_settings=MagicMock(), on_quit=MagicMock())
    mgr._on_start(None, None)
    start_cb.assert_called_once()


def test_tray_manager_calls_stop_callback():
    from tray import TrayManager
    stop_cb = MagicMock()
    mgr = TrayManager(on_start=MagicMock(), on_stop=stop_cb, on_settings=MagicMock(), on_quit=MagicMock())
    mgr._on_stop(None, None)
    stop_cb.assert_called_once()


def test_tray_manager_stop_when_no_icon_is_safe():
    from tray import TrayManager
    mgr = TrayManager(on_start=MagicMock(), on_stop=MagicMock(), on_settings=MagicMock(), on_quit=MagicMock())
    mgr.stop()   # _icon is None — must not raise


def test_tray_manager_notify_when_no_icon_is_safe():
    from tray import TrayManager
    mgr = TrayManager(on_start=MagicMock(), on_stop=MagicMock(), on_settings=MagicMock(), on_quit=MagicMock())
    mgr.notify("test")   # _icon is None — must not raise

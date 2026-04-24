import os
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from presence import PresenceKeeper
import about
import config_dialog

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_ACTIVE = os.path.join(_BASE, "icon.png")
ICON_PAUSED = os.path.join(_BASE, "icon-paused.png")

_tray_ref = []  # keep GObject alive for the process lifetime


def request_quit(keeper):
    try:
        keeper.stop()
    except Exception:
        pass
    GLib.idle_add(_do_gtk_quit)


def _do_gtk_quit():
    Gtk.main_quit()
    return False


def _icon_path(running):
    path = ICON_ACTIVE if running else ICON_PAUSED
    if os.path.exists(path):
        return path
    return "input-mouse" if running else "input-mouse-symbolic"


def _tooltip(running):
    state = "running" if running else "paused"
    return f"{about.NAME} ({about.VERSION}) — {state}"


def _build_menu(keeper):
    """Return (Gtk.Menu, update_fn) — update_fn() refreshes dynamic labels."""
    menu = Gtk.Menu()

    item_configure = Gtk.MenuItem(label="Configure…")
    item_configure.connect("activate", lambda *_: config_dialog.open_dialog(keeper))
    menu.append(item_configure)

    menu.append(Gtk.SeparatorMenuItem())

    item_toggle = Gtk.MenuItem(label="Pause" if keeper.running else "Start")

    def _on_toggle(*_):
        if keeper.running:
            keeper.stop()
        else:
            keeper.start()
        item_toggle.set_label("Pause" if keeper.running else "Start")

    item_toggle.connect("activate", _on_toggle)
    menu.append(item_toggle)

    menu.append(Gtk.SeparatorMenuItem())

    # Mode submenu with radio buttons
    mode_item = Gtk.MenuItem(label="Mode")
    mode_menu = Gtk.Menu()
    _first = None
    for label, mode in [
        ("Mouse",    PresenceKeeper.MODE_MOUSE),
        ("Keyboard", PresenceKeeper.MODE_KEYBOARD),
        ("Both",     PresenceKeeper.MODE_BOTH),
        ("Scroll",   PresenceKeeper.MODE_SCROLL),
    ]:
        if _first is None:
            mi = Gtk.RadioMenuItem.new_with_label([], label)
            _first = mi
        else:
            mi = Gtk.RadioMenuItem.new_with_label_from_widget(_first, label)
        cur = keeper.mode.value if hasattr(keeper.mode, 'value') else keeper.mode
        mi.set_active(cur == mode)
        mi.connect("toggled", lambda w, m=mode: setattr(keeper, 'mode', m) if w.get_active() else None)
        mode_menu.append(mi)
    mode_item.set_submenu(mode_menu)
    menu.append(mode_item)

    menu.append(Gtk.SeparatorMenuItem())

    item_about = Gtk.MenuItem(label=f"About {about.NAME}")
    item_about.connect("activate", lambda *_: config_dialog.open_about())
    menu.append(item_about)

    item_quit = Gtk.MenuItem(label="Quit")
    item_quit.connect("activate", lambda *_: request_quit(keeper))
    menu.append(item_quit)

    menu.show_all()

    def update():
        item_toggle.set_label("Pause" if keeper.running else "Start")

    return menu, update


def _try_xapp(keeper, autostart, menu, update_menu):
    gi.require_version('XApp', '1.0')
    from gi.repository import XApp

    icon = XApp.StatusIcon()
    icon.set_icon_name(_icon_path(keeper.running))
    icon.set_tooltip_text(_tooltip(keeper.running))
    icon.set_secondary_menu(menu)
    icon.set_visible(True)
    icon.connect("activate", lambda i, b, t: config_dialog.open_dialog(keeper))

    def _refresh(_text=None):
        running = keeper.running

        def _update():
            icon.set_icon_name(_icon_path(running))
            icon.set_tooltip_text(_tooltip(running))
            update_menu()
            return False

        GLib.idle_add(_update)

    keeper.set_status_callback(_refresh)
    _tray_ref.append(icon)

    if autostart:
        keeper.start()
    print("[tray] XApp")


def _try_appindicator(keeper, autostart, menu, update_menu):
    try:
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import AyatanaAppIndicator3 as AI
    except (ValueError, ImportError):
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AI

    ind = AI.Indicator.new(
        "keep-presence-gui",
        _icon_path(True),
        AI.IndicatorCategory.APPLICATION_STATUS,
    )
    ind.set_status(AI.IndicatorStatus.ACTIVE)
    ind.set_menu(menu)

    def _refresh(_text=None):
        running = keeper.running

        def _update():
            ind.set_icon_full(_icon_path(running), "")
            update_menu()
            return False

        GLib.idle_add(_update)

    keeper.set_status_callback(_refresh)
    _tray_ref.append(ind)

    if autostart:
        keeper.start()
    print("[tray] AppIndicator3")


def create_tray(keeper, autostart=True):
    menu, update_menu = _build_menu(keeper)

    try:
        _try_xapp(keeper, autostart, menu, update_menu)
    except Exception as e:
        print(f"[tray] XApp unavailable: {e}")
        try:
            _try_appindicator(keeper, autostart, menu, update_menu)
        except Exception as e2:
            print(f"[tray] AppIndicator3 unavailable: {e2}")
            print("[tray] no tray icon — running headless (Ctrl+C to stop)")
            if autostart:
                keeper.start()

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        keeper.stop()

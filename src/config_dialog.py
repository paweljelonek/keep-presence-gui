import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import about
import config as cfg_mod
import system_autostart
from presence import PresenceKeeper

_lock = threading.Lock()
_config_open = False
_about_open = False


def _mark_config_closed():
    global _config_open
    with _lock:
        _config_open = False


def _mark_about_closed():
    global _about_open
    with _lock:
        _about_open = False


def open_dialog(keeper):
    global _config_open
    with _lock:
        if _config_open:
            return
        _config_open = True
    GLib.idle_add(_show_config, keeper)


def open_about():
    global _about_open
    with _lock:
        if _about_open:
            return
        _about_open = True
    GLib.idle_add(_show_about_standalone)


def _show_config(keeper):
    _ConfigWindow(keeper).show_all()
    return False


def _show_about_standalone():
    _AboutWindow(on_close=_mark_about_closed).show_all()
    return False


class _ConfigWindow(Gtk.Window):

    def __init__(self, keeper):
        super().__init__(title=f"{about.NAME} - Configuration")
        self._keeper = keeper
        self.set_resizable(False)
        self.set_border_width(16)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", lambda *_: _mark_config_closed())

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(vbox)

        grid = Gtk.Grid(row_spacing=10, column_spacing=16)
        vbox.pack_start(grid, True, True, 0)

        # Mode
        grid.attach(_lbl("Mode:"), 0, 0, 1, 1)
        self._modes = [
            PresenceKeeper.MODE_MOUSE,
            PresenceKeeper.MODE_KEYBOARD,
            PresenceKeeper.MODE_BOTH,
            PresenceKeeper.MODE_SCROLL,
        ]
        self._mode_combo = Gtk.ComboBoxText()
        for m in self._modes:
            self._mode_combo.append_text(m)
        cur = keeper.mode.value if hasattr(keeper.mode, 'value') else keeper.mode
        self._mode_combo.set_active(
            self._modes.index(cur) if cur in self._modes else 0)
        grid.attach(self._mode_combo, 1, 0, 1, 1)

        # Idle interval
        grid.attach(_lbl("Idle interval (seconds):"), 0, 1, 1, 1)
        adj = Gtk.Adjustment(value=keeper.idle_seconds, lower=5, upper=3600,
                             step_increment=5, page_increment=30)
        self._seconds_spin = Gtk.SpinButton(adjustment=adj, numeric=True)
        grid.attach(self._seconds_spin, 1, 1, 1, 1)

        # Mouse pixels
        grid.attach(_lbl("Mouse movement (px):"), 0, 2, 1, 1)
        adj2 = Gtk.Adjustment(value=keeper.pixels, lower=1, upper=100, step_increment=1)
        self._pixels_spin = Gtk.SpinButton(adjustment=adj2, numeric=True)
        grid.attach(self._pixels_spin, 1, 2, 1, 1)

        # Checkboxes
        self._circular_check = Gtk.CheckButton(label="Circular mouse movement")
        self._circular_check.set_active(keeper.circular)
        grid.attach(self._circular_check, 0, 3, 2, 1)

        stored = cfg_mod.load()
        self._autostart_check = Gtk.CheckButton(
            label="Start keeping presence immediately on launch")
        self._autostart_check.set_active(stored.get("autostart", True))
        grid.attach(self._autostart_check, 0, 4, 2, 1)

        self._notify_check = Gtk.CheckButton(
            label="Show notification when presence action is performed")
        self._notify_check.set_active(stored.get("notify", False))
        grid.attach(self._notify_check, 0, 5, 2, 1)

        self._sys_autostart_check = Gtk.CheckButton(
            label="Launch the application on system startup")
        self._sys_autostart_check.set_active(system_autostart.is_enabled())
        grid.attach(self._sys_autostart_check, 0, 6, 2, 1)

        # Status label
        self._status_lbl = Gtk.Label(
            label=f"Status: {'running' if keeper.running else 'stopped'}",
            xalign=0)
        self._status_lbl.get_style_context().add_class("dim-label")
        grid.attach(self._status_lbl, 0, 7, 2, 1)

        # Separator
        vbox.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # Button row
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vbox.pack_start(btn_row, False, False, 0)

        self._toggle_btn = Gtk.Button(label="Pause" if keeper.running else "Start")
        self._toggle_btn.connect("clicked", self._on_toggle)
        btn_row.pack_start(self._toggle_btn, False, False, 0)

        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_row.pack_end(right, False, False, 0)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda *_: self.destroy())
        right.pack_start(cancel_btn, False, False, 0)

        save_btn = Gtk.Button(label="Save")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        right.pack_start(save_btn, False, False, 0)

    def _on_toggle(self, *_):
        if self._keeper.running:
            self._keeper.stop()
        else:
            self._keeper.start()
        running = self._keeper.running
        self._status_lbl.set_text(f"Status: {'running' if running else 'stopped'}")
        self._toggle_btn.set_label("Pause" if running else "Start")

    def _on_save(self, *_):
        new_cfg = {
            "mode": self._modes[self._mode_combo.get_active()],
            "idle_seconds": int(self._seconds_spin.get_value()),
            "pixels": int(self._pixels_spin.get_value()),
            "circular": self._circular_check.get_active(),
            "autostart": self._autostart_check.get_active(),
            "notify": self._notify_check.get_active(),
        }
        cfg_mod.apply_to_keeper(self._keeper, new_cfg)
        cfg_mod.save(new_cfg)
        try:
            system_autostart.set_enabled(self._sys_autostart_check.get_active())
        except OSError as e:
            print(f"[config_dialog] could not update system autostart: {e}")
        self.destroy()


class _AboutWindow(Gtk.Window):

    def __init__(self, parent=None, on_close=None):
        super().__init__(title=f"About {about.NAME}")
        self.set_resizable(False)
        self.set_border_width(16)

        if parent:
            self.set_transient_for(parent)
            self.set_modal(True)
            self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        else:
            self.set_position(Gtk.WindowPosition.CENTER)

        if on_close:
            self.connect("destroy", lambda *_: on_close())

        grid = Gtk.Grid(row_spacing=6, column_spacing=16)
        self.add(grid)

        title_lbl = Gtk.Label(xalign=0)
        title_lbl.set_markup(f"<b><big>{about.NAME}</big></b>")
        grid.attach(title_lbl, 0, 0, 2, 1)

        grid.attach(Gtk.Label(label=f"Version {about.VERSION}", xalign=0), 0, 1, 2, 1)

        desc = Gtk.Label(label=about.DESCRIPTION, xalign=0, wrap=True, max_width_chars=52)
        desc.set_margin_top(6)
        desc.set_margin_bottom(6)
        grid.attach(desc, 0, 2, 2, 1)

        grid.attach(_lbl("Author:"), 0, 3, 1, 1)
        grid.attach(Gtk.Label(label=about.AUTHOR, xalign=0), 1, 3, 1, 1)

        grid.attach(_lbl("License:"), 0, 4, 1, 1)
        lic_btn = Gtk.LinkButton(uri=about.LICENSE_URL, label=about.LICENSE)
        lic_btn.set_halign(Gtk.Align.START)
        grid.attach(lic_btn, 1, 4, 1, 1)

        grid.attach(_lbl("Repository:"), 0, 5, 1, 1)
        repo_btn = Gtk.LinkButton(uri=about.REPO_URL, label=about.REPO_URL)
        repo_btn.set_halign(Gtk.Align.START)
        grid.attach(repo_btn, 1, 5, 1, 1)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(6)
        sep.set_margin_bottom(6)
        grid.attach(sep, 0, 6, 2, 1)

        upstream_lbl = Gtk.Label(xalign=0)
        upstream_lbl.set_markup(
            f"<b>Based on {about.UPSTREAM_NAME} by {about.UPSTREAM_AUTHOR}</b>")
        grid.attach(upstream_lbl, 0, 7, 2, 1)

        upstream_link = Gtk.LinkButton(uri=about.UPSTREAM_URL, label=about.UPSTREAM_URL)
        upstream_link.set_halign(Gtk.Align.START)
        grid.attach(upstream_link, 0, 8, 2, 1)

        lic_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        lic_row.pack_start(Gtk.Label(label="Licensed under "), False, False, 0)
        upstream_lic = Gtk.LinkButton(
            uri=about.UPSTREAM_LICENSE_URL, label=about.UPSTREAM_LICENSE)
        lic_row.pack_start(upstream_lic, False, False, 0)
        lic_row.pack_start(Gtk.Label(label=" (public domain)"), False, False, 0)
        grid.attach(lic_row, 0, 9, 2, 1)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda *_: self.destroy())
        close_btn.set_halign(Gtk.Align.END)
        close_btn.set_margin_top(12)
        grid.attach(close_btn, 0, 10, 2, 1)


def _lbl(text):
    return Gtk.Label(label=text, xalign=0)

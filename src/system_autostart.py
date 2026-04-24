import os
import sys
from pathlib import Path

import about

AUTOSTART_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart"
DESKTOP_PATH = AUTOSTART_DIR / "keep-presence-gui.desktop"

_BASE_DIR = Path(__file__).resolve().parent.parent
_MAIN_PY = _BASE_DIR / "main.py"
_ICON_PATH = _BASE_DIR / "icon.png"


def is_enabled():
    return DESKTOP_PATH.exists()


def enable():
    AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
    content = _desktop_entry()
    tmp = DESKTOP_PATH.with_suffix(".desktop.tmp")
    tmp.write_text(content)
    os.replace(tmp, DESKTOP_PATH)
    DESKTOP_PATH.chmod(0o644)


def disable():
    try:
        DESKTOP_PATH.unlink()
    except FileNotFoundError:
        pass


def set_enabled(enabled):
    if enabled:
        enable()
    else:
        disable()


def _desktop_entry():
    exec_cmd = f"{sys.executable} {_MAIN_PY}"
    icon_line = f"Icon={_ICON_PATH}\n" if _ICON_PATH.exists() else ""
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={about.NAME}\n"
        f"Comment={about.DESCRIPTION}\n"
        f"Exec={exec_cmd}\n"
        f"{icon_line}"
        "Terminal=false\n"
        "Categories=Utility;\n"
        "X-GNOME-Autostart-enabled=true\n"
        "Hidden=false\n"
    )

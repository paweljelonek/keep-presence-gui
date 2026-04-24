# Keep Presence GUI

System tray application that keeps your computer awake by simulating mouse movements
or keyboard presses when you step away from your machine.

- **Author:** Paweł Jelonek
- **Repository:** https://github.com/paweljelonek/keep-presence-gui
- **License:** [MIT](LICENSE)

## Origin

The core presence-keeping logic is based on
**[keep-presence](https://github.com/carrot69/keep-presence)** by
[carrot69](https://github.com/carrot69), licensed under
[CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain).

This project wraps that logic in a GTK3 system tray GUI for convenient daily use.

## Features

- System tray icon with right-click menu
- Start / pause presence keeping
- Configurable mode: mouse, keyboard, both, or scroll
- Adjustable idle detection interval (5 s – 3600 s)
- Adjustable mouse movement distance (1 – 100 px)
- Circular or diagonal mouse movement
- Optional desktop notification each time a presence action is performed
- Persistent configuration saved to `~/.config/keep-presence-gui/`
- Optional autostart on application launch
- Optional autostart on system startup (via `.desktop` entry)
- Single-instance enforcement (second launch exits immediately)
- Graceful shutdown on SIGINT and SIGTERM
- Works on X11 (Wayland not supported due to pynput limitations)

## Requirements

- Python 3.8+
- X11 display server
- GTK 3 (`gir1.2-gtk-3.0`)
- libnotify (`gir1.2-notify-0.7`)
- A tray backend — **XApp** (Cinnamon / Linux Mint) or **AppIndicator3** (GNOME, XFCE, etc.)
- PyGObject — via system package (`python3-gi`) or pip (see Installation)

## Installation

Two paths depending on how you manage Python. Option A is simpler for most users.

### Option A — system Python (recommended)

Uses `/usr/bin/python3` and inherits the system's pre-built GTK bindings via
`--system-site-packages`.

```bash
# 1. Install system dependencies (uncomment the line for your desktop)
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-notify-0.7 \
    gir1.2-xapp-1.0                        # Cinnamon / Linux Mint
#   gir1.2-ayatana-appindicator3-0.1       # GNOME / Ubuntu
#   gir1.2-appindicator3-0.1               # XFCE

# 2. Clone and set up
git clone git@github.com:paweljelonek/keep-presence-gui.git
cd keep-presence-gui
/usr/bin/python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# 3. Run
python3 main.py
```

> `/usr/bin/python3` must be used explicitly. A pyenv shim points to a private
> Python install that does not inherit system site-packages even with that flag.

### Option B — pyenv

Use this if you manage Python versions with pyenv and need a self-contained environment.
The required PyGObject version depends on your system's GLib:

```bash
pkg-config --modversion glib-2.0   # check your GLib version
```

| GLib                   | PyGObject                      |
|------------------------|--------------------------------|
| < 2.80 (Ubuntu 22.04)  | `pip install "PyGObject<3.50"` |
| ≥ 2.80 (Ubuntu 24.04+) | `pip install PyGObject`        |

#### Ubuntu 22.04 / GLib < 2.80

```bash
sudo apt install libgirepository1.0-dev libcairo2-dev pkg-config \
    gir1.2-gtk-3.0 gir1.2-notify-0.7 \
    gir1.2-xapp-1.0                        # Cinnamon / Linux Mint
#   gir1.2-ayatana-appindicator3-0.1       # GNOME / Ubuntu
#   gir1.2-appindicator3-0.1               # XFCE

git clone git@github.com:paweljelonek/keep-presence-gui.git
cd keep-presence-gui
pyenv virtualenv 3.12.11 keep-presence
pyenv local keep-presence
pip install "PyGObject<3.50"
pip install -r requirements.txt
python main.py
```

#### Ubuntu 24.04+ / GLib ≥ 2.80

```bash
sudo apt install libgirepository-2.0-dev libcairo2-dev pkg-config \
    gir1.2-gtk-3.0 gir1.2-notify-0.7 \
    gir1.2-xapp-1.0                        # Cinnamon / Linux Mint
#   gir1.2-ayatana-appindicator3-0.1       # GNOME / Ubuntu

git clone git@github.com:paweljelonek/keep-presence-gui.git
cd keep-presence-gui
pyenv virtualenv 3.12.11 keep-presence
pyenv local keep-presence
pip install PyGObject
pip install -r requirements.txt
python main.py
```

### Tray icon not appearing (XFCE)

Make sure the panel has either the **Status Tray Plugin** (SNI / AppIndicator)
or the **Notification Area** plugin (XEmbed) added and visible.

## Usage

```bash
python main.py
```

The app starts minimized in the system tray. Right-click the icon to access the menu.
Left-click (or double-click, depending on the desktop) opens the configuration dialog.

### Tray menu

| Item                        | Action                                              |
|-----------------------------|-----------------------------------------------------|
| **Configure…**              | Open the configuration dialog                       |
| **Start / Pause**           | Toggle presence keeping                             |
| **Mode**                    | Quick-switch between mouse, keyboard, both, scroll  |
| **About Keep Presence GUI** | Show application info                               |
| **Quit**                    | Exit the application                                |

### Configuration dialog

Adjust all settings in one place and save them to disk. Changes take effect immediately
after clicking **Save**.

| Setting                      | Description                                                   |
|------------------------------|---------------------------------------------------------------|
| **Mode**                     | mouse / keyboard / both / scroll                              |
| **Idle interval**            | seconds of inactivity before the action fires                 |
| **Mouse movement**           | pixels the cursor moves per action                            |
| **Circular mouse movement**  | cycle the cursor through 4 directions instead of one diagonal |
| **Start on launch**          | start presence keeping automatically when the app opens       |
| **Show notification**        | show a desktop notification each time an action is performed  |
| **Launch on system startup** | install / remove a `.desktop` entry in `~/.config/autostart/` |

> **Tip:** set the idle interval to less than your screensaver timeout (e.g. 240 s for a
> 300 s screensaver) so the action always fires before the screen blanks.

The dialog also provides:

- **Status label** — shows current state (`running` / `stopped`)
- **Start / Pause button** — toggles presence keeping without closing the dialog
- **About** — opens the About window
- **Cancel** — closes without saving
- **Quit app** — exits the application entirely

### Tray icon states

| Icon          | Meaning                        |
|---------------|--------------------------------|
| Green monitor | Presence keeping is **active** |
| Gray monitor  | Presence keeping is **paused** |

## Project structure

```
keep-presence-gui/
├── main.py                  # Entry point — signal handling, wiring
├── src/
│   ├── about.py             # Program metadata (name, version, URLs)
│   ├── config.py            # Load / save configuration
│   ├── config_dialog.py     # GTK3 configuration & about dialogs
│   ├── notification.py      # Desktop notifications via libnotify
│   ├── presence.py          # Presence-keeping loop (based on keep-presence)
│   ├── single_instance.py   # Lock file to prevent duplicate instances
│   ├── system_autostart.py  # Manage ~/.config/autostart .desktop entry
│   └── tray.py              # System tray (XApp or AppIndicator3)
├── icon.png                 # Tray icon — active state
├── icon-paused.png          # Tray icon — paused state
├── requirements.txt
├── LICENSE
└── README.md
```

## Credits

- Original project: [carrot69/keep-presence](https://github.com/carrot69/keep-presence),
  licensed under [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain)
- GUI wrapper: Paweł Jelonek, licensed under [MIT](LICENSE)

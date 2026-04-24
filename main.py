#!/home/pawel/Projects/Jazzcat/keep-presence-gui/venv/bin/python3
import os
import sys
import signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

import tray as tray_mod
from tray import create_tray
from presence import PresenceKeeper
import config as config_mod
import single_instance


def main():
    if not single_instance.acquire():
        print("Could not take over from existing instance. Exiting.")
        sys.exit(1)

    keeper = PresenceKeeper()

    cfg = config_mod.load()
    config_mod.apply_to_keeper(keeper, cfg)

    signal.signal(signal.SIGINT, lambda *_: tray_mod.request_quit(keeper))
    signal.signal(signal.SIGTERM, lambda *_: tray_mod.request_quit(keeper))

    create_tray(keeper, autostart=cfg["autostart"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

import json
import logging
import os
from pathlib import Path
from typing import Any

from presence import Mode, PresenceKeeper

log = logging.getLogger(__name__)

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "keep-presence-gui"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS: dict[str, Any] = {
    "mode": Mode.MOUSE,
    "idle_seconds": 240,
    "pixels": 1,
    "circular": False,
    "autostart": True,
    "notify": False,
}


def load() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    try:
        with CONFIG_PATH.open() as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.warning("failed to load %s (%s); using defaults", CONFIG_PATH, e)
        return dict(DEFAULTS)

    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    return _sanitize(cfg)


def save(cfg: dict[str, Any]) -> None:
    cfg = _sanitize(cfg)
    # Enum isn't JSON-serializable by default; unwrap to its str value
    serializable = {k: (v.value if isinstance(v, Mode) else v) for k, v in cfg.items()}
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(serializable, f, indent=2)
    os.replace(tmp, CONFIG_PATH)


def apply_to_keeper(keeper: PresenceKeeper, cfg: dict[str, Any]) -> None:
    keeper.mode = cfg["mode"]
    keeper.idle_seconds = cfg["idle_seconds"]
    keeper.pixels = cfg["pixels"]
    keeper.circular = cfg["circular"]
    keeper.notify = cfg.get("notify", False)


def from_keeper(keeper: PresenceKeeper, autostart: bool | None = None) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "mode": keeper.mode,
        "idle_seconds": keeper.idle_seconds,
        "pixels": keeper.pixels,
        "circular": keeper.circular,
        "notify": keeper.notify,
    }
    if autostart is not None:
        cfg["autostart"] = autostart
    return cfg


def _sanitize(cfg: dict[str, Any]) -> dict[str, Any]:
    try:
        cfg["mode"] = Mode(cfg["mode"])
    except (KeyError, ValueError):
        cfg["mode"] = DEFAULTS["mode"]
    try:
        cfg["idle_seconds"] = max(5, int(cfg["idle_seconds"]))
    except (TypeError, ValueError):
        cfg["idle_seconds"] = DEFAULTS["idle_seconds"]
    try:
        cfg["pixels"] = max(1, int(cfg["pixels"]))
    except (TypeError, ValueError):
        cfg["pixels"] = DEFAULTS["pixels"]
    cfg["circular"] = bool(cfg.get("circular", False))
    cfg["autostart"] = bool(cfg.get("autostart", True))
    cfg["notify"] = bool(cfg.get("notify", False))
    return cfg

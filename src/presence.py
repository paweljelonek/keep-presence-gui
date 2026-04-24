# Based on https://github.com/carrot69/keep-presence (CC0-1.0)
import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional

from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController

import notification

log = logging.getLogger(__name__)


class Mode(str, Enum):
    MOUSE = "mouse"
    KEYBOARD = "keyboard"
    BOTH = "both"
    SCROLL = "scroll"


StatusCallback = Callable[[str], None]


class PresenceKeeper:

    # String aliases — legacy code still references PresenceKeeper.MODE_*
    MODE_MOUSE = Mode.MOUSE.value
    MODE_KEYBOARD = Mode.KEYBOARD.value
    MODE_BOTH = Mode.BOTH.value
    MODE_SCROLL = Mode.SCROLL.value

    def __init__(self) -> None:
        self.mouse = MouseController()
        self.keyboard = KeyboardController()

        self.idle_seconds: int = 300
        self.pixels: int = 1
        self.circular: bool = False
        self.mode: Mode = Mode.MOUSE
        self.notify: bool = False

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._mouse_direction: int = 0
        self._last_position: tuple[int, int] = (0, 0)
        self._last_action: str = ""
        self._on_status_change: Optional[StatusCallback] = None

    @property
    def running(self) -> bool:
        return self._running

    def set_status_callback(self, callback: StatusCallback) -> None:
        self._on_status_change = callback

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._last_position = self.mouse.position
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log("Started")

    def stop(self) -> None:
        self._running = False
        self._log("Stopped")

    def _log(self, msg: str) -> None:
        self._last_action = msg
        log.info(msg)
        if self._on_status_change is not None:
            self._on_status_change(msg)

    _POLL = 5  # position check interval in seconds

    def _loop(self) -> None:
        idle_elapsed = 0.0
        while self._running:
            time.sleep(self._POLL)
            if not self._running:
                break
            current = self.mouse.position
            if current != self._last_position:
                if idle_elapsed > 0:
                    self._log("User active")
                idle_elapsed = 0.0
                self._last_position = current
            else:
                idle_elapsed += self._POLL
                if idle_elapsed >= self.idle_seconds:
                    self._do_action()
                    self._last_position = self.mouse.position
                    idle_elapsed = 0.0
                    if self.notify:
                        notification.send(self._last_action)

    def _do_action(self) -> None:
        self._log("Idle detected")

        if self.mode in (Mode.MOUSE, Mode.BOTH):
            self._move_mouse()

        if self.mode == Mode.SCROLL:
            self._scroll()

        if self.mode in (Mode.KEYBOARD, Mode.BOTH):
            self._press_key()

    def _move_mouse(self) -> None:
        pos = self.mouse.position
        d = self._mouse_direction
        px = self.pixels

        dx = px if d in (0, 3) else -px
        dy = px if d in (0, 1) else -px

        new_pos = (pos[0] + dx, pos[1] + dy)
        self.mouse.position = new_pos

        # pynput silently no-ops at screen edges; snap into the viewport
        if self.mouse.position != new_pos:
            self.mouse.position = (px, px)

        if self.circular:
            self._mouse_direction = (d + 1) % 4

        self._log(f"Mouse moved to {self.mouse.position}")

    def _scroll(self) -> None:
        self.mouse.scroll(0, -2)
        self._log("Mouse wheel scrolled")

    def _press_key(self) -> None:
        self.keyboard.press(Key.shift)
        self.keyboard.release(Key.shift)
        self._log("Shift key pressed")

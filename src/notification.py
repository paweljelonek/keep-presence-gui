import logging

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

import about

log = logging.getLogger(__name__)

_notif: Notify.Notification | None = None


def _init() -> None:
    global _notif
    if _notif is None:
        Notify.init(about.NAME)
        _notif = Notify.Notification.new(about.NAME, "", "")


def send(body: str, icon: str = "dialog-information") -> None:
    try:
        _init()
        _notif.update(about.NAME, body, icon)
        _notif.show()
    except Exception:
        log.warning("notification failed", exc_info=True)


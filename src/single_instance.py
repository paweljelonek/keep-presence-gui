import fcntl
import os
import signal
from pathlib import Path

# Kept at module scope so the fd stays open for the process lifetime —
# flock is released when the fd is closed.
_lock_fd = None

_TAKEOVER_TIMEOUT = 5  # seconds to wait for old instance to exit


def acquire(name="keep-presence-gui"):
    global _lock_fd
    if _lock_fd is not None:
        return True

    lock_dir = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp")
    try:
        lock_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        lock_dir = Path("/tmp")

    lock_path = lock_dir / f"{name}.lock"

    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as e:
        print(f"[single_instance] cannot open lock file {lock_path}: {e}")
        return True  # fail-open: don't block the app on lock-file issues

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        # Another instance holds the lock — read its PID and signal it to quit.
        try:
            existing_pid = int(os.read(fd, 32).decode(errors="replace").strip())
        except (OSError, ValueError):
            existing_pid = None

        if existing_pid is not None:
            print(f"[single_instance] signalling existing instance to quit (pid {existing_pid})")
            try:
                os.kill(existing_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass  # already dead, lock will release momentarily
            except PermissionError:
                print(f"[single_instance] cannot signal pid {existing_pid}: permission denied")
                os.close(fd)
                return False

        # Block until the old instance releases the lock, with a timeout.
        print("[single_instance] waiting for existing instance to exit…")

        def _on_alarm(*_):
            raise TimeoutError

        old_handler = signal.signal(signal.SIGALRM, _on_alarm)
        signal.alarm(_TAKEOVER_TIMEOUT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
        except TimeoutError:
            print(f"[single_instance] existing instance did not exit within {_TAKEOVER_TIMEOUT}s")
            signal.signal(signal.SIGALRM, old_handler)
            os.close(fd)
            return False
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode())
    _lock_fd = fd
    return True

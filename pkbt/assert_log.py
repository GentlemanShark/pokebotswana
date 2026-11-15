"""Copy a failed assertion's screenshot into that slot's log folder.

run.bat points PKBT_RUN_DIR at logs/<run>. Each retry loop gets one folder
under logs/<run>/<slot>, and each failed try is copied there.
"""

import os
import re
import shutil
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from pkbt.config import LOGS_DIR, REPO_ROOT
from pkbt.instances import slot_dir

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_INDEXED = re.compile(r"^(\d+)-")
_tls = threading.local()
_fallback_lock = threading.Lock()
_fallback_run: Path | None = None


class _Retry:
    def __init__(self, name: str):
        self.name = name
        self.attempt = 1
        self.folder: Path | None = None


@contextmanager
def retry_loop(name: str):
    """Group this retry loop's failed screenshots into one folder."""
    stack = getattr(_tls, "stack", None)
    if stack is None:
        stack = []
        _tls.stack = stack
    stack.append(_Retry(name))
    try:
        yield
    finally:
        stack.pop()


def set_retry_attempt(attempt: int) -> None:
    """Record which try of the current retry loop is about to run."""
    retry = _current()
    if retry is not None:
        retry.attempt = attempt


def duplicate_failed_screenshot(slot_idx: int, assert_name: str) -> None:
    """Copy .session/<slot>/<slot>.png next to this slot's run log.

    Inside a retry loop the copies share one folder, named for that loop,
    as try-1.png, try-2.png, and so on. An assert outside a loop gets its
    own folder. A missing screenshot is left alone.
    """
    src = slot_dir(slot_idx) / f"{slot_idx}.png"
    try:
        if not src.is_file():
            return
        dest = _destination(slot_idx, assert_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    except OSError as error:
        print(f"[{slot_idx}] Could not save failed {assert_name} screenshot: {error}")
        return
    try:
        shown = dest.relative_to(REPO_ROOT)
    except ValueError:
        shown = dest
    print(f"[{slot_idx}] Saved {shown}")


def _current() -> _Retry | None:
    stack = getattr(_tls, "stack", None)
    if not stack:
        return None
    return stack[-1]


def _destination(slot_idx: int, assert_name: str) -> Path:
    retry = _current()
    if retry is None:
        return _new_folder(slot_idx, assert_name) / "try-1.png"
    if retry.folder is None:
        retry.folder = _new_folder(slot_idx, retry.name)
    return retry.folder / f"try-{retry.attempt}.png"


def _new_folder(slot_idx: int, name: str) -> Path:
    parent = _run_dir() / str(slot_idx)
    parent.mkdir(parents=True, exist_ok=True)
    index = 1
    for child in parent.iterdir():
        match = _INDEXED.match(child.name)
        if match and child.is_dir():
            index = max(index, int(match.group(1)) + 1)
    return parent / f"{index:03d}-{_safe(name)}"


def _safe(name: str) -> str:
    cleaned = _UNSAFE.sub("-", name)
    cleaned = re.sub(r"\s+", "-", cleaned).strip(" .-")
    return cleaned or "assert"


def _run_dir() -> Path:
    configured = os.environ.get("PKBT_RUN_DIR")
    if configured:
        return Path(configured)
    global _fallback_run
    with _fallback_lock:
        if _fallback_run is None:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            _fallback_run = LOGS_DIR / f"{stamp}-asserts"
        return _fallback_run

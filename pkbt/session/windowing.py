"""Thin wrappers around Win32 window operations for Python (Windows only)."""

import ctypes
import threading
import time
from dataclasses import dataclass

try:
    import win32gui, win32con, win32process, win32api
except ImportError as e:
    raise RuntimeError(
        "pywin32 is required on Windows. Install with: pip install pywin32"
    ) from e

# --- Internal ---

def _is_hung(hwnd: int) -> bool:
    return bool(ctypes.windll.user32.IsHungAppWindow(hwnd))

def _within(seconds: float, fn, default=None):
    """Run fn and return default if it is still blocked when the deadline passes.

    SetForegroundWindow and SetWindowPos send a message to the target thread
    and do not return while that thread is Not Responding. A caller that holds
    the replacement lock would stall every other restart until the window is closed.
    """
    outcome: dict = {}

    def run():
        try:
            outcome["value"] = fn()
        except Exception as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        return default
    if "error" in outcome:
        raise outcome["error"]
    return outcome.get("value", default)

def _show_async(hwnd: int, command: int) -> None:
    """Show, restore, or minimize without waiting on a window that is not responding."""
    ctypes.windll.user32.ShowWindowAsync(hwnd, command)

def _window_text(hwnd: int, timeout_ms: int = 200) -> str:
    """Read a window title without blocking if that window is not responding."""
    if _is_hung(hwnd):
        return ""
    buffer = ctypes.create_unicode_buffer(512)
    result = ctypes.c_size_t()
    send = ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes = [
        ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_wchar_p,
        ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_size_t),
    ]
    send.restype = ctypes.c_void_p
    ok = send(hwnd, 0x000D, 512, buffer, 0x0002, timeout_ms, ctypes.byref(result))
    if not ok:
        return ""
    return buffer.value

def hung_window_pids() -> set[int]:
    """PIDs that own a visible window Windows has marked not responding."""
    found: set[int] = set()

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd) or not _is_hung(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid:
            found.add(pid)

    win32gui.EnumWindows(cb, None)
    return found

def _top_window_from_pid(pid: int, timeout: float = 10.0) -> int:
    """Return the top-level window handle for a given PID, waiting up to timeout."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        found: list[int] = []

        def cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            _, wpid = win32process.GetWindowThreadProcessId(hwnd)
            if wpid == pid and win32gui.GetWindow(hwnd, win32con.GW_OWNER) == 0:
                # GetWindowText sends a message and never returns if the window is hung.
                title = _window_text(hwnd)
                if title.startswith("mGBA"):
                    found.append(hwnd)

        win32gui.EnumWindows(cb, None)

        if found:
            return found[0]
        time.sleep(0.05)

    raise TimeoutError(f"No top-level window found for PID {pid}")

# --- Public API ---

def get_rect(hwnd: int) -> tuple[int, int, int, int]:
    """Return (x, y, width, height) for the given window handle."""
    def read() -> tuple[int, int, int, int]:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left, top, right - left, bottom - top

    rect = _within(1.0, read, None)
    if rect is None:
        raise TimeoutError(f"Timed out reading the rect of window {hwnd}")
    return rect

def get_size(hwnd: int) -> tuple[int, int]:
    """Return (width, height) for the given window handle."""
    _, _, w, h = get_rect(hwnd)
    return w, h

def get_width(hwnd: int) -> int:
    """Return the width of the given window handle."""
    return get_size(hwnd)[0]

def get_height(hwnd: int) -> int:
    """Return the height of the given window handle."""
    return get_size(hwnd)[1]

def get_position(hwnd: int) -> tuple[int, int]:
    """Return (x, y) position (top-left corner) of the given window handle."""
    left, top, _, _ = get_rect(hwnd)
    return left, top

def _set_window_pos(hwnd: int, x: int, y: int, w: int, h: int, flags: int) -> None:
    def place() -> bool:
        win32gui.SetWindowPos(hwnd, None, x, y, w, h, flags)
        return True

    if not _within(2.0, place, False):
        raise TimeoutError(f"Timed out moving window {hwnd}")

def move(hwnd: int, x: int, y: int) -> None:
    """Move the window to (x, y) without resizing."""
    _show_async(hwnd, win32con.SW_RESTORE)
    _set_window_pos(hwnd, x, y, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)

def move_resize(hwnd: int, x: int, y: int, w: int, h: int) -> None:
    """Move and resize the window."""
    _show_async(hwnd, win32con.SW_RESTORE)
    _set_window_pos(hwnd, x, y, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)

def _focus_blocking(hwnd: int) -> bool:
    """Bring hwnd to the foreground. Windows blocks this from a background process unless the threads are attached."""
    foreground = win32gui.GetForegroundWindow()
    current_thread = win32api.GetCurrentThreadId()
    foreground_thread, _ = win32process.GetWindowThreadProcessId(foreground)
    target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
    attached_foreground = False
    attached_target = False
    try:
        if foreground_thread and foreground_thread != current_thread:
            attached_foreground = bool(win32process.AttachThreadInput(current_thread, foreground_thread, True))
        if target_thread and target_thread != current_thread:
            attached_target = bool(win32process.AttachThreadInput(current_thread, target_thread, True))
        _show_async(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
    finally:
        if attached_target:
            win32process.AttachThreadInput(current_thread, target_thread, False)
        if attached_foreground:
            win32process.AttachThreadInput(current_thread, foreground_thread, False)
    return win32gui.GetForegroundWindow() == hwnd

def _focus(hwnd: int) -> bool:
    """Focus hwnd, giving up instead of waiting on a Not Responding window."""
    if not win32gui.IsWindow(hwnd) or _is_hung(hwnd):
        return False
    foreground = win32gui.GetForegroundWindow()
    # Attaching to the foreground thread blocks until that window is closed
    # when its message loop has stopped.
    if foreground and foreground != hwnd and _is_hung(foreground):
        return False
    return bool(_within(2.0, lambda: _focus_blocking(hwnd), False))

def _try_foreground(hwnd: int) -> bool:
    if not win32gui.IsWindow(hwnd) or _is_hung(hwnd):
        return False

    def focus() -> bool:
        win32gui.SetForegroundWindow(hwnd)
        return True

    return bool(_within(2.0, focus, False))

def toggle_fast_forward(hwnd: int) -> bool:
    """Press Shift+Tab on hwnd, mGBA's fast-forward toggle. The key is only sent if that window is in front."""
    if not win32gui.IsWindow(hwnd) or _is_hung(hwnd):
        return False
    previous = win32gui.GetForegroundWindow()
    if not _focus(hwnd):
        # A tap of Alt lets a background process take the foreground.
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        if not _try_foreground(hwnd):
            return False
    deadline = time.time() + 1.0
    while win32gui.GetForegroundWindow() != hwnd and time.time() < deadline:
        time.sleep(0.05)
    if win32gui.GetForegroundWindow() != hwnd:
        return False
    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)
    if previous and previous != hwnd and win32gui.IsWindow(previous) and not _is_hung(previous):
        _try_foreground(previous)
    return True

def get_primary_screen_size() -> tuple[int, int]:
    """Width, height of the primary display in pixels."""
    w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    return w, h

def get_primary_screen_width() -> int:
    return get_primary_screen_size()[0]

def get_monitors() -> list[tuple[int, int, int, int]]:
    """(left, top, width, height) for each display. Index 0 is the primary monitor."""
    monitors = []
    for handle, _, _rect in win32api.EnumDisplayMonitors():
        info = win32api.GetMonitorInfo(handle)
        left, top, right, bottom = info["Monitor"]
        primary = bool(info["Flags"] & win32con.MONITORINFOF_PRIMARY)
        monitors.append((primary, left, top, right - left, bottom - top))
    monitors.sort(key=lambda monitor: (not monitor[0], monitor[1], monitor[2]))
    return [(left, top, width, height) for _primary, left, top, width, height in monitors]

def get_monitor(index: int = 0) -> tuple[int, int, int, int]:
    """The display at index. 0 is the primary monitor."""
    monitors = get_monitors()
    if index < 0 or index >= len(monitors):
        raise ValueError(f"Monitor {index} is not connected. {len(monitors)} displays were found.")
    return monitors[index]

def get_primary_screen_height() -> int:
    return get_primary_screen_size()[1]

def minimize_windows_starting_with(prefix: str) -> None:
    """Minimize all visible windows that start with the given prefix."""
    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd) or _is_hung(hwnd):
            return
        title = _window_text(hwnd)
        if title.startswith(prefix):
            # ShowWindow waits on the target thread. A Not Responding
            # Scripting console would stall every later replacement.
            _show_async(hwnd, win32con.SW_MINIMIZE)

    win32gui.EnumWindows(cb, None)

def arrange_in_grid(windows: list["Window"], num_cols: int, num_rows: int) -> None:
    """Arrange the given windows in a grid of the given size."""
    for i, w in enumerate(windows):
        col = i % num_cols
        row = i // num_cols
        w.move(col * w.width(), row * w.height())

def arrange_windows_auto_grid(windows: list["Window"], max_width: int, origin: tuple[int, int] = (0, 0)) -> None:
    """Arrange windows left to right, top to bottom, wrapping when they don't fit.

    origin is the top-left of the display. (0, 0) is the primary monitor.
    """
    if not windows:
        return

    origin_x, origin_y = origin
    current_x = origin_x
    current_y = origin_y
    row_height = 0

    for w in windows:
        # Check if this window fits on the current row
        if current_x + w.width() > origin_x + max_width and current_x > origin_x:
            # Move to next row
            current_x = origin_x
            current_y += row_height
            row_height = 0

        # Position the window
        w.move(current_x, current_y)

        # Update position for next window
        current_x += w.width()
        row_height = max(row_height, w.height())

@dataclass(frozen=True)
class Window:
    hwnd: int

    @classmethod
    def from_pid(cls, pid: int, timeout: float = 10.0) -> "Window":
        return cls(_top_window_from_pid(pid, timeout))

    def rect(self) -> tuple[int, int, int, int]:
        return get_rect(self.hwnd)

    def size(self) -> tuple[int, int]:
        return get_size(self.hwnd)

    def width(self) -> int:
        return get_width(self.hwnd)

    def height(self) -> int:
        return get_height(self.hwnd)

    def position(self) -> tuple[int, int]:
        return get_position(self.hwnd)

    def move(self, x: int, y: int) -> None:
        move(self.hwnd, x, y)

    def move_resize(self, x: int, y: int, w: int, h: int) -> None:
        move_resize(self.hwnd, x, y, w, h)

    def toggle_fast_forward(self) -> bool:
        return toggle_fast_forward(self.hwnd)

    def minimize(self) -> None:
        """Minimize without waiting. A Not Responding window would block ShowWindow."""
        if not win32gui.IsWindow(self.hwnd) or _is_hung(self.hwnd):
            return
        _show_async(self.hwnd, win32con.SW_MINIMIZE)

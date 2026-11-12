"""Several mGBA instances, including the freeze watchdog and same-port replacement.

A script supplies one attempt (reset, play, check). This module owns launching
the emulators, noticing when one has stopped advancing, and putting a new
window back where the frozen one was.
"""

import threading
import time
from dataclasses import dataclass
from pathlib import Path

from pkbt.config import MGBA_DEV, MGBA_SDL, SERVER_SCRIPT, TEMP_DIR
from pkbt.console import for_console
from pkbt.emulator import EmulatorProc
from pkbt.mgba_connection import MGBAConnection
from pkbt.orchestrator import Orchestrator
from pkbt.windowing import (
    Window,
    arrange_windows_auto_grid,
    get_monitor,
    hung_window_pids,
    minimize_windows_starting_with,
)

POLL_SECONDS = 2


class InstanceFrozen(Exception):
    """The watchdog asked for a restart, or the socket to this instance is gone."""


@dataclass
class InstanceSlot:
    orch: Orchestrator
    idx: int
    restart: threading.Event
    group: "InstanceGroup"
    rect: tuple[int, int, int, int] | None = None
    last_frame: int | None = None
    last_change: float = 0.0

    def connect_with_retry(self, max_attempts: int = 5, delay_seconds: float = 1.0) -> bool:
        client = self.orch.client
        for attempt in range(1, max_attempts + 1):
            if client.connect():
                return True
            print(
                f"[{self.idx}] Connection attempt {attempt}/{max_attempts} failed "
                f"for port {client.port}. Retrying..."
            )
            time.sleep(delay_seconds)
        print(f"[{self.idx}] Could not connect to mGBA on port {client.port}")
        return False

    def recover_connection(self, max_attempts: int = 3) -> bool:
        try:
            self.orch.client.disconnect()
        except Exception:
            pass
        return self.connect_with_retry(max_attempts=max_attempts, delay_seconds=1.5)

    def abort_if_frozen(self) -> None:
        if self.restart.is_set() or not self.orch.client.connected:
            raise InstanceFrozen()

    def replace(self) -> bool:
        """Kill this emulator, start another on the same port, and restore its window."""
        if not self._replace():
            return False
        self.last_frame = None
        self.last_change = time.time()
        self.restart.clear()
        return True

    def _replace(self) -> bool:
        orch = self.orch
        idx = self.idx
        with self.group.replace_lock:
            self.restart.set()
            print(f"[{idx}] Replacing instance that was on port {orch.client.port}")
            rect = self.rect or _capture_rect(orch)
            try:
                orch.client.disconnect()
            except Exception:
                pass
            if orch.emu.is_alive():
                try:
                    orch.emu.process.kill()
                except Exception:
                    pass
            try:
                orch.emu.process.wait(timeout=5)
            except Exception:
                pass
            time.sleep(0.5)
            try:
                _frame_path(idx).unlink()
            except OSError:
                pass
            # Keep this slot's original port. Discovering a new one from the
            # shared state file can attach this window to a neighbor.
            if not orch.emu.start(extra_env=_slot_env(idx, orch.client.port)):
                print(f"[{idx}] Failed to start a replacement emulator")
                return False
            new_window = None
            try:
                new_window = Window.from_pid(orch.emu.process.pid, timeout=15)
                if rect is not None:
                    new_window.move_resize(*rect)
                    self.rect = rect
            except Exception as e:
                print(f"[{idx}] Could not place the replacement window: {e}")
            minimize_windows_starting_with("Scripting")
            time.sleep(1)
            if not self.group.sdl:
                try:
                    if new_window is not None and new_window.toggle_fast_forward():
                        print(f"[{idx}] Toggled fast-forward on the replacement")
                    else:
                        print(f"[{idx}] Could not focus the replacement to toggle fast-forward")
                except Exception as e:
                    print(f"[{idx}] Could not toggle fast-forward: {e}")
            if self.group.minimize and new_window is not None:
                new_window.minimize()
                minimize_windows_starting_with("Scripting")
            if not self.connect_with_retry():
                print(f"[{idx}] Could not connect to the replacement on port {orch.client.port}")
                return False
            self._latch_fast_forward()
            print(f"[{idx}] Replacement is up on port {orch.client.port}")
            return True

    def _latch_fast_forward(self) -> None:
        """Ask server.lua to latch fast-forward. The SDL build has no Shift+Tab latch."""
        if not self.group.fast_forward or not self.group.sdl:
            return
        try:
            self.orch.client.set_fast_forward(True)
            print(f"[{self.idx}] Fast-forward on")
        except Exception as e:
            print(f"[{self.idx}] Could not set fast-forward: {e}")


class InstanceGroup:
    """A fixed set of emulator slots, one port each, watched for freezes."""

    def __init__(
        self,
        count: int,
        rom: Path,
        starting_port: int = 8888,
        exe: Path = MGBA_DEV,
        script: Path = SERVER_SCRIPT,
        stale_seconds: float = 20,
    ) -> None:
        self.rom = rom
        self.starting_port = starting_port
        self.exe = exe
        self.script = script
        self.stale_seconds = stale_seconds
        self.sdl = Path(exe).resolve() == Path(MGBA_SDL).resolve()
        self.minimize = False
        self.fast_forward = False
        self.stop = threading.Event()
        self.replace_lock = threading.Lock()
        self.slots: list[InstanceSlot] = []
        for i in range(count):
            orch = Orchestrator(
                EmulatorProc(exe, rom, [script]),
                MGBAConnection("localhost", starting_port + i),
            )
            self.slots.append(
                InstanceSlot(
                    orch=orch,
                    idx=i,
                    restart=threading.Event(),
                    group=self,
                    last_change=time.time(),
                )
            )

    def kill(self) -> None:
        """Close every emulator this group started. The Scripting window is the same process."""
        self.stop.set()
        with self.replace_lock:
            for slot in self.slots:
                slot.restart.clear()
                try:
                    slot.orch.client.disconnect()
                except Exception:
                    pass
                process = getattr(slot.orch.emu, "process", None)
                if process is None or process.poll() is not None:
                    continue
                print(f"[{slot.idx}] Closing emulator on port {slot.orch.client.port}")
                try:
                    process.kill()
                except Exception:
                    pass
                try:
                    process.wait(timeout=5)
                except Exception:
                    pass

    def start(self, ready_pause: float = 0, fast_forward: bool = False, monitor: int = 0, minimize: bool = False) -> None:
        """Launch every emulator, tile the windows, and hide the Scripting consoles.

        monitor 0 is the primary display. 1 is the next display, and so on.
        minimize puts each game window and its Scripting console away after
        fast-forward. The Qt toggle has to focus the game window first.
        The SDL build latches fast-forward over the socket once it is connected.
        """
        self.minimize = minimize
        self.fast_forward = fast_forward
        print(f"Creating {len(self.slots)} orchestrators...", end="")
        print("done")
        for slot in self.slots:
            print(f"Starting emulator {slot.idx}...", end="")
            slot.orch.perform_task(
                lambda e, c, slot_idx=slot.idx, port=self.starting_port + slot.idx: (
                    e.process.pid if e.start(extra_env=_slot_env(slot_idx, port)) else None
                )
            )
            print("done")

        time.sleep(3)
        left, top, width, _height = get_monitor(monitor)
        print(f"Arranging windows on monitor {monitor}...", end="")
        windows = [Window.from_pid(slot.orch.emu.process.pid) for slot in self.slots]
        arrange_windows_auto_grid(windows, max_width=width, origin=(left, top))
        for slot, window in zip(self.slots, windows):
            slot.rect = window.rect()
        minimize_windows_starting_with("Scripting")
        print("done")
        if fast_forward and not self.sdl:
            for slot, window in zip(self.slots, windows):
                try:
                    if window.toggle_fast_forward():
                        print(f"[{slot.idx}] Toggled fast-forward")
                    else:
                        print(f"[{slot.idx}] Could not focus the window to toggle fast-forward")
                except Exception as e:
                    print(f"[{slot.idx}] Could not toggle fast-forward: {e}")
        if minimize:
            for window in windows:
                window.minimize()
            minimize_windows_starting_with("Scripting")
            print("Minimized the game and Scripting windows")
        if ready_pause:
            time.sleep(ready_pause)

    def run(self, attempt) -> None:
        """Repeat attempt(slot) until stop is set. Frozen slots are replaced first."""
        threads = []
        for slot in self.slots:
            thread = threading.Thread(target=self._run_slot, args=(slot, attempt), daemon=True)
            thread.start()
            threads.append(thread)
        threading.Thread(target=self._watch, daemon=True).start()
        for thread in threads:
            thread.join()

    def _run_slot(self, slot: InstanceSlot, attempt) -> None:
        if not slot.connect_with_retry():
            slot.restart.set()
        else:
            slot._latch_fast_forward()
        while not self.stop.is_set():
            if slot.restart.is_set():
                if not slot.replace():
                    print(f"[{slot.idx}] Replacement failed; stopping this instance")
                    break
                continue
            try:
                attempt(slot)
            except InstanceFrozen:
                if slot.restart.is_set():
                    continue
                if not slot.recover_connection():
                    print(f"[{slot.idx}] Connection lost; replacing this instance")
                    slot.restart.set()
            except Exception as e:
                print(f"[{slot.idx}] Error during run loop: {for_console(e)}")
                if slot.restart.is_set():
                    continue
                if not slot.recover_connection():
                    print(f"[{slot.idx}] Connection lost; replacing this instance")
                    slot.restart.set()

    def _watch(self) -> None:
        """Kill an instance whose frames have stopped while another is still advancing."""
        while not self.stop.is_set():
            time.sleep(POLL_SECONDS)
            if self.stop.is_set():
                return
            now = time.time()
            advancing = False
            # A Not Responding Scripting console is the same process as its
            # emulator. The game window can still look fine while that pair is stuck.
            hung = hung_window_pids()
            stalled: list[InstanceSlot] = []
            for slot in self.slots:
                if slot.restart.is_set() or not slot.orch.emu.is_alive():
                    continue
                if slot.orch.emu.process.pid in hung:
                    stalled.append(slot)
                    continue
                frame = _read_frame(slot.idx)
                if frame is None:
                    continue
                if frame != slot.last_frame:
                    slot.last_frame = frame
                    slot.last_change = now
                    advancing = True
                elif now - slot.last_change >= self.stale_seconds:
                    stalled.append(slot)
            if not advancing:
                continue
            for slot in stalled:
                rect = _capture_rect(slot.orch)
                if rect is not None:
                    slot.rect = rect
                print(f"[{slot.idx}] Frozen on port {slot.orch.client.port}; killing it")
                slot.restart.set()
                try:
                    slot.orch.emu.process.kill()
                except Exception:
                    pass


def _slot_env(slot_idx: int, port: int) -> dict[str, str]:
    return {"PKBT_SLOT": str(slot_idx), "PKBT_PORT": str(port)}


def _frame_path(slot_idx: int):
    return TEMP_DIR / f"frame_slot_{slot_idx}.txt"


def _read_frame(slot_idx: int) -> int | None:
    try:
        return int(_frame_path(slot_idx).read_text().strip())
    except (OSError, ValueError):
        return None


def _capture_rect(orch: Orchestrator) -> tuple[int, int, int, int] | None:
    try:
        return Window.from_pid(orch.emu.process.pid, timeout=1).rect()
    except Exception:
        return None

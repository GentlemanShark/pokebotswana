"""Hatch totals shared by every slot in one script."""

import threading
import time


class EggReport:
    """Count attempts and hatched eggs, and print the totals every `every` attempts."""

    def __init__(self, every: int = 50):
        self.every = every
        self._started = time.monotonic()
        self._eggs = 0
        self._eggs_lock = threading.Lock()
        self._attempts = 0
        self._attempts_lock = threading.Lock()

    @property
    def eggs_hatched(self) -> int:
        with self._eggs_lock:
            return self._eggs

    def egg_hatched(self) -> int:
        with self._eggs_lock:
            self._eggs += 1
            return self._eggs

    def attempt_finished(self) -> None:
        """Count one finished attempt, and print the totals on every Nth one."""
        with self._attempts_lock:
            self._attempts += 1
            done = self._attempts
        if done % self.every != 0:
            return
        hatched = self.eggs_hatched
        elapsed = time.monotonic() - self._started
        print(f"Attempts: {done}")
        print(f"Eggs hatched: {hatched}")
        if hatched:
            print(f"Est. eggs per hour: {hatched / elapsed * 3600:.1f}")

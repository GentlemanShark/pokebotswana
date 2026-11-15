"""Run a Python command and copy its console output into logs/."""

import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from pkbt.config import LOGS_DIR

_SLOT_LINE = re.compile(r"\[(\d+)\]")


def log_stem(args: list[str]) -> str:
    for index, arg in enumerate(args):
        if arg == "-m" and index + 1 < len(args):
            return args[index + 1]
    for arg in args:
        if arg.endswith(".py"):
            return Path(arg).stem
    return "run"


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: run.bat -m <module>", file=sys.stderr)
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = LOGS_DIR / f"{stamp}-{log_stem(args)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "run.log"
    print(f"Logging to {run_dir}", flush=True)

    slot_logs = {}
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        log.write(f"python {shlex.join(args)}\n")
        log.flush()
        proc = subprocess.Popen(
            [sys.executable, "-u", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                sys.stdout.write(_clock(line))
                sys.stdout.flush()
                stamped = _stamp(line)
                log.write(stamped)
                log.flush()
                slot = _slot_index(line)
                if slot is not None:
                    slot_log = _slot_log(run_dir, slot, slot_logs)
                    slot_log.write(stamped)
                    slot_log.flush()
        finally:
            proc.stdout.close()
            for slot_log in slot_logs.values():
                slot_log.close()
        return proc.wait()


def _slot_index(line: str) -> str | None:
    """The leading [idx] on a line, when the line names a slot."""
    match = _SLOT_LINE.match(line)
    if match is None:
        return None
    return match.group(1)


def _slot_log(run_dir: Path, slot: str, opened: dict):
    """Open logs/<run>/<slot>/run.log the first time that slot prints."""
    log = opened.get(slot)
    if log is None:
        slot_dir = run_dir / slot
        slot_dir.mkdir(exist_ok=True)
        log = (slot_dir / "run.log").open("w", encoding="utf-8", newline="\n")
        opened[slot] = log
    return log


def _clock(line: str) -> str:
    """Prefix a console line with the local time of day."""
    if not line.strip():
        return line
    now = datetime.now().strftime("%H:%M:%S")
    if line.endswith("\n"):
        return f"{now} {line[:-1]}\n"
    return f"{now} {line}"


def _stamp(line: str) -> str:
    """Prefix a console line with the local time it was written."""
    if not line.strip():
        return line
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if line.endswith("\n"):
        return f"{now} {line[:-1]}\n"
    return f"{now} {line}"


if __name__ == "__main__":
    raise SystemExit(main())

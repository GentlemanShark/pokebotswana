"""Run a Python command and copy its console output into logs/."""

import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


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

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{stamp}-{log_stem(args)}.log"
    print(f"Logging to {log_path}", flush=True)

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
                log.write(_stamp(line))
                log.flush()
        finally:
            proc.stdout.close()
        return proc.wait()


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

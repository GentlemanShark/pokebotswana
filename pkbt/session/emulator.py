from pathlib import Path
import os
import subprocess

from pkbt.config import MGBA_SDL

class EmulatorProc:

    def __init__(self, exe: Path, rom: Path, scripts: list[Path] | None = None) -> None:
        self.exe = exe
        self.rom = rom
        self.scripts = scripts

    def start(self, extra_env: dict[str, str] | None = None) -> bool:
        """Starts the emulator with (optionally) the given scripts."""
        scripting_args = []
        for s in self.scripts or []:
            scripting_args.extend(["--script", Path(s).as_posix()])

        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        rom = Path(self.rom)
        launch = [Path(self.exe).as_posix(), *scripting_args]
        # The ROM path is the one from config.toml. Its directory is where
        # the matching .sav lives, so SDL does not use its own config for that.
        if Path(self.exe).resolve() == Path(MGBA_SDL).resolve():
            launch.extend(["-C", f"savegamePath={rom.parent.as_posix()}"])
        launch.append(rom.as_posix())
        p = subprocess.Popen(launch, env=env)

        if p is None:
            print("Failed to start emulator")
            return False
        else:
            self.process = p
            return True

    def stop(self) -> None:
        """Stops the emulator."""
        self.process.terminate()

    def is_alive(self) -> bool:
        """Check if the emulator process is still running."""
        if not hasattr(self, 'process') or self.process is None:
            return False
        
        # Check if process is still running
        return self.process.poll() is None


"""For testing purposes, we can run the module directly to start and stop the emulator."""

if __name__ == "__main__":

    import time
    from pkbt.config import MGBA_DEV, POKEMON_RED_ROM, INPUT_DISPLAY_SCRIPT, SERVER_SCRIPT

    e = EmulatorProc(
        MGBA_DEV,
        POKEMON_RED_ROM,
        [INPUT_DISPLAY_SCRIPT, SERVER_SCRIPT]
    )

    print("Starting emulator...")
    e.start()

    print(f"Emulator started successfully with PID {e.process.pid}. Stopping in 3 seconds...")
    time.sleep(3)

    print(f"Stopping emulator with PID {e.process.pid}...")
    e.stop()
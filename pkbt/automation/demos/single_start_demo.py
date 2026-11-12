"""Requirements

    - mGBA executable and Pokemon ROM paths have been set in pokebotswana.config.toml
    - Run this script by using the command line from repo root:
        $ run.bat -m pkbt.automation.demos.single_start_demo
"""

from pkbt.config import MGBA_DEV, SERVER_SCRIPT, INPUT_DISPLAY_SCRIPT, POKEMON_RED_ROM
from pkbt.orchestrator import Orchestrator
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.emulator import EmulatorProc
from pkbt.mgba_connection import MGBAConnection
import time


"""Running the demo"""

# Create orchestrator for managing client/host and performing automation.
# INPUT_DISPLAY_SCRIPT is optional, but useful for seeing the input events in real-time (see center-top of game view).
orchestrator = Orchestrator(
    EmulatorProc(MGBA_DEV, POKEMON_RED_ROM, [SERVER_SCRIPT, INPUT_DISPLAY_SCRIPT]),
    MGBAConnection('localhost', 8888)) # The starting port is always 8888, subsequent ports are incremented by 1

print("Starting mGBA instance...")
orchestrator.emu.start()
time.sleep(3)

print("Connecting to mGBA...")
orchestrator.client.connect()
time.sleep(3)

# A "task" is any function that has the following signature
def my_task(e: EmulatorProc, c: MGBAConnection) -> None:

    print("Resetting game")
    c.reset_game()
    time.sleep(1)

    print("Pressing A for default duration")
    c.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
    time.sleep(1)

    print("Pressing A for .5s duration")
    c.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A, push_time=0.5))
    time.sleep(1)

    print("Setting A to held indefinitely")
    c.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.A))
    time.sleep(1)

    print("Releasing A")
    c.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.A))
    time.sleep(1)

print("Performing user-defined task")
orchestrator.perform_task(my_task)

print("Disconnecting from mGBA and closing emulator...")
orchestrator.exit()
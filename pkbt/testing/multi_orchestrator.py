from pkbt.emulator import EmulatorProc
from pkbt.orchestrator import Orchestrator
from pkbt.mgba_connection import MGBAConnection
from pkbt.config import POKEMON_RED_ROM, SERVER_SCRIPT, MGBA_DEV, INPUT_DISPLAY_SCRIPT
from pkbt.input.key_event import KeyEvent
from pkbt.input.key_event_type import KeyEventType
from pkbt.input.key_type import KeyType
import time
import threading
from typing import Callable
from pkbt.windowing import Window, arrange_windows_auto_grid, minimize_windows_starting_with, get_primary_screen_width


"""Tweak these for test"""
NUM_INSTANCES = 15
STARTING_PORT = 8888 # Leave me alone

"""The task that will be performed by each orchestrator"""
def task(o: Orchestrator, idx: int):
    o.client.connect()
    for _ in range(6):
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(1)


"""Putting it all together and running it"""

# Create the orchestrators
orchestrators = []
for i in range(NUM_INSTANCES):
    orch = Orchestrator(
        EmulatorProc(MGBA_DEV, POKEMON_RED_ROM, [SERVER_SCRIPT, INPUT_DISPLAY_SCRIPT]),
        MGBAConnection('localhost', STARTING_PORT + i))
    orchestrators.append(orch)

# Start the emulators
emu_pids: list[int] = []
for i in range(NUM_INSTANCES):
    pid = orchestrators[i].perform_task(lambda e, c: e.process.pid if e.start() else None)
    emu_pids.append(pid)

# Arrange the windows in a grid
time.sleep(15)
windows = [Window.from_pid(pid) for pid in emu_pids]
# arrange_in_grid(windows, num_cols=3, num_rows=1)
arrange_windows_auto_grid(windows, max_width=get_primary_screen_width())
minimize_windows_starting_with("Scripting")

# Start the tasks
threads = []
for i, orchestrator in enumerate(orchestrators):
    t = threading.Thread(target=task, args=(orchestrator, i), daemon=True)
    t.start()
    threads.append(t)

# Without this, the main program will exit immediately, 
# causing daemon threads to be killed before they complete their tasks
for t in threads:
    t.join()
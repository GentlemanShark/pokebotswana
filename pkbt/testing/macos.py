"""Requirements

    - Player is standing directly adjacent to Beldum pokeball, facing it.
    - Player has only one pokemon in their party.
    - User sets all mGBA instances to unbounded fast-forward mode (Shift+Tab)
"""

from pkbt.config import POKEMON_RED_ROM
from pkbt.orchestrator import Orchestrator
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.emulator import EmulatorProc
from pkbt.mgba_connection import MGBAConnection
from pkbt.config import MGBA_DEV, SERVER_SCRIPT, SESSION_DIR
# from pkbt.windowing import Window, arrange_windows_auto_grid, minimize_windows_starting_with, get_primary_screen_width
from pkbt.image_processing import pixel_hex, save_with_crosshair, debug_shot
from pkbt.audio import play_success
import time
import threading
import random

"""Constants"""
STARTING_PORT = 8888 # Leave me alone

"""Tweak as desired"""
NUM_INSTANCES = 1
CROSSHAIR = (105, 38)
SHINY_STAR_HEX = "#ffd652"

"""Shared thread-safe variables"""
runs = 0
found_shiny = False
kill_all_threads = False

"""The task that will be performed by each orchestrator"""
def task(o: Orchestrator, idx: int):
    global runs
    global found_shiny
    global kill_all_threads

    o.client.connect()

    def start_game():
        # Reset the game and load save file
        o.client.reset_game()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    def offset_clock():
        time.sleep((o.client._port - 8888) * 0.25)

    def add_jitter():
        time.sleep(random.uniform(0, 1))

    def pick_up_egg():
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    def hatch_egg():
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.3)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.SELECT))
        time.sleep(0.7)
        for _ in range(250):
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.LEFT))
            time.sleep(0.3)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.LEFT))
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.RIGHT))
            time.sleep(0.3)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.RIGHT))

    def go_through_hatching_sequences():
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    def enter_summary():
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    def save_screenshot():
        o.client.save_screenshot_to_file(f"{idx}.png")
        time.sleep(1)

    def shiny_star_is_visible() -> bool:
        return SHINY_STAR_HEX == pixel_hex(f"{SESSION_DIR}/{idx}.png", CROSSHAIR[0], CROSSHAIR[1])

    def save_game():
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    # Main loop
    while found_shiny == False and kill_all_threads == False:

        if not o.is_healthy():
            print(f"Orchestrator for port {idx} is unhealthy, likely affects all timing, killing all threads")
            kill_all_threads = True
            break

        runs += 1
        if o.client._port == 8888:
            print(f"Runs: {runs}")
        start_game()
        offset_clock()
        add_jitter()
        pick_up_egg()
        # hatch_egg()
        # go_through_hatching_sequences()
        enter_summary()
        save_screenshot()
        if shiny_star_is_visible():
            found_shiny = True
            print(f"Shiny found on {idx}")
            _, lua_name = debug_shot(f"found-at-runs-{runs}.png")
            o.client.save_screenshot_to_file(lua_name)
            play_success(blocking=True)
            save_game()
            break

"""Putting it all together and running it"""

# Create the orchestrators
orchestrators = []
for i in range(NUM_INSTANCES):
    orch = Orchestrator(
        EmulatorProc(MGBA_DEV, POKEMON_RED_ROM, [SERVER_SCRIPT]),
        MGBAConnection('localhost', STARTING_PORT + i))
    orchestrators.append(orch)

# Start the emulators
emu_pids: list[int] = []
for i in range(NUM_INSTANCES):
    pid = orchestrators[i].perform_task(lambda e, c: e.process.pid if e.start() else None)
    emu_pids.append(pid)
    time.sleep(0.5)

# # Arrange the windows in a grid
# time.sleep(10)
# windows = [Window.from_pid(pid) for pid in emu_pids]
# # arrange_in_grid(windows, num_cols=3, num_rows=1)
# arrange_windows_auto_grid(windows, max_width=get_primary_screen_width())
# minimize_windows_starting_with("Scripting")

# User is given time to set all mGBA instances to unbounded fast-forward mode
time.sleep(3)

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
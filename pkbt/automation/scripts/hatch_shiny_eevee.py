""" Notes on the setup:
    - Daycare man already has an Eevee egg in his possession.
    - Player is standing directly west of the daycare man, facing him.
    - Player has only one pokemon in their party.
    - User manually sets all mGBA instances to unbounded fast-forward mode (Shift+Tab) before automation starts.
    - mGBA frame skip is set to 10.
    - mGBA frame advance speed is set to 5x.
"""

from pkbt.config import POKEMON_RED_ROM
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.image_processing import pixel_hex, debug_shot
from pkbt.audio import play_success
from pkbt.instances import InstanceGroup, InstanceSlot, slot_dir
import time
import threading
import random

"""Constants"""
STARTING_PORT = 8888 # Leave me alone

"""Tweak as desired"""
NUM_INSTANCES =12
CROSSHAIR = (105, 38)
SHINY_STAR_HEX = "#ffd652"

"""Shared thread-safe variables"""
runs = 0
runs_lock = threading.Lock()

def attempt(slot: InstanceSlot):
    o = slot.orch
    idx = slot.idx
    global runs

    def start_game():
        slot.abort_if_frozen()
        # The seed is the time from reset until the A press leaves PRESS START.
        # That press can hit 1024 seeds, one per frame for about 17s of game
        # time. The spread below is that long at roughly 10x fast-forward.
        # PRESS START restarts the intro after about 45s of game time.
        o.client.reset_game()
        time.sleep(random.uniform(0.7, 2.5))
        for _ in range(8):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(0.7)
        time.sleep(2)

    def pick_up_egg():
        slot.abort_if_frozen()
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

    def hatch_egg():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.3)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.SELECT))
        time.sleep(0.7)
        for _ in range(250):
            slot.abort_if_frozen()
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.LEFT))
            time.sleep(0.5)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.LEFT))
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.RIGHT))
            time.sleep(0.5)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.RIGHT))

    def go_through_hatching_sequences():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(2)

    def enter_summary():
        slot.abort_if_frozen()
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
        slot.abort_if_frozen()
        o.client.save_screenshot_to_file(f"{idx}.png")
        time.sleep(1)

    def shiny_star_is_visible() -> bool:
        return SHINY_STAR_HEX == pixel_hex(slot_dir(idx) / f"{idx}.png", CROSSHAIR[0], CROSSHAIR[1])

    def save_game():
        slot.abort_if_frozen()
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

    start_game()
    pick_up_egg()
    hatch_egg()
    go_through_hatching_sequences()
    enter_summary()
    save_screenshot()
    with runs_lock:
        runs += 1
        current_runs = runs
    if idx == 0:
        print(f"Runs: {current_runs}")
    if shiny_star_is_visible():
        group.stop.set()
        print(f"Shiny found on {idx}")
        _, lua_name = debug_shot(f"found-at-runs-{current_runs}.png")
        o.client.save_screenshot_to_file(lua_name)
        play_success(blocking=True)
        save_game()

"""Putting it all together and running it"""
group = InstanceGroup(NUM_INSTANCES, POKEMON_RED_ROM, starting_port=STARTING_PORT)
# Time to Shift+Tab the original windows. Replacements toggle it themselves.
group.start(ready_pause=12)
group.run(attempt)

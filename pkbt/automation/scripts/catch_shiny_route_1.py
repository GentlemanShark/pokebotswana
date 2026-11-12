from pkbt.config import POKEMON_RED_ROM
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.image_processing import pixel_hex, pixel_hex_when_ready
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
BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR = (220, 146)
BATTLE_SCREEN_DIALOGUE_BG_HEX = "#29526b"
BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR = (174, 53)
BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR = (220, 130)
BATTLE_SCREEN_CAUGHT_BG_HEX = "#29526b"
NON_SHINY_RATTATA_HEX = "#b573b5"
NON_SHINY_PIDGEY_HEX = "#ce8c63"
NON_SHINY_SUICUNE_HEX = "#5a73d6"
SHINY_PIDGEY_HEX = "#e7de00"

"""Shared thread-safe variables"""
runs = 0
runs_lock = threading.Lock()
stop_all = False

def attempt(slot: InstanceSlot):
    o = slot.orch
    idx = slot.idx
    global runs
    global stop_all

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

    def equip_bike():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.SELECT))
        time.sleep(0.7)

    def brief_zigzag():
        slot.abort_if_frozen()
        for i in range(1):
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.RIGHT))
            time.sleep(0.7)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.RIGHT))
            time.sleep(0.7)
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.LEFT))
            time.sleep(0.7)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.LEFT))
            time.sleep(0.7)

    def capture_pixel(x: int, y: int) -> str:
        slot.abort_if_frozen()
        return pixel_hex_when_ready(
            slot_dir(idx) / f"{idx}.png",
            x,
            y,
            lambda: o.client.save_screenshot_to_file(f"{idx}.png"),
        )

    def entered_battle():
        slot.abort_if_frozen()
        bg_hex = capture_pixel(BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR[0], BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR[1])
        return bg_hex == BATTLE_SCREEN_DIALOGUE_BG_HEX

    def wild_pokemon_is_shiny():
        slot.abort_if_frozen()
        pokemon_hex = capture_pixel(BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[0], BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[1])
        is_shiny = pokemon_hex not in [NON_SHINY_RATTATA_HEX, NON_SHINY_PIDGEY_HEX, NON_SHINY_SUICUNE_HEX]
        if is_shiny:
            print(f"Pokemon is shiny: {pokemon_hex} idx: {idx}")
        return is_shiny

    def proceed_through_battle_intro_messages():
        slot.abort_if_frozen()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    def run_away_from_battle():
        slot.abort_if_frozen()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)

    def use_mean_look():
        slot.abort_if_frozen()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3)

    def throw_first_ultra_ball():
        slot.abort_if_frozen()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3)

    def throw_additional_ultra_ball():
        slot.abort_if_frozen()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3)

    def is_caught():
        slot.abort_if_frozen()
        bg_hex = capture_pixel(BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR[0], BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR[1])
        return bg_hex == BATTLE_SCREEN_CAUGHT_BG_HEX

    def finish_battle_messages():
        slot.abort_if_frozen()
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(2.7)

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
        print(f"Saving game on {idx}")
        time.sleep(2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
        time.sleep(0.7)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
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
        time.sleep(3)

    start_game()
    equip_bike()
    while not stop_all:
        brief_zigzag()
        if entered_battle():
            runs += 1
            if runs % 50 == 0:
                print(f"Runs: {runs}")
            proceed_through_battle_intro_messages()
            if wild_pokemon_is_shiny():
                print(f"Shiny found on {idx} after {runs} runs")
                stop_all = True
                break
            else:
                run_away_from_battle()
        else:
            continue

    use_mean_look()
    throw_first_ultra_ball()
    while not is_caught():
        throw_additional_ultra_ball()
    finish_battle_messages()
    save_game()
    play_success(blocking=True)
    group.stop.set()

"""Putting it all together and running it"""
group = InstanceGroup(NUM_INSTANCES, POKEMON_RED_ROM, starting_port=STARTING_PORT)
# Time to Shift+Tab the original windows. Replacements toggle it themselves.
group.start(ready_pause=12)
group.run(attempt)

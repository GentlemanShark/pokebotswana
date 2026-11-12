from pkbt.config import POKEMON_RED_ROM
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.image_processing import pixel_hex_when_ready, dialogue_arrow_is_visible
from pkbt.text import FULL_DIALOGUE_BOX, PLAYER_PKMN_STATUS_BOX, read_text
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
BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR = (174, 56)
BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR = (220, 130)
BATTLE_SCREEN_CAUGHT_BG_HEX = "#29526b"
NON_SHINY_KAKUNA_HEX = "#8c7b00"
NON_SHINY_WEEDLE_HEX = "#efad42"
NON_SHINY_CATERPIE_HEX = "#7b9c63"
NON_SHINY_PIKACHU_HEX = "#ffef00"
NON_SHINY_METAPOD_HEX = "#9cd64a"

"""Shared thread-safe variables"""
runs = 0
pikachu_runs = 0
runs_lock = threading.Lock()
stop_all = False

def attempt(slot: InstanceSlot):
    o = slot.orch
    idx = slot.idx
    global runs
    global pikachu_runs
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

    def set_initial_menu_cursor_position():
        slot.abort_if_frozen()
        # Open the BAG menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
        time.sleep(0.2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.2)
        # Move To FULL HEAL
        for _ in range(4):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(0.2)
        # Move to POKE BALLS
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
            time.sleep(0.2)
        # Move to ULTRA BALL
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2)
        # Return to ITEMS tab
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
            time.sleep(0.2)
        # Return to main menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.2)
        # Move Cursor back to POKEDEX
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
            time.sleep(0.2)
        # Close start menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.2)

    def equip_bike():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.SELECT))
        time.sleep(0.7)

    def brief_zigzag():
        slot.abort_if_frozen()
        for i in range(1):
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.RIGHT))
            time.sleep(0.3)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.RIGHT))
            time.sleep(0.1)
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.LEFT))
            time.sleep(0.3)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.LEFT))
            time.sleep(0.1)

    def capture_pixel(x: int, y: int) -> str:
        slot.abort_if_frozen()
        return pixel_hex_when_ready(
            slot_dir(idx) / f"{idx}.png",
            x,
            y,
            lambda: o.client.save_screenshot_to_file(f"{idx}.png"),
        )

    def dialogue_arrow_is_visible_on_screen():
        slot.abort_if_frozen()
        return dialogue_arrow_is_visible(
            slot_dir(idx) / f"{idx}.png",
            lambda: o.client.save_screenshot_to_file(f"{idx}.png"),
        )

    def entered_battle():
        slot.abort_if_frozen()
        bg_hex = capture_pixel(BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR[0], BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR[1])
        return bg_hex == BATTLE_SCREEN_DIALOGUE_BG_HEX

    def get_wild_pokemon_name():
        slot.abort_if_frozen()
        path = slot_dir(idx) / f"{idx}.png"
        capture_pixel(FULL_DIALOGUE_BOX[0], FULL_DIALOGUE_BOX[1])
        text = "".join(read_text(path, FULL_DIALOGUE_BOX).split()).upper()
        prefix = "WILD"
        for suffix in ("APPEARED!", "OPPEORED!"):
            if text.startswith(prefix) and text.endswith(suffix):
                return text[len(prefix):-len(suffix)]
        return ""

    def is_player_pkmn_poisoned():
        slot.abort_if_frozen()
        text = read_text(slot_dir(idx) / f"{idx}.png", PLAYER_PKMN_STATUS_BOX).upper()
        return text.startswith("PS")

    def is_shiny_of_species(pokemon_name: str):
        slot.abort_if_frozen()
        is_shiny = False
        if pokemon_name == "KAKUNA":
            pokemon_hex = capture_pixel(BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[0], BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[1])
            # is_shiny = pokemon_hex != NON_SHINY_KAKUNA_HEX
        elif pokemon_name == "WEEDLE":
            pokemon_hex = capture_pixel(BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[0], BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[1])
            # is_shiny = pokemon_hex != NON_SHINY_WEEDLE_HEX
        elif pokemon_name == "CATERPIE":
            pokemon_hex = capture_pixel(BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[0], BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[1])
            # is_shiny = pokemon_hex != NON_SHINY_CATERPIE_HEX
        elif pokemon_name == "PIKACHU":
            pokemon_hex = capture_pixel(BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[0], BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[1])
            is_shiny = pokemon_hex != NON_SHINY_PIKACHU_HEX
        elif pokemon_name == "METAPOD":
            pokemon_hex = capture_pixel(BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[0], BATTLE_SCREEN_WILD_POKEMON_CROSSHAIR[1])
            # is_shiny = pokemon_hex != NON_SHINY_METAPOD_HEX
        else:
            raise ValueError(f"Invalid pokemon name: {pokemon_name}")
        return is_shiny

    def proceed_through_battle_intro_messages():
        slot.abort_if_frozen()
        time.sleep(0.4)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.5)

    def run_away_from_battle():
        slot.abort_if_frozen()
        time.sleep(0.1)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.1)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.1)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.1)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.1)

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

    def attempt_pokemon_heal():
        # needed to move back from ultra ball
        # 4 A to use full heal
        slot.abort_if_frozen()
        # Open START menu and move to and open BAG
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
        time.sleep(0.2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.2)
        # Move back to ITEMS
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
            time.sleep(0.2)
        # Use FULL HEAL
        for _ in range(4):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(0.5)

    def save_game():
        slot.abort_if_frozen()
        print(f"Saving game on {idx}")
        time.sleep(2)
        # Move back to START menu from BAG
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.2)
        # Move to SAVE
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(0.7)
        # Save Game
        for _ in range(3):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)

    start_game()
    set_initial_menu_cursor_position()
    equip_bike()
    while not stop_all:
        brief_zigzag()
        if entered_battle():
            while not dialogue_arrow_is_visible_on_screen():
                time.sleep(0.4)
            pokemon_name = get_wild_pokemon_name()
            runs += 1
            if pokemon_name == "PIKACHU":
                pikachu_runs += 1
            if runs % 50 == 0:
                print(f"Runs: {runs}, Pikachu Runs: {pikachu_runs}")
            proceed_through_battle_intro_messages()
            if is_shiny_of_species(pokemon_name):
                print(f"Shiny {pokemon_name} found on {idx} after {runs} runs")
                stop_all = True
                use_mean_look()
                throw_first_ultra_ball()
                while not is_caught():
                    throw_additional_ultra_ball()
                finish_battle_messages()
                attempt_pokemon_heal()
                save_game()
                play_success(blocking=True)
                group.stop.set()
                break
            else:
                run_away_from_battle()
        else:
            continue

"""Putting it all together and running it"""
group = InstanceGroup(NUM_INSTANCES, POKEMON_RED_ROM, starting_port=STARTING_PORT)
group.start(fast_forward=True)
group.run(attempt)

from pkbt.config import MGBA_SDL, POKEMON_RED_ROM
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.state_manager import initialize_state_manager
from pkbt.config import TEMP_DIR
from pkbt.image_processing import pixel_hex_when_ready, dialogue_arrow_is_visible
from pkbt.text import FULL_DIALOGUE_BOX, PLAYER_PKMN_STATUS_BOX, read_text
from pkbt.audio import play_success
from pkbt.instances import InstanceGroup, InstanceSlot
from pkbt.species import SPECIES
from pkbt.console import for_console
import time
import threading
import random

"""Constants"""
STARTING_PORT = 8888 # Leave me alone

"""Tweak as desired"""
NUM_INSTANCES = 30
BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR = (220, 146)
BATTLE_SCREEN_DIALOGUE_BG_HEX = "#29526b"
BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR = (220, 130)
BATTLE_SCREEN_CAUGHT_BG_HEX = "#29526b"

EXCLUDED_POKEMON = ["PSYDUCK", "GEODUDE", "SPEAROW", "FEAROW", "PERSIAN", "MEOWTH"]
# The number of shiny pokemon to catch before the bot stops
CATCH_LIMIT = 3
# Added to every fixed sleep. The reset delay stays a random range.
SLEEP_DELTA = 0.0

"""Shared thread-safe variables"""
encounter_counts = {
    "PONYTA": 0,
    "RAPIDASH": 0,
    "PSYDUCK": 0,
    "GEODUDE": 0,
    "SPEAROW": 0,
    "FEAROW": 0,
    "PERSIAN": 0,
    "MEOWTH": 0,
}
runs_lock = threading.Lock()
pause_all = False
catch_count = 0

def attempt(slot: InstanceSlot):
    o = slot.orch
    idx = slot.idx
    global encounter_counts
    global pause_all
    global catch_count

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
            time.sleep(0.7 + SLEEP_DELTA)
        time.sleep(2 + SLEEP_DELTA)

    def set_initial_menu_cursor_position():
        slot.abort_if_frozen()
        # Open the BAG menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
        time.sleep(0.2 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.2 + SLEEP_DELTA)
        # Move To FULL HEAL
        for _ in range(4):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(0.2 + SLEEP_DELTA)
        # Move to POKE BALLS
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
            time.sleep(0.2 + SLEEP_DELTA)
        # Move to ULTRA BALL
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2 + SLEEP_DELTA)
        # Return to ITEMS tab
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
            time.sleep(0.2 + SLEEP_DELTA)
        # Return to main menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.2 + SLEEP_DELTA)
        # Move Cursor back to POKEDEX
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
            time.sleep(0.2 + SLEEP_DELTA)
        # Close start menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.2 + SLEEP_DELTA)

    def equip_bike():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.SELECT))
        time.sleep(0.7 + SLEEP_DELTA)

    def brief_zigzag():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.B))
        for _ in range(1):
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.UP))
            time.sleep(0.2 + SLEEP_DELTA)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.UP))
            time.sleep(0.03 + SLEEP_DELTA)
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.DOWN))
            time.sleep(0.2 + SLEEP_DELTA)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.DOWN))
            time.sleep(0.03 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.B))

    def capture_pixel(x: int, y: int) -> str:
        slot.abort_if_frozen()
        return pixel_hex_when_ready(
            TEMP_DIR / f"{idx}.png",
            x,
            y,
            lambda: o.client.save_screenshot_to_file(f"{idx}.png"),
        )

    def dialogue_arrow_is_visible_on_screen():
        slot.abort_if_frozen()
        return dialogue_arrow_is_visible(
            TEMP_DIR / f"{idx}.png",
            lambda: o.client.save_screenshot_to_file(f"{idx}.png"),
        )

    def entered_battle():
        slot.abort_if_frozen()
        bg_hex = capture_pixel(BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR[0], BATTLE_SCREEN_DIALOGUE_BG_CROSSHAIR[1])
        return bg_hex == BATTLE_SCREEN_DIALOGUE_BG_HEX

    def canonical_name(name: str) -> str:
        if name in SPECIES:
            return name
        for species_name, species in SPECIES.items():
            if species.other_names and name in species.other_names:
                return species_name
        return name

    def get_wild_pokemon_name():
        slot.abort_if_frozen()
        path = TEMP_DIR / f"{idx}.png"
        capture_pixel(FULL_DIALOGUE_BOX[0], FULL_DIALOGUE_BOX[1])
        text = "".join(read_text(path, FULL_DIALOGUE_BOX).split()).upper()
        prefix = "WILD"
        for suffix in ("APPEARED!", "OPPEORED!"):
            if text.startswith(prefix) and text.endswith(suffix):
                return canonical_name(text[len(prefix):-len(suffix)])
        return ""

    def increment_encounter_count(pokemon_name: str):
        slot.abort_if_frozen()
        if pokemon_name not in encounter_counts:
            shown_name = for_console(pokemon_name).strip() or "UNKNOWN"
            filename = "".join(c if c not in '<>:"/\\|?*' else "_" for c in shown_name) + ".png"
            print(f"[{idx}] Unrecognized pokemon name: {shown_name}")
            pixel_hex_when_ready(
                TEMP_DIR / filename,
                0,
                0,
                lambda: o.client.save_screenshot_to_file(filename),
            )
            encounter_counts["UNKNOWN"] += 1
        else:
            encounter_counts[pokemon_name] += 1

    def get_total_encounter_count():
        slot.abort_if_frozen()
        return sum(encounter_counts.values())

    def is_player_pkmn_poisoned():
        slot.abort_if_frozen()
        text = read_text(TEMP_DIR / f"{idx}.png", PLAYER_PKMN_STATUS_BOX).upper()
        return text.startswith("PS")

    def is_shiny_of_species(pokemon_name: str):
        slot.abort_if_frozen()
        species = SPECIES[pokemon_name]
        pokemon_hex = capture_pixel(species.wild.crosshair[0], species.wild.crosshair[1])
        is_shiny = pokemon_hex != species.wild.normal_hex
        return is_shiny

    def proceed_through_battle_intro_messages():
        slot.abort_if_frozen()
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(1.2 + SLEEP_DELTA)

    def run_away_from_battle():
        slot.abort_if_frozen()
        time.sleep(0.1 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.1 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.1 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.1 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.1 + SLEEP_DELTA)

    def use_mean_look():
        slot.abort_if_frozen()
        time.sleep(0.7 + SLEEP_DELTA)
        # Enter FIGHT menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.3 + SLEEP_DELTA)
        # Reset cursor to first option
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
        time.sleep(0.3 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
        time.sleep(0.3 + SLEEP_DELTA)
        # Select MEAN LOOK (assumes it's in top-left position)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3 + SLEEP_DELTA)

    def use_false_swipe():
        slot.abort_if_frozen()
        time.sleep(0.7 + SLEEP_DELTA)
        # Enter FIGHT menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.3 + SLEEP_DELTA)
        # Reset cursor to first option
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
        time.sleep(0.3 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
        time.sleep(0.3 + SLEEP_DELTA)
        # Select FALSE SWIPE (assumes it's in bottom-left position)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.3 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3 + SLEEP_DELTA)

    def use_spore():
        slot.abort_if_frozen()
        time.sleep(0.7 + SLEEP_DELTA)
        # Enter FIGHT menu
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.3 + SLEEP_DELTA)
        # Reset cursor to first option
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
        time.sleep(0.3 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
        time.sleep(0.3 + SLEEP_DELTA)
        # Select SPORE (assumes it's in top-right position)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.3 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3 + SLEEP_DELTA)

    def throw_first_ultra_ball():
        slot.abort_if_frozen()
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.RIGHT))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3 + SLEEP_DELTA)

    def throw_additional_ultra_ball():
        slot.abort_if_frozen()
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3 + SLEEP_DELTA)

    def is_caught():
        slot.abort_if_frozen()
        bg_hex = capture_pixel(BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR[0], BATTLE_SCREEN_CAUGHT_BG_CROSSHAIR[1])
        return bg_hex == BATTLE_SCREEN_CAUGHT_BG_HEX

    def finish_battle_messages():
        slot.abort_if_frozen()
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.7 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(2.7 + SLEEP_DELTA)

    def attempt_pokemon_heal():
        # needed to move back from ultra ball
        # 4 A to use full heal
        slot.abort_if_frozen()
        # Open START menu and move to and open BAG
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
        time.sleep(0.2 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
        time.sleep(0.2 + SLEEP_DELTA)
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.2 + SLEEP_DELTA)
        # Move back to ITEMS
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.LEFT))
            time.sleep(0.2 + SLEEP_DELTA)
        # Use FULL HEAL
        for _ in range(4):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(0.5 + SLEEP_DELTA)

    def save_game():
        slot.abort_if_frozen()
        print(f"Saving game on {idx}")
        time.sleep(2 + SLEEP_DELTA)
        # Move back to START menu from BAG
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.2 + SLEEP_DELTA)
        # Move to SAVE
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(0.7 + SLEEP_DELTA)
        # Save Game
        for _ in range(3):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1 + SLEEP_DELTA)

    start_game()
    set_initial_menu_cursor_position()
    # equip_bike()
    while not group.stop.is_set():
        brief_zigzag()
        if entered_battle():
            while not dialogue_arrow_is_visible_on_screen():
                time.sleep(0.1 + SLEEP_DELTA)
            pokemon_name = get_wild_pokemon_name()
            proceed_through_battle_intro_messages()
            if is_shiny_of_species(pokemon_name) and pokemon_name not in EXCLUDED_POKEMON:
                shown_name = for_console(pokemon_name)
                print(f"Shiny {shown_name} found on {idx} after {get_total_encounter_count()} total encounters and {encounter_counts[pokemon_name]} {shown_name} encounters")
                pause_all = True
                use_spore()
                use_false_swipe()
                throw_first_ultra_ball()
                while not is_caught():
                    throw_additional_ultra_ball()
                finish_battle_messages()
                attempt_pokemon_heal()
                save_game()
                play_success(blocking=True)
                catch_count += 1
                if catch_count >= CATCH_LIMIT:
                    group.kill()
                    break
                time.sleep(2 + SLEEP_DELTA)
                pause_all = False
                start_game()
                set_initial_menu_cursor_position()
            else:
                run_away_from_battle()

            increment_encounter_count(pokemon_name)
            if get_total_encounter_count() % 50 == 0:
                print(f"Total Encounter Count: {get_total_encounter_count()}")
                print(f"Encounter Counts: {for_console(encounter_counts)}")
        else:
            continue

        while pause_all and not group.stop.is_set():
            time.sleep(5 + SLEEP_DELTA)
            if not pause_all:
                start_game()
                set_initial_menu_cursor_position()
                # equip_bike()
                break

"""Putting it all together and running it"""
initialize_state_manager()
group = InstanceGroup(NUM_INSTANCES, POKEMON_RED_ROM, starting_port=STARTING_PORT, exe=MGBA_SDL)
group.start(fast_forward=True, minimize=True)
group.run(attempt)

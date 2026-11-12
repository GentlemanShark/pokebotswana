from pkbt.config import MGBA_SDL, POKEMON_RED_ROM
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEvent
from pkbt.image_processing import get_pixel_hex, assert_hex_at_position, assert_not_hex_at_position
from pkbt.text import read_overworld_dialogue, assert_equals_dialogue_text, assert_contains_dialogue_text
from pkbt.audio import play_success
from pkbt.console import for_console
from pkbt.instances import InstanceGroup, InstanceSlot
from pkbt.species import SPECIES
import time
import random
import threading

"""Tweak as needed
"""
POKEMON_SPECIES = SPECIES["LARVITAR"]
NUM_INSTANCES = 30
TIME_ALLOWED_FOR_ZIGZAG = 420 # seconds
EGG_REPORT_EVERY = 50 # attempts

"""Constants
"""
STARTING_PORT = 8888 # Leave me alone

"""Shared thread-safe state
"""
script_started = time.monotonic()
eggs_hatched = 0
eggs_hatched_lock = threading.Lock()
def increment_eggs_hatched():
    global eggs_hatched
    with eggs_hatched_lock:
        eggs_hatched += 1
        return eggs_hatched
abandoned_attempts = {}
abandoned_attempts_lock = threading.Lock()
attempts = 0
attempts_lock = threading.Lock()
def increment_attempts():
    global attempts
    with attempts_lock:
        attempts += 1
        return attempts
def increment_abandoned_attempts(callback_name):
    with abandoned_attempts_lock:
        abandoned_attempts[callback_name] = abandoned_attempts.get(callback_name, 0) + 1
def abandoned_attempts_snapshot():
    with abandoned_attempts_lock:
        return dict(abandoned_attempts)
def log_egg_report():
    """Print the hatch totals every EGG_REPORT_EVERY attempts across all slots."""
    done = increment_attempts()
    if done % EGG_REPORT_EVERY != 0:
        return
    with eggs_hatched_lock:
        hatched = eggs_hatched
    elapsed = time.monotonic() - script_started
    print(f"Attempts: {done}")
    print(f"Eggs hatched: {hatched}")
    if hatched:
        print(f"Est. eggs per hour: {hatched / elapsed * 3600:.1f}")
    print(f"Abandoned attempts: {abandoned_attempts_snapshot()}")

"""See end of attempt() for all automation instructions per iteration
"""
def attempt(slot: InstanceSlot):
    o = slot.orch

    def retry(callback, timer=3, max_tries=3):
        tries = 1
        has_previosuly_failed = False
        while tries < max_tries:
            slot.abort_if_frozen()
            try:
                callback()
                if has_previosuly_failed:
                    print(f"[{slot.idx}] Successfully completed {callback.__name__} after {tries} tries")
                return True # Success
            except Exception as e:
                print(f"[{slot.idx}] Retrying {callback.__name__} after {tries} failure(s): {for_console(e)}")
                has_previosuly_failed = True
                time.sleep(timer)
                tries += 1
        increment_abandoned_attempts(callback.__name__)
        raise Exception(f"[{slot.idx}] Abandoned {callback.__name__} after {max_tries} tries, restarting game in slot {slot.idx}")

    def start_game():
        slot.abort_if_frozen()
        # The seed is the time from reset until the A press leaves PRESS START.
        # That press can hit 1024 seeds, one per frame for about 17s of game
        # time. The spread below is that long at roughly 10x fast-forward.
        # PRESS START restarts the intro after about 45s of game time.
        o.client.reset_game()
        time.sleep(random.uniform(0.7, 2.5))
        # Progress through enough of the startup sequence to reach the recap
        for _ in range(5):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(0.7)
        # Finish the grayscale recap
        def finish_recap():
            for _ in range(3):
                o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
                time.sleep(0.5)
            time.sleep(2)
            assert_hex_at_position(slot, (109, 78), "#73cea5")
        retry(finish_recap)

    def pick_up_egg():
        slot.abort_if_frozen()
        # To be safe, check that the dialogue window hasn't accidentally been opened
        try:
            assert_not_hex_at_position(slot, (13, 123), "#ffffff")
        except Exception as e:
            raise Exception(f"[{slot.idx}] Failed to check that the dialogue window hasn't accidentally been opened. {e}")
        """ Advance through the dialogue
        """
        def dialogue_ah_its_you():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "Ah, it\u2019s you")
        retry(dialogue_ah_its_you)
        def dialogue_we_were_raising_your_pokemon():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "We were roisin")
        retry(dialogue_we_were_raising_your_pokemon)
        def dialogue_had_an_egg():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "hod \xe7m EGG")
        retry(dialogue_had_an_egg)
        def dialogue_dont_know_how_it_got_there():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "We don\u2019t know how it got there")
        retry(dialogue_dont_know_how_it_got_there)
        def dialogue_do_want_it_yes():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "do wont it, yes")
        retry(dialogue_do_want_it_yes)
        def dialogue_received_the_egg_from():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "the Eoc from")
        retry(dialogue_received_the_egg_from)
        def dialogue_take_good_care_of_it():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_contains_dialogue_text(slot, "Toke good core of it.")
        retry(dialogue_take_good_care_of_it)
        """ Finish the dialogue
        """
        def finish_egg_pickup_dialogue():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
            time.sleep(0.7)
            assert_not_hex_at_position(slot, (13, 123), "#ffffff")
        retry(finish_egg_pickup_dialogue)

    def walk_down_one_step():
        slot.abort_if_frozen()
        def walked_down_one_step():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(1)
            assert_hex_at_position(slot, (162, 98), "#7b7b84")
        retry(walked_down_one_step)

    def equip_bike():
        slot.abort_if_frozen()
        def equipped_bike():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.SELECT))
            time.sleep(1)
            assert_hex_at_position(slot, (120, 87), "#000000")
        retry(equipped_bike)

    def zigzag_until_dialogue():
        started = time.monotonic()
        def dialogue_window_is_visible():
            slot.abort_if_frozen()
            # Bail out if zigzag is taking too long for whatever reason
            time_elapsed = time.monotonic() - started
            if time_elapsed > TIME_ALLOWED_FOR_ZIGZAG:
                increment_abandoned_attempts("zigzag_timeout")
                raise Exception(f"[{slot.idx}] Abandoned zigzag after {time_elapsed} seconds, restarting game in slot {slot.idx}")
            return get_pixel_hex(slot, (13, 123)) == "#ffffff"
        while not dialogue_window_is_visible():
            brief_zigzag()

    def brief_zigzag():
        slot.abort_if_frozen()
        for _ in range(4):
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.RIGHT))
            time.sleep(0.4)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.RIGHT))
            time.sleep(0.03)
            o.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.LEFT))
            time.sleep(0.4)
            o.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.LEFT))
            time.sleep(0.03)

    def complete_hatch_sequence():
        slot.abort_if_frozen()
        # Ensure we're in "Huh?" dialogue
        def dialogue_huh():
            assert_contains_dialogue_text(slot, ".Huh?")
        retry(dialogue_huh)
        # Advance to hatching screen, stopping at the nickname YES/NO selection
        def advance_to_hatching_screen_nickname():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(3.5)
            assert_hex_at_position(slot, (170, 80), "#636363")
        retry(advance_to_hatching_screen_nickname)
        # Move rename cursor to NO
        def move_rename_cursor_to_no():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(1)
            assert_hex_at_position(slot, (170, 94), "#636363")
        retry(move_rename_cursor_to_no)
        # Select NO
        def confirm_decline_nickname():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_not_hex_at_position(slot, (170, 94), "#636363")
        retry(confirm_decline_nickname)

    def open_pokemon_summary():
        slot.abort_if_frozen()
        # Open the START menu
        def open_start_menu():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.START))
            time.sleep(1)
            assert_hex_at_position(slot, (178, 14), "#636363")
        retry(open_start_menu)
        # Move cursor to POKEMON
        def move_cursor_to_pokemon():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(1)
            assert_hex_at_position(slot, (178, 29), "#636363")
        retry(move_cursor_to_pokemon)
        # Select POKEMON
        def select_pokemon_menu_item():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_hex_at_position(slot, (53, 35), "#7bd6ef")
        retry(select_pokemon_menu_item)
        # Move to the CANCEL slot
        def move_to_cancel_slot_on_pokemon_menu():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
            time.sleep(1)
            assert_hex_at_position(slot, (232, 143), "#a573f7")
        retry(move_to_cancel_slot_on_pokemon_menu)
        # Move selection to last pokemon
        def move_selection_to_last_pokemon():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.UP))
            time.sleep(1)
            assert_hex_at_position(slot, (202, 61), "#7bd6ef")
        retry(move_selection_to_last_pokemon)
        # Enter selection
        def enter_pokemon_selection():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(1)
            assert_hex_at_position(slot, (155, 96), "#636363")
        retry(enter_pokemon_selection)
        # Open SUMMARY
        def open_summary():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(2)
            assert_hex_at_position(slot, (89, 8), "#e7de9c")
        retry(open_summary)

    def pokemon_is_shiny():
        slot.abort_if_frozen()
        pokemon_hex = get_pixel_hex(slot, POKEMON_SPECIES.summary.crosshair)
        is_shiny = pokemon_hex != POKEMON_SPECIES.summary.normal_hex
        if is_shiny:
            print(f"[{slot.idx}] Shiny found after {eggs_hatched} eggs hatched")
        return is_shiny

    def save_game():
        slot.abort_if_frozen()
        # Move back to selection menu from SUMMARY
        def move_back_to_selection_menu_from_summary():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
            time.sleep(1)
            assert_hex_at_position(slot, (155, 96), "#636363")
        retry(move_back_to_selection_menu_from_summary)
        # Move back to POKEMON menu from selection menu
        def move_back_to_pokemon_menu_from_selection():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
            time.sleep(1)
            assert_hex_at_position(slot, (202, 61), "#7bd6ef")
        retry(move_back_to_pokemon_menu_from_selection)
        # Move back to START menu from POKEMON menu
        def move_back_to_start_menu_from_pokemon_menu():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
            time.sleep(1)
            assert_hex_at_position(slot, (178, 29), "#636363")
        retry(move_back_to_start_menu_from_pokemon_menu)
        # Move down to BAG menu item from POKEMON item
        def move_down_to_bag_menu_item_from_pokemon_item():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(1)
            assert_hex_at_position(slot, (178, 44), "#636363")
        retry(move_down_to_bag_menu_item_from_pokemon_item)
        # Move down to PLAYER menu item from BAG item
        def move_down_to_player_menu_item_from_bag_item():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(1)
            assert_hex_at_position(slot, (178, 59), "#636363")
        retry(move_down_to_player_menu_item_from_bag_item)
        # Move down to SAVE menu item from PLAYER item
        def move_down_to_save_menu_item_from_player_item():
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.DOWN))
            time.sleep(1)
            assert_hex_at_position(slot, (178, 75), "#636363")
        retry(move_down_to_save_menu_item_from_player_item)
        for _ in range(2):
            o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
            time.sleep(3)
        print(f"[{slot.idx}] Attempting to save game...")
        o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3)
        print(f"[{slot.idx}] Saved game...")
        # # Press A on SAVE start menu item
        # def press_a_on_save_menu_item_three_times():
        #     for _ in range(3):
        #         o.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        #         time.sleep(3)
        #     # assert_hex_at_position(slot, (170, 80), "#636363")
        #     # TODO do something here
        # retry(press_a_on_save_menu_item_three_times)

    """Automation instructions for each bot instance per iteration
    """
    try:
        start_game()
        pick_up_egg()
        walk_down_one_step()
        equip_bike()
        zigzag_until_dialogue()
        complete_hatch_sequence()
        open_pokemon_summary()
        if pokemon_is_shiny():
            save_game()
            play_success(blocking=True)
            group.kill()
        increment_eggs_hatched()
    finally:
        log_egg_report()

"""Putting it all together and running it"""
group = InstanceGroup(NUM_INSTANCES, POKEMON_RED_ROM, starting_port=STARTING_PORT, exe=MGBA_SDL)
group.start(fast_forward=True, minimize=True)
group.run(attempt)

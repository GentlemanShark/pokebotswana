"""Functions which can dictate the behavior of the bot on a game-level (as opposed to an emulator level).
Intended to be used in automation scripts like egg-hatchers and shiny-catchers.
Example:
- Advancing through dialogue
- Making a selection on a menu
"""

import time
from typing import Callable
from pkbt.instances import InstanceSlot
from pkbt.console import callable_name, for_console
from pkbt.input.key_type import KeyType
from pkbt.input.key_event import KeyEventType
from pkbt.input.key_event import KeyEvent
import random
from pkbt.text import assert_on_continue_screen, assert_contains_dialogue_text
from pkbt.image_processing import assert_not_hex_at_position, assert_hex_at_position, get_pixel_hex

# Bot may not process inputs when several mGBA instances are running in parallel.
# It will attempt to detect this and retry the action up to MAX_TRIES times.
MAX_TRIES = 3

# Basic input function(s)
def press_wait_until(slot: InstanceSlot, key: KeyType, time_before_assertion: float, assertion: Callable[[], None]):
    """Sequentially:
    - Presses the given key
    - Waits for the given time
    - Asserts the given condition

    If the assertion fails, repeats the process up to MAX_TRIES times.
    """
    def press_and_assert():
        slot.orch.client.execute_event(KeyEvent(KeyEventType.PUSH, key))
        time.sleep(time_before_assertion)
        assertion()
    press_and_assert.__name__ = f"{key.name} {callable_name(assertion)}"
    _retry(slot, press_and_assert)

def _retry(slot: InstanceSlot, callback, timer=3, max_tries=MAX_TRIES):
    tries = 1
    has_previosuly_failed = False
    while tries < max_tries:
        slot.abort_if_frozen()
        try:
            callback()
            if has_previosuly_failed:
                print(f"[{slot.idx}] Successfully completed {callback.__name__} after {tries} tries")
            return # Success
        except Exception as e:
            print(f"[{slot.idx}] Retrying {callback.__name__} after {tries} failure(s): {for_console(e)}")
            has_previosuly_failed = True
            time.sleep(timer)
            tries += 1
    raise Exception(f"[{slot.idx}] Abandoned {callback.__name__} after {max_tries} tries, restarting game in slot {slot.idx}")


# Functions for starting/restarting the game

def reset_game(slot: InstanceSlot):
    """Reset the game in the given slot.
    """
    slot.orch.client.reset_game()

def reset_game_and_proceed_to_continue_screen(slot: InstanceSlot):
    """Reset the game in the given slot and proceed to the continue screen.
    """
    slot.abort_if_frozen()
    # The seed is the time from reset until the A press leaves PRESS START.
    # That press can hit 1024 seeds, one per frame for about 17s of game
    # time. The spread below is that long at roughly 10x fast-forward.
    # PRESS START restarts the intro after about 45s of game time.
    reset_game(slot)
    time.sleep(random.uniform(0.7, 2.5))
    # Progress through enough of the startup sequence to reach the recap
    for _ in range(3):
        slot.orch.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(0.7)
    time.sleep(1)
    assert_on_continue_screen(slot)

def start_game_and_proceed_to_overworld(slot: InstanceSlot):
    """Start the game and proceed to the overworld.
    - Resets the game
    - Proceeds to the continue screen
    - Presses A to start the game
    - Presses B twice to proceed to the overworld, skipping the recap
    """
    slot.abort_if_frozen()
    reset_game_and_proceed_to_continue_screen(slot)
    slot.orch.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
    time.sleep(0.7)
    for _ in range(2):
        slot.orch.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.B))
        time.sleep(0.7)


# Functions for hatching eggs

def pick_up_egg(slot: InstanceSlot):
    """Pick up an egg from Old Man.

    Setup conditions:
    - The player is facing the Old Man
    - The Old Man has an egg to give
    - No menus are open

    I'll add more as I think of them...
    """
    slot.abort_if_frozen()
    # To be safe, check that the dialogue window hasn't accidentally been opened
    try:
        assert_not_hex_at_position(slot, (13, 123), "#ffffff")
    except Exception as e:
        raise Exception(f"[{slot.idx}] Failed to check that the dialogue window hasn't accidentally been opened. {e}")
    # Advance through the dialogue
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "Ah, it\u2019s you"))
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "We were roisin"))
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "hod \xe7m EGG"))
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "We don\u2019t know how it got there"))
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "do wont it, yes"))
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "the Eoc from"))
    press_wait_until(slot, KeyType.A, 1, lambda: assert_contains_dialogue_text(slot, "Toke good core of it."))
    # Finish the dialogue
    press_wait_until(slot, KeyType.B, 0.7, lambda: assert_not_hex_at_position(slot, (13, 123), "#ffffff"))

def walk_down_one_step_from_old_man(slot: InstanceSlot):
    """Walk down one step from Old Man.
    Setup conditions:
    - `pick_up_egg()` was successfully completed
    """
    slot.abort_if_frozen()
    press_wait_until(slot, KeyType.DOWN, 1, lambda: assert_hex_at_position(slot, (162, 98), "#7b7b84"))

def equip_bike_after_egg_pickup(slot: InstanceSlot):
    """Equip the bike.
    Setup conditions:
    - Facing downward
    - No menus are open
    - The bike is not already equipped

    I'll add more as I think of them...
    """
    slot.abort_if_frozen()
    press_wait_until(slot, KeyType.SELECT, 1, lambda: assert_hex_at_position(slot, (120, 87), "#000000"))

def zigzag_until_hatching_dialogue(slot: InstanceSlot):
    """Zigzag until the hatching dialogue is visible.
    Setup conditions:
    - `equip_bike_after_egg_pickup()` was successfully completed
    """
    TIME_ALLOWED_FOR_ZIGZAG = 420 # seconds
    started = time.monotonic()
    def dialogue_window_is_visible():
        slot.abort_if_frozen()
        # Bail out if zigzag is taking too long for whatever reason
        time_elapsed = time.monotonic() - started
        if time_elapsed > TIME_ALLOWED_FOR_ZIGZAG:
            raise Exception(f"[{slot.idx}] Abandoned zigzag after {time_elapsed} seconds, restarting game in slot {slot.idx}")
        return get_pixel_hex(slot, (13, 123)) == "#ffffff"
    while not dialogue_window_is_visible():
        def brief_zigzag():
            slot.abort_if_frozen()
            for _ in range(4):
                slot.orch.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.RIGHT))
                time.sleep(0.4)
                slot.orch.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.RIGHT))
                time.sleep(0.03)
                slot.orch.client.execute_event(KeyEvent(KeyEventType.HOLD, KeyType.LEFT))
                time.sleep(0.4)
                slot.orch.client.execute_event(KeyEvent(KeyEventType.RELEASE, KeyType.LEFT))
                time.sleep(0.03)
        brief_zigzag()

def watch_hatching_and_decline_nickname(slot: InstanceSlot):
    """Watch the hatching and decline the nickname.
    Setup conditions:
    - We're in the "Huh?" dialogue from a hatching egg
    """
    slot.abort_if_frozen()
    # Ensure we're in "Huh?" dialogue
    def dialogue_huh():
        assert_contains_dialogue_text(slot, ".Huh?")
    _retry(slot, dialogue_huh)
    # Advance to hatching screen, stopping at the nickname YES/NO selection
    press_wait_until(slot, KeyType.A, 3.5, lambda: assert_hex_at_position(slot, (170, 80), "#636363"))
    # Move rename cursor to NO
    press_wait_until(slot, KeyType.DOWN, 1, lambda: assert_hex_at_position(slot, (170, 94), "#636363"))
    # Select NO
    press_wait_until(slot, KeyType.A, 1, lambda: assert_not_hex_at_position(slot, (170, 94), "#636363"))

def open_pokemon_summary_of_last_party_member(slot: InstanceSlot):
    """Open the Pokemon summary.
    Setup conditions:
    - `watch_hatching_and_decline_nickname()` was successfully completed
    - No menus are open
    """
    slot.abort_if_frozen()
    # Open the START menu
    press_wait_until(slot, KeyType.START, 1, lambda: assert_hex_at_position(slot, (178, 14), "#636363"))
    # Move cursor to POKEMON
    press_wait_until(slot, KeyType.DOWN, 1, lambda: assert_hex_at_position(slot, (178, 29), "#636363"))
    # Select POKEMON
    press_wait_until(slot, KeyType.A, 1, lambda: assert_hex_at_position(slot, (53, 35), "#7bd6ef"))
    # Move to the CANCEL slot
    press_wait_until(slot, KeyType.UP, 1, lambda: assert_hex_at_position(slot, (232, 143), "#a573f7"))
    # Move selection to last pokemon
    press_wait_until(slot, KeyType.UP, 1, lambda: assert_hex_at_position(slot, (202, 61), "#7bd6ef"))
    # Enter selection
    press_wait_until(slot, KeyType.A, 1, lambda: assert_hex_at_position(slot, (155, 96), "#636363"))
    # Open SUMMARY
    press_wait_until(slot, KeyType.A, 2, lambda: assert_hex_at_position(slot, (89, 8), "#e7de9c"))

def save_game_from_summary(slot: InstanceSlot):
    """Save the game.
    Setup conditions:
    - Currently in the Pokemon SUMMARY view from party
    """
    slot.abort_if_frozen()
    # Move back to selection menu from SUMMARY
    press_wait_until(slot, KeyType.B, 1, lambda: assert_hex_at_position(slot, (155, 96), "#636363"))
    # Move back to POKEMON menu from selection menu
    press_wait_until(slot, KeyType.B, 1, lambda: assert_hex_at_position(slot, (202, 61), "#7bd6ef"))
    # Move back to START menu from POKEMON menu
    press_wait_until(slot, KeyType.B, 1, lambda: assert_hex_at_position(slot, (178, 29), "#636363"))
    # Move down to BAG menu item from POKEMON item
    press_wait_until(slot, KeyType.DOWN, 1, lambda: assert_hex_at_position(slot, (178, 44), "#636363"))
    # Move down to PLAYER menu item from BAG item
    press_wait_until(slot, KeyType.DOWN, 1, lambda: assert_hex_at_position(slot, (178, 59), "#636363"))
    # Move down to SAVE menu item from PLAYER item
    press_wait_until(slot, KeyType.DOWN, 1, lambda: assert_hex_at_position(slot, (178, 75), "#636363"))
    for _ in range(2):
        slot.orch.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
        time.sleep(3)
    print(f"[{slot.idx}] Attempting to save game...")
    slot.orch.client.execute_event(KeyEvent(KeyEventType.PUSH, KeyType.A))
    time.sleep(3)
    print(f"[{slot.idx}] Saved game...")
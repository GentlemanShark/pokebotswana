from pkbt.actions import start_game_and_proceed_to_overworld, pick_up_egg, walk_down_one_step_from_old_man, equip_bike_after_egg_pickup, zigzag_until_hatching_dialogue, watch_hatching_and_decline_nickname, open_pokemon_summary_of_last_party_member, save_game_from_summary
from pkbt.config import MGBA_SDL, POKEMON_RED_ROM
from pkbt.image_processing import summary_sprite_is_shiny
from pkbt.audio import play_success
from pkbt.egg_report import EggReport
from pkbt.instances import InstanceGroup, InstanceSlot
from pkbt.species import SPECIES

# Tweak as needed
POKEMON_SPECIES = SPECIES["LARVITAR"]
NUM_INSTANCES = 30

# Used to report egg hatch totals
report = EggReport(every=50)

def attempt(slot: InstanceSlot):
    """Main function for each bot instance per iteration"""

    # Helper functions
    def pokemon_is_shiny_in_summary():
        slot.abort_if_frozen()
        return summary_sprite_is_shiny(slot, POKEMON_SPECIES.summary)

    def print_shiny_alert():
        print(f"[{slot.idx}] Shiny found after {report.eggs_hatched} eggs hatched")

    # Logic per iteration
    
    try:
        start_game_and_proceed_to_overworld(slot)
        pick_up_egg(slot)
        walk_down_one_step_from_old_man(slot)
        equip_bike_after_egg_pickup(slot)
        zigzag_until_hatching_dialogue(slot)
        watch_hatching_and_decline_nickname(slot)
        open_pokemon_summary_of_last_party_member(slot)
        if pokemon_is_shiny_in_summary():
            print_shiny_alert()
            save_game_from_summary(slot)
            play_success(blocking=True)
            group.kill()
        report.egg_hatched()
    finally:
        report.attempt_finished()

# Putting it all together and running it
group = InstanceGroup(NUM_INSTANCES, POKEMON_RED_ROM, exe=MGBA_SDL)
group.start(fast_forward=True, minimize=False)
group.run(attempt)

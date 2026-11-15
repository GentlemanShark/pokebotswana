"""Read Pokemon dialogue from a GBA screenshot.

Uses the pkmngba_en training file with Tesseract's legacy engine. The file
belongs in resources/tesseract.
"""

import time

import pytesseract
from PIL import Image, ImageOps

from pkbt.config import TESSDATA_DIR, TESSERACT
from pkbt.console import for_console
from pkbt.instances import InstanceSlot, slot_dir

pytesseract.pytesseract.tesseract_cmd = TESSERACT
LANG = "pkmngba_en"
# Tesseract reads this font reliably once the crop is about this tall.
MIN_HEIGHT = 200

# left, top, right, bottom on a 240x160 frame.
# The message pane beside FIGHT / BAG / POKEMON / RUN.
BATTLE_TEXT_BOX = (10, 121, 118, 151)
# The wide box used by "Wild X appeared!" before the command menu opens.
FULL_DIALOGUE_BOX = (10, 121, 230, 151)
# Overworld message window. The white fill is 224x36, from (8, 118) through
# (231, 153). This crop stays inside the rounded frame.
OVERWORLD_DIALOGUE_BOX = (10, 121, 230, 151)
# Status text on the player's battle panel, inside the frame.
PLAYER_PKMN_STATUS_BOX = (142, 96, 162, 107)


def read_overworld_dialogue(slot: InstanceSlot, timeout=2.0) -> str:
    """Save this slot's screenshot and read the overworld message window.

    The file is .session/<slot>/<slot>.png. Any PNG already there is removed first, and
    this waits until a readable image replaces it.
    """
    filename = f"{slot.idx}.png"
    path = slot_dir(slot.idx) / filename
    try:
        path.unlink()
    except OSError:
        pass
    slot.orch.client.save_screenshot_to_file(filename)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return read_text(path, OVERWORLD_DIALOGUE_BOX)
        except (OSError, ValueError):
            time.sleep(0.05)
    raise TimeoutError(f"Screenshot {path.name} was not saved")

def capture_screenshot_and_read_text(slot: InstanceSlot, box: tuple[int, int, int, int], timeout=2.0) -> str:
    """Capture a screenshot, read the text inside the given rectangle, and return it.
    """
    filename = f"{slot.idx}.png"
    path = slot_dir(slot.idx) / filename
    try:
        path.unlink()
    except OSError:
        pass
    slot.orch.client.save_screenshot_to_file(filename)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return read_text(path, box)
        except (OSError, ValueError):
            time.sleep(0.05)
    raise TimeoutError(f"Screenshot {path.name} was not saved")

def assert_equals_dialogue_text(slot: InstanceSlot, text: str, timeout=2.0) -> None:
    """Raise if the dialogue text is not equal to the given text.
    """
    dialogue_text = read_overworld_dialogue(slot, timeout)
    if dialogue_text != text:
        raise Exception(f'Failed {assert_equals_dialogue_text.__name__}. Dialogue text is "{for_console(dialogue_text)}" instead of expected "{for_console(text)}"')

def assert_contains_dialogue_text(slot: InstanceSlot, text: str, timeout=2.0) -> None:
    """Raise if the dialogue text does not contain the given text.
    """
    dialogue_text = read_overworld_dialogue(slot, timeout)
    if text not in dialogue_text:
        raise Exception(f'Failed {assert_contains_dialogue_text.__name__}. Dialogue text is "{for_console(dialogue_text)}" instead of expected "{for_console(text)}"')

def read_text(source, box: tuple[int, int, int, int]) -> str:
    """Return the text inside box. source is an image or a path to one."""
    traineddata = TESSDATA_DIR / f"{LANG}.traineddata"
    if not traineddata.is_file():
        raise FileNotFoundError(
            f"Missing {traineddata}. The GBA English training file is pkmngba_en.traineddata."
        )
    image = _open(source)
    prepared = _prepare(image, box)
    config = f"--tessdata-dir {TESSDATA_DIR} --oem 0 --psm 6"
    return pytesseract.image_to_string(prepared, lang=LANG, config=config).strip()


def _open(source) -> Image.Image:
    if isinstance(source, Image.Image):
        return source
    return Image.open(source)


def _prepare(image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    image = image.convert("L").crop(box)
    image = ImageOps.autocontrast(image)
    scale = max(1.0, MIN_HEIGHT / image.height)
    if scale > 1:
        image = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.Resampling.BILINEAR,
        )
    return image

def assert_on_continue_screen(slot: InstanceSlot, timeout=2.0) -> None:
    """Raise if the player is not on the continue screen.
    """
    continue_text = capture_screenshot_and_read_text(slot, [23, 12, 76, 22], timeout)
    if continue_text != "CONTINUE":
        raise Exception(f'Failed {assert_on_continue_screen.__name__}. CONTINUE text is "{for_console(continue_text)}" instead of expected "CONTINUE"')
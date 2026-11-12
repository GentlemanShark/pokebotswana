import time
from pathlib import Path

from PIL import Image, ImageDraw

from pkbt.config import TEMP_DIR
from pkbt.instances import InstanceSlot

def pixel_rgb(path, x, y):
    im = Image.open(path).convert("RGB")  # 3 channels, no alpha
    return im.getpixel((x, y))            # Normal: (x, y)

def pixel_hex(path, x, y):
    r, g, b = pixel_rgb(path, x, y)
    return f"#{r:02x}{g:02x}{b:02x}"

def dialogue_arrow_is_visible(path, take_screenshot=None, timeout=2.0) -> bool:
    """True when the red continue arrow is showing in the message box.

    The arrow stays on one row. Its horizontal position follows the text, so
    the row is scanned from x=10 through x=230.

    Pass take_screenshot to wait for a new capture. Without it, path is read as it is.
    """
    dialogue_arrow_y = 127
    dialogue_arrow_x_start = 10
    dialogue_arrow_x_end = 230
    dialogue_arrow_rgb = (255, 0, 0)
    if take_screenshot is not None:
        pixel_hex_when_ready(path, dialogue_arrow_x_start, dialogue_arrow_y, take_screenshot, timeout)
    im = Image.open(path).convert("RGB")
    for x in range(dialogue_arrow_x_start, dialogue_arrow_x_end + 1):
        if im.getpixel((x, dialogue_arrow_y)) == dialogue_arrow_rgb:
            return True
    return False

def pixel_hex_when_ready(path, x, y, take_screenshot, timeout=2.0):
    """Take a new screenshot, then read one pixel from it.

    take_screenshot only has to request the file. The PNG already at path is
    removed first, and this waits until a readable image replaces it.
    """
    path = Path(path)
    try:
        path.unlink()
    except OSError:
        pass
    take_screenshot()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return pixel_hex(path, x, y)
        except (OSError, ValueError):
            time.sleep(0.05)
    raise TimeoutError(f"Screenshot {path.name} was not saved")

def get_pixel_hex(slot: InstanceSlot, xy: tuple[int, int], timeout=2.0) -> str:
    """Save this slot's screenshot and return the hex color at xy.

    xy is (x, y) on a 240x160 frame. The file is temp/<slot>.png.
    """
    x, y = xy
    filename = f"{slot.idx}.png"
    return pixel_hex_when_ready(
        TEMP_DIR / filename,
        x,
        y,
        lambda: slot.orch.client.save_screenshot_to_file(filename),
        timeout,
    )

def assert_hex_at_position(slot: InstanceSlot, xy: tuple[int, int], hex: str, timeout=2.0) -> bool:
    """Return True if the hex color at xy is equal to the given hex.

    xy is (x, y) on a 240x160 frame. The file is temp/<slot>.png.
    """
    pixel_hex = get_pixel_hex(slot, xy, timeout)
    if pixel_hex != hex:
        raise Exception(f'Failed {assert_hex_at_position.__name__}. Pixel color at {xy} is {pixel_hex} instead of {hex}')

def assert_not_hex_at_position(slot: InstanceSlot, xy: tuple[int, int], hex: str, timeout=2.0) -> bool:
    """Assert that the hex color at xy is not equal to the given hex.
    """
    pixel_hex = get_pixel_hex(slot, xy, timeout)
    if pixel_hex == hex:
        raise Exception(f'Failed {assert_not_hex_at_position.__name__}. Pixel color at {xy} is {pixel_hex} instead of not {hex}')

def save_with_crosshair(src_path, out_path, x, y):
    # Load image as RGB
    im = Image.open(src_path).convert("RGB")

    # Create a drawing context
    draw = ImageDraw.Draw(im)

    neon_green = (57, 255, 20)  # RGB neon green, no alpha

    # Vertical line (top to bottom) - x controls horizontal position
    draw.line([(x, 0), (x, im.height - 1)], fill=neon_green, width=1)
    # Horizontal line (left to right) - y controls vertical position  
    draw.line([(0, y), (im.width - 1, y)], fill=neon_green, width=1)

    # Save clone
    im.save(out_path)
from pathlib import Path
import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "config.toml"

with CONFIG_FILE.open("rb") as f:
    CONFIG = tomllib.load(f)

"""mGBA Scripts"""
SCRIPTS_DIR = REPO_ROOT / "emu" / "mgba_scripts"
SERVER_SCRIPT = SCRIPTS_DIR / "server.lua"
INPUT_DISPLAY_SCRIPT = SCRIPTS_DIR / "input_display.lua"

"""mGBA Emulator"""
MGBA_DEV = REPO_ROOT / "emu" / "mgba_dev" / "mGBA.exe"
MGBA_SDL = REPO_ROOT / "emu" / "mgba_sdl" / "mgba-sdl.exe"

"""OCR"""
TESSERACT = CONFIG["ocr"]["tesseract"]
TESSDATA_DIR = REPO_ROOT / "resources" / "tesseract"

"""ROMS"""
POKEMON_RED_ROM = Path(CONFIG["roms"]["pokemon_red"])
POKEMON_SAPPHIRE_ROM = Path(CONFIG["roms"]["pokemon_sapphire"])
POKEMON_EMERALD_ROM = Path(CONFIG["roms"]["pokemon_emerald"])

"""Runtime"""
TEMP_DIR = REPO_ROOT / "temp"
STATE_MANAGER = TEMP_DIR / "pkbt_app_state.json"

"""Input"""
DEFAULT_PUSH_TIME = CONFIG["input"]["default_push_time"]

"""Audio"""
AUDIO_DIR = REPO_ROOT / "resources" / "audio"
SUCCESS_AUDIO = AUDIO_DIR / "success.wav"
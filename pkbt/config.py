from pathlib import Path
import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "config.toml"

with CONFIG_FILE.open("rb") as f:
    CONFIG = tomllib.load(f)

"""mGBA Scripts"""
SCRIPTS_DIR = REPO_ROOT / "mgba_scripts"
SERVER_SCRIPT = SCRIPTS_DIR / CONFIG["scripts"]["server"]
INPUT_DISPLAY_SCRIPT = SCRIPTS_DIR / CONFIG["scripts"]["input_display"]

"""mGBA Emulator"""
MGBA_DEV = CONFIG["emulator"]["mgba_dev"]
MGBA_SDL = CONFIG["emulator"]["mgba_sdl"]

"""OCR"""
TESSERACT = CONFIG["ocr"]["tesseract"]
TESSDATA_DIR = REPO_ROOT / CONFIG["ocr"]["tessdata"]

"""ROMS"""
POKEMON_RED_ROM = REPO_ROOT / CONFIG["roms"]["pokemon_red"]
POKEMON_SAPPHIRE_ROM = REPO_ROOT / CONFIG["roms"]["pokemon_sapphire"]
POKEMON_EMERALD_ROM = REPO_ROOT / CONFIG["roms"]["pokemon_emerald"]

"""Runtime"""
TEMP_DIR = REPO_ROOT / CONFIG["runtime"]["temp_directory"]
STATE_MANAGER = TEMP_DIR / CONFIG["runtime"]["state_manager"]

"""Input"""
DEFAULT_PUSH_TIME = CONFIG["input"]["default_push_time"]

"""Audio"""
AUDIO_DIR = REPO_ROOT / CONFIG["audio"]["audio_dir"]
SUCCESS_AUDIO = AUDIO_DIR / CONFIG["audio"]["success"]
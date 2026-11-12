# PokeBotswana

[Jump to Quick Start](#quick-start)

Instructions to and feedback from the emulator are handled through its [official scripting API](https://mgba.io/docs/scripting.html) (using Lua), while client automation and TCP socket communication are written in Python. No building required, just a copy of the official development build.

You may create dynamic, automated scripts for multiple independent mGBA instances simultaneously which include:
* Pressing buttons, holding/releasing buttons
* Soft-resetting the emulator instance
* Taking instance screenshots
* Checking color of specific pixels
* Playing sounds under certain conditions

## Overview

From what I understand, similar functionality can be provided by using a mGBA build with Python Bindings, <small>which I failed to create with varying degrees of success (particularly for Windows)</small>...

Instead, we use a development build of mGBA which provides official Lua scripting!

Note: although nondevelopment builds <i>do</i> seem to have the UI option for Lua Scripting, it appears to be nonfunctional. <b>A Development build of mGBA is required for Lua Scriping</b>, which fortunately is available [on the mGBA website](https://mgba.io/downloads.html#development-downloads).

## Project Structure

```
pokebotswana/
├── emu/
│    ├── mgba_dev/             # Development build of mGBA
│    ├── mgba_sdl/             # SDL build of mGBA
│    └── mgba_scripts/         # Lua scripts used with mGBA API
├── pkbt/                      # Python client
├── resources/
│    └── audio/          # Used for "Success" sound alert, if you want it.
└── tools/                     # Ignore, used to manage saves for convenience
```

## Quick Start

### 1. Setup mGBA

1. Download a [development build of mGBA](https://mgba.io/downloads.html#development-downloads) (strongly recommended) or compile your own.
2. I recommend creating `emu/mgba_dev/` which contains your dev build (namely the executable).

### 2. Get Pokemon

No Pokemon roms are included, but I'm sure you can manage. I would keep them (and their saves) in `<repo-root>/roms/`.

Disclaimer for Emerald: unlike other gen 3 titles, Emerald soft resets to the same RNG seed every time, regardless of the save clock. For this reason, I would avoid using it unless you are deliberately manipulating its RNG, or implementing measures (like waiting a variable amount of time between repeated actions) to ensure randomness when doing brute-force things like soft-resetting for shiny hunts. I mostly use Fire Red or Sapphire and bypass this.

### 3. Update `config.toml` with correct ROM paths

This may not be necessary if you follow my advised project structure in Step 1.

### 4. Run extremely simple demo

1. In command prompt (Windows) or terminal (MacOS, Linux), navigate to repo root.
2. Start the Windows demo with `run.bat -m pkbt.automation.demos.single_start_demo`, or the MacOS/Linux demo with `./run.sh -m pkbt.automation.demos.single_start_demo`
3. A pair of mGBA game/scripting windows will open and a few A presses will be performed.

### 5. Automate!

I've included a script `hatch_shiny_eevee` that I've been using successfully for a while to hatch several thousand eggs per day with 15 simultaneous mGBA instances running in fast-forward mode. Because the bot works based on actual time (not frames), you'll almost certainly have to tweak its timing based on the number of instances and your computer's speed.

## FAQ

### Why design this time-based rather than frames-based? Why use screenshots at all, if we're using an emulator (and conceivably have access to game data directly)?

This is intended to be kind of a proof-of-concept for automating using legitimate, current-gen hardware. I will be working on generalizing these features to accommodate a video capture card and third-party Nintendo Switch controller.

### Is it possible to move these Pokemon into the current Pokemon generation by "legitimate" means?

Absolutely. It's a bit convoluted, and people have made tools for shortcuts, but if you wanted to be "legitimate"...

Using just the [melonDS](https://melonds.kuribo64.net/) emulator, you can migrate from gen 3 into gen 4 (e.g. Soul Silver). Then, you can trade to a gen 5 rom. After that, using the Delta iPhone emulator, you can establish a wireless trade with a 3DS running a gen 5 game. From there, (provided you have a gen 6 save file on your 3DS) you can use Pokemon Bank to transfer to Pokemon Home.

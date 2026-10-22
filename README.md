# GoldenClicker

A lightweight autoclicker for golden cookies, wrath cookies, etc. in Cookie Clicker. It connects to the game over the Chrome DevTools Protocol and pops shimmers directly through the game's own API.
Because it never looks at the screen, the game window can be minimized, unfocused, or on any monitor at any DPI scaling.
Let me know if there are issues or features you'd like!

**Works on Windows, macOS, and Linux.**
## Requirements

- Python 3.x
- Cookie Clicker (Steam version) launched with remote debugging enabled on port 9222

## Setup

1. Install dependencies: `pip install websocket-client requests`
2. In Steam, set Cookie Clicker's launch options to: `--remote-debugging-port=9222`
3. Launch Cookie Clicker
4. Run: `python GoldenClicker.py`

## How it works

On startup the script finds the game's tab at `localhost:9222`, connects over a websocket, and runs a small JavaScript snippet that pops every entry in `Game.shimmers`. If something was popped, it checks again after 0.5 seconds to catch chained spawns. Otherwise it waits 5 seconds.

## Configuration

- `port` (`CDPClient` argument): debugging port (default: `9222`)
- `title_suffix` (`CDPClient` argument): the game's tab title must end with this (default: `"Cookie Clicker"`)

# Project

This was a quick project, meant to be a very lightweight and simple autoclicker for golden cookies and wrath cookies. 
It should work regardless of where the cookie clicker window is (for now the window must be visible, but not in focus)
Let me know if there are issues or features you'd like!

# GoldenClicker

Automatically detects and clicks golden cookies in Cookie Clicker using a YOLO object detection model.

## Requirements
- Python 3.x
- Cookie Clicker open in a browser window

## Setup
1. Install dependencies:
   pip install ultralytics opencv-python mss numpy

2. Run:
   python GoldenClicker.py

## Configuration
Edit the user input section at the top of `GoldenClicker.py`:
- `CONF_THRESHOLD` — minimum confidence to trigger a click (default: 0.8)
- `SCAN_INTERVAL` — seconds between scans (default: 5)
- `DISPLAY` — show live detection window (default: True)

## Notes
- Designed for Windows with multi-monitor support
- Tested on a secondary monitor running at 150% DPI scaling

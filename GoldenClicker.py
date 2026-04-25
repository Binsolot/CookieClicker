# ------- Package Import ------- #
from ultralytics import YOLO
import numpy as np
import ctypes
import time
import mss
import cv2
# ------- Package Import ------- #


# --------- User Input --------- #
# Future: Create Light GUI if adding additional functionality. (Selecting classes to click; Upgrades; Stock Market?)
CONF_THRESHOLD = 0.8
SCAN_INTERVAL = 5 # seconds
DISPLAY = True
# --------- User Input --------- #


# -------- Function Def -------- #
def find_window(title_substring):
    """Find a window by partial title match and return its HWND."""
    # Future: Remove visibility check here and add to loop (make window visible and click functionality)
    found = []

    def callback(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_substring.lower() in buf.value.lower():
                found.append((hwnd, buf.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found


def get_window_rect(hwnd):
    """Get the logical rect of a window via DwmGetWindowAttribute."""
    rect = ctypes.wintypes.RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect))
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def get_monitor_scale(hwnd):
    """Get physical/logical scale factor using actual DPI from the monitor."""
    monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
    dpi_x = ctypes.c_uint()
    dpi_y = ctypes.c_uint()
    ctypes.windll.shcore.GetDpiForMonitor(monitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
    return dpi_x.value / 96.0  # 96 DPI = 100% scaling


def move_mouse(x, y):
    """Move mouse using SendInput. Expects physical pixel coords."""
    vl = ctypes.windll.user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
    vt = ctypes.windll.user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
    vw = ctypes.windll.user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
    vh = ctypes.windll.user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

    inp = INPUT()
    inp.type = 0
    inp.mi.dx = int((x - vl) * 65535 / vw)
    inp.mi.dy = int((y - vt) * 65535 / vh)
    inp.mi.dwFlags = 0x0001 | 0x8000 | 0x4000  # MOVE | ABSOLUTE | VIRTUALDESK
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def click_mouse():
    """Send a left click at the current cursor position."""
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

    for flag in [0x0002, 0x0004]:  # LEFTDOWN, LEFTUP
        inp = INPUT()
        inp.type = 0
        inp.mi.dwFlags = flag
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
# -------- Function Def -------- #


# ------- Setup Constants ------ #
model = YOLO("Weights/Fit1_GW.pt")

matches = find_window("Cookie Clicker")
if not matches:
    raise RuntimeError("Cookie Clicker window not found — is it open?")
if len(matches) > 1:
    print("More than one matching window. Using first found.")

hwnd, title = matches[0]
print(f"Found window: '{title}' (HWND={hwnd})")

mon_scale = get_monitor_scale(hwnd)
print(f"Monitor scale: {mon_scale:.3f}")
# ------- Setup Constants ------ #


# -------- Main Process -------- #
with mss.MSS() as sct:
    while True:
        time.sleep(SCAN_INTERVAL)

        win_left, win_top, win_w, win_h = get_window_rect(hwnd)

        frame = cv2.cvtColor(
            np.array(sct.grab({"left": win_left, "top": win_top, "width": win_w, "height": win_h}), dtype=np.uint8),
            cv2.COLOR_BGRA2BGR
        )

        detections = [box for box in model(frame, verbose=False)[0].boxes if float(box.conf[0]) >= CONF_THRESHOLD]
        

        for box in detections:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            move_mouse((win_left + cx) * mon_scale, (win_top + cy) * mon_scale)
            click_mouse()

            if DISPLAY:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"{float(box.conf[0]):.2f}", (int(x1), int(y1) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if DISPLAY:
            print(f"Scan complete — {len(detections)} detection(s) found.")
            cv2.imshow("Calibrate", frame)
            cv2.waitKey(1)
# -------- Main Process -------- #

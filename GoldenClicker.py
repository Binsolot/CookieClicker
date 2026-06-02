# ------- Package Import ------- #
from ultralytics import YOLO
import numpy as np
import ctypes
import time
import cv2
# ------- Package Import ------- #


# --------- User Input --------- #
# Future: Create Light GUI if adding additional functionality. (Selecting classes to click; Upgrades; Stock Market?)
CONF_THRESHOLD = 0.8
SCAN_INTERVAL = 5  # seconds
DISPLAY = False
# --------- User Input --------- #


# -------- Function Def -------- #
def find_window(title_substring):
    """Find a window by partial title match and return its HWND."""
    # Future: Remove visibility check here and add to loop (make window visible and click functionality)
    found = []

    def callback(hwnd, _):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        if title_substring.lower() in buf.value.lower():
            found.append((hwnd, buf.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found


def capture_window(hwnd):
    """Capture a window's content using PrintWindow"""
    rect = ctypes.wintypes.RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top

    hdc_win = ctypes.windll.user32.GetDC(hwnd)
    hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc_win)
    hbmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc_win, w, h)
    ctypes.windll.gdi32.SelectObject(hdc_mem, hbmp)

    # PW_RENDERFULLCONTENT (0x2) captures hardware-accelerated content (e.g. browser/WebGL)
    ctypes.windll.user32.PrintWindow(hwnd, hdc_mem, 0x2)

    bmi = ctypes.create_string_buffer(40)  # BITMAPINFOHEADER
    ctypes.c_int32.from_buffer(bmi, 0).value = 40  # biSize
    ctypes.c_int32.from_buffer(bmi, 4).value = w  # biWidth
    ctypes.c_int32.from_buffer(bmi, 8).value = -h  # biHeight (negative = top-down)
    ctypes.c_uint16.from_buffer(bmi, 12).value = 1  # biPlanes
    ctypes.c_uint16.from_buffer(bmi, 14).value = 32  # biBitCount

    buf = ctypes.create_string_buffer(w * h * 4)
    ctypes.windll.gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, bmi, 0)

    ctypes.windll.gdi32.DeleteObject(hbmp)
    ctypes.windll.gdi32.DeleteDC(hdc_mem)
    ctypes.windll.user32.ReleaseDC(hwnd, hdc_win)

    frame = np.frombuffer(buf, dtype=np.uint8).reshape((h, w, 4))
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)


def click_at(hwnd, x, y):
    """Click at logical coords relative to the window's client area."""
    dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
    scale = dpi / 96.0  # 96 DPI = 100% scaling

    # Convert physical -> logical
    lx = int(x / scale)
    ly = int(y / scale)

    lparam = ctypes.wintypes.LPARAM((ly << 16) | (lx & 0xFFFF))
    down = ctypes.windll.user32.PostMessageW(hwnd, 0x0201, 1, lparam)
    up   = ctypes.windll.user32.PostMessageW(hwnd, 0x0202, 0, lparam)
    if not down or not up:
        print(f"Warning: click message dropped at ({x}, {y})")
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
# ------- Setup Constants ------ #


# -------- Main Process -------- #
try:
    while True:
        if not ctypes.windll.user32.IsWindow(hwnd):
            matches = find_window("Cookie Clicker")
            if matches:
                hwnd, title = matches[0]
            else:
                print("Window lost, retrying...")
                time.sleep(SCAN_INTERVAL)
                continue

        if ctypes.windll.user32.IsIconic(hwnd):
            ctypes.windll.user32.ShowWindow(hwnd, 4)  # SW_RESTORE
            while ctypes.windll.user32.IsIconic(hwnd):  # wait for restore
                time.sleep(0.005)

        try:
            frame = capture_window(hwnd)
        except Exception as e:
            print(f"Capture failed: {e}")
            time.sleep(SCAN_INTERVAL)
            continue

        detections = [box for box in model(frame, verbose=False)[0].boxes if float(box.conf[0]) >= CONF_THRESHOLD]
        for box in detections:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            click_at(hwnd, int((x1 + x2) / 2), int((y1 + y2) / 2))

            if DISPLAY:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, f"{float(box.conf[0]):.2f}", (int(x1), int(y1) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if DISPLAY:
            print(f"Scan complete — {len(detections)} detection(s) found.")
            cv2.imshow("Current View", frame)
            cv2.waitKey(1)
        
        time.sleep(SCAN_INTERVAL)

finally:
    cv2.destroyAllWindows()
# -------- Main Process -------- #

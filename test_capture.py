# Confirm the "fly's eye" can see the screen.
import mss
import numpy as np
from PIL import Image

with mss.mss() as sct:
    monitor = sct.monitors[1]  # Get the primary monitor
    screenshot = sct.grab(monitor)  # Capture the screen

    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    img.save("test_capture.png")

    print(f"   Screen captured successfully!")
    print(f"   Resolution: {screenshot.width}x{screenshot.height} pixels")
    print(f"   Saved to: test_capture.png")
#  detect bright, saturated objects on screen.
# This simulates how the fly's reward circuit spots "sugar" (collectible items).

import mss
import numpy as np
import cv2
from PIL import Image

def capture_frame():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

def detect_items(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Filter: high saturation + high brightness = colorful item
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    mask = ((sat > 80) & (val > 100)).astype(np.uint8) * 255

    # Clean up noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Find blobs
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    items = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 200:  # ignore tiny noise
            continue
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        items.append((cx, cy, area))

    return items, mask

# --- Run ---
print(" Capturing screen...")
frame = capture_frame()

print(" Detecting colorful items...")
items, mask = detect_items(frame)

# Draw results on frame
vis = frame.copy()
for (cx, cy, area) in items:
    radius = int(np.sqrt(area / np.pi))
    cv2.circle(vis, (cx, cy), radius, (0, 255, 0), 2)
    cv2.circle(vis, (cx, cy), 4, (0, 255, 0), -1)

# Save outputs
cv2.imwrite("test_detect_result.png", vis)
cv2.imwrite("test_detect_mask.png", mask)

print(f"✅ Done!")
print(f"   Items found: {len(items)}")
for i, (cx, cy, area) in enumerate(items[:5]):
    print(f"   [{i+1}] position=({cx}, {cy})  area={area:.0f}px")
print(f"   Saved: test_detect_result.png  (detections in green)")
print(f"   Saved: test_detect_mask.png    (what the fly sees)")
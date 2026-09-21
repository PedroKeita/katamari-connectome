import sys
sys.path.insert(0, '.')
from vision.capture import ScreenCapture
from vision.wall_detector import WallDetector
import time

cap = ScreenCapture(monitor=1)
detector = WallDetector()

print("Monitorando paredes por 30s...")
for i in range(300):
    frame = cap.capture()
    threat, side = detector.detect(frame)
    if threat > 0.1:
        print(f"  threat={threat:.3f} side={side}")
    time.sleep(0.1)

cap.close()
print("Feito")
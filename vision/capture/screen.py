import mss
import numpy as np
import cv2


class ScreenCapture:

    def __init__(self, monitor=1):
        self.monitor = monitor
        self.sct = mss.mss()

    def capture(self):
        screenshot = self.sct.grab(
            self.sct.monitors[self.monitor]
        )

        frame = np.array(screenshot)

        return cv2.cvtColor(
            frame,
            cv2.COLOR_BGRA2BGR
        )

    def close(self):
        self.sct.close()
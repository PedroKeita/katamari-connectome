import time
import cv2

from vision.capture import ScreenCapture
from vision.detection.objects import detect_objects
from vision.tracking import ObjectTracker


capture = ScreenCapture()

tracker = ObjectTracker(
    max_distance=80,
    max_missing_frames=5,
    collection_radius=130
)


print("=== OBJECT TRACKING TEST ===")
print("Pressione CTRL+C para parar.")
print()


# Aproximação inicial do centro do Katamari.
# Vamos ajustar depois.
katamari_center = (825, 600)


try:

    while True:

        frame = capture.capture()

        detections, _ = detect_objects(frame)

        tracked_objects = tracker.update(
            detections,
            katamari_center=katamari_center
        )

        debug = frame.copy()

        for obj in tracked_objects:

            x = int(obj.x)
            y = int(obj.y)

            width = int(obj.width)
            height = int(obj.height)

            if obj.state == "COLLECTED":
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            cv2.rectangle(
                debug,
                (x, y),
                (x + width, y + height),
                color,
                2
            )

            label = (
                f"#{obj.id} "
                f"{obj.state} "
                f"age={obj.age}"
            )

            cv2.putText(
                debug,
                label,
                (x, max(20, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )

        cv2.namedWindow("Object Tracking", cv2.WINDOW_NORMAL)
        cv2.moveWindow("Object Tracking", 1700, 100)

        cv2.imshow("Object Tracking", debug)

        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            break

        time.sleep(0.03)

finally:

    capture.close()
    cv2.destroyAllWindows()

    print()
    print("=== TEST FINISHED ===")
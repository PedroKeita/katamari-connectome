import math


class TrackedObject:
    def __init__(self, object_id, x, y, width, height, score):
        self.id = object_id

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.score = score

        self.age = 1
        self.missing_frames = 0

        self.state = "UNCOLLECTED"

        self.previous_x = x
        self.previous_y = y

    @property
    def center(self):
        return (
            self.x + self.width / 2,
            self.y + self.height / 2
        )

    def update(self, x, y, width, height, score):
        self.previous_x = self.x
        self.previous_y = self.y

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.score = score

        self.age += 1
        self.missing_frames = 0

    @property
    def movement(self):
        dx = self.x - self.previous_x
        dy = self.y - self.previous_y

        return math.sqrt(dx * dx + dy * dy)


class ObjectTracker:
    def __init__(
        self,
        max_distance=80,
        max_missing_frames=5,
        collection_radius=130
    ):
        self.max_distance = max_distance
        self.max_missing_frames = max_missing_frames
        self.collection_radius = collection_radius

        self.objects = {}
        self.next_id = 0

        self.collected_ids = set()

    def _distance(self, object_a, detection):
        object_x, object_y = object_a.center

        detection_x = detection["x"] + detection["width"] / 2
        detection_y = detection["y"] + detection["height"] / 2

        dx = object_x - detection_x
        dy = object_y - detection_y

        return math.sqrt(dx * dx + dy * dy)

    def update(self, detections, katamari_center=None):
        matched_ids = set()
        matched_detections = set()

        # -------------------------------------------------
        # 1. Tentar associar detecções aos objetos existentes
        # -------------------------------------------------

        for object_id, tracked in list(self.objects.items()):

            best_index = None
            best_distance = self.max_distance

            for index, detection in enumerate(detections):

                if index in matched_detections:
                    continue

                distance = self._distance(tracked, detection)

                if distance < best_distance:
                    best_distance = distance
                    best_index = index

            if best_index is not None:

                detection = detections[best_index]

                tracked.update(
                    x=detection["x"],
                    y=detection["y"],
                    width=detection["width"],
                    height=detection["height"],
                    score=detection.get("score", 0.0)
                )

                matched_ids.add(object_id)
                matched_detections.add(best_index)

        # -------------------------------------------------
        # 2. Objetos que não foram encontrados neste frame
        # -------------------------------------------------

        for object_id, tracked in list(self.objects.items()):

            if object_id not in matched_ids:

                tracked.missing_frames += 1

                # Possível coleta
                if (
                    katamari_center is not None
                    and tracked.state == "UNCOLLECTED"
                ):
                    object_center = tracked.center

                    distance_to_katamari = math.dist(
                        object_center,
                        katamari_center
                    )

                    if distance_to_katamari <= self.collection_radius:
                        tracked.state = "COLLECTED"
                        self.collected_ids.add(object_id)

                # Remover somente depois de alguns frames
                if tracked.missing_frames > self.max_missing_frames:
                    del self.objects[object_id]

        # -------------------------------------------------
        # 3. Criar novos objetos
        # -------------------------------------------------

        for index, detection in enumerate(detections):

            if index in matched_detections:
                continue

            object_id = self.next_id
            self.next_id += 1

            tracked = TrackedObject(
                object_id=object_id,
                x=detection["x"],
                y=detection["y"],
                width=detection["width"],
                height=detection["height"],
                score=detection.get("score", 0.0)
            )

            self.objects[object_id] = tracked

        return list(self.objects.values())
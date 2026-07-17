"""
MediaPipe Face Detector (Final, Stable)
--------------------------------------
Requires:
  mediapipe==0.10.9
"""

import cv2
import mediapipe as mp


class MediaPipeFaceDetector:
    def __init__(
        self,
        max_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_faces,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect(self, frame):
        if frame is None:
            return []

        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        if not result.multi_face_landmarks:
            return []

        boxes = []
        for face in result.multi_face_landmarks:
            xs = [lm.x * w for lm in face.landmark]
            ys = [lm.y * h for lm in face.landmark]

            x1 = max(int(min(xs)) - 10, 0)
            y1 = max(int(min(ys)) - 10, 0)
            x2 = min(int(max(xs)) + 10, w)
            y2 = min(int(max(ys)) + 10, h)

            boxes.append((x1, y1, x2 - x1, y2 - y1))

        return boxes

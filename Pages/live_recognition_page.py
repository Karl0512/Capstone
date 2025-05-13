# dashboard_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
import cv2
import threading
import time
from insightface.app import FaceAnalysis

class LiveRecognitionPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Live Recognition")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)

        stats_label = QLabel("Welcome to the Facial Recognition.")
        stats_label.setFont(QFont("Arial", 14))
        stats_label.setAlignment(Qt.AlignCenter)

        # create label for video feed
        # create label for video feed
        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Set up a timer to update the feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 ms

        # initalize camera
        self.cap = cv2.VideoCapture(0)

        # load the insight face model
        self.face_analyzer = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
        self.face_analyzer.prepare(ctx_id=0, det_size=(640, 640))

        self.start_face_detection_thread()


        layout.addWidget(title)
        layout.addWidget(self.image_label)
        layout.addWidget(stats_label)

    def start_face_detection_thread(self):
        self.detected_faces = []
        self.detection_running = True
        self.detection_lock = threading.Lock()
        self.face_thread = threading.Thread(target=self.face_detection_loop, daemon=True)
        self.face_thread.start()

    def face_detection_loop(self):
        while self.detection_running:
            frame = self.cap.read()[1]
            if frame is None:
                continue
            small_frame = cv2.resize(frame, (640, 480))
            faces = self.face_analyzer.get(small_frame)

            # Rescale bounding boxes
            scale_x = frame.shape[1] / 640
            scale_y = frame.shape[0] / 480
            for face in faces:
                face.bbox[0::2] *= scale_x
                face.bbox[1::2] *= scale_y

            with self.detection_lock:
                self.detected_faces = faces

            time.sleep(0.03)  # ≈ 30 FPS

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        with self.detection_lock:
            faces = self.detected_faces.copy()

        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            cv2.rectangle(rgb_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def stop_camera(self):
        self.detection_running = False
        if hasattr(self, "face_thread") and self.face_thread.is_alive():
            self.face_thread.join(timeout=1)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.timer.stop()

    def hideEvent(self, event):
        self.stop_camera()
        event.accept()

    def showEvent(self, event):
        self.cap = cv2.VideoCapture(0)
        self.start_face_detection_thread()
        self.timer.start(30)
        event.accept()
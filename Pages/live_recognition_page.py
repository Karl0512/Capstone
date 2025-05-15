from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QComboBox, QDialog, QPushButton, QDialogButtonBox, QLineEdit, QScrollArea
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
from pygrabber.dshow_graph import FilterGraph
import cv2
import numpy as np
import insightface
import uuid
from Features.face_indexer import FaceIndexer


class LiveRecognitionPage(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_widgets = []
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        title = QLabel("Multi-Camera Live Recognition")
        title.setFont(QFont("Arial", 20))
        title.setAlignment(Qt.AlignCenter)

        self.add_camera_button = QPushButton("Add Camera")
        self.add_camera_button.clicked.connect(self.show_add_camera_dialog)

        # Container widget inside scroll area to hold camera widgets
        self.camera_container = QWidget()
        self.cameras_layout = QVBoxLayout()
        self.camera_container.setLayout(self.cameras_layout)

        # Scroll area that will contain the camera container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.camera_container)

        self.layout.addWidget(title)
        self.layout.addWidget(self.add_camera_button)
        self.layout.addWidget(self.scroll_area)

    def show_add_camera_dialog(self):
        graph = FilterGraph()
        devices = graph.get_input_devices()
        dialog = AddCameraDialog(devices, self)

        if dialog.exec() == QDialog.Accepted:
            source, index, purpose, location, cam_type, rtsp = dialog.get_values()

            if cam_type == "Wired":
                source_type = 'wired'
                cam_source = index
            else:
                source_type = 'rtsp'
                cam_source = rtsp

            label = f"{purpose} - {location}"
            camera_widget = CameraFeedWidget(source=cam_source, source_type=source_type, label=label)
            self.cameras_layout.addWidget(camera_widget)
            self.camera_widgets.append(camera_widget)

    def hideEvent(self, event):
        for camera in self.camera_widgets:
            camera.stop_camera()
        event.accept()

class AddCameraDialog(QDialog):
    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Camera")

        self.selected_type = None
        self.selected_index = None
        self.rtsp_address = None
        self.purpose = None
        self.location = None

        layout = QVBoxLayout()

        # Type selection
        self.type_selector = QComboBox()
        self.type_selector.addItems(["Wired", "Wireless"])
        self.type_selector.currentIndexChanged.connect(self.toggle_input_fields)
        layout.addWidget(QLabel("Camera Type:"))
        layout.addWidget(self.type_selector)

        # Wired camera selector
        self.device_selector = QComboBox()
        for i, name in enumerate(devices):
            self.device_selector.addItem(name, userData=i)

        # Wireless RTSP input
        self.rtsp_input = QLineEdit()
        self.rtsp_input.setPlaceholderText("e.g., rtsp://username:password@ip:port/stream")

        # Add both but show only one at a time
        layout.addWidget(QLabel("Select Camera:"))
        layout.addWidget(self.device_selector)
        layout.addWidget(QLabel("RTSP Address:"))
        layout.addWidget(self.rtsp_input)

        self.toggle_input_fields(0)  # Show only wired fields by default

        # Purpose and location
        self.purpose_selector = QComboBox()
        self.purpose_selector.addItems(["Entry", "Exit"])
        layout.addWidget(QLabel("Purpose:"))
        layout.addWidget(self.purpose_selector)

        self.location_selector = QComboBox()
        self.location_selector.addItems(["Gate", "Room"])
        layout.addWidget(QLabel("Location:"))
        layout.addWidget(self.location_selector)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def toggle_input_fields(self, index):
        if index == 0:  # Wired
            self.device_selector.show()
            self.rtsp_input.hide()
        else:  # Wireless
            self.device_selector.hide()
            self.rtsp_input.show()

    def get_values(self):
        camera_type = self.type_selector.currentText()
        if camera_type == "Wired":
            return (
                self.device_selector.currentText(),  # source (label)
                self.device_selector.currentData(),  # index
                self.purpose_selector.currentText(),
                self.location_selector.currentText(),
                camera_type,
                None
            )
        else:
            return (
                self.rtsp_input.text(),  # source (label and RTSP)
                None,
                self.purpose_selector.currentText(),
                self.location_selector.currentText(),
                camera_type,
                self.rtsp_input.text()
            )

class CameraFeedWidget(QWidget):
    def __init__(self, source, source_type='wired', label='Camera', parent=None):
        super().__init__(parent)
        self.label = label
        self.source = source
        self.source_type = source_type
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.face_analyzer = insightface.app.FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
        self.face_analyzer.prepare(ctx_id=-1)
        self.scale = 0.5
        self.init_ui()
        self.frame_counter = 0
        self.tracked_faces = {}
        self.embedding_threshold = 0.6
        self.face_ttl = 30
        self.faces = []
        self.face_recognize = FaceIndexer()
        self.detecting = False
        self.detected_faces = []
        self.iou_threshold = 0.3

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.title = QLabel(self.label)
        self.title.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        self.image_label.setStyleSheet("""background-color: gray""")
        layout.addWidget(self.title)
        layout.addWidget(self.image_label)

        self.start_camera()

    def iou(self, box1, box2):
        x1, y1, x2, y2 = box1
        xx1, yy1, xx2, yy2 = box2
        xi1 = max(x1, xx1)
        yi1 = max(y1, yy1)
        xi2 = min(x2, xx2)
        yi2 = min(y2, yy2)
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = (x2 - x1) * (y2 - y1)
        box2_area = (xx2 - xx1) * (yy2 - yy1)
        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0

    def start_camera(self):
        if self.source_type == 'wired':
            self.cap = cv2.VideoCapture(self.source)
        else:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)

        if self.cap.isOpened():
            self.timer.start(30)

    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame_counter += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.frame_counter % 2 == 0:
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=self.scale, fy=self.scale)
            self.faces = self.face_analyzer.get(small_frame)

        for face in self.faces:
            box = (face.bbox / self.scale).astype(int)
            x1, y1, x2, y2 = box

            matched_id = None
            for face_id, data in self.tracked_faces.items():
                if self.iou(box, data["bbox"]) > self.iou_threshold:
                    matched_id = face_id
                    self.tracked_faces[face_id]["last_seen"] = self.frame_counter
                    break

            if matched_id is None:
                new_id = str(uuid.uuid4())
                cropped_face = frame[y1:y2, x1:x2]
                embedding = face.normed_embedding
                if embedding is not None:
                    self.tracked_faces[new_id] = {
                        "bbox": box,
                        "embedding": embedding,
                        "last_seen": self.frame_counter
                    }
                    self.face_recognize.recognize_face(embedding)
            else:
                embedding = self.tracked_faces[matched_id]["embedding"]

            cv2.rectangle(rgb_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            for landmark in (face.kps / self.scale):
                cv2.circle(rgb_frame, tuple(landmark.astype(int)), 2, (0, 0, 255), -1)

        expired = [
            face_id for face_id, data in self.tracked_faces.items()
            if self.frame_counter - data["last_seen"] > self.face_ttl
        ]
        for face_id in expired:
            del self.tracked_faces[face_id]

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def stop_camera(self):
        if self.cap:
            self.cap.release()
        self.timer.stop()

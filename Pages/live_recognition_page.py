from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QComboBox, QDialog, QPushButton, QDialogButtonBox, QLineEdit, QScrollArea, QHBoxLayout, QSpacerItem
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QThread
from PySide6.QtGui import QFont, QImage, QPixmap
from pygrabber.dshow_graph import FilterGraph
import cv2
import numpy as np
import insightface
import uuid
import time

from win32ctypes.pywin32.pywintypes import datetime

from Features.face_indexer import FaceIndexer
from Features.face_services import FaceDetectionService
from functools import partial
import json
import os
from Pages.monitoring_logs import MonitoringLogs


CONFIG_PATH = "./camera_config.json"

class LiveRecognitionPage(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_widgets = []
        self.monitoring_logs = MonitoringLogs()  # Create instance for logging
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        # --- Title and Add Button in One Row ---
        title_bar = QHBoxLayout()
        title_bar.setSpacing(10)

        title = QLabel("Multi-Camera Live Recognition")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("color: #2C3E50;")  # dark blue-gray text

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.add_camera_button = QPushButton("Add Camera")
        self.add_camera_button.setFixedHeight(40)
        self.add_camera_button.clicked.connect(self.show_add_camera_dialog)
        self.add_camera_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.add_camera_button.setStyleSheet("""
            QPushButton {
                background-color: #002366;  /* nice blue */
                color: #FFD700;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: black;
            }
            QPushButton:pressed {
                background-color: #1C5980;
            }
        """)

        title_bar.addWidget(title)
        title_bar.addItem(spacer)
        title_bar.addWidget(self.add_camera_button)

        # Container widget inside scroll area to hold camera widgets
        self.camera_container = QWidget()
        self.cameras_layout = QVBoxLayout()
        self.cameras_layout.setContentsMargins(5, 5, 5, 5)
        self.cameras_layout.setSpacing(10)
        self.camera_container.setLayout(self.cameras_layout)

        # Scroll area that will contain the camera container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.camera_container)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #BDC3C7;
                border-radius: 8px;
                background-color: #ECF0F1;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #F0F3F4;
            }
            QScrollBar::handle:vertical {
                background: #95A5A6;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7F8C8D;
            }
        """)

        self.layout.addLayout(title_bar)
        self.layout.addWidget(self.scroll_area)
        self.load_saved_cameras()

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
            camera_widget = CameraFeedWidget(
                source=cam_source,
                source_type=source_type,
                label=label,
                purpose=purpose, # <- Pass purpose
                location=location,
                monitoring_logs = self.monitoring_logs
            )
            print(f"ADDING camera_widget: {id(camera_widget)}")
            camera_widget.finished.connect(partial(self.remove_camera_widget, camera_widget))
            self.cameras_layout.addWidget(camera_widget)
            self.camera_widgets.append(camera_widget)
            self.save_camera_config()

    def save_camera_config(self):
        camera_data = []
        for cam in self.camera_widgets:
            camera_data.append({
                "source": cam.source,
                "source_type": cam.source_type,
                "label": cam.label,
                "purpose": cam.purpose,
                "location": cam.location

            })

        with open(CONFIG_PATH, "w") as f:
            json.dump(camera_data, f, indent=4)

    def load_saved_cameras(self):
        if not os.path.exists(CONFIG_PATH):
            return

        with open(CONFIG_PATH, "r") as f:
            camera_data = json.load(f)

        for cam in camera_data:
            camera_widget = CameraFeedWidget(
                source=cam["source"],
                source_type=cam["source_type"],
                label=cam["label"],
                purpose=cam["purpose"],
                location=cam["location"],
                monitoring_logs=self.monitoring_logs
            )

            camera_widget.finished.connect(partial(self.remove_camera_widget, camera_widget))
            self.cameras_layout.addWidget(camera_widget)
            self.camera_widgets.append(camera_widget)

    def hideEvent(self, event):
        for camera in self.camera_widgets:
            camera.stop_camera()
        event.accept()

    def remove_camera_widget(self, camera_widget):
        print(f"REMOVING camera_widget: {id(camera_widget)}")

        camera_widget.stop_camera()
        self.cameras_layout.removeWidget(camera_widget)

        if camera_widget in self.camera_widgets:
            self.camera_widgets.remove(camera_widget)
            self.save_camera_config()
            print("Successfully removed from list.")
        else:
            print("WARNING: camera_widget not in camera_widgets list!")

        camera_widget.deleteLater()

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
        self.location_selector.addItems(["Gate", "Grade 1 Room", "Grade 2 Room", "Grade 3 Room", "Grade 4 Room", "Grade 5 Room", "Grade 6 Room", "Grade 7 Room", "Grade 8 Room", "Grade 9 Room", "Grade 10 Room","Grade 11 Room","Grade 12 Room"])
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

class FaceDetectionWorker(QObject):
    detection_complete = Signal(np.ndarray, list)  # Emits original frame and detected faces

    def __init__(self, face_service, scale=0.5):
        super().__init__()
        self.face_service = face_service
        self.scale = scale
        self.running = False

    def process_frame(self, frame):
        if not self.running:
            self.running = True
            try:
                # Process in worker thread
                small_frame = cv2.resize(frame, (0, 0), fx=self.scale, fy=self.scale)
                faces = self.face_service.detect_faces(small_frame)
                self.detection_complete.emit(frame, faces)
            finally:
                self.running = False

class CameraFeedWidget(QWidget):
    finished = Signal()

    def __init__(self, source, source_type='wired', label='Camera', purpose='Entry', location='Gate', monitoring_logs=None, parent=None):
        super().__init__(parent)
        self.label = label
        self.source = source
        self.source_type = source_type
        self.purpose = purpose
        self.location = location
        self.monitoring_logs = monitoring_logs
        self.cap = None
        self.timer = QTimer(self)
        self.last_display_time = 0
        self.current_frame = None  # Add this to store the current frame
        self.last_processed_frame = None  # Add this to track last processed frame

        # Face detection setup
        self.face_service = FaceDetectionService()
        self.face_worker = FaceDetectionWorker(self.face_service)
        self.face_thread = QThread()
        self.face_worker.moveToThread(self.face_thread)
        self.face_thread.start()

        # Tracking variables
        self.tracked_faces = {}
        self.frame_counter = 0
        self.embedding_threshold = 0.6
        self.face_ttl = 30
        self.iou_threshold = 0.3
        self.face_recognize = FaceIndexer()

        self.init_ui()
        self.init_connections()
        self.start_camera()
        self.show_preview = True

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        self.title = QLabel(self.label)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 16, QFont.DemiBold))
        self.title.setStyleSheet("color: #34495E;")  # dark slate blue

        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        self.image_label.setStyleSheet("""
            background-color: #002366;  /* medium gray */
            border-radius: 12px;
            border: 2px solid #7F8C8D;
        """)

        # Add horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_button = QPushButton("Close Camera")
        self.close_button.setFixedWidth(130)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;  /* Red */
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        button_layout.addWidget(self.close_button)

        self.toggle_preview_button = QPushButton("Turn Off Preview")
        self.toggle_preview_button.setFixedWidth(130)
        button_layout.addWidget(self.toggle_preview_button)
        self.toggle_preview_button.setStyleSheet("""
            QPushButton {
                background-color: #002366;  /* Blue */
                color: #FFD700;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: black;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
        self.toggle_preview_button.clicked.connect(self.toggle_preview)

        layout.addWidget(self.title)
        layout.addWidget(self.image_label, alignment=Qt.AlignHCenter)
        layout.addLayout(button_layout)


    def init_connections(self):
        self.timer.timeout.connect(self.update_frame)
        self.face_worker.detection_complete.connect(self.handle_detection_results)
        self.close_button.clicked.connect(self.handle_close_camera)

    def iou(self, box1, box2):
        """Calculate Intersection over Union for two bounding boxes"""
        xi1 = max(box1[0], box2[0])
        yi1 = max(box1[1], box2[1])
        xi2 = min(box1[2], box2[2])
        yi2 = min(box1[3], box2[3])
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0

    def start_camera(self):
        if self.source_type == 'wired':
            self.cap = cv2.VideoCapture(self.source)
        else:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 25)  # Limit FPS for RTSP

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.timer.start(30)  # ~33ms per frame (~30fps)

    def update_frame(self):
        """Capture and process a new frame from the camera"""
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame_counter += 1
        self.current_frame = frame.copy()  # Store the current frame

        # Throttle display updates
        current_time = time.time()
        if current_time - self.last_display_time < 1 / 30:
            return

        # Convert to RGB for display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Draw existing faces on the current frame
        self.draw_face_annotations(rgb_frame)

        # Display the frame
        if self.show_preview:
            self.display_frame(rgb_frame)
        else:
            self.image_label.clear()

        self.last_display_time = current_time

        # Start face detection every 2nd frame if we're not already processing
        if (self.frame_counter % 2 == 0 and
                not self.face_worker.running and
                not np.array_equal(frame, self.last_processed_frame)):
            self.last_processed_frame = frame.copy()
            QTimer.singleShot(0, lambda: self.face_worker.process_frame(rgb_frame.copy()))

    def handle_detection_results(self, frame, faces):
        """Process face detection results from worker thread"""
        # Update tracking with new detections
        for face in faces:
            box = (face.bbox / self.face_worker.scale).astype(int)
            x1, y1, x2, y2 = box

            # Find best matching existing face
            best_match_id = None
            best_iou = 0
            for face_id, data in self.tracked_faces.items():
                current_iou = self.iou(box, data["bbox"])
                if current_iou > self.iou_threshold and current_iou > best_iou:
                    best_iou = current_iou
                    best_match_id = face_id

            if best_match_id is not None:
                # Update existing face
                self.tracked_faces[best_match_id].update({
                    "bbox": box,
                    "last_seen": self.frame_counter,
                    "kps": getattr(face, 'kps', None)
                })
                if hasattr(face, 'normed_embedding'):
                    self.tracked_faces[best_match_id]["embedding"] = face.normed_embedding

                cooldown_seconds = 30
                last_time_str = self.tracked_faces[best_match_id].get("last_recognized_time", 0)

                try:
                    last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S").timestamp()
                except Exception:
                    # fallback if last_recognized_time is already a float
                    last_time = float(last_time_str) if last_time_str else 0

                elapsed = time.time() - last_time

                if elapsed >= cooldown_seconds:
                    # Time to re-recognize
                    result = self.face_recognize.recognize_face(
                        face.normed_embedding,
                        camera_purpose=self.purpose,
                        location=self.location
                    )

                    if result:
                        recognize_name = result["info"].get("name", "Unknown")
                        self.tracked_faces[best_match_id]["name"] = recognize_name
                        self.tracked_faces[best_match_id]["last_recognized_time"] = time.time()  # reset cooldown
                        self.tracked_faces[best_match_id]["cooldown_start"] = time.time()
                        self.tracked_faces[best_match_id]["cooldown_seconds"] = 30

            elif hasattr(face, 'normed_embedding'):
                result = self.face_recognize.recognize_face(face.normed_embedding, camera_purpose=self.purpose, location=self.location)
                if result:
                    recognize_name = result["info"].get("name", "Unknown")
                    elapsed_seconds = result.get("elapsed_seconds", 0)  # for cooldown display
                    timestamp_str = result.get("timestamp", 0)
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
                else:
                    recognize_name = "Unknown"
                    elapsed_seconds = 0
                    timestamp = 0

                if elapsed_seconds > 30:
                    remaining_cooldown = 30

                else:
                    remaining_cooldown = max(30 - elapsed_seconds, 0)
                # Add new face
                new_id = str(uuid.uuid4())
                self.tracked_faces[new_id] = {
                    "bbox": box,
                    "embedding": face.normed_embedding,
                    "last_seen": self.frame_counter,
                    "kps": getattr(face, 'kps', None),
                    "name": recognize_name or "Unknown",
                    "elapsed_seconds": elapsed_seconds,
                    "cooldown_start": time.time(),
                    "cooldown_seconds": remaining_cooldown,
                    "last_recognized_time": timestamp
                }

        # Remove expired faces
        current_frame = self.frame_counter
        expired = [fid for fid, data in self.tracked_faces.items()
                  if current_frame - data["last_seen"] > self.face_ttl]
        for face_id in expired:
            del self.tracked_faces[face_id]

    def draw_face_annotations(self, frame):
        cooldown_seconds = 30

        h, w, _ = frame.shape  # Frame height and width

        for face_id, data in self.tracked_faces.items():
            x1, y1, x2, y2 = data["bbox"]
            name = data.get("name", "Unknown")

            # Set bounding box color
            color = (0, 0, 255) if name.strip().lower() != "unknown" else (0, 255, 0)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw name above the box, clamped to frame
            name_y = max(y1 - 10, 15)
            cv2.putText(frame, name, (x1, name_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Draw cooldown countdown in RED below the box, clamped to frame
            cooldown_seconds = data.get("cooldown_seconds", 30)
            start_time = data.get("cooldown_start", time.time())
            elapsed = time.time() - start_time
            remaining = max(int(cooldown_seconds - elapsed), 0)

            if remaining > 0:
                countdown_text = f"Cooldown: {remaining}s"
                text_y = min(y2 + 25, h - 5)
                cv2.putText(frame, countdown_text, (x1, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if self.show_preview:
            self.display_frame(frame)

    def display_frame(self, frame):
        """Display the frame in the QLabel"""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def stop_camera(self):
        if self.timer and self.timer.isActive():
            self.timer.stop()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        if self.face_thread and self.face_thread.isRunning():
            self.face_thread.quit()
            self.face_thread.wait()

    def handle_close_camera(self):
        self.stop_camera()
        self.finished.emit()

    def toggle_preview(self):
        if self.show_preview:
            self.show_preview = False
            self.toggle_preview_button.setText("Show Preview")
            self.image_label.clear()  # Clear GUI preview immediately
        else:
            self.show_preview = True
            self.toggle_preview_button.setText("Turn Off Preview")
# dashboard_page.py
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QComboBox, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QGuiApplication, QImage, QPixmap
import cv2
import sys
from Features.face_services import FaceDetectionService
from Features.camera_manager import CameraManager
import numpy as np
from numpy.linalg import norm
import threading
import time

from sympy.integrals.meijerint_doc import category

from db.database import get_connection

class UserManagementPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- First Section: Title and Add Button ---
        first_section = QWidget(self)
        first_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_layout = QHBoxLayout(first_section)

        lbl_title = QLabel("User Management", first_section)
        btn_add = QPushButton("Add a Person", first_section)
        btn_add.clicked.connect(self.open_add_person_window)

        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        title_layout.addWidget(btn_add)

        # --- Second Section: Filters ---
        second_section = QWidget(self)
        second_section.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        filter_layout = QHBoxLayout(second_section)

        self.filter_name = QLineEdit()
        self.filter_name.setPlaceholderText("Filter by name")

        self.filter_section = QLineEdit()
        self.filter_section.setPlaceholderText("Filter by section/job")

        self.filter_role = QComboBox()
        self.filter_role.addItem("All")
        self.filter_role.addItems(["Students", "Staff"])

        btn_filter = QPushButton("Filter")
        btn_filter.clicked.connect(self.filter_data)

        filter_layout.addWidget(self.filter_name)
        filter_layout.addWidget(self.filter_section)
        filter_layout.addWidget(self.filter_role)
        filter_layout.addWidget(btn_filter)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Role", "Section / Job", "Contact No"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.load_data_from_db(self.table)  # Load initial data with no filter

        # --- Add widgets to layout ---
        layout.addWidget(first_section)
        layout.addWidget(second_section)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def open_add_person_window(self):
        dialog = AddPersonWindow()
        dialog.setModal(True)
        dialog.exec()

    def load_data_from_db(self, table):
        conn = get_connection()  # Replace with your DB name
        cursor = conn.cursor()

        query = f"SELECT name, role, section_or_job, contact FROM person_info"

        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            table.setRowCount(0)  # Clear table before inserting

            for row_data in rows:
                row_position = table.rowCount()
                table.insertRow(row_position)
                for column, data in enumerate(row_data):
                    table.setItem(row_position, column, QTableWidgetItem(str(data)))
        except Exception as e:
            print("Error: ", e)

        finally:
            conn.close()

    def filter_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        name = self.filter_name.text().strip()
        section = self.filter_section.text().strip()
        role = self.filter_role.currentText()

        query = "SELECT name, role, section_or_job, contact FROM person_info WHERE 1=1"
        params = []

        if name:
            query += " AND name ILIKE %s"
            params.append(f"%{name}%")

        if section:
            query += " AND section_or_job ILIKE %s"
            params.append(f"%{section}%")

        if role != "All":
            query += " AND role = %s"
            params.append(role)

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(0)  # Clear table before inserting filtered results

            for row_data in rows:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for column, data in enumerate(row_data):
                    self.table.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            print("Filter error:", e)
        finally:
            conn.close()


class AddPersonWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.face_detection_service = FaceDetectionService.get_instance()
        self.camera_manager = CameraManager()
        self.camera_manager.start()

        self.capture_angles = ["front", "left", "right", "up", "down"]
        self.current_angle_index = 0
        self.captures_per_angle = 5
        self.captured_count = 0
        self.embeddings_buffer = []
        self.scale = 0.5

        self.resize(600, 320)
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.move(screen_geometry.center() - self.rect().center())

        self.setWindowTitle("Add a Person")

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left: Camera feed
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(320, 240)
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

        # Right: Form inputs
        form_layout = QVBoxLayout()

        lbl_name = QLabel("Name:")
        self.ent_name = QLineEdit()

        lbl_role = QLabel("Role:")
        self.role_person = QComboBox()
        self.role_person.addItems(["Students", "Staff"])

        lbl_section_job = QLabel("Section / Job:")
        self.ent_section_job = QLineEdit()

        lbl_contact = QLabel("Contact:")
        self.ent_contact = QLineEdit()

        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.start_capture_sequence)

        form_layout.addWidget(lbl_name)
        form_layout.addWidget(self.ent_name)
        form_layout.addWidget(lbl_role)
        form_layout.addWidget(self.role_person)
        form_layout.addWidget(lbl_section_job)
        form_layout.addWidget(self.ent_section_job)
        form_layout.addWidget(lbl_contact)
        form_layout.addWidget(self.ent_contact)
        form_layout.addStretch()
        form_layout.addWidget(self.btn_save)

        main_layout.addLayout(form_layout)

        # Timer and camera capture setup
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.cap = cv2.VideoCapture(0)


        self.detected_faces = []


    def start_capture_sequence(self):
        self.current_angle_index = 0
        self.captured_count = 0
        self.embeddings_buffer.clear()
        self.prompt_next_angle()

    def prompt_next_angle(self):
        if self.current_angle_index >= len(self.capture_angles):
            self.save_face_encoding()
            return

        angle = self.capture_angles[self.current_angle_index]
        reply = QMessageBox.information(
            self, "Capture Angle",
            f"Please face {angle}. Click OK to start capturing {self.captures_per_angle} frames.",
            QMessageBox.Ok | QMessageBox.Cancel
        )

        if reply == QMessageBox.Ok:
            self.captured_count = 0
            self.capture_current_angle()
        else:
            print("Capture cancelled.")

    def capture_current_angle(self):
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self.capture_embedding_frame)
        self.capture_timer.start(300)  # capture every 300ms, adjust as needed

    def capture_embedding_frame(self):
        if not self.detected_faces:
            print("No face detected, waiting...")
            return  # wait for face

        embedding = self.detected_faces[0].embedding
        embedding = embedding / norm(embedding)
        self.embeddings_buffer.append(embedding)
        self.captured_count += 1
        print(f"Captured {self.captured_count} embeddings for {self.capture_angles[self.current_angle_index]}")

        if self.captured_count >= self.captures_per_angle:
            self.capture_timer.stop()
            self.current_angle_index += 1
            self.prompt_next_angle()

    def update_frame(self):
        try:
            frame = self.camera_manager.read()
        except Exception as e:
            print(f"Camera error: {e}")
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=self.scale, fy=self.scale)
        self.detected_faces = self.face_detection_service.detect_faces(small_frame)

        for face in self.detected_faces:
            box = (face.bbox / self.scale).astype(int)
            x1, y1, x2, y2 = box
            cv2.rectangle(rgb_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            for landmark in (face.kps / self.scale):
                cv2.circle(rgb_frame, tuple(landmark.astype(int)), 2, (0, 0, 255), -1)

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def save_face_encoding(self):
        if not self.embeddings_buffer:
            print("No face detected.")
            return

        embedding = self.detected_faces[0].embedding
        embedding = embedding / norm(embedding)

        role = self.role_person.currentText()
        name = self.ent_name.text().strip()
        section_or_job = self.ent_section_job.text().strip()
        contact = self.ent_contact.text().strip()


        if not name or not section_or_job:
            print("Please enter name and section/job before saving.")
            return

        save_dir = "encoding"
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{name.replace(' ', '_')}_{role}.npz"
        file_path = os.path.join(save_dir, file_name)
        embedding_array = np.array(self.embeddings_buffer)
        np.savez(file_path, embeddings=embedding_array)
        print(f"Saved encoding locally at: {file_path}")

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO person_info (name, role, section_or_job, contact, npy_path) VALUES (%s, %s, %s, %s, %s)",
                (name, role, section_or_job, contact, file_path)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print("Path saved to database successfully")
        except Exception as e:
            print(f"Error saving to database: {e}")

    def closeEvent(self, event):
        self.camera_manager.stop()
        super().closeEvent(event)


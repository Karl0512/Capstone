# dashboard_page.py
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QComboBox, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QGuiApplication, QImage, QPixmap
import cv2
import sys
from insightface.app import FaceAnalysis
import numpy as np
from numpy.linalg import norm
import threading
import time

from sympy.integrals.meijerint_doc import category

from db.database import get_connection

class UserManagementPage(QWidget):
    def __init__(self):
        super().__init__()

        # Create the main layout for the page
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)

        # make a widget for section
        first_section = QWidget(self)
        second_section = QWidget(self)


        # control the size of widget
        first_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        second_section.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        # create a layout for first section
        title_layout = QHBoxLayout(first_section)

        # add widgets to first section
        lbl_title = QLabel("User Management", first_section)
        btn_add = QPushButton("Add a Person", first_section)
        btn_add.clicked.connect(self.open_add_person_window)

        # add widgets to the layout
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(btn_add)

        # create a layout for 2nd section
        second_section_layout = QVBoxLayout(second_section)

        # add widgets to second section
        lbl_role = QLabel("Role:")
        self.cmb_role = QComboBox(second_section)
        self.cmb_role.addItems(["Students", "Staff"])
        self.cmb_role.currentIndexChanged.connect(lambda: self.load_data_from_db(table))
        self.cmb_role.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # add widgets to the layout
        second_section_layout.addWidget(lbl_role)
        second_section_layout.addWidget(self.cmb_role)

        # table

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Section", "Contact No"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.load_data_from_db(table)


        layout.addWidget(first_section)
        layout.addWidget(second_section)
        layout.addWidget(table)


        # Set the layout for the current page widget
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def open_add_person_window(self):
        dialog = AddPersonWindow()
        dialog.setModal(True)
        dialog.exec()

    def load_data_from_db(self, table):
        conn = get_connection()  # Replace with your DB name
        cursor = conn.cursor()

        role = "student_info" if self.cmb_role.currentText() == "Students" else "staff_info"

        category = "section" if self.cmb_role.currentText() == "Students" else "job"

        query = f"SELECT name, {category}, contact FROM {role}"

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

class AddPersonWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.capture_angles = ["front", "left", "right", "up", "down"]
        self.current_angle_index = 0
        self.captures_per_angle = 5
        self.captured_count = 0
        self.embeddings_buffer = []
        self.scale = 0.5

        self.resize(300, 300)
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.move(screen_geometry.center() - self.rect().center())

        self.setWindowTitle("Add a Person")
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.cap = cv2.VideoCapture(0)

        self.face_analyzer = FaceAnalysis(name="buffalo_s", providers=['CPUExecutionProvider'])
        self.face_analyzer.prepare(ctx_id=-1)

        self.detected_faces = []

        self.role_person = QComboBox()
        self.role_person.addItems(["Students", "Staff"])
        self.role_person.currentIndexChanged.connect(self.switch_role)
        self.role_person.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.student_widget = QWidget(self)
        self.student_widget.setFixedSize(300, 300)
        student_layout = QVBoxLayout(self.student_widget)

        QLabel("ID:")  # Not stored
        ent_student_id = QLineEdit()

        lbl_student_name = QLabel("Name:")
        self.ent_student_name = QLineEdit()

        lbl_student_section = QLabel("Section:")
        self.ent_student_section = QLineEdit()

        lbl_student_contact = QLabel("Contact No:")
        self.ent_student_contact = QLineEdit()

        btn_student_save = QPushButton("Save")
        btn_student_save.clicked.connect(self.start_capture_sequence)

        student_layout.addWidget(lbl_student_name)
        student_layout.addWidget(self.ent_student_name)
        student_layout.addWidget(lbl_student_section)
        student_layout.addWidget(self.ent_student_section)
        student_layout.addWidget(lbl_student_contact)
        student_layout.addWidget(self.ent_student_contact)
        student_layout.addWidget(btn_student_save)

        self.staff_widget = QWidget(self)
        self.staff_widget.setFixedSize(300, 300)
        staff_layout = QVBoxLayout(self.staff_widget)

        lbl_staff_name = QLabel("Name:")
        self.ent_staff_name = QLineEdit()

        lbl_staff_job = QLabel("Job:")
        self.ent_staff_job = QLineEdit()

        lbl_staff_contact = QLabel("Contact No:")
        self.ent_staff_contact = QLineEdit()

        btn_staff_save = QPushButton("Save")
        btn_staff_save.clicked.connect(self.start_capture_sequence)

        staff_layout.addWidget(lbl_staff_name)
        staff_layout.addWidget(self.ent_staff_name)
        staff_layout.addWidget(lbl_staff_job)
        staff_layout.addWidget(self.ent_staff_job)
        staff_layout.addWidget(lbl_staff_contact)
        staff_layout.addWidget(self.ent_staff_contact)
        staff_layout.addWidget(btn_staff_save)

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.student_widget)
        self.stack.addWidget(self.staff_widget)

        layout.addWidget(self.image_label)
        layout.addWidget(self.role_person)
        layout.addWidget(self.stack)

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

    def switch_role(self):
        if self.role_person.currentText() == "Students":
            self.stack.setCurrentWidget(self.student_widget)
        else:
            self.stack.setCurrentWidget(self.staff_widget)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=self.scale, fy=self.scale)
        self.detected_faces = self.face_analyzer.get(small_frame)

        for face in self.detected_faces:
            box = (face.bbox / self.scale).astype(int)
            x1, y1, x2, y2 = box

            # Draw face bounding box
            cv2.rectangle(rgb_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw facial landmarks if available
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
        if role == "Students":
            name = self.ent_student_name.text().strip()
            section = self.ent_student_section.text().strip()
            contact = self.ent_student_contact.text().strip()
        else:
            name = self.ent_staff_name.text().strip()
            section = ""
            contact = self.ent_staff_contact.text().strip()

        job = self.ent_staff_job.text().strip() if role == "Staff" else ""

        if not name:
            print("Please enter a name before saving.")
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
            if role == "Students":
                cursor.execute(
                    "INSERT INTO student_info (name, section, contact, npy_path) VALUES (%s, %s, %s, %s)",
                    (name, section, contact, file_path)
                )
            else:
                cursor.execute(
                    "INSERT INTO staff_info (name, job, contact, npy_path) VALUES (%s, %s, %s, %s)",
                    (name, job, contact, file_path)
                )
            conn.commit()
            cursor.close()
            conn.close()
            print("Path saved to database successfully")
        except Exception as e:
            print(f"Error saving to database: {e}")

    def closeEvent(self, event):
        self.cap.release()


# dashboard_page.py
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QComboBox, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QStackedWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QGuiApplication, QImage, QPixmap
import cv2
import sys
from insightface.app import FaceAnalysis
import numpy as np
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

        # Set the window size
        self.resize(300, 300)

        # Get the screen geometry and center the window
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.move(screen_geometry.center() - self.rect().center())

        # layout
        self.setWindowTitle("Add a Person")
        layout = QVBoxLayout()
        self.setLayout(layout)

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

        # role of the person
        self.role_person = QComboBox()
        self.role_person.addItems(["Students", "Staff"])
        self.role_person.currentIndexChanged.connect(self.switch_role)
        self.role_person.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # student widget
        self.student_widget = QWidget(self)
        self.student_widget.setFixedSize(300, 300)
        student_widget_layout = QVBoxLayout(self.student_widget)

        lbl_student_id = QLabel("ID:", )
        ent_student_id = QLineEdit()

        lbl_student_name = QLabel("Name:", )
        self.ent_student_name = QLineEdit()

        lbl_student_section = QLabel("Section", )
        self.ent_student_section = QLineEdit()

        lbl_student_contact = QLabel("Contact No:", )
        self.ent_student_contact = QLineEdit()

        btn_student_save = QPushButton("Save")
        btn_student_save.clicked.connect(self.save_face_encoding)
        btn_student_save.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        center_student_layout = QHBoxLayout()
        center_student_layout.addStretch()
        center_student_layout.addWidget(btn_student_save)
        center_student_layout.addStretch()

        # student widget layout
        student_widget_layout.addWidget(lbl_student_id)
        student_widget_layout.addWidget(ent_student_id)
        student_widget_layout.addWidget(lbl_student_name)
        student_widget_layout.addWidget(self.ent_student_name)
        student_widget_layout.addWidget(lbl_student_section)
        student_widget_layout.addWidget(self.ent_student_section)
        student_widget_layout.addWidget(lbl_student_contact)
        student_widget_layout.addWidget(self.ent_student_contact)
        student_widget_layout.addLayout(center_student_layout)

        # staff widget
        self.staff_widget = QWidget(self)
        self.staff_widget.setFixedSize(300, 300)
        staff_widget_layout = QVBoxLayout(self.staff_widget)

        lbl_staff_name = QLabel("Name:", )
        self.ent_staff_name = QLineEdit()

        lbl_staff_gender = QLabel("Gender:", )
        ent_staff_gender = QLineEdit()

        lbl_staff_job = QLabel("Job:", )
        self.ent_staff_job = QLineEdit()

        lbl_staff_contact = QLabel("Contact No:", )
        self.ent_staff_contact = QLineEdit()

        btn_staff_save = QPushButton("Save")
        btn_staff_save.clicked.connect(self.save_face_encoding)
        btn_staff_save.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        center_staff_layout = QHBoxLayout()
        center_staff_layout.addStretch()
        center_staff_layout.addWidget(btn_staff_save)
        center_staff_layout.addStretch()


        # staff widget layout
        staff_widget_layout.addWidget(lbl_staff_name)
        staff_widget_layout.addWidget(self.ent_staff_name)
        staff_widget_layout.addWidget(lbl_staff_job)
        staff_widget_layout.addWidget(self.ent_staff_job)
        staff_widget_layout.addWidget(lbl_staff_contact)
        staff_widget_layout.addWidget(self.ent_staff_contact)
        staff_widget_layout.addLayout(center_staff_layout)

        # stack the widgets
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.student_widget)
        self.stack.addWidget(self.staff_widget)

        # add the widget to the layout
        ## image ##
        layout.addWidget(self.image_label)
        layout.addWidget(self.role_person)
        layout.addWidget(self.stack)

    def switch_role(self):
        role = self.role_person.currentText()
        if role == "Students":
            self.stack.setCurrentWidget(self.student_widget)
        else:
            self.stack.setCurrentWidget(self.staff_widget)

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

    def save_face_encoding(self):
        with self.detection_lock:
            if not self.detected_faces:
                print("No face detected.")
                return
            embedding = self.detected_faces[0].embedding

        name = self.ent_student_name.text().strip() if self.role_person.currentText() == "Students" else self.ent_staff_name.text().strip()
        section = self.ent_student_section.text().strip()
        contact = self.ent_student_contact.text().strip() if self.role_person.currentText() == "Students" else self.ent_staff_contact.text().strip()
        job = self.ent_staff_job.text().strip()
        role = "Students" if self.role_person.currentText() == "Students" else "Staff"

        if not name:
            print("Please Enter a Name before saving.")
            return

        # save the .npy file locally
        save_dir = "encoding"
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{name.replace(' ', '_')}_{role}.npy"
        file_path = os.path.join(save_dir, file_name)
        np.save(file_path, np.array(embedding))
        print(f"Saved encoding locally at: {file_path}")

        # save the path and info to postgresql

        if role == "Students":
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO student_info (name, section, contact, npy_path) VALUES (%s, %s, %s, %s)",
                    (name, section, contact, file_path)
                )

                conn.commit()
                cursor.close()
                conn.close()
                print("Path saved to database successfully")
            except Exception as e:
                print(f"Error saving to database: {e}")
        elif role == "Staff":
            try:
                conn = get_connection()
                cursor = conn.cursor()
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
        # Release the camera when the window is closed
        self.cap.release()

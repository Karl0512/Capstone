from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QComboBox, QSizePolicy,
                               QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QStackedWidget,
                               QMessageBox, QFrame, QFileDialog, QDateEdit)
from PySide6.QtCore import Qt, QTimer, QRegularExpression, QDate
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QGuiApplication, QImage, QPixmap, QRegularExpressionValidator
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
from Features.pdf_report import create_pdf_report
from Components.date_range_dialog import DateRangeDialog

class ReportPage(QWidget):
    def __init__(self, username):
        super().__init__()
        self.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #002366;
                color: #FFD700;
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: #000;
            }
            QLineEdit, QComboBox, QDateEdit {
                padding: 5px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

        self.username = username

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Title and Add Button ---
        first_section = QWidget(self)
        first_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_layout = QHBoxLayout(first_section)
        title_layout.setContentsMargins(0, 0, 0, 0)

        lbl_title = QLabel("Reports")
        lbl_title.setFont(QFont("Arial", 20, QFont.Bold))

        title_layout.addWidget(lbl_title)
        title_layout.addStretch()

        # --- Filters ---
        second_section = QFrame(self)
        second_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_layout = QHBoxLayout(second_section)
        filter_layout.setSpacing(8)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_name = QLineEdit()
        self.filter_name.setPlaceholderText("Filter by name")

        self.filter_section = QLineEdit()
        self.filter_section.setPlaceholderText("Filter by section/job")

        self.filter_role = QComboBox()
        self.filter_role.addItem("All")
        self.filter_role.addItems(["Students", "Staff"])

        btn_filter = QPushButton("Apply Filters")
        btn_filter.clicked.connect(self.filter_data)

        filter_layout.addWidget(self.filter_name)
        filter_layout.addWidget(self.filter_section)
        filter_layout.addWidget(self.filter_role)
        filter_layout.addWidget(btn_filter)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Role", "Section / Job", "PDF"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.load_data_from_db(self.table)

        layout.addWidget(first_section)
        layout.addWidget(second_section)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def load_data_from_db(self, table):
        conn = get_connection()  # Replace with your DB name
        cursor = conn.cursor()

        query = f"SELECT id, name, role, section_or_job FROM person_info"

        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            table.setRowCount(0)  # Clear table before inserting

            for row_data in rows:
                row_position = table.rowCount()
                table.insertRow(row_position)
                for column, data in enumerate(row_data):
                    table.setItem(row_position, column, QTableWidgetItem(str(data)))

                # generate button
                btn_generate = QPushButton("Generate")
                btn_generate.setFixedSize(80, 28)
                btn_generate.setStyleSheet("""
                    QPushButton {
                            background-color: #28a745;
                            color: white;
                            font-weight: bold;
                            border: none;
                            border-radius: 6px;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                    """)
                btn_generate.clicked.connect(lambda _, r=row_data, btn=btn_generate: self.generate_report(r[0], r[1], r[2], r[3], btn))

                # wrap button to center

                wrapper = QWidget()
                layout = QHBoxLayout(wrapper)
                layout.addWidget(btn_generate)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                wrapper.setLayout(layout)

                table.setCellWidget(row_position, 4, wrapper)

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

        query = "SELECT id, name, role, section_or_job FROM person_info WHERE 1=1"
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

                    # generate button
                    btn_generate = QPushButton("Generate")
                    btn_generate.setFixedSize(80, 28)
                    btn_generate.setStyleSheet("""
                                    QPushButton {
                                            background-color: #28a745;
                                            color: white;
                                            font-weight: bold;
                                            border: none;
                                            border-radius: 6px;
                                            padding: 4px 8px;
                                        }
                                        QPushButton:hover {
                                            background-color: #218838;
                                        }
                                    """)
                    btn_generate.clicked.connect(lambda _, r=row_data, btn=btn_generate: self.generate_report(r[0], r[1], r[2], r[3], btn))

                    # wrap button to center

                    wrapper = QWidget()
                    layout = QHBoxLayout(wrapper)
                    layout.addWidget(btn_generate)
                    layout.setAlignment(Qt.AlignCenter)
                    layout.setContentsMargins(0, 0, 0, 0)
                    wrapper.setLayout(layout)

                    self.table.setCellWidget(row_position, 4, wrapper)

        except Exception as e:
            print("Filter error:", e)
        finally:
            conn.close()

    def generate_report(self, person_id, name, role, section_or_job, btn=None):
        try:
            # Show the date range dialog first
            date_dialog = DateRangeDialog(self)
            if date_dialog.exec() != QDialog.Accepted:
                return  # user canceled

            start_date, end_date = date_dialog.get_dates()

            # Open "Save As" dialog
            default_filename = f"report_{person_id}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save PDF Report",
                default_filename,
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Call PDF generator with date range
            create_pdf_report(
                person_id,
                name,
                role,
                section_or_job,
                output_path=file_path,
                start_date=start_date,
                end_date=end_date,
                generated_by=self.username
            )

            QMessageBox.information(self, "Success", f"PDF generated:\n{file_path} {start_date} {end_date}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {e}")

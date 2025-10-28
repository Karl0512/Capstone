from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit, QTimeEdit,
    QHBoxLayout, QPushButton, QSizePolicy, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont, QColor, QBrush
from datetime import datetime
import time

from sympy.physics.units import action

from db.database import get_connection
from Features.csv_exporter import export_table_to_csv

class MonitoringLogs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        title = QLabel("Monitoring Logs")
        title.setFont(QFont("Arial", 24))

        self.title_container = QWidget()
        self.title_container_layout = QHBoxLayout(self.title_container)
        self.title_container_layout.addWidget(title)


        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_csv.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_export_csv.clicked.connect(self.handle_export_csv)
        self.btn_export_csv.setStyleSheet("""
                    QPushButton {
                        background-color: #002366;
                        color: #FFD700;
                        font-weight: bold;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background-color: #FFD700;
                        color: black;
                    }
                """)
        self.title_container_layout.addWidget(self.btn_export_csv)
        main_layout.addWidget(self.title_container)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.entry_exit_tab = QWidget()
        self.setup_entry_exit_tab()
        self.tabs.addTab(self.entry_exit_tab, "Entry/Exit")

        self.room_entry_exit_tab = QWidget()
        self.setup_room_entry_exit_tab()
        self.tabs.addTab(self.room_entry_exit_tab, "Room Entry/Exit")

    def handle_export_csv(self):
        current_index = self.tabs.currentIndex()

        if current_index == 0:  # Entry/Exit tab
            export_table_to_csv(self.table, self, preset_name="Gate_logs")
        elif current_index == 1:  # Room Entry/Exit tab
            export_table_to_csv(self.room_table, self, preset_name="Room_Logs")

    def setup_entry_exit_tab(self):
        layout = QVBoxLayout()
        self.entry_exit_tab.setLayout(layout)

        input_style = """
            QLineEdit, QDateEdit, QTimeEdit, QComboBox {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: #F9F9F9;
            }
        """

        top_filter_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search by name")
        self.name_input.setStyleSheet(input_style)

        self.section_input = QLineEdit()
        self.section_input.setPlaceholderText("Search by section")
        self.section_input.setStyleSheet(input_style)

        top_filter_layout.addWidget(QLabel("Name:"))
        top_filter_layout.addWidget(self.name_input)
        top_filter_layout.addWidget(QLabel("Section:"))
        top_filter_layout.addWidget(self.section_input)

        self.toggle_button = QPushButton("\u25BC Show Filters")
        self.toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #002366;
                color: #FFD700;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: black;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_filters)
        top_filter_layout.addWidget(self.toggle_button)

        layout.addLayout(top_filter_layout)

        self.advanced_filters = QWidget()
        self.advanced_filters_layout = QHBoxLayout()
        self.advanced_filters.setLayout(self.advanced_filters_layout)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["All", "Staff", "Students"])
        self.role_combo.setStyleSheet(input_style)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setStyleSheet(input_style)

        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(0, 0))
        self.start_time.setStyleSheet(input_style)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet(input_style)

        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(23, 59))
        self.end_time.setStyleSheet(input_style)
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["10", "50", "100", "All"])
        self.limit_combo.setCurrentText("10")  # default limit
        self.limit_combo.setStyleSheet(input_style)

        self.advanced_filters_layout.addWidget(QLabel("Role:"))
        self.advanced_filters_layout.addWidget(self.role_combo)
        self.advanced_filters_layout.addWidget(QLabel("From:"))
        self.advanced_filters_layout.addWidget(self.start_date)
        self.advanced_filters_layout.addWidget(self.start_time)
        self.advanced_filters_layout.addWidget(QLabel("To:"))
        self.advanced_filters_layout.addWidget(self.end_date)
        self.advanced_filters_layout.addWidget(self.end_time)



        self.advanced_filters_layout.addWidget(QLabel("Limit:"))
        self.advanced_filters_layout.addWidget(self.limit_combo)

        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #002366;
                color: #FFD700;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: black;
            }
        """)
        self.search_button.clicked.connect(self.load_gate_logs)
        self.advanced_filters_layout.addWidget(self.search_button)

        self.advanced_filters.setVisible(False)
        layout.addWidget(self.advanced_filters)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Section", "Role", "Action", "Timestamp", "Status", "Toggle"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnHidden(6, True)
        layout.addWidget(self.table)

        self.load_gate_logs()

    def setup_room_entry_exit_tab(self):
        layout = QVBoxLayout()
        self.room_entry_exit_tab.setLayout(layout)

        top_filter_layout = QHBoxLayout()
        input_style = """
            QLineEdit, QDateEdit, QTimeEdit, QComboBox {
                padding: 6px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: #F9F9F9;
            }
        """

        self.room_name_input = QLineEdit()
        self.room_name_input.setPlaceholderText("Search by name")
        self.room_name_input.setStyleSheet(input_style)

        self.room_filter_input = QLineEdit()
        self.room_filter_input.setPlaceholderText("Search by room")
        self.room_filter_input.setStyleSheet(input_style)

        self.room_start_date = QDateEdit()
        self.room_start_date.setCalendarPopup(True)
        self.room_start_date.setDate(QDate.currentDate())
        self.room_start_date.setStyleSheet(input_style)

        self.room_start_time = QTimeEdit()
        self.room_start_time.setTime(QTime(0, 0))
        self.room_start_time.setStyleSheet(input_style)

        self.room_end_date = QDateEdit()
        self.room_end_date.setCalendarPopup(True)
        self.room_end_date.setDate(QDate.currentDate())
        self.room_end_date.setStyleSheet(input_style)

        self.room_end_time = QTimeEdit()
        self.room_end_time.setTime(QTime(23, 59))
        self.room_end_time.setStyleSheet(input_style)

        self.room_limit_combo = QComboBox()
        self.room_limit_combo.addItems(["10", "50", "100", "All"])
        self.room_limit_combo.setCurrentText("10")
        self.room_limit_combo.setStyleSheet(input_style)

        top_filter_layout.addWidget(QLabel("Name:"))
        top_filter_layout.addWidget(self.room_name_input)
        top_filter_layout.addWidget(QLabel("Room:"))
        top_filter_layout.addWidget(self.room_filter_input)
        top_filter_layout.addWidget(QLabel("From:"))
        top_filter_layout.addWidget(self.room_start_date)
        top_filter_layout.addWidget(self.room_start_time)
        top_filter_layout.addWidget(QLabel("To:"))
        top_filter_layout.addWidget(self.room_end_date)
        top_filter_layout.addWidget(self.room_end_time)
        top_filter_layout.addWidget(QLabel("Limit:"))
        top_filter_layout.addWidget(self.room_limit_combo)

        self.room_search_button = QPushButton("Search")
        self.room_search_button.setFixedHeight(36)
        self.room_search_button.setStyleSheet("""
            QPushButton {
                background-color: #002366;
                color: #FFD700;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: black;
            }
            QPushButton:pressed {
                background-color: #2471A3;
            }
        """)
        self.room_search_button.clicked.connect(self.load_room_logs)
        top_filter_layout.addWidget(self.room_search_button)

        layout.addLayout(top_filter_layout)

        self.room_table = QTableWidget()
        self.room_table.setColumnCount(9)
        self.room_table.setHorizontalHeaderLabels(["ID", "Name", "Role", "Timestamp", "Purpose", "Section", "Room", "Status", "Toggle"])
        self.room_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.room_table.setColumnHidden(7, True)
        layout.addWidget(self.room_table)

        self.load_room_logs()

    def toggle_filters(self):
        visible = self.advanced_filters.isVisible()
        self.advanced_filters.setVisible(not visible)
        self.toggle_button.setText("▲ Hide Filters" if not visible else "▼ Show Filters")

    def toggle_status(self, log_id, table_name):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT status FROM {table_name} WHERE id = %s", (log_id,))
        current_status = cursor.fetchone()[0]

        new_status = "void" if current_status == "active" else "active"
        action_text = "void this record" if new_status == "void" else "activate this record"

        reply = QMessageBox.question(
            self,
            "Confirm Action",
            f"Are you sure you want to {action_text}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            cursor.execute(f"UPDATE {table_name} SET status = %s WHERE id = %s", (new_status, log_id))
            conn.commit()

        conn.close()
        if table_name == "gate_logs":
            self.load_gate_logs()
        else:
            self.load_room_logs()

    def load_gate_logs(self):
        gate_logs = self.fetch_gate_logs_from_db()
        self.populate_gate_logs_table(gate_logs)

    def fetch_gate_logs_from_db(self):
        name_filter = self.name_input.text().strip()
        role_filter = self.role_combo.currentText()
        section_filter = self.section_input.text().strip()
        limit_value = self.limit_combo.currentText()

        start_dt = f"{self.start_date.date().toString('yyyy-MM-dd')} {self.start_time.time().toString('HH:mm:ss')}"
        end_dt = f"{self.end_date.date().toString('yyyy-MM-dd')} {self.end_time.time().toString('HH:mm:ss')}"

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT id, name, timestamp, role, purpose, section, status FROM gate_logs WHERE 1=1"
        params = []

        if name_filter:
            query += " AND name ILIKE %s"
            params.append(f"%{name_filter}%")

        if role_filter != "All":
            query += " AND role = %s"
            params.append(role_filter)

        if section_filter:
            query += " AND section ILIKE %s"
            params.append(f"%{section_filter}%")

        query += " AND timestamp BETWEEN %s AND %s"
        params.extend([start_dt, end_dt])
        query += " ORDER BY timestamp DESC"

        if limit_value != "All":
            query += " LIMIT %s"
            params.append(int(limit_value))

        cursor.execute(query, params)
        gate_logs = cursor.fetchall()
        conn.close()

        return gate_logs

    def populate_gate_logs_table(self, gate_logs):
        self.table.setRowCount(len(gate_logs))

        for row_idx, (id, name, timestamp, role, purpose, section, status) in enumerate(gate_logs):
            dt_obj = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
            formatted_timestamp = dt_obj.strftime("%Y-%m-%d %I:%M %p")

            row_values = [id, name, section, role, purpose, formatted_timestamp]
            for col_idx, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)

                if status == "void":
                    font = item.font()
                    font.setStrikeOut(True)
                    item.setFont(font)

                    item.setBackground(QBrush(QColor(200, 200, 200, 80)))
                    item.setForeground(QBrush(QColor(50, 50, 50, 120)))

                self.table.setItem(row_idx, col_idx, item)

            status_item = QTableWidgetItem(status)
            self.table.setItem(row_idx, 6, status_item)

            # Add the action button
            btn = self.create_status_button(id, status, "gate_logs")
            self.table.setCellWidget(row_idx, 7, btn)

    def create_status_button(self, log_id, status, table_name):
        btn = QPushButton("Void" if status == "active" else "Activate")
        btn.setFixedSize(80, 28)

        if status == "active":
            btn.setStyleSheet("""
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
        else:
            btn.setStyleSheet("""
                        QPushButton {
                            background-color: #dc3545;
                            color: white;
                            font-weight: bold;
                            border: none;
                            border-radius: 6px;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #c82333;
                        }
                    """)


        btn.clicked.connect(lambda _, log_id=log_id: self.toggle_status(log_id, table_name))

        # 👇 wrap button in QWidget with centered layout
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignCenter)  # center it
        layout.setContentsMargins(0, 0, 0, 0)  # no padding
        wrapper.setLayout(layout)

        return wrapper

    def load_room_logs(self):
        room_logs = self.fetch_room_logs_from_db()
        self.populate_room_logs_table(room_logs)

    def fetch_room_logs_from_db(self):
        name_filter = self.room_name_input.text().strip()
        room_filter = self.room_filter_input.text().strip()
        limit_value = self.room_limit_combo.currentText()

        start_dt = f"{self.room_start_date.date().toString('yyyy-MM-dd')} {self.room_start_time.time().toString('HH:mm:ss')}"
        end_dt = f"{self.room_end_date.date().toString('yyyy-MM-dd')} {self.room_end_time.time().toString('HH:mm:ss')}"

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT id, name, role, timestamp, purpose, section, room, status FROM room_logs WHERE 1=1"
        params = []

        if name_filter:
            query += " AND name ILIKE %s"
            params.append(f"%{name_filter}%")

        if room_filter:
            query += " AND room ILIKE %s"
            params.append(f"%{room_filter}%")

        query += " AND timestamp BETWEEN %s AND %s"
        params.extend([start_dt, end_dt])
        query += " ORDER BY timestamp DESC"

        if limit_value != "All":
            query += " LIMIT %s"
            params.append(int(limit_value))

        cursor.execute(query, params)
        room_logs = cursor.fetchall()
        conn.close()

        return room_logs

    def populate_room_logs_table(self, room_logs):
        self.room_table.setRowCount(len(room_logs))
        for row_idx, (id, name, role, timestamp, purpose, section, room, status) in enumerate(room_logs):
            dt_obj = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
            formatted_timestamp = dt_obj.strftime("%Y-%m-%d %I:%M %p")

            row_values = [id, name, role, formatted_timestamp, purpose, section, room]
            for col_idx, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)

                if status == "void":
                    font = item.font()
                    font.setStrikeOut(True)
                    item.setFont(font)

                    item.setBackground(QBrush(QColor(200, 200, 200, 80)))
                    item.setForeground(QBrush(QColor(50, 50, 50, 120)))

                self.room_table.setItem(row_idx, col_idx, item)

            status_item = QTableWidgetItem(status)
            self.room_table.setItem(row_idx, 7, status_item)

            btn = self.create_status_button(id, status, "room_logs")
            self.room_table.setCellWidget(row_idx, 8, btn)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit, QTimeEdit,
    QHBoxLayout, QPushButton, QSizePolicy, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont
from torchgen.api.types import layoutT

from db.database import get_connection


class MonitoringLogs(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        title = QLabel("Monitoring Logs")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Entry/Exit
        self.entry_exit_tab = QWidget()
        self.setup_entry_exit_tab()
        self.tabs.addTab(self.entry_exit_tab, "Entry/Exit")

        # Tab 2: Room Entry/Exit
        self.room_entry_exit_tab = QWidget()
        self.setup_room_entry_exit_tab()
        self.tabs.addTab(self.room_entry_exit_tab, "Room Entry/Exit")

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

        # Filter layout
        top_filter_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search by name")
        self.name_input.setStyleSheet(input_style)
        top_filter_layout.addWidget(QLabel("Name:"))
        top_filter_layout.addWidget(self.name_input)

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

        # Hidden advanced filters
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

        self.advanced_filters_layout.addWidget(QLabel("Role:"))
        self.advanced_filters_layout.addWidget(self.role_combo)
        self.advanced_filters_layout.addWidget(QLabel("From:"))
        self.advanced_filters_layout.addWidget(self.start_date)
        self.advanced_filters_layout.addWidget(self.start_time)
        self.advanced_filters_layout.addWidget(QLabel("To:"))
        self.advanced_filters_layout.addWidget(self.end_date)
        self.advanced_filters_layout.addWidget(self.end_time)

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
        self.search_button.clicked.connect(self.load_logs)
        self.advanced_filters_layout.addWidget(self.search_button)

        self.advanced_filters.setVisible(False)
        layout.addWidget(self.advanced_filters)

        # Entry/Exit table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Timestamp", "Role", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.load_logs()

    def setup_room_entry_exit_tab(self):
        layout = QVBoxLayout()
        self.room_entry_exit_tab.setLayout(layout)

        top_filter_layout = QHBoxLayout()
        top_filter_layout.setSpacing(10)

        input_style = """
                    QLineEdit, QDateEdit, QTimeEdit {
                        padding: 6px;
                        border: 1px solid #BDC3C7;
                        border-radius: 6px;
                        background-color: #F9F9F9;
                    }
                """

        self.room_name_input = QLineEdit()
        self.room_name_input.setPlaceholderText("Search by name")
        self.room_name_input.setStyleSheet(input_style)

        name_label = QLabel("Name:")
        top_filter_layout.addWidget(name_label)
        top_filter_layout.addWidget(self.room_name_input)

        self.room_filter_input = QLineEdit()
        self.room_filter_input.setPlaceholderText("Search by room")
        self.room_filter_input.setStyleSheet(input_style)

        room_label = QLabel("Room:")
        top_filter_layout.addWidget(room_label)
        top_filter_layout.addWidget(self.room_filter_input)

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

        from_label = QLabel("From:")
        top_filter_layout.addWidget(from_label)
        top_filter_layout.addWidget(self.room_start_date)
        top_filter_layout.addWidget(self.room_start_time)

        to_label = QLabel("To:")
        top_filter_layout.addWidget(to_label)
        top_filter_layout.addWidget(self.room_end_date)
        top_filter_layout.addWidget(self.room_end_time)

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

        # Table
        self.room_table = QTableWidget()
        self.room_table.setColumnCount(6)
        self.room_table.setHorizontalHeaderLabels(["Name", "Role", "Timestamp", "Purpose", "Section", "Room"])
        self.room_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.room_table)

        self.load_room_logs()

    def toggle_filters(self):
        visible = self.advanced_filters.isVisible()
        self.advanced_filters.setVisible(not visible)
        self.toggle_button.setText("▲ Hide Filters" if not visible else "▼ Show Filters")

    def load_logs(self):
        name_filter = self.name_input.text().strip()
        role_filter = self.role_combo.currentText()

        start_dt = f"{self.start_date.date().toString('yyyy-MM-dd')} {self.start_time.time().toString('HH:mm:ss')}"
        end_dt = f"{self.end_date.date().toString('yyyy-MM-dd')} {self.end_time.time().toString('HH:mm:ss')}"

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT name, timestamp, role, purpose FROM gate_logs WHERE 1=1"
        params = []

        if name_filter:
            query += " AND name ILIKE %s"
            params.append(f"%{name_filter}%")

        if role_filter != "All":
            query += " AND role = %s"
            params.append(role_filter)

        query += " AND timestamp BETWEEN %s AND %s"
        params.extend([start_dt, end_dt])
        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        logs = cursor.fetchall()

        self.table.setRowCount(len(logs))
        for row_idx, (name, timestamp, role, purpose) in enumerate(logs):
            self.table.setItem(row_idx, 0, QTableWidgetItem(name))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(timestamp)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(role))
            self.table.setItem(row_idx, 3, QTableWidgetItem(purpose))

        conn.close()

    def load_room_logs(self):
        name_filter = self.room_name_input.text().strip()
        room_filter = self.room_filter_input.text().strip()

        start_dt = f"{self.room_start_date.date().toString('yyyy-MM-dd')} {self.room_start_time.time().toString('HH:mm:ss')}"
        end_dt = f"{self.room_end_date.date().toString('yyyy-MM-dd')} {self.room_end_time.time().toString('HH:mm:ss')}"

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT name, role, timestamp, purpose, section, room FROM room_logs WHERE role='Students'"
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

        cursor.execute(query, params)
        logs = cursor.fetchall()

        self.room_table.setRowCount(len(logs))
        for row_idx, (name, role, timestamp, purpose, section, room) in enumerate(logs):
            self.room_table.setItem(row_idx, 0, QTableWidgetItem(name))
            self.room_table.setItem(row_idx, 1, QTableWidgetItem(role))
            self.room_table.setItem(row_idx, 2, QTableWidgetItem(str(timestamp)))
            self.room_table.setItem(row_idx, 3, QTableWidgetItem(purpose))
            self.room_table.setItem(row_idx, 4, QTableWidgetItem(section))
            self.room_table.setItem(row_idx, 5, QTableWidgetItem(room))

        conn.close()


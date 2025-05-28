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

        # Filter layout
        top_filter_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search by name")
        top_filter_layout.addWidget(QLabel("Name:"))
        top_filter_layout.addWidget(self.name_input)

        self.toggle_button = QPushButton("▼ Show Filters")
        self.toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_button.clicked.connect(self.toggle_filters)
        top_filter_layout.addWidget(self.toggle_button)

        layout.addLayout(top_filter_layout)

        # Hidden advanced filters
        self.advanced_filters = QWidget()
        self.advanced_filters_layout = QHBoxLayout()
        self.advanced_filters.setLayout(self.advanced_filters_layout)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["All", "Staff", "Student"])

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(0, 0))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(23, 59))

        self.advanced_filters_layout.addWidget(QLabel("Role:"))
        self.advanced_filters_layout.addWidget(self.role_combo)
        self.advanced_filters_layout.addWidget(QLabel("From:"))
        self.advanced_filters_layout.addWidget(self.start_date)
        self.advanced_filters_layout.addWidget(self.start_time)
        self.advanced_filters_layout.addWidget(QLabel("To:"))
        self.advanced_filters_layout.addWidget(self.end_date)
        self.advanced_filters_layout.addWidget(self.end_time)

        self.search_button = QPushButton("Search")
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

        label = QLabel("Room Entry/Exit Logs")
        label.setFont(QFont("Arial", 14))
        layout.addWidget(label)

        self.room_table = QTableWidget()
        self.room_table.setColumnCount(4)
        self.room_table.setHorizontalHeaderLabels(["Name", "Room", "Timestamp", "Action"])
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
        print("hello")

        #conn = get_connection()
        #cursor = conn.cursor()

        # You should have a table like room_logs(name, room_name, timestamp, action)
        #cursor.execute("SELECT name, room_name, timestamp, action FROM room_logs ORDER BY timestamp DESC")
        """logs = cursor.fetchall()

        self.room_table.setRowCount(len(logs))
        for row_idx, (name, room_name, timestamp, action) in enumerate(logs):
            self.room_table.setItem(row_idx, 0, QTableWidgetItem(name))
            self.room_table.setItem(row_idx, 1, QTableWidgetItem(room_name))
            self.room_table.setItem(row_idx, 2, QTableWidgetItem(str(timestamp)))
            self.room_table.setItem(row_idx, 3, QTableWidgetItem(action))

        conn.close()"""

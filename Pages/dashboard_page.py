from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QGroupBox, QSizePolicy, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPalette
from db.database import get_connection
import datetime


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Title
        title = QLabel("Saviour School Inc.")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Welcome to the Facial Recognition Dashboard.")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Stats cards
        stats_layout = QHBoxLayout()

        self.entry_card = self.create_stat_card("Total Entry Today", "0")
        self.exit_card = self.create_stat_card("Total Exit Today", "0")

        stats_layout.addWidget(self.entry_card)
        stats_layout.addWidget(self.exit_card)

        main_layout.addLayout(stats_layout)

        # Tables
        table_layout = QHBoxLayout()

        self.entry_table = self.create_table_group("Latest Entries")
        self.exit_table = self.create_table_group("Latest Exits")

        table_layout.addWidget(self.entry_table)
        table_layout.addWidget(self.exit_table)

        main_layout.addLayout(table_layout)

        # After UI setup, update dashboard first time
        self.update_dashboard()

        # Auto refresh every 5 minutes
        timer = QTimer(self)
        timer.timeout.connect(self.update_dashboard)
        timer.start(5 * 60 * 1000)

    def create_stat_card(self, title: str, value: str):
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background-color: #002366;
                border: 1px solid #d1d9e6;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #FFECB3;")  # subtle dark blue-gray

        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: #FFFFFF;")  # darker strong color

        # Optional: Add a subtle line under title for decoration
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #FFD700; border-radius: 1px;")
        line.setContentsMargins(0, 0, 0, 10)

        layout.addWidget(title_label)
        layout.addWidget(line)
        layout.addWidget(value_label)

        card.setLayout(layout)
        card.setFixedHeight(140)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        return card

    def create_table_group(self, title: str):
        group = QGroupBox(title)
        layout = QVBoxLayout()

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Role", "Timestamp"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(table)
        group.setLayout(layout)

        return group

    def fetch_today_counts(self):
        conn = get_connection()
        cursor = conn.cursor()

        today = datetime.date.today()

        query = """
            SELECT purpose, COUNT(*) 
            FROM gate_logs 
            WHERE DATE(timestamp) = %s 
            GROUP BY purpose
        """

        cursor.execute(query, (today,))  # Note the tuple with a comma!
        results = dict(cursor.fetchall())

        total_entry = results.get('Entry', 0)
        total_exit = results.get('Exit', 0)

        conn.close()
        return total_entry, total_exit

    def fetch_latest_logs(self, action_type, limit=10):
        """Fetch latest logs filtered by entry or exit."""
        today = datetime.date.today()
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT name, role, timestamp 
            FROM gate_logs 
            WHERE purpose = %s AND DATE(timestamp) = %s
            ORDER BY timestamp DESC 
            LIMIT %s
        """

        cursor.execute(query, (action_type, today, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_dashboard(self):
        # Update total entries and exits
        total_entry, total_exit = self.fetch_today_counts()

        # Update entry card
        entry_value_label = self.entry_card.findChildren(QLabel)[1]
        entry_value_label.setText(str(total_entry))

        # Update exit card
        exit_value_label = self.exit_card.findChildren(QLabel)[1]
        exit_value_label.setText(str(total_exit))

        # Update tables
        self.populate_table(self.entry_table.findChild(QTableWidget), 'Entry')
        self.populate_table(self.exit_table.findChild(QTableWidget), 'Exit')

    def populate_table(self, table_widget, action_type):
        logs = self.fetch_latest_logs(action_type)
        table_widget.setRowCount(len(logs))

        for row_idx, (name, role, timestamp) in enumerate(logs):
            # Name
            name_item = QTableWidgetItem(name)
            table_widget.setItem(row_idx, 0, name_item)

            # Role (center aligned)
            role_item = QTableWidgetItem(role)
            role_item.setTextAlignment(Qt.AlignCenter)
            table_widget.setItem(row_idx, 1, role_item)

            # Timestamp formatted
            if isinstance(timestamp, datetime.datetime):
                formatted_time = timestamp.strftime("%Y-%m-%d %I:%M %p")
            else:
                formatted_time = str(timestamp)

            timestamp_item = QTableWidgetItem(formatted_time)
            table_widget.setItem(row_idx, 2, timestamp_item)


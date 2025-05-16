from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from db.database import get_connection  # Make sure this exists and returns a valid DB connection

class AttendanceLogsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Attendance Logs")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Date", "Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.load_logs()

    def load_logs(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name, date, role FROM entry_logs ORDER BY date DESC")
        logs = cursor.fetchall()

        self.table.setRowCount(len(logs))

        for row_idx, (name, date, role) in enumerate(logs):
            self.table.setItem(row_idx, 0, QTableWidgetItem(name))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(date)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(role))

        conn.close()

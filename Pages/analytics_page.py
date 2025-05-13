# dashboard_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Analytics")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)

        stats_label = QLabel("Welcome to the Analytics.")
        stats_label.setFont(QFont("Arial", 14))
        stats_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(stats_label)

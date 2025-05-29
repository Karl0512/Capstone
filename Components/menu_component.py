from PIL.ImageQt import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy, QLabel
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor, QPixmap

class MenuWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Set auto-fill background to true
        self.setAutoFillBackground(True)

        # Set custom background color using palette
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#002366"))
        self.setPalette(palette)

        # Set the stylesheet for other components
        self.setStyleSheet("""
            QPushButton {
                color: #FFD700;
                border-radius: 20px;
                padding: 10px;
                background-color: transparent;
                font-family: 'Roboto Mono';
                font-weight: normal;
                font-size: 24px;
                transition: all 0.3s ease-in-out;
                text-align: left;
                margin-left: 10px;
                margin-right: 10px;
            }

            QPushButton:hover {
                background-color: #FFD700;
                color: black; 
                border: 3px solid black;
            }
        """)

        layout = QVBoxLayout()

        layout.setSpacing(10)  # Remove space between widgets
        layout.setContentsMargins(0, 0, 0, 0)  # Remove the margins around the layout

        #Logo
        logo_label = QLabel(self)
        pixmap = QPixmap("assests/images/Saviour_logo.png")
        scaled_pixmap = pixmap.scaledToWidth(120, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


        # Dashboard Menu Button
        self.dashboard_btn = QPushButton("   Dashboard")
        self.dashboard_btn.setIcon(QIcon("assests/icons/home_icon.svg"))
        self.dashboard_btn.setIconSize(QSize(24, 24))

        # Live recognition Menu Button
        self.live_recognition_button = QPushButton("   Live Recognition")
        self.live_recognition_button.setIcon(QIcon("assests/icons/recognition.svg"))
        self.live_recognition_button.setIconSize(QSize(24, 24))

        self.user_management_btn = QPushButton("   User Management")
        self.user_management_btn.setIcon(QIcon("assests/icons/user.svg"))
        self.user_management_btn.setIconSize(QSize(24, 24))

        self.attendance_logs_btn = QPushButton("   Monitoring Logs")
        self.attendance_logs_btn.setIcon(QIcon("assests/icons/attendance_icon.svg"))
        self.attendance_logs_btn.setIconSize(QSize(24, 24))

        self.analytics_btn = QPushButton("   Analytics")
        self.analytics_btn.setIcon(QIcon("assests/icons/analytics_icon.svg"))
        self.analytics_btn.setIconSize(QSize(24, 24))

        self.dashboard_btn.clicked.connect(lambda: self.main_window.navigate_to("dashboard"))
        self.live_recognition_button.clicked.connect(lambda: self.main_window.navigate_to("recognition"))
        self.user_management_btn.clicked.connect(lambda: self.main_window.navigate_to("user"))
        self.attendance_logs_btn.clicked.connect(lambda: self.main_window.navigate_to("monitoring"))
        self.analytics_btn.clicked.connect(lambda: self.main_window.navigate_to("analytics"))

        layout.addWidget(logo_label, alignment=Qt.AlignHCenter)
        layout.addWidget(self.dashboard_btn)
        layout.addWidget(self.live_recognition_button)
        layout.addWidget(self.user_management_btn)
        layout.addWidget(self.attendance_logs_btn)
        layout.addWidget(self.analytics_btn)

        self.setLayout(layout)
        self.setFixedWidth(300)  # Sidebar width
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

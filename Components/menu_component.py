from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy, QLabel
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor

class MenuWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#002366"))
        self.setPalette(palette)

        # Styles
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
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Logo
        logo_label = QLabel(self)
        pixmap = QPixmap("assests/images/Saviour_logo.png")
        scaled_pixmap = pixmap.scaledToWidth(120, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(logo_label, alignment=Qt.AlignHCenter)

        # Role-based menu
        role = self.main_window.user_role

        if role == "admin":
            # Explicit order for admin
            self._add_button(layout, "   Dashboard", "assests/icons/home_icon.svg", "dashboard")
            self._add_button(layout, "   Live Recognition", "assests/icons/recognition.svg", "recognition")
            self._add_button(layout, "   User Management", "assests/icons/user.svg", "user")
            self._add_button(layout, "   Monitoring Logs", "assests/icons/attendance_icon.svg", "monitoring")
            self._add_button(layout, "   Analytics", "assests/icons/analytics_icon.svg", "analytics")

        elif role == "staff":
            # Explicit order for guard
            self._add_button(layout, "   Dashboard", "assests/icons/home_icon.svg", "dashboard")
            self._add_button(layout, "   Live Recognition", "assests/icons/recognition.svg", "recognition")
            self._add_button(layout, "   Monitoring Logs", "assests/icons/attendance_icon.svg", "monitoring")

        self.setLayout(layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def _add_button(self, layout, text, icon_path, page_name):
        btn = QPushButton(text)
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(24, 24))
        btn.clicked.connect(lambda: self.main_window.navigate_to(page_name))
        layout.addWidget(btn)

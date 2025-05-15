# main.py
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QSizePolicy
from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtGui import QGuiApplication
from sympy.polys.polyconfig import query

# component import
from Components.menu_component import MenuWidget

# pages import
from Pages.dashboard_page import DashboardPage  # Make sure the path is correct
from Pages.live_recognition_page import LiveRecognitionPage  # Make sure the path is correct
from Pages.user_management import UserManagementPage  # Make sure the path is correct
from Pages.attendance_logs import AttendanceLogsPage  # Make sure the path is correct
from Pages.analytics_page import AnalyticsPage  # Make sure the path is correct
from Pages.user_management import AddPersonWindow

# features
from Features.camera_manager import CameraManager

import numpy as np
import cv2
from db.database import get_connection
from Features.face_indexer import FaceIndexer


class MainPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # initialize camera
        # self.cap = cv2.VideoCapture(0)

        # Layouts
        main_layout = QHBoxLayout()
        content_layout = QVBoxLayout()

        main_layout.setContentsMargins(0,0,0,0)

        # Sidebar (Menu)
        sidebar = MenuWidget(main_window)

        # Content area where the page will change
        self.content_area = QStackedWidget()


        # Set the layout for the content area
        content_layout.addWidget(self.content_area)

        # Set sidebar to stretch vertically to fit window height
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # This makes the sidebar take up the full height

        # Add sidebar and content to main layout
        main_layout.addWidget(sidebar)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def set_content(self, page_name):
        if page_name == "dashboard":
            if not hasattr(self, 'dashboard_page'):
                self.dashboard_page = DashboardPage()
                self.content_area.addWidget(self.dashboard_page)
            self.content_area.setCurrentWidget(self.dashboard_page)

        elif page_name == "recognition":
            if not hasattr(self, 'recognition_page'):
                self.recognition_page = LiveRecognitionPage()
                self.content_area.addWidget(self.recognition_page)
            self.content_area.setCurrentWidget(self.recognition_page)

        elif page_name == "user":
            if not hasattr(self, 'user_management_page'):
                self.user_management_page = UserManagementPage()
                self.content_area.addWidget(self.user_management_page)
            self.content_area.setCurrentWidget(self.user_management_page)

        elif page_name == "attendance":
            if not hasattr(self, 'attendance_logs_page'):
                self.attendance_logs_page = AttendanceLogsPage()
                self.content_area.addWidget(self.attendance_logs_page)
            self.content_area.setCurrentWidget(self.attendance_logs_page)

        elif page_name == "analytics":
            if not hasattr(self, 'analytics_page'):
                self.analytics_page = AnalyticsPage()
                self.content_area.addWidget(self.analytics_page)
            self.content_area.setCurrentWidget(self.analytics_page)

        else:
            print(f"Unknown page: {page_name}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the window size
        self.resize(1200, 800)

        # Get the screen geometry and center the window
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.move(screen_geometry.center() - self.rect().center())

        # set window title
        self.setWindowTitle("Saviour Facial Recognition")

        self.navigate_to("dashboard")

        # load the faces and info
        self.embeddings = None
        self.infos = []
        # Initialize the FaceIndexer
        face_indexer = FaceIndexer()


    def navigate_to(self, page):
        self.central_widget = MainPage(self)
        self.central_widget.set_content(page)
        self.setCentralWidget(self.central_widget)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

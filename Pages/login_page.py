import bcrypt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import  QPixmap
from psycopg2 import sql

from db.database import get_connection

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(300, 400)  # resize to liking

        layout = QVBoxLayout()

        line_edit_style = """
                    QLineEdit {
                        border: 2px solid #ccc;
                        border-radius: 10px;   /* rounded corners */
                        padding: 5px;         /* inner padding */
                        font-size: 16px;       /* larger text */
                    }
                    QLineEdit:focus {
                        border: 2px solid #0078d7;  /* highlight color when focused */
                    }
                """
        push_button_style = """
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            """
        self.logo = QLabel()
        pixmap = QPixmap("assests/images/Saviour_logo.png")
        pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo.setPixmap(pixmap)
        self.logo.setAlignment(Qt.AlignCenter)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet(line_edit_style)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(line_edit_style)

        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet(push_button_style)
        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.logo)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_button)
        layout.addWidget(self.message)

        self.setLayout(layout)

        self.login_button.clicked.connect(self.handle_login)

        self.role = None  # will hold "admin" or "guard"

    def handle_login(self):
        user = self.username.text().strip()
        pwd = self.password.text().strip()

        if not user or not pwd:
            self.message.setStyleSheet("color: red;")
            self.message.setText("❌ Please enter username and password")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = sql.SQL("SELECT password, role FROM account WHERE username = %s")
            cursor.execute(query, (user,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                store_hash, role = result

                if bcrypt.checkpw(pwd.encode("utf-8"), store_hash.encode("utf-8")):
                    self.user_role = role
                    self.username_text = user
                    self.accept()
                    return

            self.message.setStyleSheet("color: red;")
            self.message.setText("❌ Wrong Username or Password")

        except Exception as e:
            self.message.setStyleSheet("color: red;")
            self.message.setText(f"⚠ DB Error: {e}")

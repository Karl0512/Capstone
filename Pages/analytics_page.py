from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from db.database import get_connection
from collections import defaultdict
from datetime import datetime, timedelta

class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QLabel#TitleLabel {
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#SectionLabel {
                font-size: 16px;
                font-weight: bold;
            }
            QComboBox, QLineEdit, QPushButton {
                font-size: 14px;
                padding: 6px;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1e5bbf;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)

        # Title
        title = QLabel("Analytics")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Section Label
        stats_label = QLabel("Entry/Exit Trends")
        stats_label.setObjectName("SectionLabel")
        stats_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(stats_label)

        # Filters layout
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Students", "Staff"])
        filters_layout.addWidget(self.role_combo)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Today", "This Week", "This Month"])
        filters_layout.addWidget(self.filter_combo)

        self.data_type = QComboBox()
        self.data_type.addItems(["Gate Logs", "Room Logs"])
        filters_layout.addWidget(self.data_type)

        main_layout.addLayout(filters_layout)

        # Name search layout
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search by name")
        search_layout.addWidget(self.name_input)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.plot_trend)
        search_layout.addWidget(self.btn_search)

        main_layout.addLayout(search_layout)

        # Graph area
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        self.graph_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        main_layout.addWidget(self.graph_canvas)

        self.plot_trend()

    def plot_trend(self):
        filter_option = self.filter_combo.currentText()
        selected_role = self.role_combo.currentText()
        name_filter = self.name_input.text().strip()

        conn = get_connection()
        cursor = conn.cursor()

        data = defaultdict(lambda: {"entry": 0, "exit": 0})

        try:
            # Build base query with role
            if self.data_type.currentText() == "Gate Logs":
                query = "SELECT timestamp, purpose, role, section, name FROM gate_logs WHERE role = %s"
                params = [selected_role]
            else:
                query = "SELECT timestamp, purpose, role, section, name FROM room_logs WHERE role = %s"
                params = [selected_role]

            # Add name filter to SQL if provided
            if name_filter:
                query += " AND name ILIKE %s"
                params.append(f"%{name_filter}%")

            cursor.execute(query, params)
            rows = cursor.fetchall()

            now = datetime.now()

            for timestamp_obj, purpose, role, section, name in rows:
                if isinstance(timestamp_obj, str):
                    timestamp_obj = datetime.strptime(timestamp_obj, "%Y-%m-%d %H:%M:%S")

                # Filter by date (Python-side)
                if filter_option == "Today":
                    if timestamp_obj.date() != now.date():
                        continue
                elif filter_option == "This Week":
                    start_of_week = now - timedelta(days=now.weekday())
                    if timestamp_obj.date() < start_of_week.date():
                        continue
                elif filter_option == "This Month":
                    if timestamp_obj.month != now.month or timestamp_obj.year != now.year:
                        continue
                # "All" does not filter anything

                date_key = timestamp_obj.strftime("%Y-%m-%d")
                if purpose.lower() == "entry":
                    data[date_key]["entry"] += 1
                elif purpose.lower() == "exit":
                    data[date_key]["exit"] += 1

        except Exception as e:
            print("Error loading gate logs:", e)
            return
        finally:
            conn.close()

            # Clear old plot
            self.graph_canvas.figure.clear()
            ax = self.graph_canvas.figure.add_subplot(111)

            sorted_dates = sorted(data.keys())
            entry_counts = [data[date]["entry"] for date in sorted_dates]
            exit_counts = [data[date]["exit"] for date in sorted_dates]

            if not sorted_dates:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=16, transform=ax.transAxes)
                ax.set_xticks([])
                ax.set_yticks([])
            else:
                if filter_option == "Today":
                    total_entries = sum(entry_counts)
                    total_exits = sum(exit_counts)
                    if total_entries == 0 and total_exits == 0:
                        ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=16, transform=ax.transAxes)
                        ax.set_xticks([])
                        ax.set_yticks([])
                    else:
                        ax.pie(
                            [total_entries, total_exits],
                            labels=["Entries", "Exits"],
                            autopct=lambda pct: f"{int(round(pct * (total_entries + total_exits) / 100))}",
                            startangle=90,
                            colors=['#FFD700', '#1E90FF']
                        )
                        ax.axis('equal')  # Equal aspect ratio ensures the pie is a circle
                        ax.set_title(f"{selected_role} Entry/Exit - {filter_option}")
                else:
                    ax.plot(sorted_dates, entry_counts, label="Entries", marker='o')
                    ax.plot(sorted_dates, exit_counts, label="Exits", marker='x')
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Count")
                    ax.legend()
                    ax.grid(True)
                    ax.set_title(f"{selected_role} Entry/Exit - {filter_option}")

            ax.set_title(f"{selected_role} Entry/Exit - {filter_option}")
            self.graph_canvas.draw()




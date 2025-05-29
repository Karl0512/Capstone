from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QHBoxLayout, QFrame, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
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

        self.init_ui()
        self.refresh_charts()

    def init_ui(self):
        scroll_area = QScrollArea(self)
        scroll_area.setFocusPolicy(Qt.StrongFocus)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        title = QLabel("Analytics", objectName="TitleLabel", alignment=Qt.AlignCenter)
        content_layout.addWidget(title)

        # Section label for Entry/Exit Trends
        section = QLabel("Entry/Exit Trends", objectName="SectionLabel", alignment=Qt.AlignCenter)
        content_layout.addWidget(section)

        filters = QHBoxLayout()
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Students", "Staff"])
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Today", "This Week", "This Month"])
        self.data_type = QComboBox()
        self.data_type.addItems(["Gate Logs", "Room Logs"])
        for widget in [self.role_combo, self.filter_combo, self.data_type]:
            filters.addWidget(widget)
        content_layout.addLayout(filters)

        search = QHBoxLayout()
        self.name_input = QLineEdit(placeholderText="Search by name")
        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.refresh_charts)
        search.addWidget(self.name_input)
        search.addWidget(self.btn_search)
        content_layout.addLayout(search)

        line = QFrame(frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        content_layout.addWidget(line)

        # Entry/Exit Trends Canvas
        self.entry_exit_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.entry_exit_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.entry_exit_canvas.setMinimumSize(600, 400)
        content_layout.addWidget(self.entry_exit_canvas)

        # Peak Hours Canvas
        self.peak_hours_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.peak_hours_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.peak_hours_canvas.setMinimumSize(600, 400)
        content_layout.addWidget(self.peak_hours_canvas)

        # --- New Section for Top Frequent Users ---
        top_users_section = QLabel("Top Frequent Users", objectName="SectionLabel", alignment=Qt.AlignCenter)
        content_layout.addWidget(top_users_section)

        # Add a filter row for this chart
        top_users_filters = QHBoxLayout()
        self.top_role_combo = QComboBox()
        self.top_role_combo.addItems(["Students", "Staff"])
        self.top_log_type_combo = QComboBox()
        self.top_log_type_combo.addItems(["Entry", "Exit"])
        self.top_filter_combo = QComboBox()
        self.top_filter_combo.addItems(["All", "Today", "This Week", "This Month"])
        for widget in [self.top_role_combo, self.top_log_type_combo, self.top_filter_combo]:
            top_users_filters.addWidget(widget)
        content_layout.addLayout(top_users_filters)

        # Connect filter changes to refresh top users chart
        self.top_role_combo.currentIndexChanged.connect(self.refresh_charts)
        self.top_log_type_combo.currentIndexChanged.connect(self.refresh_charts)
        self.top_filter_combo.currentIndexChanged.connect(self.refresh_charts)

        # Top Frequent Users Canvas
        self.top_users_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.top_users_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.top_users_canvas.setMinimumSize(600, 400)
        content_layout.addWidget(self.top_users_canvas)

        scroll_area.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def refresh_charts(self):
        role = self.role_combo.currentText()
        data_type = self.data_type.currentText()
        filter_option = self.filter_combo.currentText()
        name_filter = self.name_input.text().strip()

        # Plot Entry/Exit Trends & Peak Hours
        daily_data, hourly_data = self.load_entry_exit_data(role, data_type, filter_option, name_filter)
        self.draw_trend_plot(daily_data, role, filter_option)
        self.draw_peak_hours_plot(hourly_data)

        # Plot Top Frequent Users
        top_role = self.top_role_combo.currentText()
        top_log_type = self.top_log_type_combo.currentText().lower()  # 'entry' or 'exit'
        top_filter = self.top_filter_combo.currentText()
        top_user_data = self.load_top_users_data(top_role, top_filter)
        self.draw_top_frequent_users(top_user_data, top_log_type, top_role, top_filter)

    def load_entry_exit_data(self, role, data_type, filter_option, name_filter):
        from collections import defaultdict
        from datetime import datetime, timedelta
        conn = get_connection()
        cursor = conn.cursor()
        daily = defaultdict(lambda: {"entry": 0, "exit": 0})
        hourly = defaultdict(lambda: {"entry": 0, "exit": 0})
        now = datetime.now()
        try:
            table = "gate_logs" if data_type == "Gate Logs" else "room_logs"
            query = f"SELECT timestamp, purpose, role, name FROM {table} WHERE role = %s"
            params = [role]

            if name_filter:
                query += " AND name ILIKE %s"
                params.append(f"%{name_filter}%")

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for timestamp, purpose, _, _name in rows:
                if isinstance(timestamp, str):
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

                if not self._date_matches_filter(timestamp, now, filter_option):
                    continue

                date_key = timestamp.strftime("%Y-%m-%d")
                hour_key = timestamp.hour
                action = purpose.lower()

                if action in ["entry", "exit"]:
                    daily[date_key][action] += 1
                    hourly[hour_key][action] += 1
        except Exception as e:
            print("Error loading logs:", e)
        finally:
            conn.close()

        return daily, hourly

    def load_top_users_data(self, role, filter_option):
        from collections import defaultdict
        from datetime import datetime, timedelta
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now()

        user_counts = defaultdict(lambda: {"entry": 0, "exit": 0})

        try:
            table = "room_logs"  # or room_logs? You can add logic if needed
            query = f"SELECT name, purpose, timestamp FROM {table} WHERE role = %s"
            params = [role]

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for name, purpose, timestamp in rows:
                if isinstance(timestamp, str):
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

                if not self._date_matches_filter(timestamp, now, filter_option):
                    continue

                action = purpose.lower()
                if action in ["entry", "exit"]:
                    user_counts[name][action] += 1
        except Exception as e:
            print("Error loading top users:", e)
        finally:
            conn.close()

        return user_counts

    def _date_matches_filter(self, timestamp, now, filter_option):
        from datetime import timedelta
        if filter_option == "Today":
            return timestamp.date() == now.date()
        elif filter_option == "This Week":
            start = now - timedelta(days=now.weekday())
            return timestamp.date() >= start.date()
        elif filter_option == "This Month":
            return timestamp.month == now.month and timestamp.year == now.year
        return True

    def draw_trend_plot(self, daily_data, role, filter_option):
        fig = self.entry_exit_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        sorted_dates = sorted(daily_data.keys())
        entry_counts = [daily_data[date]["entry"] for date in sorted_dates]
        exit_counts = [daily_data[date]["exit"] for date in sorted_dates]

        if not sorted_dates or (filter_option == "Today" and sum(entry_counts + exit_counts) == 0):
            ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=16, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        elif filter_option == "Today":
            total_entries = sum(entry_counts)
            total_exits = sum(exit_counts)
            ax.pie(
                [total_entries, total_exits],
                labels=["Entries", "Exits"],
                autopct=lambda pct: f"{int(round(pct * (total_entries + total_exits) / 100))}",
                startangle=90,
                colors=['#FFD700', '#1E90FF']
            )
            ax.axis("equal")
        else:
            ax.plot(sorted_dates, entry_counts, label="Entries", marker='o')
            ax.plot(sorted_dates, exit_counts, label="Exits", marker='x')
            ax.set_xlabel("Date")
            ax.set_ylabel("Count")
            ax.legend()
            ax.grid(True)

        ax.set_title(f"{role} Entry/Exit - {filter_option}")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        fig.tight_layout()
        self.entry_exit_canvas.draw()

    def draw_peak_hours_plot(self, hourly_data):
        fig = self.peak_hours_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        peak_hours = list(range(6, 19))
        entries = [hourly_data[h]["entry"] for h in peak_hours]
        exits = [hourly_data[h]["exit"] for h in peak_hours]

        ax.plot(peak_hours, entries, label="Entries", color="#FFD700", marker='o')
        ax.plot(peak_hours, exits, label="Exits", color="#1E90FF", marker='x')

        ax.set_xticks(peak_hours)
        ax.set_xticklabels([f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}" for h in peak_hours], rotation=45)
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Count")
        ax.legend()
        ax.grid(True)
        ax.set_title("Peak Hours")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        fig.tight_layout()
        self.peak_hours_canvas.draw()

    def draw_top_frequent_users(self, user_counts, log_type, role, filter_option):
        fig = self.top_users_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        filtered_counts = {user: counts[log_type] for user, counts in user_counts.items() if counts[log_type] > 0}
        if not filtered_counts:
            ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=16, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            sorted_users = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            users, counts = zip(*sorted_users)
            ax.bar(range(len(users)), counts, color="#4CAF50")
            ax.set_xticks(range(len(users)))
            ax.set_xticklabels(users, rotation=45, ha='right')
            ax.set_ylabel("Count")
            ax.set_title(f"Top {log_type.capitalize()} Users - {role} - {filter_option}")

        fig.subplots_adjust(bottom=0.25)  # Give room for rotated labels
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        fig.tight_layout()
        self.top_users_canvas.draw()

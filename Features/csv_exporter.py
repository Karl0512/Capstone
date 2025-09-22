# csv_exporter.py
import csv
from datetime import datetime

from PySide6.QtWidgets import QFileDialog

def export_table_to_csv(table_widget, parent=None, preset_name="logs"):
    """
    Export the contents of a QTableWidget to a CSV file.
    """
    suggested_name = f"{preset_name}_{datetime.now().strftime('%Y-%m-%d')}.csv"

    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save CSV",
        suggested_name,
        "CSV Files (*.csv);;All Files (*)"
    )
    if not path:
        return  # User canceled

    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        # Write headers
        headers = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]
        writer.writerow(headers)

        # Write data rows
        for row in range(table_widget.rowCount()):
            row_data = []
            for col in range(table_widget.columnCount()):
                item = table_widget.item(row, col)
                text = item.text() if item else ""

                # If the cell looks like a timestamp with AM/PM → force text
                if "AM" in text or "PM" in text:
                    text = f"'{text}"  # leading apostrophe makes Excel treat it as text

                row_data.append(text)
            writer.writerow(row_data)

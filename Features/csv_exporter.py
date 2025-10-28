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

        # Get headers from the table
        headers = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]

        # Identify Status and Toggle columns to exclude
        exclude_cols = [i for i, h in enumerate(headers) if h in ("Status", "Toggle")]

        # Filtered headers (no Status, no Toggle)
        filtered_headers = [h for i, h in enumerate(headers) if i not in exclude_cols]
        writer.writerow(filtered_headers)

        # Write data rows
        for row in range(table_widget.rowCount()):
            # Check the actual status column (before exclusion)
            status_col_index = next((i for i, h in enumerate(headers) if h == "Status"), None)
            if status_col_index is not None:
                status_item = table_widget.item(row, status_col_index)
                status_text = status_item.text().lower() if status_item else ""
                if status_text == "void":
                    continue  # skip voided rows

            row_data = []
            for col in range(table_widget.columnCount()):
                if col in exclude_cols:
                    continue  # skip Status & Toggle

                item = table_widget.item(row, col)
                text = item.text() if item else ""

                # If it looks like a timestamp with AM/PM → force Excel to treat as text
                if "AM" in text or "PM" in text:
                    text = f"'{text}"

                row_data.append(text)

            writer.writerow(row_data)

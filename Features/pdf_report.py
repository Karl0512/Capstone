from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime, date
import os
from db.database import get_connection
import matplotlib.pyplot as plt
from io import BytesIO
import calendar

def create_pdf_report(person_id, name, role, section_or_job, output_path=None, start_date=None, end_date=None, generated_by=None):
    # Ensure output path exists if not provided
    if output_path is None:
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = f"report_{person_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_dir, filename)

    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title and basic info
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 80, f"{name.upper()} REPORT")
    c.setFont("Helvetica", 12)
    y = height - 130
    c.drawString(100, y, f"ID: {person_id}")
    c.drawString(100, y - 20, f"Name: {name}")
    c.drawString(100, y - 40, f"Role: {role}")
    c.drawString(100, y - 60, f"Section / Job: {section_or_job}")

    if start_date and end_date:
        start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, date) else str(start_date)
        end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, date) else str(end_date)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(100, y - 100, f"Report Period: {start_str} to {end_str}")
        c.setFont("Helvetica", 12)
        y -= 30  # Adjust y position if needed

    # Connect to DB and fetch logs
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Fetch aggregated data for graphs (per day)
        cursor.execute("""
            SELECT timestamp::date, COUNT(*)
            FROM gate_logs
            WHERE person_id = %s
            GROUP BY timestamp::date
            ORDER BY timestamp::date
        """, (person_id,))
        gate_rows_graph = cursor.fetchall()

        cursor.execute("""
            SELECT timestamp::date, COUNT(*)
            FROM room_logs
            WHERE person_id = %s
            GROUP BY timestamp::date
            ORDER BY timestamp::date
        """, (person_id,))
        room_rows_graph = cursor.fetchall()

        # Fetch full timestamp + purpose for text output
        cursor.execute("""
            SELECT timestamp, role, purpose
            FROM gate_logs
            WHERE person_id = %s
            ORDER BY timestamp
        """, (person_id,))
        gate_rows_text = cursor.fetchall()

        cursor.execute("""
            SELECT timestamp, role, purpose
            FROM room_logs
            WHERE person_id = %s
            ORDER BY timestamp
        """, (person_id,))
        room_rows_text = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    # Helper: Draw logs as text
    def draw_logs_as_text(canvas, data, title, start_y):
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(100, start_y, title)
        canvas.setFont("Helvetica", 12)
        y_pos = start_y - 20
        for timestamp, action, purpose in data:
            # Format timestamp to 12-hour format with AM/PM
            if isinstance(timestamp, datetime):
                ts_str = timestamp.strftime("%Y-%m-%d %I:%M:%S %p")
            else:
                ts_str = str(timestamp)  # fallback

            canvas.drawString(100, y_pos, f"{ts_str} | {action} | {purpose}")
            y_pos -= 20
        return y_pos

    # Function to create graph image in memory
    def draw_line_chart(data, title, start_date=None):
        if not data:
            return None

        # Convert date strings to datetime.date if necessary
        dates, counts = zip(*data)
        dates = [d if isinstance(d, date) else datetime.strptime(str(d), "%Y-%m-%d").date() for d in dates]

        plt.figure(figsize=(6, 3))
        plt.plot(dates, counts, marker='o', linestyle='-', color="#002366")
        plt.title(title)
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.grid(True)
        plt.xticks(rotation=45)

        # Set x-axis to full month of start_date
        if start_date:
            start_date = start_date if isinstance(start_date, date) else datetime.strptime(str(start_date), "%Y-%m-%d").date()
            start_of_month = start_date.replace(day=1)
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_of_month = start_date.replace(day=last_day)
            plt.xlim(start_of_month, end_of_month)

        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='PNG')
        plt.close()
        buf.seek(0)
        return buf

    # Gate logs: text if ≤20 rows, otherwise graph
    if len(gate_rows_text) <= 20:
        y = draw_logs_as_text(c, gate_rows_text, "Gate Logs", y - 100)
    else:
        gate_img = draw_line_chart(gate_rows_graph, "Gate Logs Count per Day")
        if gate_img:
            c.drawImage(ImageReader(gate_img), 100, y - 300, width=400, height=150)
            y -= 200

    # Room logs
    if len(room_rows_text) <= 20:
        y = draw_logs_as_text(c, room_rows_text, "Room Logs", y - 40)
    else:
        room_img = draw_line_chart(room_rows_graph, "Room Logs Count per Day")
        if room_img:
            c.drawImage(ImageReader(room_img), 100, y - 300, width=400, height=150)

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, 80, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(100, 100, f"Generated by: {generated_by}")

    c.showPage()
    c.save()

    return output_path
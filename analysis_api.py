from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import get_connection
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64
from datetime import datetime
 
 
analysis_bp = Blueprint("analysis_bp", __name__)
 
 
 
@analysis_bp.route("/analysis", methods=["GET"])
def analysis():
    user_id = session.get("user_id")
    # Read dates from query string (GET). Format: YYYY-MM-DD
    start_date = request.args.get("start_date") or "2026-01-01"
    end_date = request.args.get("end_date") or "2026-01-05"
    if not user_id:
        return redirect(url_for("login"))
 
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD.")
        return redirect(url_for('analysis_bp.analysis'))

    conn = get_connection()
    cursor = conn.cursor()
    # Use COALESCE to handle NULL overtime, and fix the WHERE clauses
    cursor.execute(
        "SELECT p.Project_Name, "
        "(SUM(m.hours + COALESCE(m.overtime,0)) * 100.0 / "
        "(SELECT SUM(m2.hours + COALESCE(m2.overtime,0)) FROM TimesheetMain m2 "
        "JOIN TimesheetProjects p2 ON m2.project_id = p2.id "
        "WHERE m2.user_id = ? AND m2.Tdate >= ? AND m2.Tdate <= ?)) "
        "AS Time_Employee_Worked "
        "FROM TimesheetMain m "
        "JOIN TimesheetProjects p ON m.project_id = p.id "
        "WHERE m.user_id = ? AND m.Tdate >= ? AND m.Tdate <= ? "
        "GROUP BY p.Project_Name;",
        (user_id, start_date, end_date, user_id, start_date, end_date)
    )
    rows = cursor.fetchall()
    conn.close()

    labels = [n for n, _ in rows]
    data = [p for _, p in rows]

    plt.figure(figsize=(6,6))

    if not data or sum(data) == 0:
        # no data - create a placeholder pie chart
        labels = ['No data']
        data = [1]

    plt.pie(data, labels=labels, autopct="%1.1f%%")
    plt.legend(title="Projects")

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)

    img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
    return render_template("Analysis.html", chart_data=img_data, start_date=start_date, end_date=end_date)
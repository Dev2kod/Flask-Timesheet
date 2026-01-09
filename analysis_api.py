from flask import Blueprint, render_template, session, redirect, url_for
from db import get_connection
from flask import flash

analysis_bp = Blueprint("analysis_bp", __name__)



@analysis_bp.route("/analysis", methods=["GET"])
def analysis():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    "SELECT p.Project_Name, "
    "(SUM(m.hours + CASE WHEN m.overtime IS NULL THEN 0 ELSE m.overtime END) / "
    "(SELECT SUM(m2.hours + CASE WHEN m2.overtime IS NULL THEN 0 ELSE m2.overtime END) "
    "FROM TimesheetMain m2 "
    "JOIN TimesheetProjects p2 ON m2.project_id = p2.id "
    "WHERE m2.user_id = ?)) * 100 AS Time_Employee_Worked "
    "FROM TimesheetMain m "
    "JOIN TimesheetProjects p ON m.project_id = p.id "
    "WHERE m.user_id = ? "
    "GROUP BY p.Project_Name;",
    (user_id, user_id)
    )
    rows = cursor.fetchall()
    conn.close()    

    return render_template("Analysis.html", rows=rows )
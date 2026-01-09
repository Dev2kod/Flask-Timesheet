from flask import Flask, flash, render_template, request, session, jsonify, redirect, url_for
import pyodbc
from flask_bcrypt import Bcrypt
from db import get_connection
from analysis_api import analysis_bp



app = Flask(__name__)
bcrypt = Bcrypt(app)
app.register_blueprint(analysis_bp)

app.secret_key = "TCE2025SecretKey"

# Database connection string
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=SRMUMATBU10;"
    "Database=YEDP2024;"
    "Trusted_Connection=yes;"
)



def get_connection():
    return pyodbc.connect(conn_str)

@app.route("/")
def landingPage():
    return render_template("landing.html")

# -------------------
# Sign up
# -------------------
@app.route("/signup", methods=["GET", "POST"])
def create_user():
    user_id = session.get("user_id")
    if request.method == "POST":
        Lname = request.form["Lname"]
        Email = request.form["Email"]
        Username = request.form["Username"]
        Fname = request.form["Fname"]
        ContactNo = request.form["ContactNo"]
        Password = request.form["Password"]
        Password_hash = bcrypt.generate_password_hash(Password).decode("utf-8")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO UserDetail (Username, Fname, Lname, ContactNo, Email, Password) VALUES (?, ?, ?, ?, ?, ?)",
            (Username, Fname, Lname, ContactNo, Email, Password_hash)
        )
        conn.commit()
        conn.close()

        return render_template("loginform.html")
    else:
        if user_id is None:
            return render_template("SignUp.html")
        else:
            return redirect(url_for("home"))

        

# -------------------
# Login
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    user_id = session.get("user_id")

    # Handle POST (login attempt)
    if request.method == "POST":
        # If already logged in, send them to the homepage
        if user_id is not None:
            return redirect(url_for("home"))

        Username = request.form.get("Username", "").strip()
        Password = request.form.get("Password", "")

        if not Username or not Password:
            return render_template("loginform.html", error="Username and Password are required" ,flag = 1), 400

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Id, Password FROM UserDetail WHERE Username = ?",
                (Username,)
            )
            row = cursor.fetchone()
        except Exception as e:
            print("Login error:", e)
            return render_template("loginform.html", error="Server error. Please try again." , flag = 1), 500
        finally:
            if conn:
                conn.close()

        if not row:
            return render_template("loginform.html", error="Invalid username or password" ,flag = 1), 401

        user_id = row[0]
        stored_hash = row[1]

        if bcrypt.check_password_hash(stored_hash, Password):
            session["user_id"] = user_id
            return redirect(url_for("home"))
        else:
            return render_template("loginform.html", error="Invalid username or password" ,flag = 1), 401

    # show login form if not authenticated, otherwise go to homepage
    if user_id is None:
        return render_template("loginform.html" , flag = 0)
    else:
        return redirect(url_for("home"))

# -------------------
# Data helpers
# -------------------
def get_projectNames():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, Project_Name FROM TimesheetProjects")
    rows = cursor.fetchall()
    conn.close()
    projects = [{"id": row[0], "name": row[1]} for row in rows]
    return projects

def get_taskNames(project_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if project_id:
        cursor.execute("SELECT id, Proj_id, Task FROM TimesheetTasks WHERE Proj_id = ?", (project_id,))
        rows = cursor.fetchall()
        tasks = [{"id": row[0], "Proj_id": row[1], "task": row[2]} for row in rows]
    else:
        cursor.execute("SELECT id, Proj_id, Task FROM TimesheetTasks")
        rows = cursor.fetchall()
        tasks = [{"id": row[0], "Proj_id": row[1], "task": row[2]} for row in rows]
    conn.close()
    return tasks

# -------------------
# API endpoints for dropdowns
# -------------------
@app.route("/getProjects", methods=["GET"])
def addProjs():
    projects = get_projectNames()
    return jsonify({"projects": projects})

@app.route("/getTasks/<int:project_id>", methods=["GET"])
def addTaskNames(project_id):
    tasks = get_taskNames(project_id)
    return jsonify({"tasks": tasks})
# -------------------
# Home dashboard
# -------------------
@app.route("/home", methods=["GET"])
def home():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    # Get username for greeting
    cursor.execute("SELECT Username,Fname FROM UserDetail WHERE Id = ?", (user_id,))
    user_row = cursor.fetchone()
    Username = user_row[0] if user_row else "User"
    Name = user_row[1] if user_row else "User"

    # Get user's logged tasks
    cursor.execute("""
        SELECT m.id, p.Project_Name, t.Task, m.activity, m.hours, m.overtime, m.description , m.Tdate
        FROM TimesheetMain m
        JOIN TimesheetProjects p ON m.project_id = p.id
        JOIN TimesheetTasks t ON m.task_id = t.id
        WHERE m.user_id = ?
        ORDER BY m.Tdate DESC;
    """, (user_id,))
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    conn.close()

    data = [dict(zip(columns, row)) for row in rows]

    return render_template("Home.html", Username=Username ,Name= Name, data=data, entries=bool(data))

# -------------------
# Add task (insert into TimesheetMain)
# -------------------
@app.route("/add_task", methods=["POST"])
def add_task():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    try:
        Tdate = request.form.get("date")
        project_id = int(request.form.get("project_id"))
        task_id = int(request.form.get("task_id"))
        activity = request.form.get("activity")
        hours = float(request.form.get("hours"))
        overtime = request.form.get("overtime")
        overtime = float(overtime) if overtime else None
        description = request.form.get("description")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO TimesheetMain (user_id, project_id, task_id, activity, hours, overtime, description, Tdate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, project_id, task_id, activity, hours, overtime, description, Tdate))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error inserting task:", e)
        # Optionally flash a message or return error page

    return redirect(url_for("home"))


@app.route("/logout", methods=["GET"])
def logout():
    print("Logging out user:", session.get("user_id"))
    session.clear()
    return render_template("landing.html")

# -------------------
# Search tasks
# -------------------
@app.route("/search_tasks", methods=["POST"])
def search_tasks():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        data = request.get_json()
        search_term = data.get("search_term", "").strip()
        column = data.get("column", "").strip()

        if not search_term or not column:
            return jsonify({"success": False, "error": "Search term and column are required"}), 400

        # Validate column name to prevent SQL injection
        valid_columns = ["Project_Name", "Task", "activity", "Tdate", "description"]
        if column not in valid_columns:
            return jsonify({"success": False, "error": "Invalid column"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        # Build the query dynamically
        query = f"""
            SELECT m.id, p.Project_Name, t.Task, m.activity, m.hours, m.overtime, m.description, m.Tdate
            FROM TimesheetMain m
            JOIN TimesheetProjects p ON m.project_id = p.id
            JOIN TimesheetTasks t ON m.task_id = t.id
            WHERE m.user_id = ? AND {column} LIKE ?
            ORDER BY m.Tdate DESC;
        """
        
        cursor.execute(query, (user_id, f"%{search_term}%"))
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        conn.close()

        results = [dict(zip(columns, row)) for row in rows]

        return jsonify({"success": True, "results": results})

    except Exception as e:
        print("Search error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------
# Delete task
# -------------------
@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM TimesheetMain WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for("home"))



@app.route("/update_task/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        # read and validate form values
        project_raw = request.form.get("project_id")
        task_raw = request.form.get("task_id")
        Tdate = request.form.get("Tdate")
        if not project_raw or not task_raw:
            flash("Missing project or task id.", "error")
            return redirect(url_for("update_task", task_id=task_id))
        try:
            project_id = int(project_raw)
            task_id_form = int(task_raw)
        except ValueError:
            flash("Project and Task IDs must be integers.", "error")
            return redirect(url_for("update_task", task_id=task_id))

        activity = request.form.get("activity", "")
        hours_raw = request.form.get("hours")
        if hours_raw is None or hours_raw == "":
            flash("Hours is required.", "error")
            return redirect(url_for("update_task", task_id=task_id))
        try:
            hours = float(hours_raw)
        except ValueError:
            flash("Invalid hours value.", "error")
            return redirect(url_for("update_task", task_id=task_id))
        overtime_raw = request.form.get("overtime")
        overtime = float(overtime_raw) if overtime_raw not in (None, "") else None
        description = request.form.get("description", "")

        cursor.execute("""
          UPDATE TimesheetMain
          SET Tdate=?, project_id=?, task_id=?, activity=?, hours=?, overtime=?, description=?
          WHERE id=? AND user_id=?
        """, (Tdate, project_id, task_id_form, activity, hours, overtime, description, task_id, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    # GET: fetch task to prefill form
    cursor.execute("""
        SELECT m.id, m.project_id, m.task_id, p.Project_Name, t.Task, m.activity, m.hours, m.overtime, m.description, m.Tdate
        FROM TimesheetMain m
        JOIN TimesheetProjects p ON m.project_id = p.id
        JOIN TimesheetTasks t ON m.task_id = t.id
        WHERE m.id = ? AND m.user_id = ?
    """, (task_id, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        flash("Task not found.", "error")
        return redirect(url_for("home"))
    columns = [c[0] for c in cursor.description]
    task = dict(zip(columns, row))
    conn.close()
    return render_template("Update.html", task=task)



@app.route("/profile", methods=["GET"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Username, Fname, Lname, ContactNo, Email FROM UserDetail WHERE Id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
 
    if not row:
        return "User not found", 404
 
    user = {
        "Id": row[0],
        "Username": row[1],
        "Fname": row[2],
        "Lname": row[3],
        "ContactNo": row[4],
        "Email": row[5]
    }
 
    return render_template("Profile.html", user=user)
 
# -------------------
# Edit Profile
# -------------------
@app.route("/edit_profile", methods=["GET"])
def edit_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Username, Fname, Lname, ContactNo, Email FROM UserDetail WHERE Id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
 
    if not row:
        return "User not found", 404
 
    user = {
        "Username": row[0],
        "Fname": row[1],
        "Lname": row[2],
        "ContactNo": row[3],
        "Email": row[4]
    }
 
    return render_template("edit_profile.html", user=user)
 
# -------------------
# Update Profile
# -------------------
@app.route("/update_profile", methods=["POST"])
def update_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
 
    fname = request.form['Fname']
    lname = request.form['Lname']
    email = request.form['Email']
    contact = request.form['ContactNo']
 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE UserDetail
        SET Fname = ?, Lname = ?, Email = ?, ContactNo = ?
        WHERE Id = ?
    """, (fname, lname, email, contact, user_id))
    conn.commit()
    conn.close()
 
    return redirect(url_for('profile'))
 

if __name__ == "__main__":
    app.run(debug=True)
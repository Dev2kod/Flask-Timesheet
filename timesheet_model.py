# timesheet_model.py
# This file defines the database model and operations for the timesheet feature.
# Since we're using raw SQL with pyodbc (no ORM like SQLAlchemy), we'll define the table structure and helper functions here.
# This keeps the database logic separate and reusable.

from db import get_connection  # Importing the connection function from the existing db.py

# Define the table creation SQL for the Timesheet table.
# This table will store individual timesheet entries.
# Columns:
# - id: Primary key, auto-incrementing integer.
# - user_id: Foreign key to the user (assuming UserDetail table has an Id column).
# - task: Description of the task (string).
# - hours: Number of hours spent on the task (float for precision).
# - date: The date when the task was performed (date type).
# - week_start: The start date of the week (Monday) for grouping weekly records (date type).
# We use week_start to easily query weekly data.
CREATE_TIMESHEET_TABLE_SQL = """
IF OBJECT_ID('Timesheet', 'U') IS NULL
CREATE TABLE Timesheet (
    id INT IDENTITY(1,1) PRIMARY KEY,  -- Auto-incrementing ID
    user_id INT NOT NULL,  -- References the user
    task NVARCHAR(255) NOT NULL,  -- Task description
    hours FLOAT NOT NULL,  -- Hours spent
    date DATE NOT NULL,  -- Date of the task
    week_start DATE NOT NULL,  -- Start of the week (Monday)
    FOREIGN KEY (user_id) REFERENCES UserDetail(Id)  -- Assuming UserDetail has Id column
);
"""

def create_timesheet_table():
    """
    Function to create the Timesheet table if it doesn't exist.
    Call this once to set up the database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_TIMESHEET_TABLE_SQL)
    conn.commit()
    cursor.close()
    conn.close()

def insert_timesheet_entry(user_id, task, hours, date, week_start):
    """
    Insert a new timesheet entry into the database.
    Parameters:
    - user_id: ID of the user
    - task: Task description
    - hours: Hours spent
    - date: Date of the task
    - week_start: Start date of the week
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Timesheet (user_id, task, hours, date, week_start)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, task, hours, date, week_start))
    conn.commit()
    cursor.close()
    conn.close()

def get_weekly_timesheet(user_id, week_start):
    """
    Retrieve all timesheet entries for a user in a specific week from the existing TimesheetMain table.
    Joins with TimesheetProjects and TimesheetTasks to get project and task names.
    Parameters:
    - user_id: ID of the user
    - week_start: Start date of the week (Monday)
    Returns: List of dictionaries with project, task, activity, hours, date
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.Project_Name, t.Task, m.activity, m.hours + COALESCE(m.overtime, 0) as total_hours, m.Tdate
        FROM TimesheetMain m
        JOIN TimesheetProjects p ON m.project_id = p.id
        JOIN TimesheetTasks t ON m.task_id = t.id
        WHERE m.user_id = ? AND m.Tdate >= ? AND m.Tdate < DATEADD(DAY, 7, ?)
        ORDER BY m.Tdate
    """, (user_id, week_start, week_start))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # Convert rows to list of dicts
    timesheet = []
    for row in rows:
        timesheet.append({
            'project': row[0],
            'task': row[1],
            'activity': row[2] or '',
            'hours': float(row[3]),
            'date': row[4]
        })
    return timesheet

# Note: To use this, you need to call create_timesheet_table() once.
# Also, ensure the UserDetail table has an 'Id' column; if not, adjust the foreign key.
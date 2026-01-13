# timesheet_api.py
# This file contains the API endpoints for the timesheet feature using Flask Blueprint.
# Blueprints allow us to organize routes into modules, making the code modular.
# This blueprint will handle requests for viewing and adding timesheet entries.

from flask import Blueprint, request, jsonify, session
from timesheet_model import insert_timesheet_entry, get_weekly_timesheet
from datetime import datetime, timedelta

# Create a Blueprint named 'timesheet_bp'
# This allows us to group related routes together.
timesheet_bp = Blueprint('timesheet_bp', __name__, template_folder='templates')

@timesheet_bp.route('/api/timesheet/add', methods=['POST'])
def add_timesheet_entry():
    """
    API endpoint to add a new timesheet entry.
    Expects JSON data: { "task": "string", "hours": float, "date": "YYYY-MM-DD" }
    Requires user to be logged in (session check).
    Calculates the week_start (Monday of the week) based on the date.
    """
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    # Get data from request
    data = request.get_json()
    task = data.get('task')
    hours = data.get('hours')
    date_str = data.get('date')

    if not all([task, hours, date_str]):
        return jsonify({'error': 'Missing required fields: task, hours, date'}), 400

    try:
        # Parse the date
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # Calculate week_start: Monday of the week
        # weekday() returns 0 for Monday, 6 for Sunday
        week_start = date - timedelta(days=date.weekday())
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Insert into database
    insert_timesheet_entry(user_id, task, hours, date, week_start)

    return jsonify({'message': 'Timesheet entry added successfully'}), 201

@timesheet_bp.route('/api/timesheet/weekly/<week_start>', methods=['GET'])
def get_weekly_timesheet_api(week_start):
    """
    API endpoint to get weekly timesheet records for the logged-in user.
    Retrieves data from the existing TimesheetMain table with project and task details.
    URL parameter: week_start in YYYY-MM-DD format (any date in the week).
    Returns JSON with list of entries: [{"project": "...", "task": "...", "activity": "...", "hours": ..., "date": "..."}]
    """
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    try:
        # Parse week_start
        week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid week_start format. Use YYYY-MM-DD'}), 400

    # Get data from existing TimesheetMain table
    timesheet = get_weekly_timesheet(user_id, week_start_date)

    return jsonify({'timesheet': timesheet}), 200

# Note: To use this blueprint, register it in the main app.py like:
# from timesheet_api import timesheet_bp
# app.register_blueprint(timesheet_bp)
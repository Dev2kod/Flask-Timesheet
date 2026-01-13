# setup_timesheet.py
# This script sets up the timesheet database table.
# Run this once to create the Timesheet table in the database.
# Usage: python setup_timesheet.py

from timesheet_model import create_timesheet_table

if __name__ == "__main__":
    print("Creating Timesheet table...")
    create_timesheet_table()
    print("Timesheet table created successfully!")
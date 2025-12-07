"""
Database initialization script for the Study Planner application.

This script provides utilities to initialize, reset, and manage the SQLite database.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from utils.database import DatabaseManager
from utils.models import DeadlineDict, StudySessionDict, TaskHistoryDict


def init_database(db_path: str = "study_planner.db") -> bool:
    """
    Initialize the database with schema and tables.

    Args:
        db_path (str): Path to the database file.

    Returns:
        bool: True if initialization successful, False otherwise.
    """
    db_manager = DatabaseManager(db_path)

    if not db_manager.connect():
        print("Failed to connect to database")
        return False

    if not db_manager.create_tables():
        print("Failed to create tables")
        return False

    print(f"Database initialized successfully at {db_path}")
    db_manager.disconnect()
    return True


def seed_sample_data(db_path: str = "study_planner.db") -> bool:
    """
    Seed the database with sample data for testing and demonstration.

    Args:
        db_path (str): Path to the database file.

    Returns:
        bool: True if seeding successful, False otherwise.
    """
    db_manager = DatabaseManager(db_path)

    if not db_manager.connect():
        print("Failed to connect to database")
        return False

    try:
        # Add sample deadlines
        deadlines = [
            {
                'title': 'Math Assignment',
                'type': 'assignment',
                'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
                'estimated_time': 120,
                'description': 'Chapter 5 exercises',
                'status': 'not_started'
            },
            {
                'title': 'Midterm Exam',
                'type': 'exam',
                'due_date': (datetime.now() + timedelta(days=14)).isoformat(),
                'estimated_time': 180,
                'description': 'Covers chapters 1-6',
                'status': 'in_progress'
            },
            {
                'title': 'Research Project',
                'type': 'project',
                'due_date': (datetime.now() + timedelta(days=21)).isoformat(),
                'estimated_time': 480,
                'description': 'Final research paper',
                'status': 'not_started'
            },
        ]

        deadline_ids = []
        for deadline in deadlines:
            deadline_id = db_manager.add_deadline(deadline)
            if deadline_id:
                deadline_ids.append(deadline_id)
                print(f"Added deadline: {deadline['title']} (ID: {deadline_id})")

        # Add sample study sessions
        sessions = [
            {
                'date': datetime.now().isoformat(),
                'tasks': 'Math, Physics',
                'energy_level': 8,
                'completion_rate': 0.95
            },
            {
                'date': (datetime.now() - timedelta(days=1)).isoformat(),
                'tasks': 'Chemistry, Biology',
                'energy_level': 7,
                'completion_rate': 0.85
            },
            {
                'date': (datetime.now() - timedelta(days=2)).isoformat(),
                'tasks': 'History, Literature',
                'energy_level': 6,
                'completion_rate': 0.90
            },
        ]

        for session in sessions:
            session_id = db_manager.add_study_session(session)
            if session_id:
                print(f"Added study session (ID: {session_id})")

        # Add sample task history
        tasks = [
            {
                'task_name': 'Algebra Practice',
                'deadline_id': deadline_ids[0] if deadline_ids else None,
                'time_spent': 90,
                'difficulty_actual': 6,
                'completed_date': (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                'task_name': 'Calculus Review',
                'deadline_id': deadline_ids[0] if deadline_ids else None,
                'time_spent': 120,
                'difficulty_actual': 7,
                'completed_date': datetime.now().isoformat()
            },
            {
                'task_name': 'Physics Lab',
                'deadline_id': None,
                'time_spent': 150,
                'difficulty_actual': 8,
                'completed_date': (datetime.now() - timedelta(days=2)).isoformat()
            },
        ]

        for task in tasks:
            task_id = db_manager.add_task_history(task)
            if task_id:
                print(f"Added task history: {task['task_name']} (ID: {task_id})")

        # Display database info
        print("\n" + "="*50)
        print("Database Seeding Complete!")
        print("="*50)
        db_info = db_manager.get_database_info()
        for key, value in db_info.items():
            print(f"{key}: {value}")

        db_manager.disconnect()
        return True

    except Exception as e:
        print(f"Error seeding database: {e}")
        db_manager.disconnect()
        return False


def reset_database(db_path: str = "study_planner.db") -> bool:
    """
    Reset the database by clearing all data.

    Args:
        db_path (str): Path to the database file.

    Returns:
        bool: True if reset successful, False otherwise.
    """
    db_manager = DatabaseManager(db_path)

    if not db_manager.connect():
        print("Failed to connect to database")
        return False

    if not db_manager.clear_all_data():
        print("Failed to clear database")
        return False

    print(f"Database reset successfully")
    db_manager.disconnect()
    return True


def main():
    """Main entry point for database initialization."""
    if len(sys.argv) < 2:
        print("Usage: python init_db.py [init|seed|reset] [db_path]")
        print("\nCommands:")
        print("  init      - Initialize database with schema")
        print("  seed      - Seed database with sample data")
        print("  reset     - Clear all data from database")
        sys.exit(1)

    command = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "study_planner.db"

    if command == "init":
        init_database(db_path)
    elif command == "seed":
        init_database(db_path)
        seed_sample_data(db_path)
    elif command == "reset":
        reset_database(db_path)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

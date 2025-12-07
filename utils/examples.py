"""
Example usage and quick start guide for the Study Planner database module.

This module demonstrates all major features of the DatabaseManager class.
"""

from datetime import datetime, timedelta
from utils.database import DatabaseManager
from utils.models import DeadlineDict, StudySessionDict, TaskHistoryDict


def example_basic_usage():
    """Example: Basic database operations."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Database Operations")
    print("="*60)

    # Initialize database manager
    db = DatabaseManager("study_planner.db")
    db.connect()
    db.create_tables()

    # Add a deadline
    deadline: DeadlineDict = {
        'title': 'Data Structures Midterm',
        'type': 'exam',
        'due_date': (datetime.now() + timedelta(days=14)).isoformat(),
        'estimated_time': 180,
        'description': 'Covers arrays, linked lists, and trees',
        'status': 'not_started'
    }

    deadline_id = db.add_deadline(deadline)
    print(f"Added deadline with ID: {deadline_id}")

    # Retrieve the deadline
    retrieved = db.get_deadline(deadline_id)
    print(f"Retrieved deadline: {retrieved['title']}")

    # Update the deadline
    db.update_deadline(deadline_id, {'status': 'in_progress'})
    print(f"Updated deadline status to: in_progress")

    db.disconnect()


def example_deadline_management():
    """Example: Comprehensive deadline management."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Deadline Management")
    print("="*60)

    db = DatabaseManager("study_planner.db")
    db.connect()

    # Create multiple deadlines
    deadlines_data = [
        {
            'title': 'Python Assignment',
            'type': 'assignment',
            'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
            'estimated_time': 120,
            'description': 'Implement a calculator program'
        },
        {
            'title': 'Database Project',
            'type': 'project',
            'due_date': (datetime.now() + timedelta(days=21)).isoformat(),
            'estimated_time': 480,
            'description': 'Design and implement a student management system'
        },
        {
            'title': 'Math Quiz',
            'type': 'exam',
            'due_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'estimated_time': 60,
            'description': 'Chapters 1-3'
        },
    ]

    deadline_ids = []
    for deadline in deadlines_data:
        deadline_id = db.add_deadline(deadline)
        deadline_ids.append(deadline_id)
        print(f"Added: {deadline['title']}")

    # Get all deadlines
    all_deadlines = db.get_all_deadlines()
    print(f"\nTotal deadlines: {len(all_deadlines)}")

    # Get deadlines sorted by due date
    print("\nDeadlines sorted by due date:")
    for d in all_deadlines:
        print(f"  - {d['title']}: {d['due_date']} ({d['type']})")

    # Filter by type
    assignments = db.get_all_deadlines(deadline_type='assignment')
    print(f"\nAssignments: {len(assignments)}")

    db.disconnect()


def example_study_sessions():
    """Example: Managing study sessions."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Study Sessions")
    print("="*60)

    db = DatabaseManager("study_planner.db")
    db.connect()

    # Record today's study session
    session: StudySessionDict = {
        'date': datetime.now().isoformat(),
        'tasks': 'Python exercises, Database design',
        'energy_level': 8,
        'completion_rate': 0.92
    }

    session_id = db.add_study_session(session)
    print(f"Recorded study session (ID: {session_id})")
    print(f"  Tasks: {session['tasks']}")
    print(f"  Energy: {session['energy_level']}/10")
    print(f"  Completion: {session['completion_rate']*100}%")

    # Record multiple sessions
    for i in range(1, 4):
        past_session: StudySessionDict = {
            'date': (datetime.now() - timedelta(days=i)).isoformat(),
            'tasks': f'Study topic {i}',
            'energy_level': 6 + i,
            'completion_rate': 0.8 + i * 0.05
        }
        db.add_study_session(past_session)

    # Get sessions from the last week
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).isoformat()
    recent_sessions = db.get_study_sessions(start_date=week_ago)
    print(f"\nSessions in last 7 days: {len(recent_sessions)}")

    db.disconnect()


def example_task_history():
    """Example: Tracking task history."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Task History Tracking")
    print("="*60)

    db = DatabaseManager("study_planner.db")
    db.connect()

    # Create a deadline first
    deadline: DeadlineDict = {
        'title': 'Algorithm Assignment',
        'type': 'assignment',
        'due_date': (datetime.now() + timedelta(days=5)).isoformat(),
        'estimated_time': 300,
        'description': 'Implement sorting algorithms'
    }
    deadline_id = db.add_deadline(deadline)

    # Log completed tasks
    tasks_data = [
        {
            'task_name': 'Study quicksort',
            'deadline_id': deadline_id,
            'time_spent': 60,
            'difficulty_actual': 6,
            'completed_date': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'task_name': 'Implement mergesort',
            'deadline_id': deadline_id,
            'time_spent': 90,
            'difficulty_actual': 7,
            'completed_date': (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            'task_name': 'Debug and test',
            'deadline_id': deadline_id,
            'time_spent': 75,
            'difficulty_actual': 5,
            'completed_date': datetime.now().isoformat()
        },
    ]

    for task in tasks_data:
        task_id = db.add_task_history(task)
        print(f"Logged: {task['task_name']} ({task['time_spent']} min, difficulty: {task['difficulty_actual']}/10)")

    # Get all tasks for this deadline
    history = db.get_task_history_by_deadline(deadline_id)
    total_time = sum(t['time_spent'] for t in history)
    avg_difficulty = sum(t['difficulty_actual'] for t in history) / len(history)

    print(f"\nStats for '{deadline['title']}':")
    print(f"  Total time spent: {total_time} minutes")
    print(f"  Average difficulty: {avg_difficulty:.1f}/10")
    print(f"  Tasks completed: {len(history)}")

    db.disconnect()


def example_analytics():
    """Example: Productivity analytics."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Productivity Analytics")
    print("="*60)

    db = DatabaseManager("study_planner.db")
    db.connect()

    # Add sample data for the past week
    now = datetime.now()
    for i in range(7):
        date = (now - timedelta(days=i))

        # Add study sessions
        session: StudySessionDict = {
            'date': date.isoformat(),
            'tasks': f'Tasks for day {i}',
            'energy_level': 5 + (i % 5),
            'completion_rate': 0.75 + (i % 4) * 0.05
        }
        db.add_study_session(session)

        # Add task history
        for j in range(2):
            task: TaskHistoryDict = {
                'task_name': f'Task {i}-{j}',
                'time_spent': 45 + (i * 5),
                'difficulty_actual': 4 + (j % 6),
                'completed_date': date.isoformat()
            }
            db.add_task_history(task)

    # Calculate stats
    week_start = (now - timedelta(days=7)).isoformat()
    week_end = now.isoformat()
    stats = db.get_productivity_stats(week_start, week_end)

    print("Weekly Productivity Stats:")
    print(f"\nStudy Sessions:")
    print(f"  Total sessions: {stats['study_sessions']['total_sessions']}")
    if stats['study_sessions']['avg_energy']:
        print(f"  Avg energy level: {stats['study_sessions']['avg_energy']:.1f}/10")
    if stats['study_sessions']['avg_completion']:
        print(f"  Avg completion rate: {stats['study_sessions']['avg_completion']:.1%}")

    print(f"\nTask History:")
    print(f"  Tasks completed: {stats['task_history']['total_tasks']}")
    if stats['task_history']['total_time']:
        print(f"  Total time: {stats['task_history']['total_time']} minutes")
    if stats['task_history']['avg_difficulty']:
        print(f"  Avg difficulty: {stats['task_history']['avg_difficulty']:.1f}/10")

    db.disconnect()


def example_error_handling():
    """Example: Error handling and edge cases."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Error Handling")
    print("="*60)

    db = DatabaseManager("study_planner.db")

    # Test connection without connecting
    try:
        print("Testing operation without connection...")
        db.get_all_deadlines()
    except RuntimeError as e:
        print(f"[PASS] Caught expected error: {e}")

    # Connect and create tables
    db.connect()

    # Test missing required fields
    try:
        print("\nTesting deadline with missing fields...")
        incomplete_deadline = {'title': 'Test'}  # Missing required fields
        db.add_deadline(incomplete_deadline)
    except ValueError as e:
        print(f"[PASS] Caught expected error: {e}")

    # Test invalid deadline type
    try:
        print("\nTesting invalid deadline type...")
        bad_deadline: DeadlineDict = {
            'title': 'Bad',
            'type': 'invalid_type',  # Should be one of: assignment, exam, project, other
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        db.add_deadline(bad_deadline)
        print("[FAIL] Should have caught invalid type")
    except Exception as e:
        print(f"[PASS] Caught expected error")

    db.disconnect()


def example_database_info():
    """Example: Checking database information."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Database Information")
    print("="*60)

    db = DatabaseManager("study_planner.db")
    db.connect()
    db.create_tables()

    # Add some data
    deadline: DeadlineDict = {
        'title': 'Test',
        'type': 'assignment',
        'due_date': datetime.now().isoformat(),
        'estimated_time': 120
    }
    db.add_deadline(deadline)

    session: StudySessionDict = {
        'date': datetime.now().isoformat(),
        'tasks': 'Study',
        'energy_level': 8,
        'completion_rate': 0.9
    }
    db.add_study_session(session)

    # Get database info
    info = db.get_database_info()
    print("Database Information:")
    for key, value in info.items():
        if key == 'db_file_size_bytes':
            print(f"  {key}: {value} bytes ({value/1024:.2f} KB)")
        else:
            print(f"  {key}: {value}")

    db.disconnect()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Study Planner Database - Usage Examples")
    print("="*60)

    try:
        example_basic_usage()
        example_deadline_management()
        example_study_sessions()
        example_task_history()
        example_analytics()
        example_error_handling()
        example_database_info()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

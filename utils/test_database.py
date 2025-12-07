"""
Test suite for the Study Planner database persistence layer.

Comprehensive tests for DatabaseManager class including CRUD operations,
error handling, and edge cases.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from utils.database import DatabaseManager
from utils.models import DeadlineDict, StudySessionDict, TaskHistoryDict


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.connect()
        self.db_manager.create_tables()

    def tearDown(self):
        """Clean up after each test."""
        self.db_manager.disconnect()
        Path(self.db_path).unlink(missing_ok=True)

    # ==================== Connection Tests ====================

    def test_connect(self):
        """Test database connection."""
        self.assertIsNotNone(self.db_manager.connection)

    def test_disconnect(self):
        """Test database disconnection."""
        result = self.db_manager.disconnect()
        self.assertTrue(result)
        self.assertIsNone(self.db_manager.connection)

    def test_connect_disconnect_reconnect(self):
        """Test multiple connect/disconnect cycles."""
        self.db_manager.disconnect()
        self.assertTrue(self.db_manager.connect())
        self.assertIsNotNone(self.db_manager.connection)

    # ==================== Deadline Tests ====================

    def test_add_deadline(self):
        """Test adding a deadline."""
        deadline: DeadlineDict = {
            'title': 'Test Assignment',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120,
            'description': 'Test deadline'
        }
        deadline_id = self.db_manager.add_deadline(deadline)
        self.assertIsNotNone(deadline_id)
        self.assertIsInstance(deadline_id, int)

    def test_add_deadline_missing_required_field(self):
        """Test adding deadline with missing required field."""
        incomplete_deadline: DeadlineDict = {
            'title': 'Test',
            'type': 'assignment'
            # Missing due_date and estimated_time
        }
        with self.assertRaises(ValueError):
            self.db_manager.add_deadline(incomplete_deadline)

    def test_get_all_deadlines(self):
        """Test retrieving all deadlines."""
        # Add multiple deadlines
        for i in range(3):
            deadline: DeadlineDict = {
                'title': f'Deadline {i}',
                'type': 'assignment',
                'due_date': (datetime.now() + timedelta(days=i)).isoformat(),
                'estimated_time': 120 + i * 30
            }
            self.db_manager.add_deadline(deadline)

        deadlines = self.db_manager.get_all_deadlines()
        self.assertEqual(len(deadlines), 3)

    def test_get_deadline_by_id(self):
        """Test retrieving a specific deadline."""
        deadline: DeadlineDict = {
            'title': 'Specific Deadline',
            'type': 'exam',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 180
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        retrieved = self.db_manager.get_deadline(deadline_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['title'], 'Specific Deadline')
        self.assertEqual(retrieved['type'], 'exam')

    def test_get_nonexistent_deadline(self):
        """Test retrieving a nonexistent deadline."""
        result = self.db_manager.get_deadline(99999)
        self.assertIsNone(result)

    def test_update_deadline(self):
        """Test updating a deadline."""
        deadline: DeadlineDict = {
            'title': 'Original Title',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120,
            'status': 'not_started'
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        updates = {
            'title': 'Updated Title',
            'status': 'in_progress',
            'estimated_time': 150
        }
        result = self.db_manager.update_deadline(deadline_id, updates)
        self.assertTrue(result)

        updated = self.db_manager.get_deadline(deadline_id)
        self.assertEqual(updated['title'], 'Updated Title')
        self.assertEqual(updated['status'], 'in_progress')
        self.assertEqual(updated['estimated_time'], 150)

    def test_update_nonexistent_deadline(self):
        """Test updating a nonexistent deadline."""
        result = self.db_manager.update_deadline(99999, {'title': 'New Title'})
        self.assertFalse(result)

    def test_delete_deadline(self):
        """Test deleting a deadline."""
        deadline: DeadlineDict = {
            'title': 'To Delete',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        result = self.db_manager.delete_deadline(deadline_id)
        self.assertTrue(result)

        retrieved = self.db_manager.get_deadline(deadline_id)
        self.assertIsNone(retrieved)

    def test_delete_nonexistent_deadline(self):
        """Test deleting a nonexistent deadline."""
        result = self.db_manager.delete_deadline(99999)
        self.assertFalse(result)

    def test_get_deadlines_by_status(self):
        """Test filtering deadlines by status."""
        # Add deadlines with different statuses
        for status in ['not_started', 'in_progress', 'completed']:
            deadline: DeadlineDict = {
                'title': f'Deadline {status}',
                'type': 'assignment',
                'due_date': datetime.now().isoformat(),
                'estimated_time': 120,
                'status': status
            }
            self.db_manager.add_deadline(deadline)

        in_progress = self.db_manager.get_all_deadlines(status='in_progress')
        self.assertEqual(len(in_progress), 1)
        self.assertEqual(in_progress[0]['status'], 'in_progress')

    # ==================== Study Session Tests ====================

    def test_add_study_session(self):
        """Test adding a study session."""
        session: StudySessionDict = {
            'date': datetime.now().isoformat(),
            'tasks': 'Math, Physics',
            'energy_level': 8,
            'completion_rate': 0.95
        }
        session_id = self.db_manager.add_study_session(session)
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, int)

    def test_add_study_session_missing_required_field(self):
        """Test adding session with missing required field."""
        incomplete_session: StudySessionDict = {
            'date': datetime.now().isoformat(),
            'tasks': 'Math'
            # Missing energy_level and completion_rate
        }
        with self.assertRaises(ValueError):
            self.db_manager.add_study_session(incomplete_session)

    def test_get_study_session_by_id(self):
        """Test retrieving a specific study session."""
        session: StudySessionDict = {
            'date': datetime.now().isoformat(),
            'tasks': 'Chemistry',
            'energy_level': 7,
            'completion_rate': 0.85
        }
        session_id = self.db_manager.add_study_session(session)

        retrieved = self.db_manager.get_study_session(session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['tasks'], 'Chemistry')
        self.assertEqual(retrieved['energy_level'], 7)

    def test_get_study_sessions_by_date_range(self):
        """Test retrieving study sessions within a date range."""
        now = datetime.now()

        # Add sessions across multiple days
        for i in range(3):
            session: StudySessionDict = {
                'date': (now - timedelta(days=i)).isoformat(),
                'tasks': f'Task {i}',
                'energy_level': 5 + i,
                'completion_rate': 0.8 + i * 0.05
            }
            self.db_manager.add_study_session(session)

        # Get sessions from last 1 day (should get today and yesterday)
        start = (now - timedelta(days=1)).isoformat()
        end = now.isoformat()
        sessions = self.db_manager.get_study_sessions(start_date=start, end_date=end)

        # Since we're comparing ISO formatted datetimes and times have changed,
        # we should get at least the two most recent sessions
        self.assertGreaterEqual(len(sessions), 2)

    # ==================== Task History Tests ====================

    def test_add_task_history(self):
        """Test adding a task history record."""
        task: TaskHistoryDict = {
            'task_name': 'Algebra Problem',
            'time_spent': 90,
            'difficulty_actual': 6,
            'completed_date': datetime.now().isoformat()
        }
        task_id = self.db_manager.add_task_history(task)
        self.assertIsNotNone(task_id)
        self.assertIsInstance(task_id, int)

    def test_add_task_history_with_deadline(self):
        """Test adding task history linked to a deadline."""
        # First create a deadline
        deadline: DeadlineDict = {
            'title': 'Math Assignment',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        # Add task history linked to deadline
        task: TaskHistoryDict = {
            'task_name': 'Math Problem Set',
            'deadline_id': deadline_id,
            'time_spent': 100,
            'difficulty_actual': 7,
            'completed_date': datetime.now().isoformat()
        }
        task_id = self.db_manager.add_task_history(task)
        self.assertIsNotNone(task_id)

        # Verify the link
        retrieved = self.db_manager.get_task_history()
        self.assertTrue(any(t['deadline_id'] == deadline_id for t in retrieved))

    def test_get_task_history_by_name(self):
        """Test retrieving task history by task name."""
        task_name = 'Unique Task'
        task: TaskHistoryDict = {
            'task_name': task_name,
            'time_spent': 60,
            'difficulty_actual': 5,
            'completed_date': datetime.now().isoformat()
        }
        self.db_manager.add_task_history(task)

        history = self.db_manager.get_task_history(task_name=task_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['task_name'], task_name)

    def test_get_task_history_by_deadline(self):
        """Test retrieving task history for a specific deadline."""
        deadline: DeadlineDict = {
            'title': 'Project',
            'type': 'project',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 240
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        # Add multiple tasks for this deadline
        for i in range(3):
            task: TaskHistoryDict = {
                'task_name': f'Task {i}',
                'deadline_id': deadline_id,
                'time_spent': 60 + i * 10,
                'difficulty_actual': 5 + i,
                'completed_date': (datetime.now() - timedelta(days=i)).isoformat()
            }
            self.db_manager.add_task_history(task)

        history = self.db_manager.get_task_history_by_deadline(deadline_id)
        self.assertEqual(len(history), 3)
        self.assertTrue(all(t['deadline_id'] == deadline_id for t in history))

    # ==================== Analytics Tests ====================

    def test_productivity_stats(self):
        """Test productivity statistics calculation."""
        now = datetime.now()
        start = (now - timedelta(days=7)).isoformat()
        end = now.isoformat()

        # Add sample data
        session: StudySessionDict = {
            'date': now.isoformat(),
            'tasks': 'Math, Physics',
            'energy_level': 8,
            'completion_rate': 0.95
        }
        self.db_manager.add_study_session(session)

        task: TaskHistoryDict = {
            'task_name': 'Test Task',
            'time_spent': 120,
            'difficulty_actual': 7,
            'completed_date': now.isoformat()
        }
        self.db_manager.add_task_history(task)

        stats = self.db_manager.get_productivity_stats(start, end)
        self.assertIn('study_sessions', stats)
        self.assertIn('task_history', stats)
        self.assertIn('deadlines', stats)

    # ==================== Database Maintenance Tests ====================

    def test_clear_all_data(self):
        """Test clearing all data from database."""
        # Add some data
        deadline: DeadlineDict = {
            'title': 'Test',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        self.db_manager.add_deadline(deadline)

        session: StudySessionDict = {
            'date': datetime.now().isoformat(),
            'tasks': 'Math',
            'energy_level': 8,
            'completion_rate': 0.9
        }
        self.db_manager.add_study_session(session)

        # Clear data
        result = self.db_manager.clear_all_data()
        self.assertTrue(result)

        # Verify tables are empty
        deadlines = self.db_manager.get_all_deadlines()
        sessions = self.db_manager.get_study_sessions()
        self.assertEqual(len(deadlines), 0)
        self.assertEqual(len(sessions), 0)

    def test_get_database_info(self):
        """Test getting database information."""
        # Add some data
        deadline: DeadlineDict = {
            'title': 'Test',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        self.db_manager.add_deadline(deadline)

        info = self.db_manager.get_database_info()
        self.assertIn('deadlines_count', info)
        self.assertIn('sessions_count', info)
        self.assertIn('task_history_count', info)
        self.assertIn('schema_version', info)
        self.assertEqual(info['deadlines_count'], 1)

    # ==================== Edge Cases ====================

    def test_deadline_deletion_with_task_history(self):
        """Test deadline deletion with associated task history."""
        # Add deadline and task history
        deadline: DeadlineDict = {
            'title': 'Test',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        task: TaskHistoryDict = {
            'task_name': 'Task',
            'deadline_id': deadline_id,
            'time_spent': 60,
            'difficulty_actual': 5,
            'completed_date': datetime.now().isoformat()
        }
        self.db_manager.add_task_history(task)

        # Verify task history exists before deletion
        history_before = self.db_manager.get_task_history_by_deadline(deadline_id)
        self.assertEqual(len(history_before), 1)

        # Delete deadline (cascades to delete associated task_history)
        result = self.db_manager.delete_deadline(deadline_id)
        self.assertTrue(result)

        # Verify deadline is deleted
        deadline_after = self.db_manager.get_deadline(deadline_id)
        self.assertIsNone(deadline_after)

        # Verify task history is also deleted (cascading delete)
        history_after = self.db_manager.get_task_history()
        self.assertEqual(len(history_after), 0)

    def test_empty_update(self):
        """Test updating with empty dictionary."""
        deadline: DeadlineDict = {
            'title': 'Test',
            'type': 'assignment',
            'due_date': datetime.now().isoformat(),
            'estimated_time': 120
        }
        deadline_id = self.db_manager.add_deadline(deadline)

        result = self.db_manager.update_deadline(deadline_id, {})
        self.assertFalse(result)


class TestConcurrency(unittest.TestCase):
    """Test thread safety of DatabaseManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.connect()
        self.db_manager.create_tables()

    def tearDown(self):
        """Clean up after tests."""
        self.db_manager.disconnect()
        Path(self.db_path).unlink(missing_ok=True)

    def test_thread_safety_multiple_adds(self):
        """Test thread safety with multiple concurrent adds."""
        from threading import Thread

        def add_deadline():
            for i in range(10):
                deadline: DeadlineDict = {
                    'title': f'Deadline {i}',
                    'type': 'assignment',
                    'due_date': datetime.now().isoformat(),
                    'estimated_time': 120
                }
                self.db_manager.add_deadline(deadline)

        threads = [Thread(target=add_deadline) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        deadlines = self.db_manager.get_all_deadlines()
        self.assertEqual(len(deadlines), 30)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()

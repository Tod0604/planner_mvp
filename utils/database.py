# Singleton accessor for DatabaseManager
_db_instance = None
def get_database():
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
        _db_instance.connect()
    return _db_instance
"""
SQLite persistence layer for the Study Planner application.

This module provides database management functionality including connection handling,
schema management, CRUD operations, and query optimization through indexing.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from threading import Lock

from utils.models import DeadlineDict, StudySessionDict, TaskHistoryDict


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class DatabaseManager:
    """
    Manages SQLite database operations for the Study Planner application.

    This class provides connection pooling, schema management, CRUD operations,
    and query optimization through proper indexing.

    Attributes:
        db_path (Path): Path to the SQLite database file.
        connection (sqlite3.Connection): Database connection.
        _lock (Lock): Thread lock for thread-safe operations.
    """

    # Schema version for migration tracking
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "study_planner.db"):
        """
        Initialize the DatabaseManager.

        Args:
            db_path (str): Path to the SQLite database file. Defaults to
                          'study_planner.db' in the current directory.
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._lock = Lock()
        logger.info(f"DatabaseManager initialized with db_path: {self.db_path}")

    @contextmanager
    def _get_cursor(self):
        """
        Context manager for safely getting a database cursor.

        Yields:
            sqlite3.Cursor: A database cursor.

        Raises:
            RuntimeError: If database connection is not established.
        """
        if not self.connection:
            raise RuntimeError(
                "Database connection not established. Call connect() first."
            )
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def connect(self) -> bool:
        """
        Establish a connection to the SQLite database.

        Creates the database file if it doesn't exist and enables foreign keys.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            with self._lock:
                self.connection = sqlite3.connect(
                    str(self.db_path),
                    check_same_thread=False,
                    timeout=10.0
                )
                # Enable foreign key constraints
                self.connection.execute("PRAGMA foreign_keys = ON")
                self.connection.row_factory = sqlite3.Row
                logger.info(f"Connected to database: {self.db_path}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close the database connection.

        Returns:
            bool: True if disconnection successful, False otherwise.
        """
        try:
            with self._lock:
                if self.connection:
                    self.connection.close()
                    self.connection = None
                    logger.info("Disconnected from database")
                    return True
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")
            return False
        return True

    def create_tables(self) -> bool:
        """
        Create database tables if they don't exist.

        Creates the following tables:
        - schema_version: Tracks database schema version for migrations
        - deadlines: Stores deadline information
        - study_sessions: Stores study session data
        - task_history: Stores task completion history

        Also creates indexes for query optimization.

        Returns:
            bool: True if tables created successfully, False otherwise.
        """
        if not self.connection:
            logger.error("Database connection not established")
            return False

        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    # Create schema version table for migration tracking
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS schema_version (
                            version INTEGER PRIMARY KEY,
                            migration_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            description TEXT NOT NULL
                        )
                    """)

                    # Create deadlines table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS deadlines (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            type TEXT NOT NULL CHECK(type IN ('assignment', 'exam', 'project', 'other')),
                            due_date TEXT NOT NULL,
                            estimated_time INTEGER NOT NULL CHECK(estimated_time > 0),
                            description TEXT,
                            status TEXT NOT NULL DEFAULT 'not_started' 
                                CHECK(status IN ('not_started', 'in_progress', 'completed', 'overdue')),
                            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create study_sessions table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS study_sessions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            tasks TEXT NOT NULL,
                            energy_level INTEGER NOT NULL CHECK(energy_level BETWEEN 1 AND 10),
                            completion_rate REAL NOT NULL 
                                CHECK(completion_rate BETWEEN 0.0 AND 1.0),
                            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create task_history table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS task_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            task_name TEXT NOT NULL,
                            deadline_id INTEGER,
                            time_spent INTEGER NOT NULL CHECK(time_spent > 0),
                            difficulty_actual INTEGER NOT NULL CHECK(difficulty_actual BETWEEN 1 AND 10),
                            completed_date TEXT NOT NULL,
                            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (deadline_id) REFERENCES deadlines(id) 
                                ON DELETE SET NULL
                        )
                    """)

                    # Create indexes for query optimization
                    self._create_indexes(cursor)

                    # Check and update schema version
                    cursor.execute("SELECT MAX(version) FROM schema_version")
                    result = cursor.fetchone()
                    current_version = result[0] if result[0] else 0

                    if current_version < self.SCHEMA_VERSION:
                        cursor.execute(
                            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                            (self.SCHEMA_VERSION, "Initial schema creation")
                        )
                        logger.info(f"Schema version updated to {self.SCHEMA_VERSION}")

                    self.connection.commit()
                    logger.info("Tables created successfully")
                    return True

        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            self.connection.rollback()
            return False

    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """
        Create indexes for query optimization.

        Args:
            cursor (sqlite3.Cursor): Database cursor.
        """
        indexes = [
            # Deadlines indexes
            "CREATE INDEX IF NOT EXISTS idx_deadlines_due_date ON deadlines(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_deadlines_status ON deadlines(status)",
            "CREATE INDEX IF NOT EXISTS idx_deadlines_type ON deadlines(type)",
            "CREATE INDEX IF NOT EXISTS idx_deadlines_created_at ON deadlines(created_at)",

            # Study sessions indexes
            "CREATE INDEX IF NOT EXISTS idx_sessions_date ON study_sessions(date)",

            # Task history indexes
            "CREATE INDEX IF NOT EXISTS idx_task_history_task_name ON task_history(task_name)",
            "CREATE INDEX IF NOT EXISTS idx_task_history_deadline_id ON task_history(deadline_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_history_completed_date ON task_history(completed_date)",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                logger.warning(f"Index creation warning: {e}")

    # ==================== DEADLINE OPERATIONS ====================

    def add_deadline(self, deadline: DeadlineDict) -> Optional[int]:
        """
        Add a new deadline to the database.

        Args:
            deadline (DeadlineDict): Deadline data containing title, type, due_date,
                                    estimated_time, and optional description.

        Returns:
            Optional[int]: ID of the newly created deadline, or None if failed.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = {'title', 'type', 'due_date', 'estimated_time'}
        if not required_fields.issubset(deadline.keys()):
            raise ValueError(f"Missing required fields: {required_fields - deadline.keys()}")

        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO deadlines 
                        (title, type, due_date, estimated_time, description, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            deadline['title'],
                            deadline['type'],
                            deadline['due_date'],
                            deadline['estimated_time'],
                            deadline.get('description', ''),
                            deadline.get('status', 'not_started')
                        )
                    )
                    self.connection.commit()
                    deadline_id = cursor.lastrowid
                    logger.info(f"Deadline added with ID: {deadline_id}")
                    return deadline_id

        except sqlite3.Error as e:
            logger.error(f"Error adding deadline: {e}")
            self.connection.rollback()
            return None

    def get_all_deadlines(
        self,
        status: Optional[str] = None,
        deadline_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DeadlineDict]:
        """
        Retrieve all deadlines with optional filtering.

        Args:
            status (Optional[str]): Filter by status (e.g., 'not_started', 'in_progress').
            deadline_type (Optional[str]): Filter by deadline type.
            limit (Optional[int]): Limit number of results.

        Returns:
            List[DeadlineDict]: List of deadline records.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    query = "SELECT * FROM deadlines WHERE 1=1"
                    params = []

                    if status:
                        query += " AND status = ?"
                        params.append(status)

                    if deadline_type:
                        query += " AND type = ?"
                        params.append(deadline_type)

                    query += " ORDER BY due_date ASC"

                    if limit:
                        query += " LIMIT ?"
                        params.append(limit)

                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    deadlines = [dict(row) for row in rows]
                    logger.debug(f"Retrieved {len(deadlines)} deadlines")
                    return deadlines

        except sqlite3.Error as e:
            logger.error(f"Error retrieving deadlines: {e}")
            return []

    def get_deadline(self, deadline_id: int) -> Optional[DeadlineDict]:
        """
        Retrieve a specific deadline by ID.

        Args:
            deadline_id (int): ID of the deadline.

        Returns:
            Optional[DeadlineDict]: Deadline record or None if not found.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute("SELECT * FROM deadlines WHERE id = ?", (deadline_id,))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    logger.debug(f"Deadline with ID {deadline_id} not found")
                    return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving deadline: {e}")
            return None

    def update_deadline(self, deadline_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a deadline with the provided fields.

        Args:
            deadline_id (int): ID of the deadline to update.
            updates (Dict[str, Any]): Dictionary of fields to update.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not updates:
            logger.warning("No updates provided")
            return False

        # Filter valid fields
        valid_fields = {'title', 'type', 'due_date', 'estimated_time', 'description', 'status'}
        updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not updates:
            logger.warning("No valid fields to update")
            return False

        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    # Verify deadline exists
                    cursor.execute("SELECT id FROM deadlines WHERE id = ?", (deadline_id,))
                    if not cursor.fetchone():
                        logger.warning(f"Deadline with ID {deadline_id} not found")
                        return False

                    # Build dynamic UPDATE query
                    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                    set_clause += ", updated_at = CURRENT_TIMESTAMP"
                    values = list(updates.values()) + [deadline_id]

                    cursor.execute(
                        f"UPDATE deadlines SET {set_clause} WHERE id = ?",
                        values
                    )
                    self.connection.commit()
                    logger.info(f"Deadline {deadline_id} updated successfully")
                    return True

        except sqlite3.Error as e:
            logger.error(f"Error updating deadline: {e}")
            self.connection.rollback()
            return False

    def delete_deadline(self, deadline_id: int) -> bool:
        """
        Delete a deadline and its associated task history.

        Args:
            deadline_id (int): ID of the deadline to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    # Check if deadline exists
                    cursor.execute("SELECT id FROM deadlines WHERE id = ?", (deadline_id,))
                    if not cursor.fetchone():
                        logger.warning(f"Deadline with ID {deadline_id} not found")
                        return False

                    # Delete associated task history (if any)
                    cursor.execute(
                        "DELETE FROM task_history WHERE deadline_id = ?",
                        (deadline_id,)
                    )

                    # Delete the deadline
                    cursor.execute("DELETE FROM deadlines WHERE id = ?", (deadline_id,))
                    self.connection.commit()
                    logger.info(f"Deadline {deadline_id} deleted successfully")
                    return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting deadline: {e}")
            self.connection.rollback()
            return False

    # ==================== STUDY SESSION OPERATIONS ====================

    def add_study_session(self, session: StudySessionDict) -> Optional[int]:
        """
        Add a new study session to the database.

        Args:
            session (StudySessionDict): Study session data containing date, tasks,
                                       energy_level, and completion_rate.

        Returns:
            Optional[int]: ID of the newly created session, or None if failed.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = {'date', 'tasks', 'energy_level', 'completion_rate'}
        if not required_fields.issubset(session.keys()):
            raise ValueError(f"Missing required fields: {required_fields - session.keys()}")

        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO study_sessions 
                        (date, tasks, energy_level, completion_rate, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            session['date'],
                            session['tasks'],
                            session['energy_level'],
                            session['completion_rate']
                        )
                    )
                    self.connection.commit()
                    session_id = cursor.lastrowid
                    logger.info(f"Study session added with ID: {session_id}")
                    return session_id

        except sqlite3.Error as e:
            logger.error(f"Error adding study session: {e}")
            self.connection.rollback()
            return None

    def get_study_sessions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[StudySessionDict]:
        """
        Retrieve study sessions within a date range.

        Args:
            start_date (Optional[str]): Start date in ISO format (YYYY-MM-DD HH:MM:SS).
            end_date (Optional[str]): End date in ISO format (YYYY-MM-DD HH:MM:SS).
            limit (Optional[int]): Maximum number of results to return.

        Returns:
            List[StudySessionDict]: List of study session records.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    query = "SELECT * FROM study_sessions WHERE 1=1"
                    params = []

                    if start_date:
                        query += " AND date >= ?"
                        params.append(start_date)

                    if end_date:
                        query += " AND date <= ?"
                        params.append(end_date)

                    query += " ORDER BY date DESC"

                    if limit:
                        query += " LIMIT ?"
                        params.append(limit)

                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    sessions = [dict(row) for row in rows]
                    logger.debug(f"Retrieved {len(sessions)} study sessions")
                    return sessions

        except sqlite3.Error as e:
            logger.error(f"Error retrieving study sessions: {e}")
            return []

    def get_study_session(self, session_id: int) -> Optional[StudySessionDict]:
        """
        Retrieve a specific study session by ID.

        Args:
            session_id (int): ID of the study session.

        Returns:
            Optional[StudySessionDict]: Study session record or None if not found.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM study_sessions WHERE id = ?",
                        (session_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    logger.debug(f"Study session with ID {session_id} not found")
                    return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving study session: {e}")
            return None

    # ==================== TASK HISTORY OPERATIONS ====================

    def add_task_history(self, task: TaskHistoryDict) -> Optional[int]:
        """
        Add a task completion record to history.

        Args:
            task (TaskHistoryDict): Task history data containing task_name, time_spent,
                                   difficulty_actual, completed_date, and optional deadline_id.

        Returns:
            Optional[int]: ID of the newly created task history record, or None if failed.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = {'task_name', 'time_spent', 'difficulty_actual', 'completed_date'}
        if not required_fields.issubset(task.keys()):
            raise ValueError(f"Missing required fields: {required_fields - task.keys()}")

        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO task_history 
                        (task_name, deadline_id, time_spent, difficulty_actual, completed_date, created_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            task['task_name'],
                            task.get('deadline_id'),
                            task['time_spent'],
                            task['difficulty_actual'],
                            task['completed_date']
                        )
                    )
                    self.connection.commit()
                    history_id = cursor.lastrowid
                    logger.info(f"Task history added with ID: {history_id}")
                    return history_id

        except sqlite3.Error as e:
            logger.error(f"Error adding task history: {e}")
            self.connection.rollback()
            return None

    def get_task_history(
        self,
        task_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TaskHistoryDict]:
        """
        Retrieve task history with optional filtering.

        Args:
            task_name (Optional[str]): Filter by task name.
            start_date (Optional[str]): Start date in ISO format (YYYY-MM-DD HH:MM:SS).
            end_date (Optional[str]): End date in ISO format (YYYY-MM-DD HH:MM:SS).
            limit (Optional[int]): Maximum number of results to return.

        Returns:
            List[TaskHistoryDict]: List of task history records.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    query = "SELECT * FROM task_history WHERE 1=1"
                    params = []

                    if task_name:
                        query += " AND task_name = ?"
                        params.append(task_name)

                    if start_date:
                        query += " AND completed_date >= ?"
                        params.append(start_date)

                    if end_date:
                        query += " AND completed_date <= ?"
                        params.append(end_date)

                    query += " ORDER BY completed_date DESC"

                    if limit:
                        query += " LIMIT ?"
                        params.append(limit)

                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    tasks = [dict(row) for row in rows]
                    logger.debug(f"Retrieved {len(tasks)} task history records")
                    return tasks

        except sqlite3.Error as e:
            logger.error(f"Error retrieving task history: {e}")
            return []

    def get_task_history_by_deadline(self, deadline_id: int) -> List[TaskHistoryDict]:
        """
        Retrieve all task history records for a specific deadline.

        Args:
            deadline_id (int): ID of the deadline.

        Returns:
            List[TaskHistoryDict]: List of task history records.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM task_history WHERE deadline_id = ? ORDER BY completed_date DESC",
                        (deadline_id,)
                    )
                    rows = cursor.fetchall()
                    tasks = [dict(row) for row in rows]
                    return tasks

        except sqlite3.Error as e:
            logger.error(f"Error retrieving task history by deadline: {e}")
            return []

    # ==================== ANALYTICS OPERATIONS ====================

    def get_productivity_stats(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Calculate productivity statistics for a date range.

        Args:
            start_date (str): Start date in ISO format (YYYY-MM-DD HH:MM:SS).
            end_date (str): End date in ISO format (YYYY-MM-DD HH:MM:SS).

        Returns:
            Dict[str, Any]: Dictionary containing productivity metrics.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    # Total study sessions
                    cursor.execute(
                        """
                        SELECT COUNT(*) as total_sessions, 
                               AVG(energy_level) as avg_energy,
                               AVG(completion_rate) as avg_completion
                        FROM study_sessions
                        WHERE date BETWEEN ? AND ?
                        """,
                        (start_date, end_date)
                    )
                    session_stats = dict(cursor.fetchone())

                    # Task completion stats
                    cursor.execute(
                        """
                        SELECT COUNT(*) as total_tasks,
                               SUM(time_spent) as total_time,
                               AVG(difficulty_actual) as avg_difficulty
                        FROM task_history
                        WHERE completed_date BETWEEN ? AND ?
                        """,
                        (start_date, end_date)
                    )
                    task_stats = dict(cursor.fetchone())

                    # Deadline completion rate
                    cursor.execute(
                        """
                        SELECT 
                            COUNT(*) as total_deadlines,
                            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_deadlines
                        FROM deadlines
                        WHERE created_at BETWEEN ? AND ?
                        """,
                        (start_date, end_date)
                    )
                    deadline_stats = dict(cursor.fetchone())

                    return {
                        'study_sessions': session_stats,
                        'task_history': task_stats,
                        'deadlines': deadline_stats
                    }

        except sqlite3.Error as e:
            logger.error(f"Error calculating productivity stats: {e}")
            return {}

    # ==================== DATABASE MAINTENANCE ====================

    def clear_all_data(self) -> bool:
        """
        Clear all data from tables (for testing purposes only).

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    cursor.execute("DELETE FROM task_history")
                    cursor.execute("DELETE FROM study_sessions")
                    cursor.execute("DELETE FROM deadlines")
                    self.connection.commit()
                    logger.warning("All data cleared from database")
                    return True

        except sqlite3.Error as e:
            logger.error(f"Error clearing database: {e}")
            self.connection.rollback()
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database statistics and information.

        Returns:
            Dict[str, Any]: Database statistics.
        """
        try:
            with self._lock:
                with self._get_cursor() as cursor:
                    stats = {}

                    # Count records in each table
                    cursor.execute("SELECT COUNT(*) FROM deadlines")
                    stats['deadlines_count'] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM study_sessions")
                    stats['sessions_count'] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM task_history")
                    stats['task_history_count'] = cursor.fetchone()[0]

                    # Get schema version
                    cursor.execute("SELECT MAX(version) FROM schema_version")
                    result = cursor.fetchone()
                    stats['schema_version'] = result[0] if result[0] else 0

                    # Get database file size
                    if self.db_path.exists():
                        stats['db_file_size_bytes'] = self.db_path.stat().st_size

                    return stats

        except sqlite3.Error as e:
            logger.error(f"Error getting database info: {e}")
            return {}

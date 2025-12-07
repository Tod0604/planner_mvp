"""
Calendar and Plan Persistence Layer

Stores daily plans, feedback, and metrics to enable:
- Per-date plan retrieval
- Time allocation tracking
- Feedback collection and analysis
- Model retraining with real data
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from threading import Lock


class CalendarStore:
    """Thread-safe SQLite-based calendar and plan storage."""

    def __init__(self, db_path: str = "study_plans.db"):
        """Initialize calendar store with SQLite database."""
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Table: daily_plans
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_plans (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL UNIQUE,
                    plan_json TEXT NOT NULL,
                    available_minutes INTEGER,
                    total_planned_minutes INTEGER,
                    num_tasks INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table: daily_feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_feedback (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL UNIQUE,
                    completion_ratio REAL CHECK(completion_ratio BETWEEN 0.0 AND 1.0),
                    tiredness_end_of_day INTEGER CHECK(tiredness_end_of_day BETWEEN 1 AND 5),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (date) REFERENCES daily_plans(date)
                )
            """)

            # Table: plan_metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plan_metrics (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, metric_name),
                    FOREIGN KEY (date) REFERENCES daily_plans(date)
                )
            """)

            # Create indexes for efficient queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_plans(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_date ON daily_feedback(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON plan_metrics(date)")

            conn.commit()
            conn.close()

    def save_plan(
        self,
        date: str,
        plan: Dict[str, Any],
        available_minutes: int,
        metrics: Optional[Dict[str, float]] = None,
    ) -> bool:
        """
        Save a daily plan with metadata.

        Args:
            date: ISO format date string (YYYY-MM-DD)
            plan: Plan dictionary from generate_plan()
            available_minutes: Minutes available for study that day
            metrics: Optional dict of metrics (e.g., energy_level, productivity_score)

        Returns:
            True if saved successfully
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Extract metrics from plan
                total_planned_minutes = sum(plan.get("recommended_minutes", []))
                num_tasks = len(plan.get("ranked_tasks", []))

                # Insert or update plan
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO daily_plans
                    (date, plan_json, available_minutes, total_planned_minutes, num_tasks, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (date, json.dumps(plan), available_minutes, total_planned_minutes, num_tasks),
                )

                # Save metrics if provided
                if metrics:
                    for metric_name, metric_value in metrics.items():
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO plan_metrics (date, metric_name, metric_value)
                            VALUES (?, ?, ?)
                            """,
                            (date, metric_name, metric_value),
                        )

                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Error saving plan: {e}")
                return False

    def get_plan(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a saved plan for a specific date.

        Args:
            date: ISO format date string (YYYY-MM-DD)

        Returns:
            Plan dict or None if not found
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT plan_json FROM daily_plans WHERE date = ?", (date,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    return json.loads(row[0])
                return None
            except Exception as e:
                print(f"Error retrieving plan: {e}")
                return None

    def save_feedback(
        self,
        date: str,
        completion_ratio: float,
        tiredness_end_of_day: int,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Save daily feedback after plan execution.

        Args:
            date: ISO format date string (YYYY-MM-DD)
            completion_ratio: 0.0-1.0 ratio of plan completion
            tiredness_end_of_day: 1-5 scale of tiredness
            notes: Optional feedback notes

        Returns:
            True if saved successfully
        """
        if not (0.0 <= completion_ratio <= 1.0):
            print("Error: completion_ratio must be between 0.0 and 1.0")
            return False

        if not (1 <= tiredness_end_of_day <= 5):
            print("Error: tiredness_end_of_day must be between 1 and 5")
            return False

        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO daily_feedback
                    (date, completion_ratio, tiredness_end_of_day, notes, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (date, completion_ratio, tiredness_end_of_day, notes),
                )

                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Error saving feedback: {e}")
                return False

    def get_feedback(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve feedback for a specific date.

        Args:
            date: ISO format date string (YYYY-MM-DD)

        Returns:
            Feedback dict or None if not found
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT completion_ratio, tiredness_end_of_day, notes FROM daily_feedback WHERE date = ?",
                    (date,),
                )
                row = cursor.fetchone()
                conn.close()

                if row:
                    return {
                        "completion_ratio": row[0],
                        "tiredness_end_of_day": row[1],
                        "notes": row[2],
                    }
                return None
            except Exception as e:
                print(f"Error retrieving feedback: {e}")
                return None

    def list_plans(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        List all plans within a date range.

        Args:
            start_date: ISO format date string (YYYY-MM-DD)
            end_date: ISO format date string (YYYY-MM-DD)

        Returns:
            List of plan summaries
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT date, available_minutes, total_planned_minutes, num_tasks, created_at
                    FROM daily_plans
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date ASC
                    """,
                    (start_date, end_date),
                )

                rows = cursor.fetchall()
                conn.close()

                return [
                    {
                        "date": row[0],
                        "available_minutes": row[1],
                        "total_planned_minutes": row[2],
                        "num_tasks": row[3],
                        "created_at": row[4],
                    }
                    for row in rows
                ]
            except Exception as e:
                print(f"Error listing plans: {e}")
                return []

    def get_plan_with_feedback(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve plan + feedback for a specific date.

        Args:
            date: ISO format date string (YYYY-MM-DD)

        Returns:
            Combined dict with plan and feedback or None
        """
        plan = self.get_plan(date)
        feedback = self.get_feedback(date)

        if not plan:
            return None

        return {
            "date": date,
            "plan": plan,
            "feedback": feedback,
        }

    def get_feedback_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get feedback for all dates in range.

        Args:
            start_date: ISO format date string (YYYY-MM-DD)
            end_date: ISO format date string (YYYY-MM-DD)

        Returns:
            List of feedback records with dates
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT date, completion_ratio, tiredness_end_of_day, notes
                    FROM daily_feedback
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date ASC
                    """,
                    (start_date, end_date),
                )

                rows = cursor.fetchall()
                conn.close()

                return [
                    {
                        "date": row[0],
                        "completion_ratio": row[1],
                        "tiredness_end_of_day": row[2],
                        "notes": row[3],
                    }
                    for row in rows
                ]
            except Exception as e:
                print(f"Error retrieving feedback range: {e}")
                return []

    def delete_plan(self, date: str) -> bool:
        """Delete plan for a specific date."""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM daily_plans WHERE date = ?", (date,))
                cursor.execute("DELETE FROM daily_feedback WHERE date = ?", (date,))
                cursor.execute("DELETE FROM plan_metrics WHERE date = ?", (date,))

                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Error deleting plan: {e}")
                return False

    def export_data(self, output_path: str) -> bool:
        """
        Export all plans and feedback to JSON for analysis.

        Args:
            output_path: Path to export JSON file

        Returns:
            True if exported successfully
        """
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get all plans
                cursor.execute("SELECT date, plan_json, available_minutes FROM daily_plans ORDER BY date")
                plans = cursor.fetchall()

                # Get all feedback
                cursor.execute(
                    "SELECT date, completion_ratio, tiredness_end_of_day, notes FROM daily_feedback"
                )
                feedback_rows = cursor.fetchall()
                conn.close()

                # Combine data
                export_data = {
                    "plans": [
                        {
                            "date": row[0],
                            "plan": json.loads(row[1]),
                            "available_minutes": row[2],
                        }
                        for row in plans
                    ],
                    "feedback": [
                        {
                            "date": row[0],
                            "completion_ratio": row[1],
                            "tiredness_end_of_day": row[2],
                            "notes": row[3],
                        }
                        for row in feedback_rows
                    ],
                    "export_date": datetime.now().isoformat(),
                }

                with open(output_path, "w") as f:
                    json.dump(export_data, f, indent=2)

                return True
            except Exception as e:
                print(f"Error exporting data: {e}")
                return False


# Singleton instance
_calendar_store: Optional[CalendarStore] = None


def get_calendar_store() -> CalendarStore:
    """Get or create the singleton CalendarStore instance."""
    global _calendar_store
    if _calendar_store is None:
        _calendar_store = CalendarStore()
    return _calendar_store

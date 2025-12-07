"""
Data models for the Study Planner application.

This module defines TypedDict models for type hints and documentation purposes,
ensuring consistent data structures across the application.
"""

from typing import TypedDict, Optional, List
from datetime import datetime


class DeadlineDict(TypedDict, total=False):
    """Type definition for a deadline record."""

    id: int
    title: str
    type: str  # e.g., 'assignment', 'exam', 'project'
    due_date: str  # ISO format: YYYY-MM-DD HH:MM:SS
    estimated_time: int  # in minutes
    description: str
    status: str  # e.g., 'not_started', 'in_progress', 'completed', 'overdue'
    created_at: str  # ISO format: YYYY-MM-DD HH:MM:SS
    updated_at: str  # ISO format: YYYY-MM-DD HH:MM:SS


class StudySessionDict(TypedDict, total=False):
    """Type definition for a study session record."""

    id: int
    date: str  # ISO format: YYYY-MM-DD HH:MM:SS
    tasks: str  # JSON string or comma-separated task names
    energy_level: int  # 1-10 scale
    completion_rate: float  # 0.0-1.0 (percentage)
    created_at: str  # ISO format: YYYY-MM-DD HH:MM:SS
    updated_at: str  # ISO format: YYYY-MM-DD HH:MM:SS


class TaskHistoryDict(TypedDict, total=False):
    """Type definition for a task history record."""

    id: int
    task_name: str
    deadline_id: Optional[int]
    time_spent: int  # in minutes
    difficulty_actual: int  # 1-10 scale
    completed_date: str  # ISO format: YYYY-MM-DD HH:MM:SS
    created_at: str  # ISO format: YYYY-MM-DD HH:MM:SS


class DatabaseSchemaVersion(TypedDict, total=False):
    """Type definition for schema version tracking."""

    version: int
    migration_date: str  # ISO format: YYYY-MM-DD HH:MM:SS
    description: str

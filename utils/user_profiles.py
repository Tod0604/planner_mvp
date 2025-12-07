"""
User Profiles & Personalization Module

Manages multiple user profiles with individual learning preferences,
time tracking data, and personalized analytics.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from threading import Lock
from pathlib import Path
import hashlib
import secrets


class UserProfileManager:
    """Manages user profiles, preferences, and time tracking data"""
    
    def __init__(self, db_path: str = "study_planner.db"):
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables for user profiles and time tracking"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    learning_goal TEXT,
                    education_level TEXT,
                    subject_area TEXT,
                    preferred_session_duration INTEGER,
                    password_hash TEXT,
                    password_salt TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferred_start_time TEXT,
                    preferred_end_time TEXT,
                    best_study_hours TEXT,
                    break_frequency_minutes INTEGER,
                    focus_level_1_5 INTEGER,
                    subjects_of_interest TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Time tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_tracking (
                    tracking_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    clock_in_time TEXT NOT NULL,
                    clock_out_time TEXT,
                    duration_minutes INTEGER,
                    difficulty_rating INTEGER,
                    notes TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # User analytics table (for caching calculations)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_analytics (
                    user_id TEXT PRIMARY KEY,
                    avg_session_duration INTEGER,
                    most_productive_hour TEXT,
                    productivity_score REAL,
                    total_study_hours REAL,
                    favorite_subjects TEXT,
                    last_updated TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """Hash a password with a random salt using PBKDF2
        
        Returns:
            Tuple of (password_hash, salt) both as hex strings
        """
        salt = secrets.token_bytes(32)
        # Use PBKDF2 with 100,000 iterations (NIST recommendation)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return password_hash.hex(), salt.hex()
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash and salt
        
        Args:
            password: The password to verify
            password_hash: The stored password hash (hex string)
            salt: The stored salt (hex string)
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            salt_bytes = bytes.fromhex(salt)
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt_bytes,
                100000
            )
            return computed_hash.hex() == password_hash
        except (ValueError, AttributeError):
            return False
    
    def create_user(self, user_id: str, name: str, learning_goal: str = "", 
                   preferred_session_duration: int = 60, email: str = None,
                   education_level: str = None, subject_area: str = None,
                   password: str = None) -> Dict:
        """Create a new user profile
        
        Args:
            user_id: Unique user identifier
            name: User's display name
            learning_goal: Optional learning goal
            preferred_session_duration: Preferred study session length in minutes
            email: Optional email address (must be unique)
            education_level: Optional education level (High School, University, Professional)
            subject_area: Optional subject area of interest
            password: Optional password for account security
            
        Returns:
            Dictionary with status and user_id or error message
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            password_hash = None
            password_salt = None
            
            # Hash password if provided
            if password:
                password_hash, password_salt = self.hash_password(password)
            
            try:
                cursor.execute('''
                    INSERT INTO users (user_id, name, email, learning_goal, 
                                     education_level, subject_area,
                                     preferred_session_duration, password_hash, 
                                     password_salt, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, name, email, learning_goal, education_level, subject_area,
                      preferred_session_duration, password_hash, password_salt, now, now))
                
                # Initialize preferences
                cursor.execute('''
                    INSERT INTO user_preferences (user_id, break_frequency_minutes, focus_level_1_5)
                    VALUES (?, ?, ?)
                ''', (user_id, 5, 3))
                
                conn.commit()
                return {"status": "success", "user_id": user_id, "name": name}
            except sqlite3.IntegrityError as e:
                error_msg = str(e)
                if "email" in error_msg.lower():
                    return {"status": "error", "message": f"Email {email} already exists"}
                else:
                    return {"status": "error", "message": f"User {user_id} already exists"}
            finally:
                conn.close()

    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user profile details"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            return dict(user) if user else None
    
    def get_all_users(self) -> List[Dict]:
        """Get all user profiles"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id, name, learning_goal FROM users ORDER BY updated_at DESC')
            users = cursor.fetchall()
            conn.close()
            
            return [dict(u) for u in users]
    
    def update_user_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Update user learning preferences"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            for key, value in preferences.items():
                if key in ['best_study_hours', 'subjects_of_interest']:
                    value = json.dumps(value) if isinstance(value, (list, dict)) else value
                update_fields.append(f"{key} = ?")
                params.append(value)
            
            params.append(user_id)
            
            try:
                cursor.execute(f'''
                    UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = ?
                ''', params)
                conn.commit()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
            finally:
                conn.close()
    
    def clock_in(self, user_id: str, task_name: str, date: str = None) -> Dict:
        """Clock in for a task"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            tracking_id = f"{user_id}_{task_name}_{datetime.now().timestamp()}"
            
            try:
                cursor.execute('''
                    INSERT INTO time_tracking 
                    (tracking_id, user_id, task_name, date, clock_in_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tracking_id, user_id, task_name, date, now))
                
                conn.commit()
                return {
                    "status": "success",
                    "tracking_id": tracking_id,
                    "task_name": task_name,
                    "clock_in_time": now
                }
            finally:
                conn.close()
    
    def clock_out(self, user_id: str, tracking_id: str, 
                 difficulty_rating: int = None, notes: str = "") -> Dict:
        """Clock out from a task"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            clock_out_time = datetime.now().isoformat()
            
            # Get clock in time
            cursor.execute('''
                SELECT clock_in_time FROM time_tracking WHERE tracking_id = ? AND user_id = ?
            ''', (tracking_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                return {"status": "error", "message": "Tracking record not found"}
            
            clock_in_str = result[0]
            clock_in = datetime.fromisoformat(clock_in_str)
            clock_out = datetime.fromisoformat(clock_out_time)
            duration_minutes = int((clock_out - clock_in).total_seconds() / 60)
            
            try:
                cursor.execute('''
                    UPDATE time_tracking 
                    SET clock_out_time = ?, duration_minutes = ?, difficulty_rating = ?, notes = ?
                    WHERE tracking_id = ? AND user_id = ?
                ''', (clock_out_time, duration_minutes, difficulty_rating, notes, tracking_id, user_id))
                
                conn.commit()
                return {
                    "status": "success",
                    "tracking_id": tracking_id,
                    "duration_minutes": duration_minutes,
                    "clock_out_time": clock_out_time
                }
            finally:
                conn.close()
    
    def get_active_clock_in(self, user_id: str) -> Optional[Dict]:
        """Get currently active clock-in session"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT tracking_id, task_name, clock_in_time, date
                FROM time_tracking 
                WHERE user_id = ? AND clock_out_time IS NULL
                ORDER BY clock_in_time DESC LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return dict(result) if result else None
    
    def get_time_tracking_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get user's time tracking history"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT tracking_id, task_name, date, clock_in_time, clock_out_time,
                       duration_minutes, difficulty_rating, notes
                FROM time_tracking 
                WHERE user_id = ? AND date >= ? AND clock_out_time IS NOT NULL
                ORDER BY date DESC, clock_in_time DESC
            ''', (user_id, start_date))
            
            records = cursor.fetchall()
            conn.close()
            
            return [dict(r) for r in records]
    
    def calculate_analytics(self, user_id: str) -> Dict:
        """Calculate personalized analytics for user"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get completed sessions
            cursor.execute('''
                SELECT duration_minutes, clock_in_time, difficulty_rating
                FROM time_tracking 
                WHERE user_id = ? AND clock_out_time IS NOT NULL
            ''', (user_id,))
            
            sessions = cursor.fetchall()
            
            if not sessions:
                conn.close()
                return {
                    "status": "insufficient_data",
                    "message": "Not enough data to calculate analytics"
                }
            
            sessions_list = [dict(s) for s in sessions]
            
            # Calculate average session duration
            avg_duration = sum(s['duration_minutes'] for s in sessions_list) / len(sessions_list)
            
            # Find most productive hour
            hour_counts = {}
            for session in sessions_list:
                clock_in = datetime.fromisoformat(session['clock_in_time'])
                hour = f"{clock_in.hour:02d}:00"
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            most_productive_hour = max(hour_counts, key=hour_counts.get) if hour_counts else "N/A"
            
            # Calculate productivity score (0-100)
            avg_difficulty = sum(s['difficulty_rating'] or 0 for s in sessions_list) / len(sessions_list)
            productivity_score = min(100, (avg_duration / 60) * 50 + (5 - avg_difficulty) * 10)
            
            # Total study hours
            total_minutes = sum(s['duration_minutes'] for s in sessions_list)
            total_hours = total_minutes / 60
            
            # Get favorite subjects (most tracked tasks)
            cursor.execute('''
                SELECT task_name, COUNT(*) as count
                FROM time_tracking 
                WHERE user_id = ? AND clock_out_time IS NOT NULL
                GROUP BY task_name
                ORDER BY count DESC LIMIT 3
            ''', (user_id,))
            
            favorite_tasks = cursor.fetchall()
            favorite_subjects = json.dumps([dict(t)['task_name'] for t in favorite_tasks])
            
            analytics = {
                "status": "success",
                "avg_session_duration": round(avg_duration, 1),
                "most_productive_hour": most_productive_hour,
                "productivity_score": round(productivity_score, 1),
                "total_study_hours": round(total_hours, 1),
                "favorite_subjects": json.loads(favorite_subjects),
                "session_count": len(sessions_list)
            }
            
            # Update analytics cache
            cursor.execute('''
                INSERT OR REPLACE INTO user_analytics 
                (user_id, avg_session_duration, most_productive_hour, productivity_score,
                 total_study_hours, favorite_subjects, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, analytics['avg_session_duration'], most_productive_hour,
                  analytics['productivity_score'], analytics['total_study_hours'],
                  favorite_subjects, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return analytics
    
    def get_personalized_insights(self, user_id: str) -> Dict:
        """Get personalized insights and recommendations"""
        analytics = self.calculate_analytics(user_id)
        
        if analytics.get('status') != 'success':
            return analytics
        
        insights = {
            "status": "success",
            "insights": []
        }
        
        # Best time insight
        if analytics['most_productive_hour'] != 'N/A':
            end_hour = int(analytics['most_productive_hour'].split(':')[0]) + 2
            insights['insights'].append({
                "type": "best_time",
                "title": "Your Best Study Time",
                "message": f"Your most productive study time is around {analytics['most_productive_hour']}. "
                          f"We recommend scheduling important tasks during {analytics['most_productive_hour']}—{end_hour:02d}:00.",
                "metric": analytics['most_productive_hour']
            })
        
        # Session duration insight
        insights['insights'].append({
            "type": "session_duration",
            "title": "Preferred Session Length",
            "message": f"Your typical study session lasts {analytics['avg_session_duration']:.0f} minutes. "
                      f"Consider planning tasks that fit this timeframe.",
            "metric": f"{analytics['avg_session_duration']:.0f} min"
        })
        
        # Productivity trend
        if analytics['productivity_score'] >= 70:
            insights['insights'].append({
                "type": "productivity",
                "title": "Strong Productivity Pattern",
                "message": "You're maintaining strong study habits! Keep up the consistency.",
                "metric": f"{analytics['productivity_score']:.0f}/100"
            })
        elif analytics['productivity_score'] >= 50:
            insights['insights'].append({
                "type": "productivity",
                "title": "Moderate Productivity",
                "message": "Try increasing session duration or reducing difficulty spikes for better results.",
                "metric": f"{analytics['productivity_score']:.0f}/100"
            })
        
        # Favorite subjects
        if analytics['favorite_subjects']:
            insights['insights'].append({
                "type": "favorites",
                "title": "Your Focus Areas",
                "message": f"You spend most time on: {', '.join(analytics['favorite_subjects'][:2])}",
                "metric": ", ".join(analytics['favorite_subjects'][:2])
            })
        
        # Study hours milestone
        insights['insights'].append({
            "type": "study_hours",
            "title": "Total Study Hours",
            "message": f"You've completed {analytics['total_study_hours']:.1f} hours of focused study.",
            "metric": f"{analytics['total_study_hours']:.1f}h"
        })
        
        return insights


# Singleton accessor
_user_manager: Optional[UserProfileManager] = None

def get_user_profile_manager() -> UserProfileManager:
    """Get or create singleton UserProfileManager"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserProfileManager()
    return _user_manager

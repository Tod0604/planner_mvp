"""
Intelligent Planning Engine - Integrates deadlines with task planning.

This module provides deadline-aware planning capabilities that:
1. Extract tasks from upcoming deadlines
2. Suggest task priorities based on deadline urgency
3. Detect schedule conflicts
4. Track deadline progress
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
from utils.database import get_database
from utils.models import DeadlineDict, TaskHistoryDict

logger = logging.getLogger(__name__)


class DeadlineTask:
    """Represents a task extracted from a deadline."""
    
    def __init__(self, deadline_id: int, title: str, due_date: str, 
                 estimated_time: int, urgency_score: float, type: str = 'other', days_until: int = 0):
        self.deadline_id = deadline_id
        self.title = title
        self.due_date = due_date
        self.estimated_time = estimated_time
        self.urgency_score = urgency_score
        self.type = type
        self.days_until = days_until
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'deadline_id': self.deadline_id,
            'title': self.title,
            'due_date': self.due_date,
            'estimated_time': self.estimated_time,
            'urgency_score': self.urgency_score,
            'type': self.type,
            'days_until': self.days_until
        }


class IntelligentPlanner:
    """Intelligent planning engine with deadline integration."""
    
    def __init__(self):
        self.db = get_database()
    
    # ==================== DEADLINE ANALYSIS ====================
    
    def calculate_urgency_score(self, due_date_str: str, estimated_time: int) -> float:
        """Calculate urgency score for a deadline (0-1 scale).
        
        Factors considered:
        - Days until due date
        - Estimated time required
        
        Args:
            due_date_str: Due date in YYYY-MM-DD format
            estimated_time: Estimated time in minutes
            
        Returns:
            Urgency score between 0 and 1
        """
        try:
            # Handle both date-only and datetime formats
            if "T" in due_date_str:
                due_date = datetime.strptime(due_date_str.split("T")[0], '%Y-%m-%d').date()
            else:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            days_until = (due_date - today).days
            
            # If overdue, maximum urgency
            if days_until < 0:
                return 1.0
            
            # Calculate based on days_until and estimated_time
            # More days = lower urgency, less days = higher urgency
            # More time required = higher urgency to start sooner
            
            days_factor = max(0, min(1.0, 1.0 / (days_until + 1)))
            time_factor = min(1.0, estimated_time / 480)  # Normalize to 8 hours
            
            urgency = (days_factor * 0.7) + (time_factor * 0.3)
            return min(1.0, urgency)
        except Exception as e:
            logger.error(f"Error calculating urgency score: {e}")
            return 0.5
    
    def get_urgent_deadlines(self, days_ahead: int = 7) -> List[DeadlineTask]:
        """Get urgent deadlines within the next N days.
        
        Args:
            days_ahead: Number of days to look ahead (default: 7)
            
        Returns:
            List of DeadlineTask objects sorted by urgency
        """
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        # Get all non-completed deadlines
        all_deadlines = self.db.get_all_deadlines()
        
        deadline_tasks = []
        for deadline in all_deadlines:
            if deadline['status'] != 'completed':
                # Check if due date is within the range
                try:
                    due_date_str = deadline['due_date']
                    if "T" in due_date_str:
                        due_date = datetime.strptime(due_date_str.split("T")[0], "%Y-%m-%d").date()
                    else:
                        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    
                    if today <= due_date <= future_date:
                        urgency = self.calculate_urgency_score(
                            deadline['due_date'],
                            deadline['estimated_time']
                        )
                        task = DeadlineTask(
                            deadline_id=deadline['id'],
                            title=deadline['title'],
                            due_date=deadline['due_date'],
                            estimated_time=deadline['estimated_time'],
                            urgency_score=urgency,
                            type=deadline.get('type', 'other'),
                            days_until=(due_date - today).days
                        )
                        deadline_tasks.append(task)
                except Exception as e:
                    logger.error(f"Error processing deadline {deadline.get('id')}: {e}")
        
        # Sort by urgency score (descending)
        deadline_tasks.sort(key=lambda x: x.urgency_score, reverse=True)
        return deadline_tasks
    
    def get_deadline_recommendations(self, available_minutes: int) -> List[Dict[str, Any]]:
        """Get recommended tasks based on deadlines and available time.
        
        Args:
            available_minutes: Available study time in minutes
            
        Returns:
            List of recommended tasks
        """
        urgent_tasks = self.get_urgent_deadlines()
        recommendations = []
        total_time = 0
        
        for task in urgent_tasks:
            if total_time + task.estimated_time <= available_minutes:
                recommendations.append({
                    'task': task.title,
                    'deadline_id': task.deadline_id,
                    'estimated_time': task.estimated_time,
                    'urgency_score': task.urgency_score,
                    'due_date': task.due_date
                })
                total_time += task.estimated_time
            elif total_time < available_minutes:
                # Add partial time if there's remaining time
                remaining = available_minutes - total_time
                if remaining >= 30:  # Minimum 30 minutes
                    recommendations.append({
                        'task': task.title,
                        'deadline_id': task.deadline_id,
                        'estimated_time': remaining,
                        'urgency_score': task.urgency_score,
                        'due_date': task.due_date,
                        'partial': True
                    })
                break
        
        return recommendations
    
    # ==================== SCHEDULE ANALYSIS ====================
    
    def detect_schedule_conflicts(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Detect days with too many deadlines or insufficient study time.
        
        Args:
            days_ahead: Number of days to analyze
            
        Returns:
            List of conflict records with day, deadline count, total time required
        """
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        # Get all deadlines
        all_deadlines = self.db.get_all_deadlines()
        
        # Group by due date
        by_date = {}
        for deadline in all_deadlines:
            try:
                due_date_str = deadline['due_date']
                if "T" in due_date_str:
                    due_date = datetime.strptime(due_date_str.split("T")[0], "%Y-%m-%d").date()
                else:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                
                if today <= due_date <= future_date and deadline['status'] != 'completed':
                    date_key = due_date.isoformat()
                    if date_key not in by_date:
                        by_date[date_key] = []
                    by_date[date_key].append(deadline)
            except Exception as e:
                logger.error(f"Error processing deadline for conflict detection: {e}")
                continue
        
        # Find conflicts (multiple deadlines on same day or high total time)
        conflicts = []
        for due_date, items in by_date.items():
            if len(items) > 1 or sum(d['estimated_time'] for d in items) > 480:
                conflict = {
                    'date': due_date,
                    'deadline_count': len(items),
                    'total_estimated_time': sum(d['estimated_time'] for d in items),
                    'deadlines': [d['title'] for d in items],
                    'severity': 'high' if len(items) > 2 else 'medium'
                }
                conflicts.append(conflict)
        
        return conflicts
    
    # ==================== TASK-DEADLINE TRACKING ====================
    
    def link_task_to_deadline(self, task_name: str, deadline_id: int, 
                             time_spent: int, difficulty_actual: int,
                             completed: bool = False) -> int:
        """Link a completed task to its deadline.
        
        Args:
            task_name: Name of the task
            deadline_id: ID of the related deadline
            time_spent: Actual time spent in minutes
            difficulty_actual: Actual difficulty (1-10)
            completed: Whether task is completed
            
        Returns:
            history_id of the recorded task
        """
        task_history: TaskHistoryDict = {
            'task_name': task_name,
            'deadline_id': deadline_id,
            'time_spent': time_spent,
            'difficulty_actual': difficulty_actual,
            'completed_date': datetime.now().isoformat(),
            'status': 'completed' if completed else 'in_progress'
        }
        return self.db.add_task_history(task_history)
    
    def get_deadline_progress(self, deadline_id: int) -> Dict[str, Any]:
        """Get completion progress for a deadline.
        
        Args:
            deadline_id: ID of the deadline
            
        Returns:
            Dictionary with progress metrics
        """
        try:
            deadline = self.db.get_deadline(deadline_id)
            if not deadline:
                return {'completion_percent': 0, 'completed_tasks': 0, 'total_tasks': 0}
            
            tasks = self.db.get_task_history_by_deadline(deadline_id)
            
            # Task history records represent completed tasks
            total_time_spent = sum(t.get('time_spent', 0) for t in tasks) if tasks else 0
            avg_difficulty = (sum(t.get('difficulty_actual', 0) for t in tasks) / len(tasks)) if tasks else 0
            
            return {
                'deadline_id': deadline_id,
                'title': deadline.get('title', 'Unknown'),
                'total_tasks': len(tasks) if tasks else 0,
                'completed_tasks': len(tasks) if tasks else 0,
                'completion_percent': (100 if tasks else 0),
                'total_time_spent': total_time_spent,
                'avg_difficulty': avg_difficulty
            }
        except Exception as e:
            logger.error(f"Error getting deadline progress for {deadline_id}: {e}")
            return {'completion_percent': 0, 'completed_tasks': 0, 'total_tasks': 0}
    
    # ==================== PLANNING INTEGRATION ====================
    
    def enhance_plan_with_deadlines(self, user_plan: Dict[str, Any], 
                                   available_minutes: int) -> Dict[str, Any]:
        """Enhance a user plan with deadline-aware recommendations.
        
        Args:
            user_plan: Original plan from main.py
            available_minutes: Available study time
            
        Returns:
            Enhanced plan with deadline recommendations
        """
        deadline_recommendations = self.get_deadline_recommendations(available_minutes)
        conflicts = self.detect_schedule_conflicts(days_ahead=7)
        
        # Add deadline context to plan
        user_plan['deadline_recommendations'] = deadline_recommendations
        user_plan['schedule_conflicts'] = conflicts
        user_plan['urgent_deadlines'] = [
            t.to_dict() for t in self.get_urgent_deadlines(days_ahead=3)
        ]
        
        # Generate deadline-aware summary
        if deadline_recommendations:
            deadline_names = ', '.join([r['task'] for r in deadline_recommendations[:3]])
            summary = f"Focus on upcoming deadlines: {deadline_names}. "
            summary += user_plan.get('summary', '')
            user_plan['summary'] = summary
        
        return user_plan
    
    # ==================== STATISTICS ====================
    
    def get_deadline_statistics(self) -> Dict[str, Any]:
        """Get overall deadline statistics.
        
        Returns:
            Dictionary with deadline metrics
        """
        all_deadlines = self.db.get_all_deadlines()
        
        total = len(all_deadlines)
        completed = sum(1 for d in all_deadlines if d['status'] == 'completed')
        in_progress = sum(1 for d in all_deadlines if d['status'] == 'in_progress')
        not_started = sum(1 for d in all_deadlines if d['status'] == 'not_started')
        
        return {
            'total_deadlines': total,
            'completed': completed,
            'in_progress': in_progress,
            'not_started': not_started,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def get_productivity_report(self, days: int = 30) -> Dict[str, Any]:
        """Get productivity report for the past N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with productivity metrics
        """
        stats = self.get_deadline_statistics()
        
        return {
            'period_days': days,
            'total_deadlines': stats.get('total_deadlines', 0),
            'completed_deadlines': stats.get('completed', 0),
            'completion_rate': stats.get('completion_rate', 0),
            'deadline_stats': stats
        }


# Singleton instance
_planner = None


def get_intelligent_planner() -> IntelligentPlanner:
    """Get or create singleton intelligent planner instance."""
    global _planner
    if _planner is None:
        _planner = IntelligentPlanner()
    return _planner

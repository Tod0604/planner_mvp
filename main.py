"""
Core Planning Pipeline
End-to-end pipeline: input → features → models → plan
"""

import os
import json
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from features.build_features import FeatureBuilder
from models.train_models import TaskRankingModel, TimeAllocationModel, DifficultyAdjustmentModel


class StudyPlanner:
    """Main study planner pipeline"""
    
    def __init__(self, models_dir: str = 'models'):
        self.models_dir = models_dir
        self.task_ranker = None
        self.time_model = None
        self.difficulty_model = None
        self.feature_builder = FeatureBuilder()
        self.load_models()
    
    def load_models(self) -> None:
        """Load trained models from disk"""
        
        ranker_path = os.path.join(self.models_dir, 'task_ranker.pkl')
        time_path = os.path.join(self.models_dir, 'time_allocator.pkl')
        diff_path = os.path.join(self.models_dir, 'difficulty_adjuster.pkl')
        
        try:
            self.task_ranker = TaskRankingModel.load(ranker_path)
            self.time_model = TimeAllocationModel.load(time_path)
            self.difficulty_model = DifficultyAdjustmentModel.load(diff_path)
            print("✓ Models loaded successfully")
        except FileNotFoundError:
            print("⚠ Models not found. Run training first: python models/train_models.py")
            raise
    
    def generate_plan(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized study plan.
        
        Args:
            user_input: Dict with keys:
                - tasks: List of task names
                - time_spent: List of minutes
                - difficulty_rating: List (1-5)
                - energy_level: int (1-5)
                - goals_for_tomorrow: List of strings
                - available_minutes: int
        
        Returns:
            Dict with:
                - ranked_tasks: List of tasks in recommended order
                - recommended_minutes: List of durations
                - difficulty_adjustment: int (-1, 0, +1)
                - summary: str (human-readable)
        """
        
        # Step 1: Build features
        features_dict = self.feature_builder.build_features(user_input)
        features_df = pd.DataFrame([features_dict])
        
        # Step 2: Get predictions from models
        ranking_scores = self.task_ranker.predict_ranking(features_df)
        recommended_minutes = self.time_model.predict_time(features_df)
        difficulty_adjustment = self.difficulty_model.predict_adjustment(features_df)[0]
        
        # Step 3: Rank tasks
        task_indices = np.argsort(-ranking_scores)  # Sort by score descending
        ranked_tasks = [user_input['tasks'][i] for i in task_indices]
        ranked_minutes = [int(recommended_minutes[0]) for _ in ranked_tasks]
        
        # Distribute available time
        total_available = user_input['available_minutes']
        total_requested = sum(ranked_minutes)
        
        if total_requested > 0:
            scale_factor = total_available / total_requested
            ranked_minutes = [max(30, min(120, int(m * scale_factor))) for m in ranked_minutes]
        
        # Step 4: Generate summary
        summary = self._generate_summary(
            ranked_tasks[:3],
            ranked_minutes[:3],
            int(difficulty_adjustment),
            features_dict
        )
        
        return {
            'ranked_tasks': ranked_tasks,
            'recommended_minutes': ranked_minutes,
            'difficulty_adjustment': int(difficulty_adjustment),
            'summary': summary,
            'metrics': {
                'energy_level': user_input['energy_level'],
                'fatigue_score': features_dict['fatigue_score'],
                'productivity_score': round(features_dict['productivity_score'], 2),
                'time_pressure': round((sum(user_input['time_spent']) / user_input['available_minutes']) if user_input['available_minutes'] > 0 else 0, 2)
            }
        }
    
    def _generate_summary(
        self,
        top_tasks: List[str],
        durations: List[int],
        difficulty_adj: int,
        features: Dict
    ) -> str:
        """Generate human-readable summary"""
        
        if not top_tasks:
            return "No tasks provided."
        
        summary = f"Start with '{top_tasks[0]}' for {durations[0]} minutes. "
        
        if len(top_tasks) > 1:
            summary += f"Then '{top_tasks[1]}' for {durations[1]} minutes. "
        
        if len(top_tasks) > 2:
            summary += f"Finally '{top_tasks[2]}' for {durations[2]} minutes. "
        
        # Add difficulty adjustment note
        if difficulty_adj == 1:
            summary += "Your performance suggests increasing challenge slightly. "
        elif difficulty_adj == -1:
            summary += "Consider starting with slightly easier tasks. "
        else:
            summary += "Maintain current difficulty level. "
        
        # Add fatigue note
        if features['fatigue_score'] >= 3:
            summary += "You seem fatigued - take short breaks between tasks."
        elif features['fatigue_score'] < 1:
            summary += "You have good energy - optimal time to tackle harder tasks!"
        
        return summary


def generate_plan(user_input_json: str) -> Dict[str, Any]:
    """
    Main entry point for plan generation.
    
    Args:
        user_input_json: JSON string with user input
        
    Returns:
        Study plan dictionary
    """
    # Parse input
    if isinstance(user_input_json, str):
        user_input = json.loads(user_input_json)
    else:
        user_input = user_input_json
    
    # Generate plan
    planner = StudyPlanner()
    plan = planner.generate_plan(user_input)
    
    return plan


if __name__ == "__main__":
    # Example usage
    example_input = {
        "tasks": ["Math review", "ML project", "Reading"],
        "time_spent": [60, 90, 30],
        "difficulty_rating": [3, 4, 2],
        "energy_level": 4,
        "goals_for_tomorrow": ["Finish ML assignment", "Review Week 3"],
        "available_minutes": 180
    }
    
    print("📋 Generating study plan...")
    print(f"Input: {json.dumps(example_input, indent=2)}\n")
    
    try:
        plan = generate_plan(example_input)
        print("✓ Plan generated successfully!\n")
        print(json.dumps(plan, indent=2))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nTrain models first: python models/train_models.py")

"""
Synthetic Data Generator for Study Planner
Generates synthetic daily logs for training/testing ML models
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


def generate_synthetic_data(num_records: int = 300) -> pd.DataFrame:
    """
    Generate synthetic daily study logs.
    
    Args:
        num_records: Number of synthetic records to generate (200-500)
        
    Returns:
        DataFrame with columns:
        - date
        - task_name
        - time_spent (minutes)
        - difficulty_rating (1-5)
        - energy_level (1-5)
        - task_type (study/project/reading)
        - completion_ratio (0-1)
        - next_day_recommended_task
        - next_day_recommended_duration
    """
    
    np.random.seed(42)
    
    task_pool = [
        "Math review",
        "ML project",
        "Reading",
        "Coding practice",
        "Data analysis",
        "Research paper",
        "Quiz prep",
        "Assignment",
        "Group study",
        "Algorithm practice"
    ]
    
    task_types = {
        "Math review": "study",
        "ML project": "project",
        "Reading": "reading",
        "Coding practice": "project",
        "Data analysis": "project",
        "Research paper": "reading",
        "Quiz prep": "study",
        "Assignment": "project",
        "Group study": "study",
        "Algorithm practice": "project"
    }
    
    records = []
    start_date = datetime.now() - timedelta(days=num_records)
    
    for i in range(num_records):
        date = start_date + timedelta(days=i)
        
        # Generate 2-4 tasks per day
        num_tasks_today = np.random.randint(2, 5)
        
        for _ in range(num_tasks_today):
            task_name = np.random.choice(task_pool)
            
            # Realistic time spent (30-120 minutes)
            time_spent = np.random.normal(loc=70, scale=25)
            time_spent = max(30, min(120, int(time_spent)))
            
            # Difficulty rating (1-5)
            difficulty_rating = np.random.randint(1, 6)
            
            # Energy level (1-5)
            energy_level = np.random.randint(1, 6)
            
            # Task type
            task_type = task_types[task_name]
            
            # Completion ratio: higher with more energy, lower with high difficulty
            base_completion = 0.7 + (energy_level / 5) * 0.2 - (difficulty_rating / 5) * 0.1
            completion_ratio = max(0, min(1, base_completion + np.random.normal(0, 0.1)))
            
            # Rule-based next day recommendation
            if completion_ratio > 0.8:
                # High completion - suggest next task of similar or slightly higher difficulty
                next_difficulty = min(5, difficulty_rating + 1)
                next_duration = time_spent + np.random.randint(5, 20)
            elif completion_ratio < 0.5:
                # Low completion - suggest easier task next day
                next_difficulty = max(1, difficulty_rating - 1)
                next_duration = max(30, time_spent - np.random.randint(10, 30))
            else:
                # Medium completion - maintain similar difficulty
                next_difficulty = difficulty_rating
                next_duration = time_spent + np.random.randint(-10, 10)
            
            next_task = np.random.choice(task_pool)
            next_duration = max(30, min(120, int(next_duration)))
            
            records.append({
                'date': date.strftime('%Y-%m-%d'),
                'task_name': task_name,
                'time_spent': time_spent,
                'difficulty_rating': difficulty_rating,
                'energy_level': energy_level,
                'task_type': task_type,
                'completion_ratio': round(completion_ratio, 2),
                'next_day_recommended_task': next_task,
                'next_day_recommended_duration': next_duration
            })
    
    df = pd.DataFrame(records)
    return df


def save_synthetic_data(df: pd.DataFrame, filepath: str = 'data/synthetic_logs.csv') -> str:
    """Save synthetic data to CSV"""
    df.to_csv(filepath, index=False)
    print(f"✓ Saved {len(df)} records to {filepath}")
    return filepath


def load_synthetic_data(filepath: str = 'data/synthetic_logs.csv') -> pd.DataFrame:
    """Load synthetic data from CSV"""
    return pd.read_csv(filepath)


if __name__ == "__main__":
    # Generate and save synthetic data
    print("📊 Generating synthetic study data...")
    df = generate_synthetic_data(num_records=350)
    
    print(f"\n✓ Generated {len(df)} records")
    print(f"\nDataFrame shape: {df.shape}")
    print(f"\nFirst few records:\n{df.head()}")
    print(f"\nData summary:\n{df.describe()}")
    print(f"\nTask type distribution:\n{df['task_type'].value_counts()}")
    
    # Save to CSV
    save_synthetic_data(df)

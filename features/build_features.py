"""
Feature Engineering Module for Study Planner
Converts raw logs into model-ready features
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class SimpleLabelEncoder:
    """Simple label encoder without sklearn dependency"""
    def __init__(self):
        self.classes_ = []
        self.mapping_ = {}
    
    def fit(self, y):
        self.classes_ = list(set(y))
        self.mapping_ = {v: i for i, v in enumerate(self.classes_)}
        return self
    
    def transform(self, y):
        return [self.mapping_.get(v, 0) for v in y]
    
    def fit_transform(self, y):
        return self.fit(y).transform(y)


class FeatureBuilder:
    """Build features from raw study logs"""
    
    def __init__(self):
        self.task_type_encoder = SimpleLabelEncoder()
        self.task_name_encoder = SimpleLabelEncoder()
        self.is_fitted = False
        
    def fit(self, df: pd.DataFrame) -> 'FeatureBuilder':
        """Fit encoders on training data"""
        self.task_type_encoder.fit(df['task_type'].unique())
        self.task_name_encoder.fit(df['task_name'].unique())
        self.is_fitted = True
        return self
    
    def build_features(self, user_input: Dict) -> Dict:
        """
        Build features from user input JSON.
        
        Args:
            user_input: Dict with keys:
                - tasks: List of task names
                - time_spent: List of minutes
                - difficulty_rating: List (1-5)
                - energy_level: int (1-5)
                - goals_for_tomorrow: List of strings
                - available_minutes: int
        
        Returns:
            Dict with engineered features
        """
        
        # Calculate last 3 days statistics from current input
        num_tasks = len(user_input['tasks'])
        
        # Average time spent
        avg_time_3d = float(np.mean(user_input['time_spent']))
        
        # Task difficulty trend (simple: recent - old)
        if num_tasks >= 2:
            difficulty_trend = float(user_input['difficulty_rating'][-1] - user_input['difficulty_rating'][0])
        else:
            difficulty_trend = 0.0
        
        # Normalized difficulty
        norm_difficulty = float(np.mean(user_input['difficulty_rating']) / 5.0)
        
        # Fatigue score
        fatigue_score = float(5 - user_input['energy_level'])
        
        # Productivity score (mock completion ratio)
        productivity_score = float((user_input['energy_level'] / 5.0) * 0.8)
        
        # Task frequency
        task_frequency = float(num_tasks)
        
        # Encode task type - use first task or default
        task_type_encoded = 0.0
        
        # Completion ratio - mock based on energy
        completion_ratio = float(min(1.0, (user_input['energy_level'] / 5.0) * 0.85))
        
        # Create feature vector matching training features
        features = {
            'avg_time_spent_3d': avg_time_3d,
            'difficulty_trend': difficulty_trend,
            'normalized_difficulty': norm_difficulty,
            'fatigue_score': fatigue_score,
            'productivity_score': productivity_score,
            'task_frequency': task_frequency,
            'task_type_encoded': task_type_encoded,
            'energy_level': float(user_input['energy_level']),
            'completion_ratio': completion_ratio
        }
        
        return features
    
    def build_features_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build features from batch of logs (for training).
        
        Args:
            df: DataFrame from synthetic_generator
            
        Returns:
            DataFrame with all features
        """
        
        grouped = df.groupby(df.index // 3)  # Group by 3-day windows
        features_list = []
        
        for group_id, group_df in grouped:
            group_records = group_df.to_dict('records')
            
            for i, record in enumerate(group_records):
                if i == 0:
                    continue  # Skip first record in group
                
                # Get previous records (up to 3 days)
                prev_records = group_records[max(0, i-3):i]
                
                if not prev_records:
                    continue
                
                # Calculate features
                avg_time = np.mean([r['time_spent'] for r in prev_records])
                difficulties = [r['difficulty_rating'] for r in prev_records]
                difficulty_trend = difficulties[-1] - difficulties[0] if len(difficulties) > 1 else 0
                norm_difficulty = np.mean(difficulties) / 5.0
                
                energy = record['energy_level']
                fatigue_score = 5 - energy
                
                completion_avg = np.mean([r['completion_ratio'] for r in prev_records])
                productivity_score = (energy / 5.0) * completion_avg
                
                task_frequency = len(prev_records)
                
                # Encode task type
                task_type_encoded = self.task_type_encoder.transform([record['task_type']])[0] if self.is_fitted else 0
                
                features_dict = {
                    'avg_time_spent_3d': avg_time,
                    'difficulty_trend': difficulty_trend,
                    'normalized_difficulty': norm_difficulty,
                    'fatigue_score': fatigue_score,
                    'productivity_score': productivity_score,
                    'task_frequency': task_frequency,
                    'task_type_encoded': task_type_encoded,
                    'energy_level': energy,
                    'completion_ratio': record['completion_ratio'],
                    'target_duration': record['next_day_recommended_duration'],
                    'difficulty_adjustment_target': 0  # Will be set based on rules
                }
                
                features_list.append(features_dict)
        
        return pd.DataFrame(features_list)


def create_training_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Create training features from synthetic data.
    
    Returns:
        X: Feature matrix
        y: Target variable (next day recommended duration)
        feature_names: List of feature names
    """
    
    feature_builder = FeatureBuilder()
    feature_builder.fit(df)
    
    features_df = feature_builder.build_features_batch(df)
    
    # Split features and targets
    feature_cols = [col for col in features_df.columns if col not in ['target_duration', 'difficulty_adjustment_target']]
    
    X = features_df[feature_cols]
    y = features_df['target_duration']
    
    return X, y, feature_cols


if __name__ == "__main__":
    # Test feature building
    from data.synthetic_generator import generate_synthetic_data, save_synthetic_data
    
    print("📊 Building features from synthetic data...")
    
    # Generate data
    df = generate_synthetic_data(num_records=300)
    save_synthetic_data(df)
    
    # Build features
    X, y, feature_names = create_training_features(df)
    
    print(f"\n✓ Created {len(X)} feature vectors")
    print(f"✓ Features: {len(feature_names)}")
    print(f"\nFeature names: {feature_names}")
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"\nTarget (duration) shape: {y.shape}")
    print(f"\nFeature statistics:\n{X.describe()}")

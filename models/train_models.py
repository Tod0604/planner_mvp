"""
ML Models for Study Planner
1. Task Ranking Model (LightGBM Ranker)
2. Time Allocation Model (Linear Regression)
3. Difficulty Adjustment Model (Logistic Regression)
"""

import numpy as np
import pandas as pd
import pickle
import os
import sys
from typing import List, Tuple, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TaskRankingModel:
    """
    Task ranking model using Linear Regression.
    Predicts which task should be done first based on features.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = None
        
    def train(self, X: pd.DataFrame, y: pd.Series) -> 'TaskRankingModel':
        """
        Train task ranking model.
        
        Args:
            X: Feature matrix
            y: Target (difficulty adjustment scores)
        """
        X_scaled = self.scaler.fit_transform(X)
        
        # Use raw values for regression
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self.feature_names = X.columns.tolist()
        
        print("✓ Task Ranking Model trained")
        return self
    
    def predict_ranking(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict task ranking scores.
        
        Args:
            X: Feature matrix
            
        Returns:
            Ranking scores (normalized 0-1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X_scaled = self.scaler.transform(X)
        scores = self.model.predict(X_scaled)
        # Normalize to 0-1 range
        scores = np.clip((scores - scores.min()) / (scores.max() - scores.min() + 1e-10), 0, 1)
        return scores
    
    def save(self, filepath: str = 'models/task_ranker.pkl') -> str:
        """Save model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"✓ Saved Task Ranking Model to {filepath}")
        return filepath
    
    @staticmethod
    def load(filepath: str = 'models/task_ranker.pkl') -> 'TaskRankingModel':
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"✓ Loaded Task Ranking Model from {filepath}")
        return model


class TimeAllocationModel:
    """
    Linear Regression for time allocation.
    Predicts recommended duration for each task.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = None
        
    def train(self, X: pd.DataFrame, y: pd.Series) -> 'TimeAllocationModel':
        """
        Train time allocation model.
        
        Args:
            X: Feature matrix
            y: Target (recommended duration in minutes)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self.feature_names = X.columns.tolist()
        
        print("✓ Time Allocation Model trained")
        return self
    
    def predict_time(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict time allocation.
        
        Args:
            X: Feature matrix
            
        Returns:
            Recommended minutes (30-120)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        # Clip to reasonable range
        predictions = np.clip(predictions, 30, 120)
        return predictions
    
    def save(self, filepath: str = 'models/time_allocator.pkl') -> str:
        """Save model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"✓ Saved Time Allocation Model to {filepath}")
        return filepath
    
    @staticmethod
    def load(filepath: str = 'models/time_allocator.pkl') -> 'TimeAllocationModel':
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"✓ Loaded Time Allocation Model from {filepath}")
        return model


class DifficultyAdjustmentModel:
    """
    Logistic Regression for difficulty adjustment.
    Predicts: -1 (easier), 0 (same), +1 (harder)
    """
    
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000, random_state=42, multi_class='multinomial')
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = None
        self.classes_ = np.array([-1, 0, 1])
        
    def train(self, X: pd.DataFrame, y: pd.Series) -> 'DifficultyAdjustmentModel':
        """
        Train difficulty adjustment model.
        
        Args:
            X: Feature matrix
            y: Target (-1, 0, or 1)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self.feature_names = X.columns.tolist()
        
        print("✓ Difficulty Adjustment Model trained")
        return self
    
    def predict_adjustment(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict difficulty adjustment.
        
        Args:
            X: Feature matrix
            
        Returns:
            Adjustment class (-1, 0, +1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        return predictions
    
    def save(self, filepath: str = 'models/difficulty_adjuster.pkl') -> str:
        """Save model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"✓ Saved Difficulty Adjustment Model to {filepath}")
        return filepath
    
    @staticmethod
    def load(filepath: str = 'models/difficulty_adjuster.pkl') -> 'DifficultyAdjustmentModel':
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"✓ Loaded Difficulty Adjustment Model from {filepath}")
        return model


def create_difficulty_targets(df: pd.DataFrame) -> pd.Series:
    """
    Create difficulty adjustment targets from synthetic data.
    
    Rules:
    - If completion > 0.8: predict +1 (harder)
    - If completion < 0.5: predict -1 (easier)
    - Otherwise: predict 0 (same)
    """
    targets = []
    for _, row in df.iterrows():
        if row['completion_ratio'] > 0.8:
            targets.append(1)  # Harder
        elif row['completion_ratio'] < 0.5:
            targets.append(-1)  # Easier
        else:
            targets.append(0)  # Same
    
    return pd.Series(targets, name='difficulty_adjustment')


if __name__ == "__main__":
    # Test model training
    from features.build_features import create_training_features
    from data.synthetic_generator import generate_synthetic_data, save_synthetic_data
    
    print("[TRAINING] Starting ML model training...")
    
    # Generate synthetic data
    df = generate_synthetic_data(num_records=300)
    save_synthetic_data(df)
    
    # Build features
    X, y_duration, feature_names = create_training_features(df)
    
    # Add difficulty targets
    y_difficulty = create_difficulty_targets(df.iloc[3:])  # Skip first few rows
    y_difficulty = y_difficulty.reset_index(drop=True)
    
    # Align lengths
    min_len = min(len(X), len(y_difficulty))
    X = X.iloc[:min_len]
    y_difficulty = y_difficulty.iloc[:min_len]
    
    # Train models
    print("[TRAINING] Training models...")
    
    ranker = TaskRankingModel().train(X, y_difficulty + 2)  # Convert to 0-2 range
    time_model = TimeAllocationModel().train(X, y_duration)
    diff_model = DifficultyAdjustmentModel().train(X, y_difficulty)
    
    # Save models
    os.makedirs('models', exist_ok=True)
    ranker.save()
    time_model.save()
    diff_model.save()
    
    print("[TRAINING] All models trained and saved")

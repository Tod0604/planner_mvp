"""
Dedicated training script to properly train and save models
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.synthetic_generator import generate_synthetic_data, save_synthetic_data
from features.build_features import create_training_features
from models.train_models import (
    TaskRankingModel,
    TimeAllocationModel,
    DifficultyAdjustmentModel,
    create_difficulty_targets
)

def main():
    print("🤖 Training ML models...")
    
    # Generate synthetic data
    print("\n📊 Generating synthetic data...")
    df = generate_synthetic_data(num_records=500)
    save_synthetic_data(df)
    print(f"✓ Generated {len(df)} records")
    
    # Build features
    print("\n🔧 Building features...")
    X, y_duration, feature_names = create_training_features(df)
    print(f"✓ Built features: shape={X.shape}")
    
    # Create difficulty targets
    print("📈 Creating difficulty targets...")
    y_difficulty = create_difficulty_targets(df.iloc[3:])
    y_difficulty = y_difficulty.reset_index(drop=True)
    
    # Align lengths
    min_len = min(len(X), len(y_difficulty))
    X = X.iloc[:min_len]
    y_difficulty = y_difficulty.iloc[:min_len]
    print(f"✓ Aligned data: {len(X)} samples")
    
    # Train models
    print("\n🎓 Training models...")
    
    ranker = TaskRankingModel()
    ranker.train(X, y_difficulty + 2)  # Convert to 0-2 range
    ranker.save()
    
    time_model = TimeAllocationModel()
    time_model.train(X, y_duration)
    time_model.save()
    
    diff_model = DifficultyAdjustmentModel()
    diff_model.train(X, y_difficulty)
    diff_model.save()
    
    print("\n✓ All models trained and saved successfully!")
    print("\nYou can now run the application:")
    print("  1. FastAPI: python -m uvicorn api.app:app --reload")
    print("  2. Streamlit: streamlit run api/ui.py")

if __name__ == "__main__":
    main()

"""
Test and verification script for Study Planner MVP
Validates all components work together
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from data.synthetic_generator import generate_synthetic_data, save_synthetic_data
        print("  ✓ data.synthetic_generator")
        
        from features.build_features import FeatureBuilder
        print("  ✓ features.build_features")
        
        from models.train_models import TaskRankingModel, TimeAllocationModel, DifficultyAdjustmentModel
        print("  ✓ models.train_models")
        
        from main import StudyPlanner, generate_plan
        print("  ✓ main.StudyPlanner")
        
        # Optional: API and UI imports
        try:
            from api.app import app
            print("  ✓ api.app")
        except ImportError as e:
            print(f"  ⚠ api.app (requires fastapi): {e}")
        
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_data_generation():
    """Test synthetic data generation"""
    print("\n📊 Testing data generation...")
    try:
        from data.synthetic_generator import generate_synthetic_data, save_synthetic_data, load_synthetic_data
        
        print("  Generating synthetic data...")
        df = generate_synthetic_data(num_records=100)
        print(f"  ✓ Generated {len(df)} records")
        print(f"    Columns: {list(df.columns)}")
        
        print("  Saving synthetic data...")
        save_synthetic_data(df)
        print("  ✓ Saved to data/synthetic_study_data.csv")
        
        print("  Loading synthetic data...")
        df_loaded = load_synthetic_data()
        print(f"  ✓ Loaded {len(df_loaded)} records")
        
        return True
    except Exception as e:
        print(f"  ✗ Data generation failed: {e}")
        return False

def test_feature_engineering():
    """Test feature engineering"""
    print("\n🔧 Testing feature engineering...")
    try:
        from data.synthetic_generator import load_synthetic_data
        from features.build_features import FeatureBuilder
        
        print("  Loading synthetic data...")
        df = load_synthetic_data()
        
        print("  Building feature builder...")
        fb = FeatureBuilder()
        
        print("  Training feature builder...")
        fb.fit(df)
        print("  ✓ Feature builder fitted")
        
        print("  Building features for batch...")
        X = fb.build_features_batch(df.head(10))
        print(f"  ✓ Built features: shape={X.shape}")
        print(f"    Features: {list(X.columns)}")
        
        print("  Testing single sample...")
        sample_input = {
            "tasks": ["Task1", "Task2"],
            "time_spent": [60, 90],
            "difficulty_rating": [3, 4],
            "energy_level": 3,
            "goals_for_tomorrow": ["Goal1"],
            "available_minutes": 180
        }
        features = fb.build_features(sample_input)
        print(f"  ✓ Built single sample features: {len(features)} features")
        
        return True
    except Exception as e:
        print(f"  ✗ Feature engineering failed: {e}")
        return False

def test_model_training():
    """Test model training"""
    print("\n🤖 Testing model training...")
    try:
        from data.synthetic_generator import load_synthetic_data
        from features.build_features import FeatureBuilder
        from models.train_models import (
            TaskRankingModel, 
            TimeAllocationModel, 
            DifficultyAdjustmentModel,
            create_difficulty_targets
        )
        
        print("  Loading data...")
        df = load_synthetic_data()
        
        print("  Building features...")
        fb = FeatureBuilder()
        fb.fit(df)
        X = fb.build_features_batch(df)
        
        print("  Creating targets...")
        y_ranking, y_time, y_difficulty = create_difficulty_targets(df)
        print(f"  ✓ Created targets: ranking={len(y_ranking)}, time={len(y_time)}, difficulty={len(y_difficulty)}")
        
        print("  Training Task Ranking Model...")
        task_ranker = TaskRankingModel()
        task_ranker.train(X, y_ranking)
        print("  ✓ Task Ranking Model trained")
        
        print("  Training Time Allocation Model...")
        time_allocator = TimeAllocationModel()
        time_allocator.train(X, y_time)
        print("  ✓ Time Allocation Model trained")
        
        print("  Training Difficulty Adjustment Model...")
        difficulty_adjuster = DifficultyAdjustmentModel()
        difficulty_adjuster.train(X, y_difficulty)
        print("  ✓ Difficulty Adjustment Model trained")
        
        print("  Testing model save/load...")
        task_ranker.save('models/task_ranker_test.pkl')
        loaded = TaskRankingModel()
        loaded.load('models/task_ranker_test.pkl')
        print("  ✓ Model save/load working")
        
        # Cleanup test files
        os.remove('models/task_ranker_test.pkl')
        
        return True
    except Exception as e:
        print(f"  ✗ Model training failed: {e}")
        return False

def test_plan_generation():
    """Test main plan generation"""
    print("\n📋 Testing plan generation...")
    try:
        from data.synthetic_generator import load_synthetic_data
        from features.build_features import FeatureBuilder
        from models.train_models import (
            TaskRankingModel, 
            TimeAllocationModel, 
            DifficultyAdjustmentModel,
            create_difficulty_targets
        )
        from main import StudyPlanner
        
        # Setup: Generate and train models if needed
        print("  Preparing models...")
        df = load_synthetic_data()
        fb = FeatureBuilder()
        fb.fit(df)
        X = fb.build_features_batch(df)
        y_ranking, y_time, y_difficulty = create_difficulty_targets(df)
        
        task_ranker = TaskRankingModel()
        task_ranker.train(X, y_ranking)
        task_ranker.save('models/task_ranker.pkl')
        
        time_allocator = TimeAllocationModel()
        time_allocator.train(X, y_time)
        time_allocator.save('models/time_allocator.pkl')
        
        difficulty_adjuster = DifficultyAdjustmentModel()
        difficulty_adjuster.train(X, y_difficulty)
        difficulty_adjuster.save('models/difficulty_adjuster.pkl')
        
        print("  Creating study planner...")
        planner = StudyPlanner()
        print("  ✓ StudyPlanner initialized")
        
        print("  Testing plan generation...")
        user_input = {
            "tasks": ["Read Chapter", "Problem Set", "Review"],
            "time_spent": [60, 90, 30],
            "difficulty_rating": [3, 4, 2],
            "energy_level": 4,
            "goals_for_tomorrow": ["Submit assignment"],
            "available_minutes": 180
        }
        
        plan = planner.generate_plan(user_input)
        
        print("  ✓ Plan generated successfully")
        print(f"    Ranked tasks: {plan['ranked_tasks']}")
        print(f"    Recommended minutes: {plan['recommended_minutes']}")
        print(f"    Difficulty adjustment: {plan['difficulty_adjustment']}")
        print(f"    Summary: {plan['summary'][:100]}...")
        
        return True
    except Exception as e:
        print(f"  ✗ Plan generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structure():
    """Test that all required files exist"""
    print("\n📁 Verifying project structure...")
    
    required_files = [
        "data/synthetic_generator.py",
        "features/build_features.py",
        "models/train_models.py",
        "api/app.py",
        "api/ui.py",
        "main.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("=" * 60)
    print("  Study Planner MVP - Test Suite")
    print("=" * 60)
    
    results = {
        "Structure": test_structure(),
        "Imports": test_imports(),
        "Data Generation": test_data_generation(),
        "Feature Engineering": test_feature_engineering(),
        "Model Training": test_model_training(),
        "Plan Generation": test_plan_generation(),
    }
    
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Your Study Planner MVP is ready.")
        print("\nNext steps:")
        print("  1. Start API: python -m uvicorn api.app:app --reload")
        print("  2. Start UI:  streamlit run api/ui.py")
        print("  3. Open browser: http://localhost:8501")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

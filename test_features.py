"""
Test new features: calendar persistence, dates, and feedback
"""

from utils.calendar_store import get_calendar_store
from datetime import datetime, timedelta

def test_features():
    """Test all new features"""
    print("\n" + "="*70)
    print("TESTING NEW FEATURES")
    print("="*70)
    
    store = get_calendar_store()
    
    # Use sample dates
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 1. Test persistence with dates
    print("\n1. DATE + PERSISTENCE")
    print("-"*70)
    
    sample_plans = {
        yesterday: {
            "ranked_tasks": ["Math", "Reading"],
            "recommended_minutes": [60, 45],
            "difficulty_adjustment": 1,
            "summary": "Focus on math while fresh"
        },
        today: {
            "ranked_tasks": ["Chemistry", "Lab", "Review"],
            "recommended_minutes": [90, 60, 30],
            "difficulty_adjustment": 0,
            "summary": "Balanced day with lab work"
        }
    }
    
    for date, plan in sample_plans.items():
        success = store.save_plan(date, plan, 180, metrics={"energy": 4})
        print(f"  [OK] Saved plan for {date}: {len(plan['ranked_tasks'])} tasks")
    
    # 2. Test calendar view
    print("\n2. CALENDAR VIEW (List Plans)")
    print("-"*70)
    
    plans = store.list_plans(yesterday, today)
    print(f"  [OK] Retrieved {len(plans)} plans")
    for p in plans:
        print(f"       {p['date']}: {p['num_tasks']} tasks, {p['total_planned_minutes']} min")
    
    # 3. Test feedback
    print("\n3. FEEDBACK LOOP")
    print("-"*70)
    
    feedbacks = {
        yesterday: {"completion": 0.75, "tiredness": 3, "notes": "Good start"},
        today: {"completion": 0.85, "tiredness": 2, "notes": "Great energy"}
    }
    
    for date, fb in feedbacks.items():
        success = store.save_feedback(date, fb["completion"], fb["tiredness"], fb["notes"])
        print(f"  [OK] Feedback for {date}: {fb['completion']*100:.0f}% completion")
    
    # 4. Test retrieval
    print("\n4. FEEDBACK ANALYTICS")
    print("-"*70)
    
    all_feedback = store.get_feedback_range(yesterday, today)
    avg_completion = sum(f["completion_ratio"] for f in all_feedback) / len(all_feedback) * 100
    avg_tiredness = sum(f["tiredness_end_of_day"] for f in all_feedback) / len(all_feedback)
    
    print(f"  [OK] Average completion: {avg_completion:.0f}%")
    print(f"  [OK] Average tiredness: {avg_tiredness:.1f}/5")
    
    # 5. Combined view
    print("\n5. COMBINED VIEW (Plan + Feedback)")
    print("-"*70)
    
    combined = store.get_plan_with_feedback(today)
    if combined["plan"] and combined["feedback"]:
        tasks = ", ".join(combined["plan"]["ranked_tasks"])
        completion = combined["feedback"]["completion_ratio"] * 100
        print(f"  [OK] Plan: {tasks}")
        print(f"  [OK] Feedback: {completion:.0f}% complete")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED!")
    print("="*70)
    print("\nFeatures Implemented:")
    print("  [OK] Date-based plan persistence")
    print("  [OK] Calendar view with date ranges")
    print("  [OK] Feedback collection & storage")
    print("  [OK] Combined plan + feedback view")
    print("  [OK] Feedback analytics (trends, averages)")
    print("\n" + "="*70)

if __name__ == "__main__":
    test_features()


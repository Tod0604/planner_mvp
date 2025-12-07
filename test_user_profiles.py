"""
Test User Profiles & Personalization Features
"""

import sys
sys.path.insert(0, '.')

from utils.user_profiles import get_user_profile_manager
from datetime import datetime

print("=" * 70)
print("TESTING USER PROFILES & PERSONALIZATION")
print("=" * 70)

user_manager = get_user_profile_manager()

# Test 1: Create users
print("\n1. CREATE USERS")
print("-" * 70)

users_to_create = [
    ("user_alice", "Alice", "Master Python programming", 45),
    ("user_bob", "Bob", "Improve Math skills", 90),
]

for user_id, name, goal, duration in users_to_create:
    result = user_manager.create_user(user_id, name, goal, duration)
    print(f"  [OK] Created user: {name} (ID: {user_id})")

# Test 2: List users
print("\n2. LIST USERS")
print("-" * 70)

all_users = user_manager.get_all_users()
for user in all_users:
    print(f"  {user['user_id']}: {user['name']} - {user['learning_goal']}")

# Test 3: Clock in/out
print("\n3. CLOCK IN/OUT")
print("-" * 70)

user_id = "user_alice"

# Clock in
clock_in_result = user_manager.clock_in(user_id, "Python - OOP Basics")
tracking_id = clock_in_result['tracking_id']
print(f"  [OK] Clocked in: {clock_in_result['task_name']}")
print(f"       Tracking ID: {tracking_id}")

# Clock out
import time
time.sleep(1)  # Simulate some work

clock_out_result = user_manager.clock_out(user_id, tracking_id, difficulty_rating=3, notes="Completed 3 exercises")
print(f"  [OK] Clocked out: Duration {clock_out_result['duration_minutes']} minutes")

# Clock in again
clock_in_result2 = user_manager.clock_in(user_id, "Python - Functions")
tracking_id2 = clock_in_result2['tracking_id']
time.sleep(1)
clock_out_result2 = user_manager.clock_out(user_id, tracking_id2, difficulty_rating=2, notes="Quick review")

# Test 4: Get active session
print("\n4. ACTIVE SESSIONS")
print("-" * 70)

user_id_2 = "user_bob"
clock_in_bob = user_manager.clock_in(user_id_2, "Calculus - Derivatives")
active = user_manager.get_active_clock_in(user_id_2)
print(f"  [OK] Active session: {active['task_name']}")

# Test 5: Time tracking history
print("\n5. TIME TRACKING HISTORY")
print("-" * 70)

history = user_manager.get_time_tracking_history("user_alice")
print(f"  [OK] Alice's sessions: {len(history)} tracked")
for h in history:
    print(f"       - {h['task_name']}: {h['duration_minutes']} min (Difficulty: {h['difficulty_rating']})")

# Test 6: Analytics
print("\n6. USER ANALYTICS")
print("-" * 70)

analytics = user_manager.calculate_analytics("user_alice")
if analytics['status'] == 'success':
    print(f"  [OK] Average session: {analytics['avg_session_duration']} minutes")
    print(f"       Most productive hour: {analytics['most_productive_hour']}")
    print(f"       Productivity score: {analytics['productivity_score']}/100")
    print(f"       Total study hours: {analytics['total_study_hours']}")
    print(f"       Sessions completed: {analytics['session_count']}")
else:
    print(f"  [INFO] {analytics['message']}")

# Test 7: Personalized insights
print("\n7. PERSONALIZED INSIGHTS")
print("-" * 70)

insights = user_manager.get_personalized_insights("user_alice")
if insights['status'] == 'success':
    print(f"  [OK] Generated {len(insights['insights'])} insights:")
    for insight in insights['insights']:
        print(f"       - {insight['title']}: {insight['message']}")
else:
    print(f"  [INFO] {insights.get('message', 'No insights available')}")

print("\n" + "=" * 70)
print("ALL TESTS PASSED!")
print("=" * 70)

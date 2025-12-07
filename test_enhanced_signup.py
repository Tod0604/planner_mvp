"""
Test Enhanced Sign-Up Features with Email, Education Level, Subject Area, and Password
"""

import sys
sys.path.insert(0, '.')

from utils.user_profiles import get_user_profile_manager
import os

# Clean up old database for fresh test
if os.path.exists("study_planner.db"):
    os.remove("study_planner.db")

print("=" * 70)
print("TESTING ENHANCED SIGN-UP WITH EMAIL, EDUCATION, SUBJECT, PASSWORD")
print("=" * 70)

user_manager = get_user_profile_manager()

# Test 1: Create user with all new fields
print("\n1. CREATE USER WITH ENHANCED FIELDS")
print("-" * 70)

result = user_manager.create_user(
    user_id="user_alice",
    name="Alice Johnson",
    email="alice@example.com",
    education_level="University",
    subject_area="Computer Science",
    learning_goal="Master Machine Learning",
    preferred_session_duration=60,
    password="SecurePass123"
)
print(f"  Status: {result['status']}")
print(f"  Created user: {result['user_id']}")

# Test 2: Retrieve user and verify data
print("\n2. RETRIEVE AND VERIFY USER DATA")
print("-" * 70)

user = user_manager.get_user("user_alice")
print(f"  User ID: {user['user_id']}")
print(f"  Name: {user['name']}")
print(f"  Email: {user['email']}")
print(f"  Education Level: {user['education_level']}")
print(f"  Subject Area: {user['subject_area']}")
print(f"  Learning Goal: {user['learning_goal']}")
print(f"  Preferred Duration: {user['preferred_session_duration']} min")
print(f"  Password Hash stored: {bool(user['password_hash'])}")
print(f"  Password Salt stored: {bool(user['password_salt'])}")

# Test 3: Test password verification
print("\n3. PASSWORD VERIFICATION")
print("-" * 70)

# Correct password
is_valid = user_manager.verify_password(
    "SecurePass123",
    user['password_hash'],
    user['password_salt']
)
print(f"  Correct password verification: {is_valid}")
assert is_valid, "Password verification failed for correct password"

# Wrong password
is_valid = user_manager.verify_password(
    "WrongPassword",
    user['password_hash'],
    user['password_salt']
)
print(f"  Wrong password rejected: {not is_valid}")
assert not is_valid, "Wrong password should not verify"

# Test 4: Create user without password
print("\n4. CREATE USER WITHOUT PASSWORD")
print("-" * 70)

result = user_manager.create_user(
    user_id="user_bob",
    name="Bob Smith",
    email="bob@example.com",
    education_level="High School",
    subject_area="Mathematics",
    learning_goal="Prepare for Calculus",
    preferred_session_duration=45
)
print(f"  Status: {result['status']}")
print(f"  Created user: {result['user_id']}")

user_bob = user_manager.get_user("user_bob")
print(f"  Password hash stored: {bool(user_bob['password_hash'])}")
print(f"  Password salt stored: {bool(user_bob['password_salt'])}")

# Test 5: Test duplicate email validation
print("\n5. DUPLICATE EMAIL VALIDATION")
print("-" * 70)

result = user_manager.create_user(
    user_id="user_charlie",
    name="Charlie Brown",
    email="alice@example.com",  # Same as Alice's email
    education_level="Professional",
    subject_area="Data Science"
)
print(f"  Status: {result['status']}")
print(f"  Error message: {result.get('message', 'N/A')}")
assert result['status'] == 'error', "Duplicate email should be rejected"
assert "email" in result.get('message', '').lower(), "Error should mention email"

# Test 6: Create user with minimal fields
print("\n6. CREATE USER WITH MINIMAL FIELDS")
print("-" * 70)

result = user_manager.create_user(
    user_id="user_diana",
    name="Diana Prince"
)
print(f"  Status: {result['status']}")
print(f"  Created user: {result['user_id']}")

user_diana = user_manager.get_user("user_diana")
print(f"  Email: {user_diana['email']}")
print(f"  Education Level: {user_diana['education_level']}")
print(f"  Subject Area: {user_diana['subject_area']}")

print("\n" + "=" * 70)
print("ALL ENHANCED SIGN-UP TESTS PASSED!")
print("=" * 70)

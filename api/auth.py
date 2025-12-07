"""
Authentication & Session Management for Study Planner
"""

import streamlit as st
from utils.user_profiles import get_user_profile_manager
from datetime import datetime


def init_auth_state():
    """Initialize authentication session state"""
    if "auth_state" not in st.session_state:
        st.session_state.auth_state = {
            "is_logged_in": False,
            "current_user_id": None,
            "current_user_name": None,
            "login_time": None
        }


def login(user_id: str, user_name: str = None, password: str = None) -> bool:
    """Log in a user with optional password verification
    
    Args:
        user_id: The user's ID
        user_name: The user's name (for backwards compatibility)
        password: Optional password for verification
        
    Returns:
        True if login successful, False otherwise
    """
    user_manager = get_user_profile_manager()
    user = user_manager.get_user(user_id)
    
    if not user:
        return False
    
    # Verify password if user has one set and password provided
    if user.get('password_hash') and password:
        if not user_manager.verify_password(password, user['password_hash'], user['password_salt']):
            return False
    elif user.get('password_hash') and not password:
        # User has password but none provided
        return False
    
    st.session_state.auth_state["is_logged_in"] = True
    st.session_state.auth_state["current_user_id"] = user_id
    st.session_state.auth_state["current_user_name"] = user['name']
    st.session_state.auth_state["login_time"] = datetime.now().isoformat()
    st.session_state.current_user = user_id  # Keep for backward compatibility
    
    return True


def logout():
    """Log out the current user"""
    st.session_state.auth_state["is_logged_in"] = False
    st.session_state.auth_state["current_user_id"] = None
    st.session_state.auth_state["current_user_name"] = None
    st.session_state.auth_state["login_time"] = None
    st.session_state.current_user = None
    st.session_state.active_tracking_id = None


def is_logged_in() -> bool:
    """Check if user is logged in"""
    return st.session_state.auth_state.get("is_logged_in", False)


def get_current_user() -> dict:
    """Get current logged-in user info"""
    if not is_logged_in():
        return None
    
    return {
        "user_id": st.session_state.auth_state["current_user_id"],
        "name": st.session_state.auth_state["current_user_name"],
        "login_time": st.session_state.auth_state["login_time"]
    }


def show_login_page():
    """Display login/signup page"""
    # Note: set_page_config is called in main ui.py, not here
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.title("Study Planner")
        st.caption("Personalized AI-powered study planning for students")
        st.markdown("---")
        
        # Create tabs for login and signup
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            
            user_manager = get_user_profile_manager()
            all_users = user_manager.get_all_users()
            
            if all_users:
                # Dropdown to select existing user
                user_names = {u['user_id']: u['name'] for u in all_users}
                selected_user_id = st.selectbox(
                    "Select Your Profile",
                    options=list(user_names.keys()),
                    format_func=lambda x: user_names[x],
                    label_visibility="collapsed"
                )
                
                # Get selected user to check if password is required
                selected_user = user_manager.get_user(selected_user_id)
                
                if selected_user and selected_user.get('password_hash'):
                    # User has password set, require password for login
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    
                    if st.button("Login", use_container_width=True, type="primary"):
                        if login(selected_user_id, password=password):
                            st.success(f"Welcome back, {st.session_state.auth_state['current_user_name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid password. Please try again.")
                else:
                    # No password set, simple login
                    if st.button("Login", use_container_width=True, type="primary"):
                        if login(selected_user_id):
                            st.success(f"Welcome back, {st.session_state.auth_state['current_user_name']}!")
                            st.rerun()
                        else:
                            st.error("Login failed. Please try again.")
            else:
                st.info("No profiles found. Create one to get started!")
        
        with tab2:
            st.subheader("Create New Profile")
            
            # Basic info
            user_id = st.text_input("Profile ID", placeholder="e.g., user_alice")
            name = st.text_input("Your Name", placeholder="e.g., Alice")
            email = st.text_input("Email", placeholder="e.g., alice@example.com")
            
            # Education and subject
            col_left, col_right = st.columns(2)
            
            with col_left:
                education_level = st.selectbox(
                    "Education Level",
                    options=["", "High School", "University", "Professional"],
                    label_visibility="collapsed"
                )
                education_level = education_level if education_level else None
            
            with col_right:
                subject_area = st.text_input("Subject Area", placeholder="e.g., Mathematics, Computer Science")
            
            # Learning preferences
            col_left2, col_right2 = st.columns(2)
            
            with col_left2:
                learning_goal = st.text_input("Learning Goal", placeholder="e.g., Master Python")
            
            with col_right2:
                preferred_duration = st.number_input(
                    "Preferred Session (min)",
                    min_value=15,
                    max_value=180,
                    value=60
                )
            
            # Password (optional)
            st.markdown("**Optional: Set a password for security**")
            col_pwd1, col_pwd2 = st.columns(2)
            
            with col_pwd1:
                password = st.text_input("Password", type="password", placeholder="Leave blank for no password")
            
            with col_pwd2:
                password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            
            # Form validation and submission
            if st.button("Create Profile", use_container_width=True, type="primary"):
                # Validation
                errors = []
                
                if not name or not user_id:
                    errors.append("Profile ID and Name are required")
                
                if email and "@" not in email:
                    errors.append("Please enter a valid email address")
                
                if password != password_confirm:
                    errors.append("Passwords do not match")
                
                if password and len(password) < 6:
                    errors.append("Password must be at least 6 characters")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    user_manager = get_user_profile_manager()
                    result = user_manager.create_user(
                        user_id=user_id,
                        name=name,
                        email=email if email else None,
                        education_level=education_level,
                        subject_area=subject_area if subject_area else None,
                        learning_goal=learning_goal if learning_goal else None,
                        preferred_session_duration=preferred_duration,
                        password=password if password else None
                    )
                    
                    if result['status'] == 'success':
                        st.success("Profile created! Logging in...")
                        if login(user_id, name):
                            st.rerun()
                    else:
                        st.error(result.get('message', 'Error creating profile'))
        
        st.markdown("---")
        st.caption("Your data is stored locally for privacy")


def show_user_header():
    """Display user profile header in top right"""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col3:
        if is_logged_in():
            user_info = get_current_user()
            
            # User profile menu
            with st.container(border=True):
                st.caption(f"User: **{user_info['name']}**")
                
                # Quick status
                user_manager = get_user_profile_manager()
                active = user_manager.get_active_clock_in(user_info['user_id'])
                
                if active:
                    st.caption(f"Tracking: {active['task_name']}")
                
                # Logout button
                if st.button("Logout", use_container_width=True, key="logout_btn"):
                    logout()
                    st.rerun()

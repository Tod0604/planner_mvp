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


def login(user_id: str, user_name: str = None) -> bool:
    """Log in a user"""
    user_manager = get_user_profile_manager()
    user = user_manager.get_user(user_id)
    
    if not user:
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
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                user_id = st.text_input("Profile ID", placeholder="e.g., user_alice")
                learning_goal = st.text_input("Learning Goal", placeholder="e.g., Master Python")
            
            with col_right:
                name = st.text_input("Your Name", placeholder="e.g., Alice")
                preferred_duration = st.number_input(
                    "Preferred Session (min)",
                    min_value=15,
                    max_value=180,
                    value=60
                )
            
            if st.button("Create Profile", use_container_width=True, type="primary"):
                if not name or not user_id:
                    st.error("Please fill in all required fields")
                else:
                    user_manager = get_user_profile_manager()
                    result = user_manager.create_user(user_id, name, learning_goal, preferred_duration)
                    
                    if result['status'] == 'success':
                        st.success(f"Profile created! Logging in...")
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

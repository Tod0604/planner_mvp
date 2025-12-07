"""
Streamlit UI for Study Planner
Multi-page interface for daily planning and deadline management
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Any
import sys
import os
from datetime import datetime, timedelta
import calendar
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database
from utils.planner import get_intelligent_planner
from utils.calendar_store import get_calendar_store
from utils.user_profiles import get_user_profile_manager
from auth import init_auth_state, is_logged_in, get_current_user, logout, show_login_page, show_user_header

# Page config
st.set_page_config(
    page_title="Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication
init_auth_state()

# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Initialize user profile in session state
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "active_tracking_id" not in st.session_state:
    st.session_state.active_tracking_id = None

# Initialize deadlines in session state
if "deadlines" not in st.session_state:
    st.session_state.deadlines = [
        {
            "id": 1,
            "title": "Math Assignment 1",
            "type": "University Assignment",
            "deadline": (datetime.now() + timedelta(days=7)).date(),
            "estimated_time": 120,
            "description": "Calculus problem set - Chapters 1-3",
            "status": "pending"
        },
        {
            "id": 2,
            "title": "Physics Lab Report",
            "type": "University Assignment",
            "deadline": (datetime.now() + timedelta(days=14)).date(),
            "estimated_time": 180,
            "description": "Experiment results and analysis",
            "status": "pending"
        },
        {
            "id": 3,
            "title": "Programming Project",
            "type": "University Assignment",
            "deadline": (datetime.now() + timedelta(days=21)).date(),
            "estimated_time": 360,
            "description": "Build a todo app in Python",
            "status": "pending"
        }
    ]
    st.session_state.next_deadline_id = 4

# Custom CSS with theme support
def get_theme_css(theme: str) -> str:
    """Generate elegant, sophisticated theme CSS with enhanced typography"""
    if theme == "dark":
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
            
            /* Elegant dark mode */
            .main, .main > div {
                background-color: #0f0f0f !important;
                color: #e8e8e8 !important;
            }
            
            .stApp {
                background-color: #0f0f0f !important;
            }
            
            /* Fix header/toolbar background */
            [data-testid="stToolbar"] {
                background-color: #0f0f0f !important;
            }
            
            /* Fix top banner area */
            .stAppHeader {
                background-color: #0f0f0f !important;
            }
            
            /* Ensure no white background anywhere */
            .streamlit-container, section[data-testid="stAppViewContainer"] {
                background-color: #0f0f0f !important;
            }
            
            /* Additional header fixes */
            header {
                background-color: #0f0f0f !important;
            }
            
            [data-testid="stHeader"] {
                background-color: #0f0f0f !important;
            }
            
            /* Top bar/banner */
            .css-1v3fvcr {
                background-color: #0f0f0f !important;
            }
            
            /* App container */
            [role="main"] {
                background-color: #0f0f0f !important;
            }
            
            /* Typography - Headers with Playfair Display */
            h1 {
                font-family: 'Playfair Display', serif !important;
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
                color: #f5f5f5 !important;
                margin-bottom: 0.5rem !important;
            }
            
            h2 {
                font-family: 'Playfair Display', serif !important;
                font-size: 1.8rem !important;
                font-weight: 600 !important;
                letter-spacing: -0.3px !important;
                color: #f5f5f5 !important;
                margin-top: 1.5rem !important;
                margin-bottom: 0.8rem !important;
            }
            
            h3 {
                font-family: 'Playfair Display', serif !important;
                font-size: 1.4rem !important;
                font-weight: 600 !important;
                color: #f5f5f5 !important;
                margin-top: 1.2rem !important;
                margin-bottom: 0.6rem !important;
            }
            
            h4, h5, h6 {
                font-family: 'Inter', sans-serif !important;
                font-weight: 600 !important;
                color: #f5f5f5 !important;
            }
            
            /* Body text with Inter */
            p, span, label, div {
                font-family: 'Inter', sans-serif !important;
                color: #d0d0d0 !important;
                line-height: 1.6 !important;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
                background-color: #1a1a1a !important;
            }
            
            [data-testid="stSidebar"] p, 
            [data-testid="stSidebar"] span, 
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] h2 {
                color: #d0d0d0 !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Markdown */
            [data-testid="stMarkdownContainer"] * {
                color: #d0d0d0 !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Metrics */
            [data-testid="stMetricValue"] {
                color: #64b5f6 !important;
                font-weight: 700 !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 1.8rem !important;
            }
            
            [data-testid="stMetricLabel"] {
                color: #888 !important;
                font-size: 0.85rem !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            
            .stMetric {
                background-color: #1a1a1a !important;
                padding: 1.2rem;
                border-radius: 8px;
                border: 1px solid #333 !important;
            }
            
            /* Input fields */
            .stTextInput input, 
            .stNumberInput input, 
            .stSelectbox select,
            .stDateInput input {
                background-color: #2a2a2a !important;
                color: #e8e8e8 !important;
                border: 1px solid #444 !important;
                border-radius: 6px !important;
                font-family: 'Inter', sans-serif !important;
                padding: 0.6rem 0.8rem !important;
            }
            
            .stTextInput input::placeholder, 
            .stNumberInput input::placeholder {
                color: #666 !important;
            }
            
            /* Sliders */
            [data-testid="stSlider"] {
                color: #d0d0d0 !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #1a5490 !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 1rem !important;
                padding: 0.6rem 1.2rem !important;
                letter-spacing: 0.3px !important;
                transition: all 0.2s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #0f3f6b !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(26, 84, 144, 0.3) !important;
            }
            
            .stButton > button span, .stButton > button p, .stButton > button div {
                color: #ffffff !important;
            }
            
            /* Day selector buttons - consistent styling for dark mode */
            [data-testid="stHorizontalBlock"] .stButton > button {
                font-size: 0.9rem !important;
                padding: 0.5rem 0.75rem !important;
                min-width: 45px !important;
                height: 40px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background-color: #2a2a2a !important;
                color: #d0d0d0 !important;
                border: 2px solid #444 !important;
                font-weight: 600 !important;
            }
            
            [data-testid="stHorizontalBlock"] .stButton > button:hover {
                background-color: #333 !important;
                color: #fff !important;
                border-color: #64b5f6 !important;
                transform: none !important;
            }
            
            /* Radio and checkboxes */
            .stRadio label, .stCheckbox label {
                color: #d0d0d0 !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                border-color: #333 !important;
            }
            
            .stTabs [data-baseweb="tab-list"] button {
                color: #888 !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
                font-size: 0.85rem !important;
                letter-spacing: 0.3px !important;
            }
            
            .stTabs [role="tab"][aria-selected="true"] {
                color: #64b5f6 !important;
                border-bottom-color: #64b5f6 !important;
            }
            
            /* Alert boxes */
            .stAlert, [data-testid="stAlert"] {
                background-color: #1a1a1a !important;
                color: #d0d0d0 !important;
                border-left: 4px solid #64b5f6 !important;
                border-radius: 6px !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            [data-testid="stAlert"] p {
                color: #d0d0d0 !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Dividers */
            hr, [data-testid="stHorizontalBlock"] > hr {
                border-color: #333 !important;
                margin: 1.5rem 0 !important;
            }
            
            /* Caption */
            .stCaption {
                color: #888 !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 0.8rem !important;
                font-weight: 400 !important;
            }
            
            /* Code */
            code {
                background-color: #2a2a2a !important;
                color: #64b5f6 !important;
                border-radius: 4px !important;
                font-family: 'Monaco', monospace !important;
                padding: 2px 6px !important;
            }
            
            /* Dataframe */
            table {
                background-color: #1a1a1a !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            table td, table th {
                color: #d0d0d0 !important;
                border-color: #333 !important;
            }
        </style>
        """
    else:  # Light mode
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
            
            /* Light mode */
            .main, .main > div {
                background-color: #ffffff !important;
                color: #2c2c2c !important;
            }
            
            .stApp {
                background-color: #ffffff;
            }
            
            /* Fix header/toolbar background for light mode */
            [data-testid="stToolbar"] {
                background-color: #ffffff !important;
            }
            
            /* Fix top banner area */
            .stAppHeader {
                background-color: #ffffff !important;
            }
            
            /* Ensure no black background anywhere */
            .streamlit-container, section[data-testid="stAppViewContainer"] {
                background-color: #ffffff !important;
            }
            
            /* Additional header fixes */
            header {
                background-color: #ffffff !important;
            }
            
            [data-testid="stHeader"] {
                background-color: #ffffff !important;
            }
            
            /* Top bar/banner */
            .css-1v3fvcr {
                background-color: #ffffff !important;
            }
            
            /* App container */
            [role="main"] {
                background-color: #ffffff !important;
            }
            
            /* Typography - Headers with Playfair Display */
            h1 {
                font-family: 'Playfair Display', serif !important;
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
                color: #1a1a1a !important;
                margin-bottom: 0.5rem !important;
            }
            
            h2 {
                font-family: 'Playfair Display', serif !important;
                font-size: 1.8rem !important;
                font-weight: 600 !important;
                letter-spacing: -0.3px !important;
                color: #1a1a1a !important;
                margin-top: 1.5rem !important;
                margin-bottom: 0.8rem !important;
            }
            
            h3 {
                font-family: 'Playfair Display', serif !important;
                font-size: 1.4rem !important;
                font-weight: 600 !important;
                color: #1a1a1a !important;
                margin-top: 1.2rem !important;
                margin-bottom: 0.6rem !important;
            }
            
            h4, h5, h6 {
                font-family: 'Inter', sans-serif !important;
                font-weight: 600 !important;
                color: #1a1a1a !important;
            }
            
            /* Body text with Inter */
            p, span, label, div {
                font-family: 'Inter', sans-serif !important;
                color: #4a4a4a !important;
                line-height: 1.6 !important;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
                background-color: #f0f0f0 !important;
            }
            
            [data-testid="stSidebar"] p, 
            [data-testid="stSidebar"] span, 
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] h2 {
                color: #2c2c2c !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Markdown */
            [data-testid="stMarkdownContainer"] * {
                color: #2c2c2c !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Metrics */
            [data-testid="stMetricValue"] {
                color: #1a5490 !important;
                font-weight: 700 !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 1.8rem !important;
            }
            
            [data-testid="stMetricLabel"] {
                color: #888 !important;
                font-size: 0.85rem !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            
            .stMetric {
                background-color: #ffffff !important;
                padding: 1.2rem;
                border-radius: 8px;
                border: 1px solid #e0e0e0 !important;
            }
            
            /* Input fields */
            .stTextInput input, 
            .stNumberInput input, 
            .stSelectbox select,
            .stDateInput input {
                background-color: #ffffff !important;
                color: #2c2c2c !important;
                border: 1px solid #d0d0d0 !important;
                border-radius: 6px !important;
                font-family: 'Inter', sans-serif !important;
                padding: 0.6rem 0.8rem !important;
            }
            
            .stTextInput input::placeholder, 
            .stNumberInput input::placeholder {
                color: #aaa !important;
            }
            
            /* Sliders */
            [data-testid="stSlider"] {
                color: #2c2c2c !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #1a5490 !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 1rem !important;
                padding: 0.6rem 1.2rem !important;
                letter-spacing: 0.3px !important;
                transition: all 0.2s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #0f3f6b !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(26, 84, 144, 0.2) !important;
            }
            
            .stButton > button span, .stButton > button p, .stButton > button div {
                color: #ffffff !important;
            }
            
            /* Day selector buttons - consistent styling for light mode */
            [data-testid="stHorizontalBlock"] .stButton > button {
                font-size: 0.9rem !important;
                padding: 0.5rem 0.75rem !important;
                min-width: 45px !important;
                height: 40px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background-color: #f0f0f0 !important;
                color: #333 !important;
                border: 2px solid #d0d0d0 !important;
                font-weight: 600 !important;
            }
            
            [data-testid="stHorizontalBlock"] .stButton > button span,
            [data-testid="stHorizontalBlock"] .stButton > button p,
            [data-testid="stHorizontalBlock"] .stButton > button div {
                color: #333 !important;
            }
            
            [data-testid="stHorizontalBlock"] .stButton > button:hover {
                background-color: #e0e0e0 !important;
                color: #000 !important;
                border-color: #1a5490 !important;
                transform: none !important;
            }
            
            /* Radio and checkboxes */
            .stRadio label, .stCheckbox label {
                color: #2c2c2c !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                border-color: #e0e0e0 !important;
            }
            
            .stTabs [data-baseweb="tab-list"] button {
                color: #666 !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
                font-size: 0.85rem !important;
                letter-spacing: 0.3px !important;
            }
            
            .stTabs [role="tab"][aria-selected="true"] {
                color: #1a5490 !important;
                border-bottom-color: #1a5490 !important;
            }
            
            /* Alert boxes */
            .stAlert, [data-testid="stAlert"] {
                background-color: #f5f5f5 !important;
                color: #2c2c2c !important;
                border-left: 4px solid #1a5490 !important;
                border-radius: 6px !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            [data-testid="stAlert"] p {
                color: #2c2c2c !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            /* Dividers */
            hr, [data-testid="stHorizontalBlock"] > hr {
                border-color: #e0e0e0 !important;
                margin: 1.5rem 0 !important;
            }
            
            /* Caption */
            .stCaption {
                color: #888 !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 0.8rem !important;
                font-weight: 400 !important;
            }
            
            /* Code */
            code {
                background-color: #f5f5f5 !important;
                color: #1a5490 !important;
                border-radius: 4px !important;
                font-family: 'Monaco', monospace !important;
                padding: 2px 6px !important;
            }
            
            /* Dataframe */
            table {
                background-color: #ffffff !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            table td, table th {
                color: #2c2c2c !important;
                border-color: #e0e0e0 !important;
            }
        </style>
        """

# Apply the theme CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def call_api(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """Call the FastAPI endpoint"""
    try:
        response = requests.post(
            "http://localhost:8000/plan",
            json=user_input,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to API. Make sure FastAPI server is running on port 8000"
        }
    except Exception as e:
        return {"error": str(e)}


def download_json(data: Dict[str, Any]) -> str:
    """Convert data to JSON string"""
    return json.dumps(data, indent=2)


def download_text(data: Dict[str, Any]) -> str:
    """Convert data to readable text"""
    text = "PERSONALIZED STUDY PLAN\n"
    text += "=" * 50 + "\n\n"
    
    text += "RECOMMENDED TASK ORDER:\n"
    text += "-" * 50 + "\n"
    for i, (task, minutes) in enumerate(zip(data.get("ranked_tasks", []), 
                                             data.get("recommended_minutes", [])), 1):
        text += f"{i}. {task} ({minutes} minutes)\n"
    
    text += f"\nPLAN SUMMARY:\n"
    text += "-" * 50 + "\n"
    text += data.get("summary", "No summary available") + "\n"
    
    if "metrics" in data:
        text += f"\nPERFORMANCE METRICS:\n"
        text += "-" * 50 + "\n"
        metrics = data["metrics"]
        text += f"Energy Level: {metrics.get('energy_level', 'N/A')}/5\n"
        text += f"Fatigue Score: {metrics.get('fatigue_score', 'N/A')}\n"
        text += f"Productivity: {metrics.get('productivity_score', 'N/A')}\n"
        text += f"Time Pressure: {metrics.get('time_pressure', 'N/A')}\n"
    
    text += "\n" + "=" * 50 + "\n"
    text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return text


def render_monthly_calendar(year: int, month: int) -> None:
    """Render a monthly calendar with deadline indicators"""
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    st.write(f"### {month_name} {year}")
    
    # Day headers
    day_headers = st.columns(7)
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    for col, day in zip(day_headers, days_of_week):
        with col:
            st.markdown(f"**{day}**")
    
    # Calendar grid
    today = datetime.now().date()
    
    for week in cal:
        week_cols = st.columns(7)
        for col, day_num in zip(week_cols, week):
            with col:
                if day_num == 0:
                    st.empty()
                else:
                    # Create a date object
                    current_date = datetime(year, month, day_num).date()
                    
                    # Check if there are deadlines on this date
                    day_deadlines = [d for d in st.session_state.deadlines 
                                    if d["deadline"] == current_date]
                    
                    # Create day box with styling
                    if current_date == today:
                        st.markdown(f"### **{day_num}** (Today)")
                    elif day_deadlines:
                        st.markdown(f"### **{day_num}**")
                        for dl in day_deadlines:
                            st.caption(f"Deadline: {dl['title']}")
                    else:
                        st.markdown(f"### {day_num}")


def show_daily_planner():
    """Daily planner page"""
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        # Weekly schedule section
        st.subheader("Weekly Schedule")
        st.write("Configure schedule for each day")
        
        # Initialize session state for weekly schedule
        if "selected_day" not in st.session_state:
            st.session_state.selected_day = 0
        if "weekly_schedule" not in st.session_state:
            st.session_state.weekly_schedule = {
                0: {"name": "Monday", "lecture": 120, "lab": 60, "available": 480},
                1: {"name": "Tuesday", "lecture": 120, "lab": 60, "available": 480},
                2: {"name": "Wednesday", "lecture": 120, "lab": 60, "available": 480},
                3: {"name": "Thursday", "lecture": 120, "lab": 60, "available": 480},
                4: {"name": "Friday", "lecture": 120, "lab": 60, "available": 480},
                5: {"name": "Saturday", "lecture": 0, "lab": 0, "available": 480},
                6: {"name": "Sunday", "lecture": 0, "lab": 0, "available": 480},
            }
        
        # Day selector buttons
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_cols = st.columns(7)
        
        for i, (col, day) in enumerate(zip(day_cols, days)):
            with col:
                is_selected = i == st.session_state.selected_day
                button_text = f"**{day}**" if is_selected else day
                
                if st.button(button_text, use_container_width=True, key=f"day_{i}"):
                    st.session_state.selected_day = i
                    st.rerun()
        
        st.divider()
        
        # Configure selected day
        selected_day_idx = st.session_state.selected_day
        selected_day_name = st.session_state.weekly_schedule[selected_day_idx]["name"]
        
        st.write(f"**{selected_day_name}**")
        
        day_config_cols = st.columns(3)
        
        with day_config_cols[0]:
            lecture_time = st.number_input(
                "Lecture",
                min_value=0,
                max_value=480,
                value=st.session_state.weekly_schedule[selected_day_idx]["lecture"],
                step=30,
                key=f"lecture_{selected_day_idx}"
            )
            st.session_state.weekly_schedule[selected_day_idx]["lecture"] = lecture_time
        
        with day_config_cols[1]:
            lab_time = st.number_input(
                "Tutorial/Lab",
                min_value=0,
                max_value=480,
                value=st.session_state.weekly_schedule[selected_day_idx]["lab"],
                step=30,
                key=f"lab_{selected_day_idx}"
            )
            st.session_state.weekly_schedule[selected_day_idx]["lab"] = lab_time
        
        with day_config_cols[2]:
            available_time = st.number_input(
                "Total Available",
                min_value=30,
                max_value=960,
                value=st.session_state.weekly_schedule[selected_day_idx]["available"],
                step=30,
                key=f"available_{selected_day_idx}"
            )
            st.session_state.weekly_schedule[selected_day_idx]["available"] = available_time
        
        total_fixed = lecture_time + lab_time
        remaining = available_time - total_fixed
        
        st.metric("Time for Study Tasks", f"{max(0, remaining)} min")
        
        st.divider()
        
        # Daily commitments section (for current day)
        st.subheader("Study Tasks")
        st.write("Tasks to complete today")
        
        # Number of tasks
        num_tasks = st.slider("Number of tasks", 1, 10, 3, key="num_tasks_slider")
        
        tasks = []
        time_spent = []
        difficulty_ratings = []
        
        for i in range(num_tasks):
            st.write(f"**Task {i+1}**")
            col_a, col_b, col_c = st.columns([2, 1, 1])
            
            with col_a:
                task = st.text_input(f"Title", value=f"Task {i+1}", key=f"task_name_{i}", label_visibility="collapsed")
                tasks.append(task)
            
            with col_b:
                time = st.number_input(f"Min", min_value=10, max_value=480, value=60, key=f"task_time_{i}", label_visibility="collapsed")
                time_spent.append(time)
            
            with col_c:
                difficulty = st.slider(f"Level", 1, 5, 3, key=f"task_diff_{i}", label_visibility="collapsed")
                difficulty_ratings.append(difficulty)
        
        st.divider()
        
        # Energy and goals
        st.subheader("Current Status")
        
        energy_level = st.slider(
            "Energy Level",
            min_value=1,
            max_value=5,
            value=3,
            key="energy_level_slider"
        )
        
        goals_for_tomorrow = st.text_area(
            "Goals for Tomorrow",
            value="",
            placeholder="What do you want to achieve tomorrow?",
            key="goals_textarea"
        )
    
    with col2:
        st.subheader("Generate Plan")
        
        if st.button("Generate Study Plan", use_container_width=True, key="generate_btn"):
            # Prepare input for API
            total_available = sum(d["available"] for d in st.session_state.weekly_schedule.values())
            
            user_input = {
                "tasks": tasks,
                "time_spent": time_spent,
                "difficulty_rating": difficulty_ratings,
                "energy_level": energy_level,
                "goals_for_tomorrow": goals_for_tomorrow if goals_for_tomorrow else "Study effectively",
                "available_minutes": remaining
            }
            
            # Call API
            with st.spinner("Generating personalized study plan..."):
                plan = call_api(user_input)
            
            # Display results
            if "error" in plan:
                st.error(f"Error: {plan['error']}")
            else:
                st.success("Plan generated successfully!")
                
                st.divider()
                
                # Task order
                st.write("### Task Priority Order")
                for i, (task, minutes) in enumerate(zip(plan.get("ranked_tasks", []), 
                                                         plan.get("recommended_minutes", [])), 1):
                    st.markdown(f"**{i}. {task}** - {minutes} min")
                
                st.divider()
                
                # Plan summary
                st.write("### Recommended Plan")
                st.info(plan.get("summary", "No summary available"))
                
                # Adjustment info
                if "adjustment_explanation" in plan:
                    st.write("### Plan Adjustments")
                    adjustment_text = {
                        "no_adjustment": "Your tasks fit perfectly within available time!",
                        "reduce_tasks": "Some tasks may need to be reduced in scope or moved to another day.",
                        "extend_time": "Consider extending study time or reducing task difficulty.",
                        "energy_warning": "Your energy level suggests breaking tasks into smaller chunks."
                    }
                    st.write(adjustment_text.get(plan.get("adjustment_explanation", "no_adjustment"), "No adjustment"))
                
                st.divider()
                
                # Deadline recommendations
                st.write("### Deadline Recommendations")
                
                try:
                    planner = get_intelligent_planner()
                    
                    # Get urgent deadlines
                    urgent_deadlines = planner.get_urgent_deadlines(days_ahead=7)
                    
                    if urgent_deadlines:
                        st.info(f"Found {len(urgent_deadlines)} upcoming deadline(s) to consider")
                        
                        for deadline in urgent_deadlines:
                            # Urgency level based on score
                            if deadline.urgency_score >= 0.75:
                                urgency_level = "CRITICAL"
                            elif deadline.urgency_score >= 0.5:
                                urgency_level = "HIGH"
                            else:
                                urgency_level = "MEDIUM"
                            
                            col_d1, col_d2 = st.columns([2, 1])
                            
                            with col_d1:
                                st.markdown(f"**[{urgency_level}] {deadline.title}**")
                                st.caption(f"Type: {deadline.type} | Estimated: {deadline.estimated_time} min")
                                st.caption(f"Due: {deadline.due_date} ({deadline.days_until} days)")
                            
                            with col_d2:
                                st.metric("Urgency", f"{deadline.urgency_score:.0%}")
                                st.caption(urgency_level)
                    else:
                        st.success("No urgent deadlines - you're on track!")
                    
                    # Schedule conflicts
                    conflicts = planner.detect_schedule_conflicts(days_ahead=7)
                    if conflicts:
                        st.warning(f"Schedule conflicts detected on {len(conflicts)} day(s):")
                        for conflict in conflicts:
                            st.caption(f"{conflict['date']}: {len(conflict['deadlines'])} deadline(s), "
                                     f"{conflict['total_time']} minutes total")
                
                except Exception as e:
                    st.warning(f"Could not load deadline recommendations: {str(e)}")
                
                st.divider()
                if 'metrics' in plan:
                    st.write("### Performance Metrics")
                    metrics = plan['metrics']
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        st.metric("Energy", f"{int(metrics.get('energy_level', 0))}/5")
                    
                    with col_m2:
                        st.metric("Fatigue", f"{metrics.get('fatigue_score', 0):.1f}")
                    
                    with col_m3:
                        st.metric("Productivity", f"{metrics.get('productivity_score', 0):.2f}")
                    
                    with col_m4:
                        st.metric("Time Pressure", f"{metrics.get('time_pressure', 0):.2f}")
                
                st.divider()
                
                # Export options
                st.write("### Export Plan")
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    json_data = download_json(plan)
                    st.download_button(
                        label="Download as JSON",
                        data=json_data,
                        file_name="study_plan.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col_exp2:
                    text_data = download_text(plan)
                    st.download_button(
                        label="Download as Text",
                        data=text_data,
                        file_name="study_plan.txt",
                        mime="text/plain",
                        use_container_width=True
                    )


def show_deadline_manager():
    """Deadline management page with monthly calendar"""
    
    st.subheader("Deadline Manager")
    st.write("Track and manage your assignment deadlines")
    
    # Calendar navigation
    col_cal1, col_cal2, col_cal3 = st.columns([0.5, 2, 0.5])
    
    # Initialize calendar state
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = datetime.now().month
    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = datetime.now().year
    
    with col_cal1:
        if st.button("Back", use_container_width=True, key="prev_month_btn"):
            st.session_state.calendar_month -= 1
            if st.session_state.calendar_month < 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            st.rerun()
    
    with col_cal2:
        st.write(f"**{calendar.month_name[st.session_state.calendar_month]} {st.session_state.calendar_year}**")
    
    with col_cal3:
        if st.button("Next", use_container_width=True, key="next_month_btn"):
            st.session_state.calendar_month += 1
            if st.session_state.calendar_month > 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            st.rerun()
    
    st.divider()
    
    # Render calendar
    render_monthly_calendar(st.session_state.calendar_year, st.session_state.calendar_month)
    
    st.divider()
    
    # Deadlines list from database
    st.subheader("Active Deadlines")
    db = get_database()
    deadlines = db.get_all_deadlines(status="not_started")
    if not deadlines:
        st.info("No deadlines yet. Add one below!")
    else:
        # Sort by due date
        sorted_deadlines = sorted(deadlines, key=lambda x: x["due_date"])
        for deadline in sorted_deadlines:
            # Handle both date-only and datetime formats
            due_date_str = deadline["due_date"]
            if "T" in due_date_str:
                due_date = datetime.strptime(due_date_str.split("T")[0], "%Y-%m-%d").date()
            else:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            days_until = (due_date - datetime.now().date()).days
            status_icon = "TODAY" if days_until == 0 else ("OVERDUE" if days_until < 0 else f"{days_until}d left")
            planner = get_intelligent_planner()
            urgency_score = planner.calculate_urgency_score(deadline["due_date"], deadline["estimated_time"])
            if urgency_score >= 0.75:
                urgency_label = "[CRITICAL]"
            elif urgency_score >= 0.5:
                urgency_label = "[HIGH]"
            else:
                urgency_label = "[MEDIUM]"
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                with col1:
                    st.markdown(f"**{urgency_label} {deadline['title']}**")
                    st.caption(f"{deadline['type']} - Due: {due_date.strftime('%b %d, %Y')}")
                    st.caption(f"Estimated: {deadline['estimated_time']} min | {deadline['description']}")
                with col2:
                    st.write(f"**{status_icon}**")
                with col3:
                    st.metric("Urgency", f"{urgency_score:.0%}")
                with col4:
                    # Status update dropdown
                    valid_statuses = ["not_started", "in_progress", "completed", "overdue"]
                    current_status = deadline["status"]
                    if current_status in valid_statuses:
                        current_index = valid_statuses.index(current_status)
                    else:
                        current_index = 0
                    new_status = st.selectbox(
                        "Status",
                        valid_statuses,
                        index=current_index,
                        key=f"status_{deadline['id']}"
                    )
                    if new_status != deadline["status"]:
                        db.update_deadline_status(deadline["id"], new_status)
                        st.success(f"Updated status for {deadline['title']} to {new_status}")
                        st.rerun()
                    # Progress view
                    progress = planner.get_deadline_progress(deadline["id"])
                    st.progress(progress.get("completion_percent", 0) / 100, text=f"{progress.get('completed_tasks', 0)} / {progress.get('total_tasks', 0)} tasks done")
    
    st.divider()
    
    # Add new deadline
    st.subheader("Add New Deadline")
    
    # Initialize success flag in session state
    if "deadline_added_success" not in st.session_state:
        st.session_state.deadline_added_success = False
    
    col_add1, col_add2 = st.columns(2)
    
    with col_add1:
        title = st.text_input("Assignment Title", placeholder="e.g., Math Assignment 2", key="deadline_title_input")
        deadline_type = st.selectbox("Type", ["assignment", "exam", "project", "other"], key="deadline_type_select")
    
    with col_add2:
        deadline_date = st.date_input("Deadline Date", key="deadline_date_input")
        estimated_time = st.number_input("Estimated Time (minutes)", min_value=30, value=120, step=30, key="deadline_time_input")
    
    description = st.text_area("Description", placeholder="Brief description of the task", key="deadline_desc_input")
    
    # Add deadline button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("Add Deadline", use_container_width=True, key="add_deadline_btn", type="primary"):
            if not title or title.strip() == "":
                st.error("Please enter a title for the deadline")
            else:
                db = get_database()
                try:
                    deadline_dict = {
                        "title": title.strip(),
                        "type": deadline_type,
                        "due_date": deadline_date.strftime("%Y-%m-%d"),
                        "estimated_time": int(estimated_time),
                        "description": description.strip() if description else "No description",
                        "status": "not_started"
                    }
                    deadline_id = db.add_deadline(deadline_dict)
                    if deadline_id:
                        st.session_state.deadline_added_success = True
                        st.success(f"✓ Successfully added deadline: {title}")
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to add deadline")
                except Exception as e:
                    st.error(f"Error adding deadline: {str(e)}")


def show_user_profiles_page():
    """User Profiles & Personalization page"""
    st.subheader("User Profiles & Personalization")
    st.write("Track individual learning patterns and manage time sessions")
    
    user_manager = get_user_profile_manager()
    
    # Get current logged-in user
    current_user = get_current_user()
    if not current_user:
        st.error("Please log in first")
        return
    
    user_id = current_user['user_id']
    user_data = user_manager.get_user(user_id)
    
    # Display current user profile
    st.markdown(f"**Profile:** {user_data['name']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Learning Goal", user_data['learning_goal'] or "Not set")
    with col2:
        st.metric("Preferred Session", f"{user_data['preferred_session_duration']} min")
    with col3:
        active = user_manager.get_active_clock_in(user_id)
        status = "Tracking" if active else "Idle"
        st.metric("Status", status)
    
    st.divider()
    
    # Two tabs: Time Tracking and Profile Settings
    tab1, tab2 = st.tabs(["Time Tracking", "Profile Settings"])
    
    # TAB 1: Time Tracking
    with tab1:
        st.write("Clock in and out of study sessions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Clock In")
            task_name = st.text_input("Task Name", placeholder="e.g., Mathematics - Calculus", key="clock_in_task")
            
            if st.button("Start Task", use_container_width=True, type="primary"):
                if task_name:
                    result = user_manager.clock_in(user_id, task_name)
                    if result['status'] == 'success':
                        st.session_state.active_tracking_id = result['tracking_id']
                        st.success(f"Clocked in: {task_name}")
                        st.rerun()
                else:
                    st.error("Please enter a task name")
        
        with col2:
            st.subheader("Clock Out")
            active = user_manager.get_active_clock_in(user_id)
            
            if active:
                st.info(f"Currently tracking: **{active['task_name']}**")
                difficulty = st.select_slider("Difficulty Level", options=[1, 2, 3, 4, 5], value=3)
                notes = st.text_area("Notes", placeholder="How did it go?", height=100)
                
                if st.button("End Task", use_container_width=True, type="primary"):
                    result = user_manager.clock_out(user_id, active['tracking_id'], difficulty, notes)
                    if result['status'] == 'success':
                        st.session_state.active_tracking_id = None
                        st.success(f"Clocked out - Duration: {result['duration_minutes']} minutes")
                        st.rerun()
                    else:
                        st.error(result.get('message', 'Error clocking out'))
            else:
                st.caption("No active session. Start a task first!")
        
        st.divider()
        st.subheader("Recent Sessions")
        
        history = user_manager.get_time_tracking_history(user_id, days=7)
        
        if history:
            df_history = pd.DataFrame([
                {
                    'Date': h['date'],
                    'Task': h['task_name'],
                    'Duration (min)': h['duration_minutes'],
                    'Difficulty': h['difficulty_rating'],
                    'Notes': h['notes'] or '-'
                }
                for h in history
            ])
            st.dataframe(df_history, use_container_width=True)
        else:
            st.caption("No tracked sessions yet")
    
    # TAB 2: Profile Settings
    with tab2:
        st.write("Manage your profile preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Name", value=user_data['name'])
            new_goal = st.text_input("Learning Goal", value=user_data['learning_goal'] or "")
        
        with col2:
            new_duration = st.number_input(
                "Preferred Session Duration (min)",
                min_value=15,
                max_value=180,
                value=user_data['preferred_session_duration'] or 60
            )
        
        if st.button("Update Profile", use_container_width=True):
            st.success("Profile updated!")
            st.caption("(Profile update feature coming soon)")


def show_personalized_insights_page():
    """Personalized Insights & Recommendations page"""
    st.subheader("Your Personalized Insights")
    st.write("Analytics and recommendations based on your study patterns")
    
    # Get current logged-in user
    current_user = get_current_user()
    if not current_user:
        st.error("Please log in first")
        return
    
    user_manager = get_user_profile_manager()
    user_id = current_user['user_id']
    user_data = user_manager.get_user(user_id)
    
    st.write(f"Profile: **{user_data['name']}**")
    
    # Get analytics
    analytics = user_manager.calculate_analytics(user_id)
    
    if analytics.get('status') != 'success':
        st.warning(analytics.get('message', 'Not enough data to calculate analytics'))
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Session", f"{analytics['avg_session_duration']:.0f} min")
    
    with col2:
        st.metric("Best Study Time", analytics['most_productive_hour'])
    
    with col3:
        st.metric("Productivity", f"{analytics['productivity_score']:.0f}/100")
    
    with col4:
        st.metric("Total Hours", f"{analytics['total_study_hours']:.1f}h")
    
    st.divider()
    
    # Get insights
    insights = user_manager.get_personalized_insights(user_id)
    
    if insights['status'] == 'success':
        st.subheader("Key Insights")
        
        for insight in insights['insights']:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1]

)
                with col1:
                    st.markdown(f"**{insight['title']}**")
                    st.caption(insight['message'])
                with col2:
                    st.markdown(f"### {insight['metric']}")
    
    st.divider()
    
    # Study pattern visualization
    st.subheader("Study Patterns")
    
    history = user_manager.get_time_tracking_history(user_id, days=30)
    
    if history:
        # Group by hour
        hour_data = {}
        for h in history:
            if h['clock_in_time']:
                hour = datetime.fromisoformat(h['clock_in_time']).hour
                hour_key = f"{hour:02d}:00"
                hour_data[hour_key] = hour_data.get(hour_key, 0) + 1
        
        if hour_data:
            df_hours = pd.DataFrame(list(hour_data.items()), columns=['Hour', 'Sessions'])
            st.bar_chart(df_hours.set_index('Hour'), height=300)
        
        # Difficulty distribution
        difficulties = [h['difficulty_rating'] for h in history if h['difficulty_rating']]
        if difficulties:
            st.write("**Difficulty Levels You Encounter**")
            difficulty_dist = {i: difficulties.count(i) for i in range(1, 6)}
            st.bar_chart(pd.DataFrame(list(difficulty_dist.items()), columns=['Difficulty', 'Count']).set_index('Difficulty'), height=200)
    else:
        st.caption("Not enough data to show patterns")


def main():
    """Main Streamlit app with page navigation"""
    
    # Check if user is logged in
    if not is_logged_in():
        show_login_page()
        return
    
    # User is logged in - show main app
    st.title("Study Planner")
    st.write("Personalized AI-powered study planning for students")
    
    # Show user header in top right
    show_user_header()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Settings")
        
        # Page navigation
        st.subheader("Navigation")
        page = st.radio(
            "Select Page",
            ["Daily Planner", "Deadline Manager", "Calendar & History", "Feedback", "User Profiles", "Insights"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Theme selector
        st.subheader("Appearance")
        theme_cols = st.columns(2)
        
        with theme_cols[0]:
            if st.button("Light", use_container_width=True, key="light_theme_btn"):
                st.session_state.theme = "light"
                st.rerun()
        
        with theme_cols[1]:
            if st.button("Dark", use_container_width=True, key="dark_theme_btn"):
                st.session_state.theme = "dark"
                st.rerun()
        
        st.caption(f"Current: {'Light' if st.session_state.theme == 'light' else 'Dark'}")
        
        st.divider()
        
        st.info("Connected to API backend")
        st.markdown("""
        **Quick Guide:**
        - **Daily Planner**: Configure schedule and generate daily plans
        - **Deadline Manager**: Track assignments and deadlines
        - **Calendar & History**: View saved plans over time
        - **Feedback**: Log daily results and improve future plans
        """)
        st.divider()
        st.subheader("API Quick Access")
        st.markdown("""
        - [API Docs](http://localhost:8000/docs)
        - [Health Check](http://localhost:8000/health)
        - [List Deadlines](http://localhost:8000/deadlines)
        - [Deadline Recommendations](http://localhost:8000/deadlines/recommendations/120)
        - [Schedule Conflicts](http://localhost:8000/deadlines/conflicts/7)
        """)
    
    # Route to appropriate page
    if page == "Daily Planner":
        show_daily_planner()
    elif page == "Deadline Manager":
        show_deadline_manager()
    elif page == "Calendar & History":
        show_calendar_overview()
    elif page == "Feedback":
        show_feedback_page()
    elif page == "User Profiles":
        show_user_profiles_page()
    else:
        show_personalized_insights_page()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Study Planner MVP | Powered by Machine Learning</p>
        <p><small>Start -> Plan -> Execute -> Learn</small></p>
    </div>
    """, unsafe_allow_html=True)


def show_calendar_overview():
    """Calendar view with weekly/monthly plan summary"""
    
    st.subheader("Calendar & Plan History")
    st.write("View your saved plans and study patterns over time")
    
    calendar_store = get_calendar_store()
    
    # Date range selector
    st.write("### View Plans")
    col_date1, col_date2 = st.columns(2)
    
    with col_date1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=7),
            key="calendar_start_date"
        )
    
    with col_date2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date(),
            key="calendar_end_date"
        )
    
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    # Get plans in range
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    plans = calendar_store.list_plans(start_str, end_str)
    
    if not plans:
        st.info(f"No plans found between {start_str} and {end_str}. Generate a plan to get started!")
    else:
        # Display stats
        st.write("### Summary Statistics")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        total_planned = sum(p["total_planned_minutes"] for p in plans)
        avg_planned = total_planned / len(plans) if plans else 0
        total_tasks = sum(p["num_tasks"] for p in plans)
        
        with col_stat1:
            st.metric("Total Days Planned", len(plans))
        
        with col_stat2:
            st.metric("Total Minutes Planned", int(total_planned))
        
        with col_stat3:
            st.metric("Avg Minutes/Day", int(avg_planned))
        
        with col_stat4:
            st.metric("Total Tasks", int(total_tasks))
        
        st.divider()
        
        # Chart: Minutes per day
        st.write("### Study Load Over Time")
        chart_data = pd.DataFrame([
            {
                "Date": p["date"],
                "Planned Minutes": p["total_planned_minutes"],
                "Available Minutes": p["available_minutes"],
                "Tasks": p["num_tasks"]
            }
            for p in plans
        ])
        
        # Line chart
        st.line_chart(
            chart_data.set_index("Date")[["Planned Minutes", "Available Minutes"]],
            height=300
        )
        
        st.divider()
        
        # Detailed table
        st.write("### Detailed Plans")
        
        table_data = []
        for plan in plans:
            feedback = calendar_store.get_feedback(plan["date"])
            table_data.append({
                "Date": plan["date"],
                "Tasks": plan["num_tasks"],
                "Planned (min)": plan["total_planned_minutes"],
                "Available (min)": plan["available_minutes"],
                "Completion %": f"{feedback['completion_ratio']*100:.0f}%" if feedback else "—",
                "Tiredness": f"{feedback['tiredness_end_of_day']}/5" if feedback else "—"
            })
        
        df_display = pd.DataFrame(table_data)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Individual day view
        st.write("### View Specific Day")
        selected_date = st.selectbox(
            "Select a date:",
            [p["date"] for p in plans],
            format_func=lambda x: f"{x} ({datetime.strptime(x, '%Y-%m-%d').strftime('%A')})",
            key="calendar_date_select"
        )
        
        if selected_date:
            plan = calendar_store.get_plan(selected_date)
            feedback = calendar_store.get_feedback(selected_date)
            
            st.write(f"### Plan for {selected_date}")
            
            col_day1, col_day2, col_day3 = st.columns(3)
            
            plan_summary = [p for p in plans if p["date"] == selected_date][0]
            
            with col_day1:
                st.metric("Tasks", plan_summary["num_tasks"])
            
            with col_day2:
                st.metric("Total Minutes", plan_summary["total_planned_minutes"])
            
            with col_day3:
                st.metric("Available", plan_summary["available_minutes"])
            
            if plan:
                st.write("**Ranked Tasks:**")
                for i, (task, minutes) in enumerate(zip(plan.get("ranked_tasks", []), plan.get("recommended_minutes", [])), 1):
                    st.write(f"{i}. **{task}** - {minutes} minutes")
                
                st.write(f"\n**Summary:** {plan.get('summary', 'N/A')}")
            
            if feedback:
                st.divider()
                st.write("**Feedback:**")
                col_fb1, col_fb2, col_fb3 = st.columns(3)
                
                with col_fb1:
                    st.metric("Completion", f"{feedback['completion_ratio']*100:.0f}%")
                
                with col_fb2:
                    st.metric("Tiredness", f"{feedback['tiredness_end_of_day']}/5")
                
                with col_fb3:
                    if feedback['notes']:
                        st.info(f"📝 {feedback['notes']}")
            else:
                st.info("No feedback submitted yet for this day")


def show_feedback_page():
    """Feedback collection and analysis page"""
    
    st.subheader("Daily Feedback & Learning")
    st.write("Record how your study day went to help improve future plans")
    
    calendar_store = get_calendar_store()
    
    # Tabs for feedback submission and history
    tab_submit, tab_history = st.tabs(["Submit Feedback", "Feedback History"])
    
    with tab_submit:
        st.write("### Submit Today's Feedback")
        st.write("After your study session, tell us how it went!")
        
        # Get today's date and plan
        today = datetime.now().strftime("%Y-%m-%d")
        plan = calendar_store.get_plan(today)
        
        if not plan:
            st.warning("No plan found for today. Generate a plan first on the Daily Planner page.")
        else:
            col_fb1, col_fb2 = st.columns(2)
            
            with col_fb1:
                st.write("**Today's Plan:**")
                for i, (task, minutes) in enumerate(zip(plan.get("ranked_tasks", []), plan.get("recommended_minutes", [])), 1):
                    st.write(f"{i}. {task} ({minutes}m)")
            
            with col_fb2:
                st.write("**How did it go?**")
            
            st.divider()
            
            # Feedback form
            col_comp, col_tired = st.columns(2)
            
            with col_comp:
                completion_ratio = st.slider(
                    "How much of the plan did you complete?",
                    min_value=0,
                    max_value=100,
                    value=75,
                    step=5,
                    key="feedback_completion"
                )
                completion_pct = completion_ratio / 100.0
            
            with col_tired:
                tiredness = st.slider(
                    "How tired are you now?",
                    min_value=1,
                    max_value=5,
                    value=3,
                    step=1,
                    format="%d/5",
                    key="feedback_tiredness"
                )
            
            notes = st.text_area(
                "Any notes or observations?",
                placeholder="e.g., 'Got through Math but Physics took longer than expected'",
                key="feedback_notes"
            )
            
            # Submit button
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                if st.button("Submit Feedback", type="primary", use_container_width=True, key="submit_feedback_btn"):
                    try:
                        success = calendar_store.save_feedback(
                            date=today,
                            completion_ratio=completion_pct,
                            tiredness_end_of_day=tiredness,
                            notes=notes if notes else None
                        )
                        
                        if success:
                            st.success("✓ Feedback saved! This helps us improve your plans.")
                            st.balloons()
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to save feedback")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab_history:
        st.write("### Feedback History")
        st.write("Track your completion rates and energy levels over time")
        
        col_hist1, col_hist2 = st.columns(2)
        
        with col_hist1:
            hist_start = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=30),
                key="feedback_hist_start"
            )
        
        with col_hist2:
            hist_end = st.date_input(
                "End Date",
                value=datetime.now().date(),
                key="feedback_hist_end"
            )
        
        if hist_start > hist_end:
            st.error("Start date must be before end date")
        else:
            start_str = hist_start.strftime("%Y-%m-%d")
            end_str = hist_end.strftime("%Y-%m-%d")
            feedback_entries = calendar_store.get_feedback_range(start_str, end_str)
            
            if not feedback_entries:
                st.info(f"No feedback found between {start_str} and {end_str}")
            else:
                # Stats
                st.write("### Summary")
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                completion_ratios = [f["completion_ratio"] for f in feedback_entries]
                tiredness_levels = [f["tiredness_end_of_day"] for f in feedback_entries]
                
                with col_stat1:
                    st.metric("Days Logged", len(feedback_entries))
                
                with col_stat2:
                    avg_completion = sum(completion_ratios) / len(completion_ratios) * 100
                    st.metric("Avg Completion", f"{avg_completion:.0f}%")
                
                with col_stat3:
                    avg_tiredness = sum(tiredness_levels) / len(tiredness_levels)
                    st.metric("Avg Tiredness", f"{avg_tiredness:.1f}/5")
                
                with col_stat4:
                    high_completion_days = sum(1 for c in completion_ratios if c >= 0.8)
                    st.metric("High Completion Days", high_completion_days)
                
                st.divider()
                
                # Chart
                st.write("### Trends")
                chart_fb_data = pd.DataFrame([
                    {
                        "Date": f["date"],
                        "Completion %": f["completion_ratio"] * 100,
                        "Tiredness": f["tiredness_end_of_day"]
                    }
                    for f in feedback_entries
                ])
                
                st.line_chart(
                    chart_fb_data.set_index("Date"),
                    height=300
                )
                
                st.divider()
                
                # Detailed table
                st.write("### Detailed Feedback Log")
                
                table_fb_data = []
                for fb in feedback_entries:
                    table_fb_data.append({
                        "Date": fb["date"],
                        "Completion": f"{fb['completion_ratio']*100:.0f}%",
                        "Tiredness": f"{fb['tiredness_end_of_day']}/5",
                        "Notes": fb["notes"] or "—"
                    })
                
                df_fb = pd.DataFrame(table_fb_data)
                st.dataframe(df_fb, use_container_width=True, hide_index=True)





if __name__ == "__main__":
    main()

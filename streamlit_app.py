import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

# Set page config
st.set_page_config(
    page_title="Femme - Menstrual Cycle Tracking",
    page_icon="🌸",
    layout="wide"
)

# API endpoint
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #FFF5F5;
    }
    .main {
        padding: 2rem;
    }
    .st-emotion-cache-1v0mbdj.e115fcil1 {
        border-radius: 10px;
        padding: 1.5rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# User login/registration section
def login_section():
    st.title("🌸 Femme - Your Personal Cycle Companion")
    
    with st.form("login_form"):
        user_id = st.text_input("Enter your User ID")
        submitted = st.form_submit_button("Start Tracking")
        
        if submitted and user_id:
            try:
                # Create user if doesn't exist
                response = requests.post(f"{API_URL}/users/", json={"user_id": user_id})
                # Handle both successful creation and existing user cases
                if response.status_code in [200, 201] or 'IntegrityError' in str(response.content):
                    st.session_state.user_id = user_id
                    st.success("Welcome to Femme!")
                    st.rerun()
                else:
                    st.error("An unexpected error occurred. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to server: {str(e)}")

# Cycle data input section
def cycle_data_input():
    st.subheader("📝 Daily Wellness Check-in")
    
    with st.form("cycle_data_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cycle_phase = st.selectbox(
                "Current Cycle Phase",
                ["menstrual", "follicular", "ovulation", "luteal"]
            )
            sleep_score = st.slider("Sleep Quality", 1, 10, 5)
            mood_score = st.slider("Mood", 1, 10, 5)
        
        with col2:
            stress_level = st.slider("Stress Level", 1, 10, 5)
            pain_level = st.slider("Pain Level", 1, 10, 5)
            energy_level = st.slider("Energy Level", 1, 10, 5)
        
        submitted = st.form_submit_button("Save Daily Check-in")
        
        if submitted:
            try:
                data = {
                    "user_id": st.session_state.user_id,
                    "cycle_phase": cycle_phase,
                    "sleep_score": sleep_score,
                    "mood_score": mood_score,
                    "stress_level": stress_level,
                    "pain_level": pain_level,
                    "energy_level": energy_level
                }
                response = requests.post(f"{API_URL}/cycle-data/", json=data)
                if response.status_code == 200:
                    st.success("Daily check-in saved successfully!")
                else:
                    st.error("Error saving data")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to server: {str(e)}")

# Notifications section
def display_notifications():
    st.subheader("🔔 Your Personalized Recommendations")
    
    try:
        response = requests.get(f"{API_URL}/notifications/generate/{st.session_state.user_id}")
        if response.status_code == 200:
            notification = response.json()
            
            with st.container():
                st.info(notification["message"])
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("I'll do it! 👍", key="accept_notification"):
                        feedback = {
                            "notification_id": notification["notification_id"],
                            "action_taken": 1,
                            "effectiveness": 8.0,  # Default positive feedback
                            "next_day_energy": 7,
                            "next_day_mood": 7
                        }
                        requests.post(f"{API_URL}/notifications/feedback/", json=feedback)
                        st.success("Great choice! Keep up the good work!")
                
                with col2:
                    if st.button("Maybe later 🤔", key="decline_notification"):
                        feedback = {
                            "notification_id": notification["notification_id"],
                            "action_taken": 0,
                            "effectiveness": 5.0,
                            "next_day_energy": 5,
                            "next_day_mood": 5
                        }
                        requests.post(f"{API_URL}/notifications/feedback/", json=feedback)
                        st.info("No problem! We'll suggest something else next time.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching notifications: {str(e)}")

# Analytics section
def display_analytics():
    st.subheader("📊 Your Wellness Insights")
    
    try:
        response = requests.get(f"{API_URL}/analytics/user/{st.session_state.user_id}")
        if response.status_code == 200:
            analytics = response.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("🌟 Most Effective Activities for You:")
                for action in analytics["top_actions"]:
                    st.write(f"- {action.replace('_', ' ').title()}")
            
            with col2:
                effectiveness_data = []
                for action, stats in analytics["action_effectiveness"].items():
                    effectiveness_data.append({
                        "action": action.replace('_', ' ').title(),
                        "score": stats["average"]
                    })
                
                if effectiveness_data:
                    df = pd.DataFrame(effectiveness_data)
                    if not df.empty and all(col in df.columns for col in ["action", "score"]):
                        fig = px.bar(
                            df,
                            x="action",
                            y="score",
                            title="Activity Effectiveness",
                            color="score",
                            color_continuous_scale="RdYlBu",
                            labels={"action": "Action", "score": "Effectiveness Score"}
                        )
                        st.plotly_chart(fig)
                    else:
                        st.warning("No effectiveness data available to display.")
                else:
                    st.warning("No effectiveness data available to display.")
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching analytics: {str(e)}")

# Main app layout
def main():
    if not st.session_state.user_id:
        login_section()
    else:
        st.sidebar.title(f"Welcome, {st.session_state.user_id}!")
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cycle_data_input()
            st.markdown("---")
            display_analytics()
        
        with col2:
            display_notifications()

if __name__ == "__main__":
    main()
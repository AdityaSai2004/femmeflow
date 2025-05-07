# Femme: Menstrual Cycle Q-Learning App

## Overview
Femme is a hyperpersonalised wellness and menstrual cycle tracking application that leverages Q-learning (a reinforcement learning algorithm) to deliver tailored recommendations and insights for users. The app consists of a Streamlit-based frontend and a FastAPI backend, enabling users to log daily wellness data, receive actionable suggestions, and view analytics on their habits and cycle phases.

## Features
- **User Registration & Login:** Simple user onboarding with unique user IDs.
- **Daily Wellness Check-in:** Log cycle phase, sleep, mood, stress, pain, and energy levels.
- **Personalised Recommendations:** Receive daily suggestions (e.g., mindfulness, movement, nutrition) based on your current state and Q-learning-driven insights.
- **Feedback Loop:** Provide feedback on recommendations, which is used to improve future suggestions.
- **Analytics Dashboard:** Visualise the effectiveness of different actions and track your wellness trends over time.

## How It Works
Femme uses a Q-learning agent to learn which actions (recommendations) are most effective for each user in different states (combinations of cycle phase, mood, sleep, etc.). Over time, the system adapts to each user's unique patterns, delivering hyperpersonalised suggestions that are most likely to improve their wellbeing.

### Q-Learning & Hyperpersonalisation
- **State:** Defined by user data (cycle phase, sleep, mood, stress, pain, energy, time of day).
- **Actions:** Possible recommendations (e.g., stretch, mindfulness, magnesium, nap, snack, movement).
- **Reward:** Calculated from user feedback and next-day improvements in energy/mood.
- **Learning:** The agent updates its Q-table for each user, learning which actions yield the best outcomes in each state.
- **Hyperpersonalisation:** Each user has a separate Q-table, so recommendations become increasingly tailored as more data is collected.

## Project Structure
- `streamlit_app.py`: Streamlit frontend for user interaction and analytics.
- `menstrual_cycle_app.py`: FastAPI backend implementing the Q-learning logic, user management, and API endpoints.
- `populate_db.py`: (Optional) Script for populating the database with sample data.

## Getting Started
### Prerequisites
- Python 3.8+
- Recommended: Create a virtual environment

### Installation
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd femme
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, install: streamlit, fastapi, uvicorn, sqlalchemy, pandas, plotly, requests)*

### Running the App
1. **Start the FastAPI backend:**
   ```sh
   uvicorn menstrual_cycle_app:app --reload
   ```
   This will start the API at `http://localhost:8000`.

2. **Start the Streamlit frontend:**
   ```sh
   streamlit run streamlit_app.py
   ```
   Access the app at the URL shown in your terminal (usually `http://localhost:8501`).

## Usage
- Register or log in with a user ID.
- Complete your daily wellness check-in.
- Review and act on personalised recommendations.
- Provide feedback to help the system learn.
- Explore your analytics dashboard for insights.

## API Endpoints (Backend)
- `POST /users/`: Register a new user.
- `POST /cycle-data/`: Submit daily wellness data.
- `GET /notifications/generate/{user_id}`: Get a personalised recommendation.
- `POST /notifications/feedback/`: Submit feedback on a recommendation.
- `GET /analytics/user/{user_id}`: Retrieve analytics for a user.

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License
MIT License

---
*Femme: Empowering women with AI-driven, hyperpersonalised wellness insights.*
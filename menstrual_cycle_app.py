# menstrual_cycle_app.py - FastAPI application for menstrual cycle Q-learning
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import random
from datetime import datetime, time
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# FastAPI app initialization
app = FastAPI(title="Menstrual Cycle Q-Learning API")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./menstrual_cycle_ql.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now)

class CycleData(Base):
    __tablename__ = "cycle_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    cycle_phase = Column(String)  # menstrual, follicular, ovulation, luteal
    sleep_score = Column(Integer)
    mood_score = Column(Integer)
    stress_level = Column(Integer)
    pain_level = Column(Integer)
    energy_level = Column(Integer)

class QTable(Base):
    __tablename__ = "q_tables"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    state = Column(String)
    action = Column(String)
    q_value = Column(Float)

class QTableHistory(Base):
    __tablename__ = "q_table_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    state = Column(String)
    action = Column(String)
    q_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    action_taken = Column(Integer, default=0)
    reward = Column(Float)
    next_day_energy = Column(Integer)
    next_day_mood = Column(Integer)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    action = Column(String)
    state = Column(String)
    action_taken = Column(Integer, default=0)
    effectiveness = Column(Float, default=0.0)

# Create all tables
Base.metadata.create_all(bind=engine)

# Pydantic models for API
class UserCreate(BaseModel):
    user_id: str

class CycleDataInput(BaseModel):
    user_id: str
    cycle_phase: str
    sleep_score: int
    mood_score: int
    stress_level: int
    pain_level: int
    energy_level: int

class NotificationResponse(BaseModel):
    notification_id: int
    user_id: str
    message: str
    action: str

class NotificationFeedback(BaseModel):
    notification_id: int
    action_taken: int  # 0 or 1
    effectiveness: float  # 0-10 rating
    next_day_energy: int  # 1-10 rating
    next_day_mood: int  # 1-10 rating

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Environment definition
class MenstrualCycleEnvironment:
    def __init__(self, user_id, db):
        self.user_id = user_id
        self.db = db
        self.state_features = ["cycle_phase", "sleep_score", "mood_score", 
                             "stress_level", "pain_level", "time_of_day", "energy_level"]
        self.actions = ["stretch_prompt", "mindfulness", "magnesium_suggestion", 
                       "nap_suggestion", "healthy_snack", "movement_break"]
        
    def get_current_state(self):
        """Extract current state from user data"""
        # Get the most recent cycle data for the user
        cycle_data = self.db.query(CycleData).filter_by(
            user_id=self.user_id
        ).order_by(CycleData.timestamp.desc()).first()

        if not cycle_data:
            return None

        # Time of day (morning, afternoon, evening, night)
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_of_day = "morning"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon"
        elif 17 <= current_hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        # Create state representation
        state = {
            "cycle_phase": cycle_data.cycle_phase,
            "sleep_score": cycle_data.sleep_score,
            "mood_score": cycle_data.mood_score,
            "stress_level": cycle_data.stress_level,
            "pain_level": cycle_data.pain_level,
            "time_of_day": time_of_day,
            "energy_level": cycle_data.energy_level
        }

        return json.dumps(state)

    def reward_function(self, notification_feedback):
        """Calculate reward based on user feedback and next-day improvements"""
        action_taken = notification_feedback.action_taken
        effectiveness = notification_feedback.effectiveness
        next_day_energy = notification_feedback.next_day_energy
        next_day_mood = notification_feedback.next_day_mood
        
        # If action not taken, small negative reward
        if action_taken == 0:
            return -1
        
        # Calculate immediate reward from effectiveness
        immediate_reward = effectiveness - 5  # Center around 0
        
        # Calculate improvement reward from next-day metrics
        # Get previous day's data
        prev_data = self.db.query(CycleData).filter_by(
            user_id=self.user_id
        ).order_by(CycleData.timestamp.desc()).first()
        
        if prev_data:
            energy_improvement = next_day_energy - prev_data.energy_level
            mood_improvement = next_day_mood - prev_data.mood_score
            improvement_reward = (energy_improvement + mood_improvement) / 2
        else:
            improvement_reward = 0
        
        # Combine immediate and improvement rewards
        total_reward = immediate_reward + improvement_reward
        return total_reward

# Q-Learning agent
class MenstrualCycleQLearningAgent:
    def __init__(self, user_id, db, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.user_id = user_id
        self.db = db
        self.actions = actions
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        
    def get_q_value(self, state, action):
        """Get Q-value from database"""
        q_entry = self.db.query(QTable).filter_by(
            user_id=self.user_id,
            state=state,
            action=action
        ).first()
        
        if q_entry:
            return q_entry.q_value
        else:
            # Initialize with small random value
            new_q = random.uniform(-0.1, 0.1)
            self.db.add(QTable(user_id=self.user_id, state=state, action=action, q_value=new_q))
            self.db.commit()
            return new_q
    
    def update_q_value(self, state, action, reward, next_state, action_taken=0, 
                      effectiveness=0, next_day_energy=None, next_day_mood=None):
        """Update Q-value using Q-learning formula"""
        current_q = self.get_q_value(state, action)
        
        # Find max Q-value for next state
        max_next_q = max([self.get_q_value(next_state, a) for a in self.actions])
        
        # Q-learning update formula
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        
        # Update in Q-table
        q_entry = self.db.query(QTable).filter_by(
            user_id=self.user_id,
            state=state,
            action=action
        ).first()
        
        if q_entry:
            q_entry.q_value = new_q
        else:
            self.db.add(QTable(user_id=self.user_id, state=state, action=action, q_value=new_q))
        
        # Add to Q-table history
        history_entry = QTableHistory(
            user_id=self.user_id,
            state=state,
            action=action,
            q_value=new_q,
            action_taken=action_taken,
            reward=reward,
            next_day_energy=next_day_energy,
            next_day_mood=next_day_mood
        )
        self.db.add(history_entry)
        self.db.commit()
    
    def choose_action(self, state):
        """Choose action using epsilon-greedy policy with cycle phase awareness"""
        state_dict = json.loads(state)
        cycle_phase = state_dict.get("cycle_phase")
        pain_level = state_dict.get("pain_level", 5)
        
        # First, see if we should explore
        if random.random() < self.epsilon:
            # Explore: choose random action with preference for pain management during menstrual phase
            if cycle_phase == "menstrual" and pain_level >= 6:
                pain_management_actions = ["magnesium_suggestion", "stretch_prompt"]
                if random.random() < 0.6:  # 60% chance to pick pain management action
                    return random.choice(pain_management_actions)
            return random.choice(self.actions)
        else:
            # Exploit: choose best action with potential cycle phase boost
            if cycle_phase == "menstrual" and pain_level >= 6:
                # For high pain during menstrual phase, temporarily boost Q-values of pain management actions
                q_values = []
                for action in self.actions:
                    q_value = self.get_q_value(state, action)
                    if action in ["magnesium_suggestion", "stretch_prompt"]:
                        q_value += 0.5  # Temporary boost for decision-making only
                    q_values.append((action, q_value))
                return max(q_values, key=lambda x: x[1])[0]
            else:
                # Normal Q-value selection
                q_values = [(action, self.get_q_value(state, action)) for action in self.actions]
                return max(q_values, key=lambda x: x[1])[0]

# Notification content generator
def generate_notification(action, state_str):
    """Generate personalized notification based on action and cycle phase"""
    state = json.loads(state_str)
    cycle_phase = state.get("cycle_phase", "")
    pain_level = state.get("pain_level", 5)
    energy_level = state.get("energy_level", 5)
    
    # Base messages with cycle phase awareness
    messages = {
        "stretch_prompt": [
            f"Time for some gentle stretching! During {cycle_phase} phase, focus on {get_stretch_type(cycle_phase)}",
            f"Your body could use some movement. Try these {cycle_phase}-friendly stretches",
            "Quick stretch break! Listen to your body and move gently"
        ],
        "mindfulness": [
            f"Take a moment to check in with yourself. During {cycle_phase}, practice deep breathing",
            "Time for a mindful moment. Close your eyes and breathe deeply",
            "Pause for peace. A short meditation can help balance your energy"
        ],
        "magnesium_suggestion": [
            f"During {cycle_phase}, magnesium can help with comfort. Consider taking a supplement",
            "Magnesium-rich foods like dark chocolate or nuts could help with symptoms",
            "Remember your magnesium supplement to support your body's needs"
        ],
        "nap_suggestion": [
            f"Your energy seems low. A short nap could help during {cycle_phase} phase",
            "Listen to your body - a 20-minute power nap might be just what you need",
            "Rest is important! Consider a short nap to recharge"
        ],
        "healthy_snack": [
            f"Time for a {cycle_phase}-supporting snack! Focus on {get_snack_suggestion(cycle_phase)}",
            "Nourish your body with a balanced snack",
            "Hungry? Choose a nutrient-rich snack to support your energy"
        ],
        "movement_break": [
            f"Time to move! During {cycle_phase}, try {get_movement_type(cycle_phase)}",
            "A short walk or gentle movement can help with energy and mood",
            "Your body needs movement - choose an activity that feels good"
        ]
    }
    
    # Select appropriate message based on state
    message_list = messages.get(action, ["Time to take care of yourself!"])
    selected_message = random.choice(message_list)
    
    # Add pain-specific additions if needed
    if pain_level >= 7 and cycle_phase == "menstrual":
        selected_message += "\nRemember to be gentle with yourself and listen to your body's needs."
    
    # Add energy-specific additions
    if energy_level <= 3:
        selected_message += "\nKeep it gentle and rest if needed."
    
    return selected_message

def get_stretch_type(cycle_phase):
    """Get phase-appropriate stretch suggestions"""
    stretch_types = {
        "menstrual": "hip-opening and gentle yoga",
        "follicular": "dynamic stretches and flow movements",
        "ovulation": "energetic and full-range stretches",
        "luteal": "calming and restorative stretches"
    }
    return stretch_types.get(cycle_phase, "comfortable stretches")

def get_snack_suggestion(cycle_phase):
    """Get phase-appropriate snack suggestions"""
    snack_types = {
        "menstrual": "iron-rich foods and dark chocolate",
        "follicular": "light, nutrient-dense foods",
        "ovulation": "fresh fruits and vegetables",
        "luteal": "complex carbs and protein-rich foods"
    }
    return snack_types.get(cycle_phase, "balanced, nutritious foods")

def get_movement_type(cycle_phase):
    """Get phase-appropriate movement suggestions"""
    movement_types = {
        "menstrual": "gentle walking or stretching",
        "follicular": "moderate cardio or strength training",
        "ovulation": "high-intensity activities or dance",
        "luteal": "yoga or light cardio"
    }
    return movement_types.get(cycle_phase, "movement that feels good")

# API endpoints
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.user_id == user.user_id).first()
    if existing_user:
        return existing_user
    
    # Create new user if doesn't exist
    db_user = User(user_id=user.user_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/cycle-data/")
def add_cycle_data(data: CycleDataInput, db: Session = Depends(get_db)):
    db_data = CycleData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@app.get("/notifications/generate/{user_id}")
def generate_user_notification(user_id: str, db: Session = Depends(get_db)):
    # Initialize environment and agent
    env = MenstrualCycleEnvironment(user_id, db)
    agent = MenstrualCycleQLearningAgent(user_id, db, env.actions)
    
    # Get current state
    state = env.get_current_state()
    if not state:
        raise HTTPException(status_code=404, detail="No cycle data found for user")
    
    # Choose action
    action = agent.choose_action(state)
    
    # Generate notification message
    message = generate_notification(action, state)
    
    # Save notification
    notification = Notification(
        user_id=user_id,
        message=message,
        action=action,
        state=state
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return NotificationResponse(
        notification_id=notification.id,
        user_id=user_id,
        message=message,
        action=action
    )

@app.post("/notifications/feedback/")
def process_notification_feedback(feedback: NotificationFeedback, db: Session = Depends(get_db)):
    # Get notification
    notification = db.query(Notification).filter_by(id=feedback.notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Update notification with feedback
    notification.action_taken = feedback.action_taken
    notification.effectiveness = feedback.effectiveness
    
    # Initialize environment and agent
    env = MenstrualCycleEnvironment(notification.user_id, db)
    agent = MenstrualCycleQLearningAgent(notification.user_id, db, env.actions)
    
    # Calculate reward
    reward = env.reward_function(feedback)
    
    # Get current state for next state
    next_state = env.get_current_state()
    if not next_state:
        next_state = notification.state  # Use previous state if no new state available
    
    # Update Q-values
    agent.update_q_value(
        notification.state,
        notification.action,
        reward,
        next_state,
        feedback.action_taken,
        feedback.effectiveness,
        feedback.next_day_energy,
        feedback.next_day_mood
    )
    
    db.commit()
    return {"status": "success", "reward": reward}

@app.get("/analytics/user/{user_id}")
def get_user_analytics(user_id: str, db: Session = Depends(get_db)):
    # Get user's Q-table history
    history = db.query(QTableHistory).filter_by(user_id=user_id).all()
    
    # Calculate action effectiveness
    action_effectiveness = {}
    for entry in history:
        if entry.action not in action_effectiveness:
            action_effectiveness[entry.action] = {"total_reward": 0, "count": 0}
        action_effectiveness[entry.action]["total_reward"] += entry.reward
        action_effectiveness[entry.action]["count"] += 1
    
    # Calculate average effectiveness per action
    for action in action_effectiveness:
        count = action_effectiveness[action]["count"]
        if count > 0:
            action_effectiveness[action]["average"] = (
                action_effectiveness[action]["total_reward"] / count
            )
        else:
            action_effectiveness[action]["average"] = 0
    
    # Get top actions
    top_actions = sorted(
        action_effectiveness.items(),
        key=lambda x: x[1]["average"],
        reverse=True
    )[:3]
    
    return {
        "top_actions": [action[0] for action in top_actions],
        "action_effectiveness": action_effectiveness
    }
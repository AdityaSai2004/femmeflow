# populate_db.py - Script to populate the SQLite database with sample data
from datetime import datetime, timedelta
import random
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from menstrual_cycle_app import Base, User, CycleData, QTable, QTableHistory, Notification

# Database setup
SQLALCHEMA_DATABASE_URL = "sqlite:///./menstrual_cycle_ql.db"
engine = create_engine(SQLALCHEMA_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def create_sample_users(db, num_users=5):
    users = []
    for i in range(num_users):
        user_id = f"user_{i+1}"
        existing_user = db.query(User).filter_by(user_id=user_id).first()
        if existing_user:
            print(f"User {user_id} already exists, skipping...")
            users.append(existing_user)
            continue
        user = User(user_id=user_id)
        db.add(user)
        users.append(user)
    db.commit()
    return users

def create_cycle_data(db, users, days_of_data=30):
    cycle_phases = ["menstrual", "follicular", "ovulation", "luteal"]
    phase_durations = {"menstrual": 5, "follicular": 7, "ovulation": 2, "luteal": 14}
    
    for user in users:
        current_date = datetime.now() - timedelta(days=days_of_data)
        current_phase_idx = random.randint(0, 3)
        days_in_current_phase = 0
        
        for day in range(days_of_data):
            current_phase = cycle_phases[current_phase_idx]
            
            # Simulate daily variations in health metrics
            base_scores = {
                "menstrual": {"sleep": 6, "mood": 5, "stress": 7, "pain": 7, "energy": 4},
                "follicular": {"sleep": 7, "mood": 7, "stress": 5, "pain": 3, "energy": 7},
                "ovulation": {"sleep": 8, "mood": 8, "stress": 4, "pain": 2, "energy": 8},
                "luteal": {"sleep": 6, "mood": 6, "stress": 6, "pain": 4, "energy": 6}
            }
            
            # Add random variation to base scores
            cycle_data = CycleData(
                user_id=user.user_id,
                timestamp=current_date,
                cycle_phase=current_phase,
                sleep_score=min(10, max(1, base_scores[current_phase]["sleep"] + random.randint(-2, 2))),
                mood_score=min(10, max(1, base_scores[current_phase]["mood"] + random.randint(-2, 2))),
                stress_level=min(10, max(1, base_scores[current_phase]["stress"] + random.randint(-2, 2))),
                pain_level=min(10, max(1, base_scores[current_phase]["pain"] + random.randint(-2, 2))),
                energy_level=min(10, max(1, base_scores[current_phase]["energy"] + random.randint(-2, 2)))
            )
            db.add(cycle_data)
            
            # Update phase if needed
            days_in_current_phase += 1
            if days_in_current_phase >= phase_durations[current_phase]:
                current_phase_idx = (current_phase_idx + 1) % 4
                days_in_current_phase = 0
            
            current_date += timedelta(days=1)
    
    db.commit()

def initialize_q_tables(db, users):
    actions = ["stretch_prompt", "mindfulness", "magnesium_suggestion", 
               "nap_suggestion", "healthy_snack", "movement_break"]
    cycle_phases = ["menstrual", "follicular", "ovulation", "luteal"]
    
    # Initial Q-values based on common patterns
    base_q_values = {
        "menstrual": {
            "stretch_prompt": 0.3,
            "mindfulness": 0.4,
            "magnesium_suggestion": 0.6,
            "nap_suggestion": 0.5,
            "healthy_snack": 0.4,
            "movement_break": 0.2
        },
        "follicular": {
            "stretch_prompt": 0.4,
            "mindfulness": 0.3,
            "magnesium_suggestion": 0.2,
            "nap_suggestion": 0.3,
            "healthy_snack": 0.5,
            "movement_break": 0.6
        },
        "ovulation": {
            "stretch_prompt": 0.5,
            "mindfulness": 0.4,
            "magnesium_suggestion": 0.2,
            "nap_suggestion": 0.2,
            "healthy_snack": 0.4,
            "movement_break": 0.6
        },
        "luteal": {
            "stretch_prompt": 0.3,
            "mindfulness": 0.5,
            "magnesium_suggestion": 0.4,
            "nap_suggestion": 0.4,
            "healthy_snack": 0.5,
            "movement_break": 0.3
        }
    }
    
    for user in users:
        for phase in cycle_phases:
            # Create a sample state
            state = json.dumps({
                "cycle_phase": phase,
                "sleep_score": 7,
                "mood_score": 7,
                "stress_level": 5,
                "pain_level": 4,
                "time_of_day": "morning",
                "energy_level": 6
            })
            
            for action in actions:
                # Add some random variation to base Q-values
                q_value = base_q_values[phase][action] + random.uniform(-0.1, 0.1)
                q_table = QTable(
                    user_id=user.user_id,
                    state=state,
                    action=action,
                    q_value=q_value
                )
                db.add(q_table)
    
    db.commit()

def create_sample_notifications(db, users):
    actions = ["stretch_prompt", "mindfulness", "magnesium_suggestion", 
               "nap_suggestion", "healthy_snack", "movement_break"]
    
    for user in users:
        # Get user's cycle data
        cycle_data = db.query(CycleData).filter_by(
            user_id=user.user_id
        ).order_by(CycleData.timestamp.desc()).first()
        
        if cycle_data:
            state = json.dumps({
                "cycle_phase": cycle_data.cycle_phase,
                "sleep_score": cycle_data.sleep_score,
                "mood_score": cycle_data.mood_score,
                "stress_level": cycle_data.stress_level,
                "pain_level": cycle_data.pain_level,
                "time_of_day": "morning",
                "energy_level": cycle_data.energy_level
            })
            
            # Create a few sample notifications
            for _ in range(3):
                action = random.choice(actions)
                notification = Notification(
                    user_id=user.user_id,
                    message=f"Sample notification for {action}",
                    action=action,
                    state=state,
                    action_taken=random.choice([0, 1]),
                    effectiveness=random.uniform(5.0, 9.0)
                )
                db.add(notification)
    
    db.commit()

def main():
    db = SessionLocal()
    try:
        print("Creating sample users...")
        users = create_sample_users(db)
        
        print("Creating cycle data...")
        create_cycle_data(db, users)
        
        print("Initializing Q-tables...")
        initialize_q_tables(db, users)
        
        print("Creating sample notifications...")
        create_sample_notifications(db, users)
        
        print("Database population completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
import logging
import sys
import os

# Add project root to sys.path to allow imports from app
# This assumes init_db.py is in app/db/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# python-dotenv in database.py will attempt to load .env if present.
# We will rely on DATABASE_URL being in the environment.

from app.db.database import engine
# Ensure all your models are imported here so Base knows about them
from app.models.models import Base, Question, UserAnswer, User # Added User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Attempting to create database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully (if they didn't exist).")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        # raise # Optionally re-raise, or just log for this script
    else:
        logger.info("init_db() completed.")
        # Create a default user
        create_default_user()
        # Create sample questions
        create_sample_questions()


def create_sample_questions():
    from app.db.database import SessionLocal
    # Question model is already imported at the top as:
    # from app.models.models import Base, Question, UserAnswer, User 

    db = SessionLocal()
    try:
        logger.info("Checking for sample questions...")
        if db.query(Question).count() == 0:
            logger.info("Creating sample questions...")
            questions_data = [
                {
                    "problem_statement": "What is 2 + 2?",
                    "option_1": "3", "option_2": "4", "option_3": "5", "option_4": "6",
                    "correct_answer": 2, 
                    "explanation": "Basic arithmetic: 2 + 2 = 4."
                },
                {
                    "problem_statement": "What is the capital of France?",
                    "option_1": "Berlin", "option_2": "Madrid", "option_3": "Paris", "option_4": "Rome",
                    "correct_answer": 3,
                    "explanation": "Paris is the capital of France."
                },
                {
                    "problem_statement": "Which planet is known as the Red Planet?",
                    "option_1": "Earth", "option_2": "Mars", "option_3": "Jupiter", "option_4": "Saturn",
                    "correct_answer": 2,
                    "explanation": "Mars is known as the Red Planet due to its reddish appearance, caused by iron oxide (rust) on its surface."
                },
                {
                    "problem_statement": "What is the largest mammal in the world?",
                    "option_1": "Elephant", "option_2": "Blue Whale", "option_3": "Giraffe", "option_4": "Great White Shark",
                    "correct_answer": 2,
                    "explanation": "The Blue Whale is the largest mammal, and in fact, the largest animal known to have ever existed."
                },
                {
                    "problem_statement": "In Python, what keyword is used to define a function?",
                    "option_1": "fun", "option_2": "define", "option_3": "def", "option_4": "function",
                    "correct_answer": 3,
                    "explanation": "The 'def' keyword is used to define functions in Python."
                },
                {
                    "problem_statement": "What does HTML stand for?",
                    "option_1": "HyperText Markup Language", "option_2": "HighText Machine Language", 
                    "option_3": "HyperTransfer Mode Language", "option_4": "Hyperlink and Text Markup Language",
                    "correct_answer": 1,
                    "explanation": "HTML stands for HyperText Markup Language, the standard markup language for creating web pages."
                },
                {
                    "problem_statement": "Which of these is a version control system?",
                    "option_1": "Docker", "option_2": "Kubernetes", "option_3": "Git", "option_4": "Jenkins",
                    "correct_answer": 3,
                    "explanation": "Git is a distributed version control system widely used for tracking changes in source code during software development."
                }
            ]
            for q_data in questions_data:
                question = Question(
                    problem_statement=q_data["problem_statement"],
                    option_1=q_data["option_1"],
                    option_2=q_data["option_2"],
                    option_3=q_data["option_3"],
                    option_4=q_data["option_4"],
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data["explanation"]
                )
                db.add(question)
            db.commit()
            logger.info(f"{len(questions_data)} sample questions created.")
        else:
            logger.info("Sample questions already exist.")
    except Exception as e:
        logger.error(f"Error creating sample questions: {e}")
        db.rollback() # Rollback in case of error during commit
    finally:
        db.close()


def create_default_user():
    from app.db.database import SessionLocal
    from app.crud.crud_user import get_user_by_username, create_user
    from app.schemas.schemas import UserCreate

    db = SessionLocal()
    try:
        logger.info("Checking for default user...")
        default_username = "testuser"
        user = get_user_by_username(db, username=default_username)
        if not user:
            logger.info(f"Creating default user: {default_username}")
            user_in = UserCreate(
                username=default_username,
                email="testuser@example.com",
                password="testpass", # Raw password, create_user will hash it
                full_name="Test User"
            )
            create_user(db, user=user_in)
            logger.info(f"Default user {default_username} created.")
        else:
            logger.info(f"Default user {default_username} already exists.")
    except Exception as e:
        logger.error(f"Error creating default user: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Initializing database (non-interactive mode)...")
    # Check if DATABASE_URL is set, as a proxy for successful env var setup
    db_url_check = os.getenv("DATABASE_URL")
    if not db_url_check:
        logger.error("DATABASE_URL environment variable is not set. Cannot initialize database.")
    else:
        logger.info(f"DATABASE_URL is set (length: {len(db_url_check)}). Proceeding with init_db().")
        init_db()

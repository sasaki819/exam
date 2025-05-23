import os
from dotenv import load_dotenv

# Load .env file from the project root if it exists
# This allows overriding default settings with environment variables
# For example, during development or in production.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
dotenv_path = os.path.join(project_root, ".env")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed") # Default for safety
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Ensure SECRET_KEY is not the default in a production-like environment
# if os.getenv("ENVIRONMENT") == "production" and SECRET_KEY == "a_very_secret_key_that_should_be_changed":
#     raise ValueError("Default SECRET_KEY is used in production. Please set a strong SECRET_KEY environment variable.")

# You can add other application-wide configurations here
# For example:
# PROJECT_NAME = os.getenv("PROJECT_NAME", "FastAPI Quiz App")
# API_V1_STR = "/api/v1"

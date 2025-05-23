# QuizWiz - Exam Preparation Web Application

## Description

QuizWiz is a web application designed to help users prepare for exams by providing a platform for practicing questions from a question bank. It features user authentication, dynamic question serving with immediate feedback, and personalized performance summaries. The application is built with a modern Python backend using FastAPI and a vanilla JavaScript frontend. It is fully containerized with Docker for easy setup and deployment.

## Features

*   **User Authentication:** Secure login system using JWT (JSON Web Tokens).
*   **Dynamic Question Display:** Presents questions with a problem statement and four multiple-choice options.
*   **Immediate Feedback:** Users receive instant feedback (Correct/Incorrect), the correct answer, and explanations upon submitting an answer.
*   **Prioritized Question Serving:** Implements a smart algorithm to serve questions:
    1.  Questions unanswered by the user.
    2.  Questions with the highest global incorrect answer rate (among those not always answered correctly by the user).
    3.  Fallback to questions with the highest global correct answer rate (for review).
*   **User-Specific Summary Screen:** Provides a detailed summary of the user's performance, including overall statistics (total attempted, correct/incorrect counts, success rate) and a breakdown of performance per question.
*   **Sample Data Seeding:** Includes a script to initialize the database with a default user (`testuser`/`testpass`) and a set of sample questions to get started quickly.
*   **Comprehensive Automated Test Suite:** Includes unit and integration tests using Pytest to ensure application reliability.
*   **Dockerized Environment:** Fully containerized using Docker and Docker Compose for consistent development, testing, and production environments.

## Technology Stack

*   **Backend:** Python 3.9, FastAPI
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy (with Alembic for migrations, though Alembic setup was problematic and bypassed in final DB init)
*   **Authentication:** JWT (python-jose, passlib for hashing)
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript
*   **Testing:** Pytest, HTTPX
*   **Containerization:** Docker, Docker Compose

## Prerequisites

*   Python 3.9 or higher (for local setup without Docker)
*   Docker and Docker Compose (for containerized setup)
*   Access to a PostgreSQL instance (if running locally without Docker)

## Local Setup & Installation (Without Docker)

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url> 
    # Replace <repository_url> with the actual URL of your repository
    ```
2.  **Navigate to Project Directory:**
    ```bash
    cd <project_directory>
    ```
3.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    ```
    *   Linux/macOS: `source venv/bin/activate`
    *   Windows: `venv\Scripts\activate`

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up `.env` File:**
    Create a `.env` file in the project root. For a local PostgreSQL setup, it should contain:
    ```env
    DATABASE_URL=postgresql://your_local_pg_user:your_local_pg_password@localhost:5432/quiz_app_db
    SECRET_KEY=a_very_strong_and_unique_secret_key_please_change_me
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    
    # The following POSTGRES_ variables are primarily for Docker Compose and may not be strictly needed
    # by the application when running locally if your database is already created and configured.
    # POSTGRES_USER=your_local_pg_user 
    # POSTGRES_PASSWORD=your_local_pg_password
    # POSTGRES_DB=quiz_app_db
    ```
    *   Replace `your_local_pg_user`, `your_local_pg_password`, and `quiz_app_db` with your actual local PostgreSQL credentials and database name.
    *   Ensure `SECRET_KEY` is a strong, unique random string.

6.  **Initialize Database:**
    Ensure your PostgreSQL server is running and you have created the database specified in `DATABASE_URL`. Then run:
    ```bash
    python app/db/init_db.py
    ```
    This will create tables and seed initial data (default user `testuser`/`testpass` and sample questions).

## Running Locally (Without Docker)

1.  **Start the Application:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
2.  **Access the Application:**
    Open your web browser and go to `http://localhost:8000`. You should be redirected to the login page.

## Docker Setup & Running

This is the recommended way to run the application for a consistent environment.

1.  **Ensure Docker and Docker Compose are Installed.**

2.  **Create `.env` File:**
    In the project root, create a `.env` file with the following content:
    ```env
    # For the FastAPI application (app service)
    DATABASE_URL=postgresql://quiz_user:quiz_password@db:5432/quiz_db
    SECRET_KEY=your_super_secret_key_here_please_change_ MIGHT_BE_VERY_LONG
    ACCESS_TOKEN_EXPIRE_MINUTES=30

    # For the PostgreSQL database service (db service in docker-compose)
    POSTGRES_USER=quiz_user
    POSTGRES_PASSWORD=quiz_password
    POSTGRES_DB=quiz_db
    ```
    **Important:** Change `SECRET_KEY` to a strong, unique random string.

3.  **Build and Run with Docker Compose:**
    ```bash
    docker-compose build
    docker-compose up -d
    ```
4.  **Initialize Database (First Time Only):**
    After the containers are up and running for the first time, execute:
    ```bash
    docker-compose exec app python app/db/init_db.py
    ```
5.  **Access the Application:**
    Open your web browser and go to `http://localhost:8000`.

6.  **Stop the Services:**
    ```bash
    docker-compose down
    ```
    To remove the database volume (all data will be lost): `docker-compose down -v`

## Running Automated Tests

1.  **Ensure Dependencies are Installed:**
    If you haven't installed all dependencies (including `pytest` and `httpx`):
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run Tests:**
    From the project root directory, execute:
    ```bash
    pytest
    ```
    For more verbose output:
    ```bash
    pytest -v
    ```
    Tests use an in-memory SQLite database and do not require a running PostgreSQL server or Docker.

## API Endpoints Overview

*   `POST /auth/token`: User login, returns JWT.
*   `POST /questions/`: Create a new question (requires authentication).
*   `GET /questions/next/`: Fetch the next prioritized question for the authenticated user.
*   `POST /questions/{question_id}/answer/`: Submit an answer for a specific question (requires authentication).
*   `GET /summary/`: Retrieve the authenticated user's performance summary.
*   (HTML pages served at `/`, `/login`, `/exam`, `/summary`)

## Project Structure

```
.
├── app/                    # Main application code
│   ├── crud/               # CRUD operations (database interactions)
│   ├── db/                 # Database setup, initialization, session management
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # API and page routers (endpoints)
│   ├── schemas/            # Pydantic schemas (data validation, serialization)
│   ├── core/               # Core logic (config, security)
│   └── main.py             # FastAPI application instance and startup
├── static/                 # Static files (CSS, JavaScript)
│   ├── css/
│   └── js/
├── templates/              # HTML templates (Jinja2)
├── tests/                  # Automated tests
│   ├── api/
│   ├── crud/
│   └── core/
├── .dockerignore           # Files to ignore in Docker build context
├── .env                    # Environment variables (local or for Docker, not committed)
├── .gitignore              # Files to ignore by Git
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose setup
├── MANUAL_TESTING_GUIDE.md # Detailed guide for manual QA
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

---
Happy Quizzing!
```

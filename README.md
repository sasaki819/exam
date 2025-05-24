# QuizWiz - Exam Preparation Web Application

## Description

QuizWiz is a web application designed to help users prepare for exams by providing a platform for practicing questions from a question bank. It supports multiple exam types, allowing users to focus their preparation. It features user authentication, dynamic question serving with immediate feedback, and personalized performance summaries (overall and per exam type). The application is built with a modern Python backend using FastAPI and a vanilla JavaScript frontend. It is fully containerized with Docker for easy setup and deployment. Administrative users can manage exam types and questions through dedicated interfaces.

## Features

*   **User Authentication:** Secure login system using JWT (JSON Web Tokens).
*   **Multi-Exam Type Support:**
    *   Supports different exam categories (e.g., "DX検定2025", "AWS SAA").
    *   Users can select their desired exam type before starting a quiz.
*   **Dynamic Question Display:** Presents questions with a problem statement and four multiple-choice options relevant to the selected exam type.
*   **Immediate Feedback:** Users receive instant feedback (Correct/Incorrect), the correct answer, and explanations upon submitting an answer.
*   **Prioritized Question Serving:** Implements a smart algorithm to serve questions within the selected exam type:
    1.  Questions unanswered by the user.
    2.  Questions with the highest global incorrect answer rate (among those not always answered correctly by the user).
    3.  Fallback to questions with the highest global correct answer rate (for review).
*   **User-Specific Summary Screen:**
    *   Provides a detailed summary of the user's performance.
    *   Supports filtering of summary data by exam type.
*   **Administrative Management Interfaces:**
    *   **Exam Type Management:** CRUD (Create, Read, Update, Delete) operations for exam types via a dedicated page (`/manage-exam-types`).
    *   **Question Management:** CRUD operations for questions, including association with exam types, via a dedicated page (`/manage-questions`).
*   **Sample Data Seeding:** Includes a script to initialize the database with a default user (`testuser`/`testpass`) and a set of sample questions and exam types to get started quickly.
*   **Comprehensive Automated Test Suite:** Includes unit and integration tests using Pytest to ensure application reliability.
*   **Dockerized Environment:** Fully containerized using Docker and Docker Compose for consistent development, testing, and production environments.

## Question Import and Export

QuizWiz now supports bulk import and export of questions for specific exam types, facilitating easier content management.

*   **Location**: These features are available on the "Manage Questions" page (`/manage-questions`). Both import and export operations are performed for the exam type currently selected in the filter dropdown on that page.
*   **File Format**: The data format used for both import and export is JSON.

### Exporting Questions

*   When an exam type is selected in the filter, clicking the "Export Questions for Selected Type" button will initiate a download.
*   The downloaded file will be a JSON file (e.g., `exam_type_My_Exam_1_questions.json`).
*   This file contains a JSON array of all questions belonging to the selected exam type.
*   Each question object in the array will include its problem statement, options, correct answer, and explanation (if any). Fields like internal ID or exam type ID are not included in the export.

### Importing Questions

*   Users can upload a JSON file to add multiple questions to the currently selected exam type.
*   The import file must be a JSON array (a list) of question objects. Each object should conform to the following structure:

    ```json
    {
      "problem_statement": "What is 2 + 2?",
      "option_1": "3",
      "option_2": "4",
      "option_3": "5",
      "option_4": "6",
      "correct_answer": 2,
      "explanation": "The sum of 2 and 2 is 4."
    }
    ```

*   **Key Fields for Each Question Object**:
    *   `problem_statement` (string, required): The text of the question.
    *   `option_1` (string, required): Text for the first choice.
    *   `option_2` (string, required): Text for the second choice.
    *   `option_3` (string, required): Text for the third choice.
    *   `option_4` (string, required): Text for the fourth choice.
    *   `correct_answer` (integer, required): A number from 1 to 4, indicating which option is correct.
    *   `explanation` (string, optional): An explanation for the answer. If not provided, it will be stored as null.

*   **Import Process & Feedback**:
    *   The system will attempt to import each question from the JSON array.
    *   After the import attempt, a summary will be displayed, indicating how many questions were successfully imported and how many failed.
    *   If there are failures, detailed error messages will be provided for each failed question, including the row number (0-indexed from the file) and the problematic data.
    *   Successfully imported questions will be immediately available for quizzing under the selected exam type.

## Technology Stack

*   **Backend:** Python 3.9, FastAPI
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy (with Alembic for migrations, though Alembic setup was problematic and bypassed in final DB init)
*   **Authentication:** JWT (python-jose, passlib for hashing)
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript
*   **Testing:** Pytest, HTTPX (via TestClient)
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
    ```
    *   Replace `your_local_pg_user`, `your_local_pg_password`, and `quiz_app_db` with your actual local PostgreSQL credentials and database name.
    *   Ensure `SECRET_KEY` is a strong, unique random string.

6.  **Initialize Database:**
    Ensure your PostgreSQL server is running and you have created the database specified in `DATABASE_URL`. Then run:
    ```bash
    python app/db/init_db.py
    ```
    This will create tables and seed initial data (default user `testuser`/`testpass`, sample exam types, and sample questions).

## Running Locally (Without Docker)

1.  **Start the Application:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
2.  **Access the Application:**
    Open your web browser and go to `http://localhost:8000`. You should be redirected to the login page. Default credentials: `testuser` / `testpass`.
    *   To manage exam types: Navigate to `/manage-exam-types` after logging in.
    *   To manage questions: Navigate to `/manage-questions` after logging in.

## Docker Setup & Running

This is the recommended way to run the application for a consistent environment.

1.  **Ensure Docker and Docker Compose are Installed.** (Use `docker compose` v2 syntax)

2.  **Create `.env` File:**
    In the project root, create a `.env` file with the following content:
    ```env
    # For the FastAPI application (app service)
    DATABASE_URL=postgresql://quiz_user:quiz_password@db:5432/quiz_db
    SECRET_KEY=your_super_secret_key_here_please_change_ME_REALLY_CHANGE_ME
    ACCESS_TOKEN_EXPIRE_MINUTES=30

    # For the PostgreSQL database service (db service in docker-compose)
    POSTGRES_USER=quiz_user
    POSTGRES_PASSWORD=quiz_password
    POSTGRES_DB=quiz_db
    ```
    **Important:** Change `SECRET_KEY` to a strong, unique random string.

3.  **Build and Run with Docker Compose:**
    (Using `docker compose` v2 syntax)
    ```bash
    docker compose build
    docker compose up -d
    ```
4.  **Initialize Database (First Time Only):**
    After the containers are up and running for the first time, execute:
    ```bash
    docker compose exec app python app/db/init_db.py
    ```
5.  **Access the Application:**
    Open your web browser and go to `http://localhost:8000`. Default credentials: `testuser` / `testpass`.
    *   To manage exam types: Navigate to `/manage-exam-types` after logging in.
    *   To manage questions: Navigate to `/manage-questions` after logging in.

6.  **Stop the Services:**
    ```bash
    docker compose down
    ```
    To remove the database volume (all data will be lost): `docker compose down -v`

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
*   **Exam Types:**
    *   `POST /exam-types/`: Create a new exam type.
    *   `GET /exam-types/`: List all exam types.
    *   `GET /exam-types/{exam_type_id}`: Get a specific exam type.
    *   `PUT /exam-types/{exam_type_id}`: Update an exam type.
    *   `DELETE /exam-types/{exam_type_id}`: Delete an exam type.
*   **Questions:**
    *   `POST /questions/`: Create a new question (requires `exam_type_id`).
    *   `GET /questions/`: List questions (can be filtered by `exam_type_id`).
    *   `GET /questions/next/?exam_type_id={exam_type_id}`: Fetch the next prioritized question for the authenticated user for a specific exam type.
    *   `GET /questions/{question_id}`: Get a specific question.
    *   `PUT /questions/{question_id}`: Update a question (can change `exam_type_id`).
    *   `DELETE /questions/{question_id}`: Delete a question.
    *   `POST /questions/{question_id}/answer/`: Submit an answer for a specific question.
*   **Summary:**
    *   `GET /summary/`: Retrieve the authenticated user's performance summary (can be filtered by `exam_type_id`).
*   **HTML Pages:**
    *   Served at `/`, `/login`, `/exam`, `/summary`, `/manage-exam-types`, `/manage-questions`.

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
│   └── conftest.py         # Pytest fixtures and test setup
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

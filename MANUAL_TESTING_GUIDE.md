# Manual Testing Guide for FastAPI Quiz App

This guide outlines the steps to manually test the core functionality of the FastAPI Quiz App.

## Prerequisites

1.  **Python Environment:** Python 3.8+ with `pip`.
2.  **PostgreSQL Server:** A running PostgreSQL server.
3.  **Database Creation:**
    *   Create a PostgreSQL database (e.g., `quiz_app_db`).
    *   Ensure you have a database user with privileges to connect and create tables in this database.
4.  **Code Checkout:** The application code is checked out.
5.  **`.env` File:**
    *   Create a `.env` file in the project root (same directory as `requirements.txt`).
    *   Add the following line, replacing with your actual database credentials and details:
        ```
        DATABASE_URL="postgresql://user:password@localhost/quiz_app_db"
        SECRET_KEY="your_very_strong_secret_key_here" 
        # ACCESS_TOKEN_EXPIRE_MINUTES=30 (optional, defaults to 30)
        ```
        **Important:** `SECRET_KEY` should be a strong, random string.

## Setup and Installation

1.  **Install Dependencies:**
    Open a terminal in the project root and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Database and Seed Data:**
    Ensure your PostgreSQL server is running and accessible. Then, run the database initialization script:
    ```bash
    python app/db/init_db.py
    ```
    This script will:
    *   Create the necessary database tables.
    *   Create a default user:
        *   Username: `testuser`
        *   Password: `testpass`
    *   Seed sample questions into the database.
    *   You can run this script multiple times; it's designed to avoid duplicating users or questions.

## Running the Application

1.  **Start Uvicorn Server:**
    In the project root, run:
    ```bash
    uvicorn app.main:app --reload
    ```
    The application will typically be available at `http://127.0.0.1:8000`.

## Testing Workflow

1.  **Accessing Protected Pages (Pre-Login):**
    *   Open a web browser and navigate to `http://127.0.0.1:8000/exam`.
    *   **Expected:** You should be redirected to `http://127.0.0.1:8000/login`.
    *   Try navigating to `http://127.0.0.1:8000/summary`.
    *   **Expected:** You should be redirected to `http://127.0.0.1:8000/login`.

2.  **Login:**
    *   Navigate to `http://127.0.0.1:8000/login` (or you might already be there).
    *   Enter Username: `testuser`
    *   Enter Password: `testpass`
    *   Click the "Login" button.
    *   **Expected:** Successful login, and you should be redirected to `http://127.0.0.1:8000/exam`.
    *   **Test Invalid Login:** Try logging in with incorrect credentials.
    *   **Expected:** An error message should be displayed on the login page.

3.  **Taking the Exam (`/exam`):**
    *   You should now be on the exam page.
    *   **Expected:** A question is displayed with its problem statement and four radio button options. The "Submit Answer" button is active. The result area and "Next Question" button are hidden.
    *   **Answer Questions:**
        *   **Question 1:** Select an answer (e.g., the correct one). Click "Submit Answer".
        *   **Expected:**
            *   The "Submit Answer" button becomes disabled/hidden.
            *   The result area appears, showing "Correct!" or "Incorrect!", the correct answer option, and an explanation.
            *   The "Next Question" button becomes visible.
        *   Click "Next Question".
        *   **Expected:** A new question is displayed. The result area and "Next Question" button are hidden again. "Submit Answer" is active.
        *   **Question 2:** Select a different answer (e.g., an incorrect one). Click "Submit Answer".
        *   **Expected:** Similar feedback, but now showing "Incorrect!".
        *   Click "Next Question".
        *   Continue answering a few more questions (at least 3-5). Try to answer some correctly and some incorrectly to generate varied statistics. Note down which questions you answered and how.
    *   **No More Questions:** If you answer all available unique questions, the system might indicate "No unanswered questions available" or cycle through questions based on the prioritization logic (e.g., those you got wrong). Observe this behavior. The current prioritization is: 1. Unanswered, 2. Highest global incorrect (not always correct by user), 3. Highest global correct.

4.  **Viewing Summary (`/summary`):**
    *   While logged in, click the "View Summary" link on the exam page (or manually navigate to `http://127.0.0.1:8000/summary`).
    *   **Expected:**
        *   **Overall Performance:**
            *   "Total Unique Questions Attempted" should match the number of distinct questions you attempted.
            *   "Total Answers Submitted" should match the total number of times you clicked "Submit Answer".
            *   "Correct Answers" and "Incorrect Answers" should reflect your performance.
            *   "Correct Answer Rate" should be calculated correctly.
        *   **Performance Per Question:**
            *   A table should list each question you attempted.
            *   For each question, "Times Answered", "Times Correct", and "Times Incorrect" should accurately reflect your interaction with that specific question.
            *   The problem statement should be displayed.

5.  **Logout:**
    *   On either the `/exam` or `/summary` page, click the "Logout" link/button.
    *   **Expected:** You should be redirected to `http://127.0.0.1:8000/login`.
    *   localStorage (in browser developer tools) should no longer contain the `accessToken`.

6.  **Accessing Protected Pages (Post-Logout):**
    *   After logging out, try navigating to `http://127.0.0.1:8000/exam` again.
    *   **Expected:** Redirected to `/login`.
    *   Try navigating to `http://127.0.0.1:8000/summary` again.
    *   **Expected:** Redirected to `/login`.

7.  **API Endpoint Check (Optional - using tools like `curl` or Postman/Insomnia):**
    *   **Get Token:**
        ```bash
        curl -X POST "http://127.0.0.1:8000/auth/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=testuser&password=testpass"
        ```
        **Expected:** JSON response with `access_token` and `token_type`.
    *   **Access Protected API Endpoint (e.g., `/questions/next/`):**
        Replace `YOUR_ACCESS_TOKEN` with the token obtained above.
        ```bash
        curl -X GET "http://127.0.0.1:8000/questions/next/" -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
        ```
        **Expected:** JSON response with a question object.
    *   **Access Protected API Endpoint without Token:**
        ```bash
        curl -X GET "http://127.0.0.1:8000/questions/next/"
        ```
        **Expected:** JSON response with `{"detail":"Not authenticated"}` or similar (status 401/403).

## Further Checks

*   Review server logs (`uvicorn` output) for any unexpected errors during testing.
*   If using a database inspection tool, verify that `UserAnswer` entries are being created correctly with the appropriate `user_id`, `question_id`, `selected_answer`, and `is_correct` status.

This guide provides a comprehensive approach to manually testing the core features. Adjust question answering sequences to test different scenarios of the prioritization logic in `/questions/next/`.
```

## Running Automated Tests

The project also includes a suite of automated tests using `pytest`.

### Prerequisites for Automated Tests

*   All dependencies from `requirements.txt` must be installed, including `pytest` and `httpx`.
    ```bash
    pip install -r requirements.txt
    ```
*   The tests are configured to use an in-memory SQLite database, so no external database setup (like PostgreSQL for manual testing) is required specifically for running the automated tests. The test environment automatically handles the creation and teardown of the test database schema.

### Running Tests

1.  **Navigate to Project Root:**
    Open your terminal and ensure you are in the root directory of the project (the same directory that contains the `tests/` folder and `pytest.ini` if you choose to add one).

2.  **Execute Pytest:**
    Run the following command:
    ```bash
    pytest
    ```
    Or, for more verbose output:
    ```bash
    pytest -v
    ```
    Pytest will automatically discover and run all test files (named `test_*.py` or `*_test.py`) in the `tests` directory and its subdirectories.

### Test Output

*   You will see output indicating the progress of the tests.
*   A summary at the end will show the number of tests passed, failed, or skipped.
*   If there are failures, `pytest` provides detailed tracebacks to help diagnose the issues.

### Test Coverage (Optional)

If you want to measure test coverage:

1.  Install `pytest-cov`:
    ```bash
    pip install pytest-cov
    ```
2.  Run pytest with coverage:
    ```bash
    pytest --cov=app --cov-report=html
    ```
    This will generate an HTML report in a `htmlcov/` directory, which you can open in a web browser to see detailed coverage information. Replace `app` with the actual name of your main application package if it's different.

## Running with Docker

This section describes how to run the application using Docker and Docker Compose.

### Prerequisites for Docker

*   **Docker and Docker Compose:** Ensure Docker Desktop (for Windows/Mac) or Docker Engine and Docker Compose (for Linux) are installed on your system.

### Setup for Docker

1.  **`.env` File for Docker:**
    The application uses a `.env` file to configure database connections and other settings when run with Docker Compose.
    *   Ensure a `.env` file exists in the project root. If not, create one.
    *   Its content should be similar to this (this file is also used by `docker-compose.yml`):
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
    *   **Important:** Change `SECRET_KEY` to a strong, unique random string for your deployment. The `DATABASE_URL` uses `db` as the hostname, which refers to the PostgreSQL service defined in `docker-compose.yml`. The `POSTGRES_*` variables are used by the PostgreSQL image to initialize the database.

### Building and Running with Docker Compose

1.  **Build the Services:**
    Open a terminal in the project root and run:
    ```bash
    docker-compose build
    ```
    This command builds the Docker image for the `app` service as defined in the `Dockerfile`.

2.  **Start the Services:**
    To start the application and the PostgreSQL database services, run:
    ```bash
    docker-compose up -d
    ```
    The `-d` flag runs the containers in detached mode (in the background). If you want to see the logs directly in the terminal, you can omit `-d` (i.e., `docker-compose up`).

3.  **Database Initialization (First Time Only):**
    After starting the services for the first time (or after clearing the database volume), the database schema needs to be created, and initial data (default user, sample questions) needs to be seeded.
    Run the following command in your terminal:
    ```bash
    docker-compose exec app python app/db/init_db.py
    ```
    This command executes the `init_db.py` script inside the already running `app` container. You should see log output from the script indicating table creation and data seeding.

4.  **Accessing the Application:**
    Once the services are running and the database is initialized, the FastAPI Quiz App will be accessible at:
    `http://localhost:8000`
    You can then proceed with the "Testing Workflow" outlined earlier in this guide, starting from accessing the login page.

### Managing Docker Compose Services

*   **Viewing Logs:**
    To view the logs from the application container:
    ```bash
    docker-compose logs -f app
    ```
    To view logs from the database container:
    ```bash
    docker-compose logs -f db
    ```
    To view logs from all services:
    ```bash
    docker-compose logs -f
    ```

*   **Stopping the Services:**
    To stop the running application and database services:
    ```bash
    docker-compose down
    ```
    If you want to remove the database volume (which will delete all database data), use:
    ```bash
    docker-compose down -v
    ```

*   **Rebuilding the Application Image:**
    If you make changes to the application code or `Dockerfile`, you'll need to rebuild the `app` image:
    ```bash
    docker-compose build app 
    # or just 'docker-compose build' if you want to ensure all build contexts are fresh
    ```
    Then restart the services:
    ```bash
    docker-compose up -d # (or without -d to see logs)
    ```

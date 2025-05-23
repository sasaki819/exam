from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from fastapi import status

from app.models import models # For type hinting and direct model interaction if needed
from app.schemas import schemas # For request/response validation if needed
from app.core.security import create_access_token # To create tokens for testing protected routes
from datetime import timedelta

# Test POST /auth/token with valid credentials
def test_login_for_access_token(client: TestClient, test_user: models.User, db_session: SQLAlchemySession):
    login_data = {
        "username": test_user.username,
        "password": "testpassword"  # The raw password used in the test_user fixture
    }
    response = client.post("/auth/token", data=login_data) # Use data for application/x-www-form-urlencoded
    
    assert response.status_code == status.HTTP_200_OK
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

# Test POST /auth/token with invalid credentials
def test_login_for_access_token_invalid_username(client: TestClient, db_session: SQLAlchemySession):
    login_data = {
        "username": "wronguser",
        "password": "testpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_for_access_token_invalid_password(client: TestClient, test_user: models.User, db_session: SQLAlchemySession):
    login_data = {
        "username": test_user.username,
        "password": "wrongpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"


# Test a protected endpoint (e.g., /questions/next/ as it's simple GET and protected)
# This indirectly tests get_current_user
def test_protected_route_no_token(client: TestClient, db_session: SQLAlchemySession):
    # Create a dummy question so /questions/next/ doesn't fail with 404 if DB is empty
    # This is more of an integration test detail for /next/ but helps isolate auth here
    question_data = schemas.QuestionCreate(
        problem_statement="Test question for auth", 
        option_1="A", option_2="B", option_3="C", option_4="D", 
        correct_answer=1, explanation="Auth test"
    )
    db_question = models.Question(**question_data.model_dump())
    db_session.add(db_question)
    db_session.commit()

    response = client.get("/questions/next/") # Attempt to access without token
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated" # Or "Could not validate credentials" depending on FastAPI version and setup

def test_protected_route_invalid_token(client: TestClient, db_session: SQLAlchemySession):
    # (Setup dummy question as above if necessary, client fixture should handle clean DB)
    question_data = schemas.QuestionCreate(
        problem_statement="Test question for auth invalid token", 
        option_1="A", option_2="B", option_3="C", option_4="D", 
        correct_answer=1, explanation="Auth test invalid"
    )
    db_question = models.Question(**question_data.model_dump())
    db_session.add(db_question)
    db_session.commit()

    headers = {"Authorization": "Bearer aninvalidtoken"}
    response = client.get("/questions/next/", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"

def test_protected_route_valid_token(client: TestClient, test_user: models.User, db_session: SQLAlchemySession):
    # (Setup dummy question as above)
    question_data = schemas.QuestionCreate(
        problem_statement="Test question for auth valid token", 
        option_1="A", option_2="B", option_3="C", option_4="D", 
        correct_answer=1, explanation="Auth test valid"
    )
    db_question = models.Question(**question_data.model_dump())
    db_session.add(db_question)
    db_session.commit()
    
    # Generate a token for the test_user
    access_token = create_access_token(
        data={"sub": test_user.username}, expires_delta=timedelta(minutes=15)
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.get("/questions/next/", headers=headers)
    assert response.status_code == status.HTTP_200_OK # Assuming a question is found
    # Further checks on the response data can be done if needed, but for auth, 200 is key.
    assert "id" in response.json() # Check if it looks like a question object
    assert response.json()["problem_statement"] == "Test question for auth valid token"

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from fastapi import status

from app.schemas import schemas
from app.models import models
from app.crud import crud_question, crud_user_answer # For setting up test scenarios

# Sample question data for reuse
sample_question_api_data = {
    "problem_statement": "API Test: What is 2x2?",
    "option_1": "2", "option_2": "4", "option_3": "6", "option_4": "8",
    "correct_answer": 2, "explanation": "Multiplication."
}

def test_create_question_api(authenticated_client: TestClient, db_session: SQLAlchemySession):
    question_payload = schemas.QuestionCreate(**sample_question_api_data)
    
    response = authenticated_client.post("/questions/", json=question_payload.model_dump())
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["problem_statement"] == question_payload.problem_statement
    assert "id" in data
    
    # Verify in DB
    db_q = db_session.query(models.Question).filter(models.Question.id == data["id"]).first()
    assert db_q is not None
    assert db_q.problem_statement == question_payload.problem_statement

def test_read_question_api(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # Create a question directly via CRUD for this test
    question_in_db = crud_question.create_question(db_session, schemas.QuestionCreate(**sample_question_api_data))
    
    response = authenticated_client.get(f"/questions/{question_in_db.id}/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == question_in_db.id
    assert data["problem_statement"] == question_in_db.problem_statement

def test_read_question_api_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/questions/99999/") # Non-existent ID
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_read_questions_api(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # Create a couple of questions
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**sample_question_api_data, "problem_statement": "API Q1"}))
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**sample_question_api_data, "problem_statement": "API Q2"}))
    
    response = authenticated_client.get("/questions/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2

def test_submit_answer_correct(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    question_data = {**sample_question_api_data, "correct_answer": 3, "problem_statement": "Submit Correct Test"}
    question = crud_question.create_question(db_session, schemas.QuestionCreate(**question_data))
    
    answer_payload = schemas.UserAnswerSubmit(selected_answer=3) # Correct answer
    response = authenticated_client.post(f"/questions/{question.id}/answer/", json=answer_payload.model_dump())
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["question_id"] == question.id
    assert data["submitted_answer"] == answer_payload.selected_answer
    assert data["is_correct"] is True
    assert data["correct_answer_option"] == question.correct_answer
    assert data["explanation"] == question.explanation
    
    # Verify in DB
    db_ua = db_session.query(models.UserAnswer).filter(
        models.UserAnswer.question_id == question.id,
        models.UserAnswer.user_id == test_user.id
    ).first()
    assert db_ua is not None
    assert db_ua.selected_answer == answer_payload.selected_answer
    assert db_ua.is_correct is True

def test_submit_answer_incorrect(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    question_data = {**sample_question_api_data, "correct_answer": 1, "problem_statement": "Submit Incorrect Test"}
    question = crud_question.create_question(db_session, schemas.QuestionCreate(**question_data))
    
    answer_payload = schemas.UserAnswerSubmit(selected_answer=2) # Incorrect answer
    response = authenticated_client.post(f"/questions/{question.id}/answer/", json=answer_payload.model_dump())
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_correct"] is False
    
    # Verify in DB
    db_ua = db_session.query(models.UserAnswer).filter(
        models.UserAnswer.question_id == question.id,
        models.UserAnswer.user_id == test_user.id
    ).first()
    assert db_ua is not None
    assert db_ua.is_correct is False

def test_get_next_question_new_user(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    # Ensure there's at least one question in the DB
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**sample_question_api_data, "problem_statement": "Next Q New User"}))
    
    response = authenticated_client.get("/questions/next/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data # It's a question object

def test_get_next_question_user_answered_some(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    q1 = crud_question.create_question(db_session, schemas.QuestionCreate(**{**sample_question_api_data, "problem_statement": "Next Q Some Ans 1"}))
    q2 = crud_question.create_question(db_session, schemas.QuestionCreate(**{**sample_question_api_data, "problem_statement": "Next Q Some Ans 2"}))
    
    # User answers Q1
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), test_user.id)
    
    response = authenticated_client.get("/questions/next/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == q2.id # Should get the unanswered question Q2

def test_get_next_question_no_unanswered_prioritizes_incorrect_rate(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    # Create questions
    q1_data = {**sample_question_api_data, "problem_statement": "Q_Prio_1", "correct_answer": 1}
    q2_data = {**sample_question_api_data, "problem_statement": "Q_Prio_2", "correct_answer": 1}
    q1 = crud_question.create_question(db_session, schemas.QuestionCreate(**q1_data))
    q2 = crud_question.create_question(db_session, schemas.QuestionCreate(**q2_data))

    # User answers Q1 correctly, Q2 incorrectly
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), test_user.id) # Correct
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=2), test_user.id) # Incorrect

    # Another user to establish global stats: answers Q2 incorrectly as well
    from app.crud import crud_user
    other_user = crud_user.create_user(db_session, schemas.UserCreate(username="other_user_prio", password="pw"))
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=2), other_user.id) # Incorrect

    response = authenticated_client.get("/questions/next/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Q2 has a global incorrect rate of 1.0 (2 incorrect / 2 total for Q2)
    # Q1 has a global incorrect rate of 0.0 (0 incorrect / 1 total for Q1)
    # User answered Q1 correctly, so it's in 'always_correct_ids' for this user.
    # User answered Q2 incorrectly, so it's NOT in 'always_correct_ids'.
    # Thus, Q2 should be prioritized.
    assert data["id"] == q2.id

# Add more tests for /next/ covering other prioritization steps if time permits.
# E.g., user answered all, some always correctly, others not.
# E.g., user answered all, all always correctly -> fallback to global correct rate.
# E.g., no questions in DB -> 404 (already implicitly tested by some auth tests if question setup is missing)
# E.g., questions exist but no answers yet globally -> random choice from unanswered or any if all answered by user.

def test_get_next_question_no_questions_in_db(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # Ensure DB is empty of questions
    db_session.query(models.UserAnswer).delete()
    db_session.query(models.Question).delete()
    db_session.commit()

    response = authenticated_client.get("/questions/next/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No questions available in the database."

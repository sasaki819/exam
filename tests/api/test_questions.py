from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from fastapi import status
from typing import Dict # For type hinting dictionary

from app.schemas import schemas
from app.models import models
from app.crud import crud_question, crud_user_answer, crud_exam_type # For setting up test scenarios

# Sample question data for reuse, now requires exam_type_id
def get_sample_question_api_data(exam_type_id: int) -> Dict:
    return {
        "problem_statement": "API Test: What is 2x2?",
        "option_1": "2", "option_2": "4", "option_3": "6", "option_4": "8",
        "correct_answer": 2, "explanation": "Multiplication.",
        "exam_type_id": exam_type_id
    }

def test_create_question_api(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    question_payload_dict = get_sample_question_api_data(test_exam_type.id)
    question_payload = schemas.QuestionCreate(**question_payload_dict)
    
    response = authenticated_client.post("/questions/", json=question_payload.model_dump())
    
    assert response.status_code == status.HTTP_201_CREATED # Updated to 201 as per router
    data = response.json()
    assert data["problem_statement"] == question_payload.problem_statement
    assert data["exam_type_id"] == test_exam_type.id
    assert "id" in data
    
    db_q = db_session.query(models.Question).filter(models.Question.id == data["id"]).first()
    assert db_q is not None
    assert db_q.problem_statement == question_payload.problem_statement

def test_create_question_invalid_exam_type_id(authenticated_client: TestClient):
    question_payload_dict = get_sample_question_api_data(99999) # Non-existent exam_type_id
    response = authenticated_client.post("/questions/", json=question_payload_dict)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "ExamType with id 99999 not found" in response.json()["detail"]

def test_create_question_missing_exam_type_id(authenticated_client: TestClient):
    question_payload_dict = get_sample_question_api_data(1) # Dummy ID, will remove
    del question_payload_dict["exam_type_id"]
    response = authenticated_client.post("/questions/", json=question_payload_dict)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_read_question_api(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    question_in_db = crud_question.create_question(db_session, schemas.QuestionCreate(**get_sample_question_api_data(test_exam_type.id)))
    response = authenticated_client.get(f"/questions/{question_in_db.id}/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == question_in_db.id
    assert data["problem_statement"] == question_in_db.problem_statement

def test_read_question_api_not_found(authenticated_client: TestClient):
    response = authenticated_client.get("/questions/99999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_read_questions_api_no_filter(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**get_sample_question_api_data(test_exam_type.id), "problem_statement": "API Q1 Type A"}))
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**get_sample_question_api_data(test_exam_type.id), "problem_statement": "API Q2 Type A"}))
    
    response = authenticated_client.get("/questions/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2

def test_read_questions_api_with_exam_type_filter(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    et1 = test_exam_type # Re-use the fixture one
    et2_data = schemas.ExamTypeCreate(name="Filter Test ET 2")
    et2 = crud_exam_type.create_exam_type(db_session, et2_data)

    crud_question.create_question(db_session, schemas.QuestionCreate(**{**get_sample_question_api_data(et1.id), "problem_statement": "Q for ET1"}))
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**get_sample_question_api_data(et2.id), "problem_statement": "Q for ET2"}))

    # Filter for et1
    response_et1 = authenticated_client.get(f"/questions/?exam_type_id={et1.id}")
    assert response_et1.status_code == status.HTTP_200_OK
    data_et1 = response_et1.json()
    assert len(data_et1) == 1
    assert data_et1[0]["problem_statement"] == "Q for ET1"
    assert data_et1[0]["exam_type_id"] == et1.id

    # Filter for et2
    response_et2 = authenticated_client.get(f"/questions/?exam_type_id={et2.id}")
    assert response_et2.status_code == status.HTTP_200_OK
    data_et2 = response_et2.json()
    assert len(data_et2) == 1
    assert data_et2[0]["problem_statement"] == "Q for ET2"
    assert data_et2[0]["exam_type_id"] == et2.id
    
    # Filter for non-existent exam_type_id
    response_non_existent_et = authenticated_client.get("/questions/?exam_type_id=99999")
    assert response_non_existent_et.status_code == status.HTTP_200_OK # API returns empty list for valid but non-matching filter
    assert len(response_non_existent_et.json()) == 0


def test_submit_answer_correct(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType):
    question_data = {**get_sample_question_api_data(test_exam_type.id), "correct_answer": 3, "problem_statement": "Submit Correct Test"}
    question = crud_question.create_question(db_session, schemas.QuestionCreate(**question_data))
    
    answer_payload = schemas.UserAnswerSubmit(selected_answer=3)
    response = authenticated_client.post(f"/questions/{question.id}/answer/", json=answer_payload.model_dump())
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_correct"] is True
    
def test_get_next_question_requires_exam_type_id(authenticated_client: TestClient):
    response = authenticated_client.get("/questions/next/") # Missing exam_type_id
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_next_question_invalid_exam_type_id(authenticated_client: TestClient):
    response = authenticated_client.get("/questions/next/?exam_type_id=99999") # Invalid exam_type_id
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "ExamType with id 99999 not found" in response.json()["detail"]

def test_get_next_question_no_questions_for_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    # test_exam_type exists but has no questions
    response = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert f"No questions available for exam type {test_exam_type.id}" in response.json()["detail"]


def test_get_next_question_new_user_specific_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    crud_question.create_question(db_session, schemas.QuestionCreate(**{**get_sample_question_api_data(test_exam_type.id), "problem_statement": "Next Q New User ET Specific"}))
    response = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["exam_type_id"] == test_exam_type.id

def test_get_next_question_user_answered_all_in_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType):
    q1 = crud_question.create_question(db_session, schemas.QuestionCreate(**{**get_sample_question_api_data(test_exam_type.id), "problem_statement": "Q All Ans 1"}))
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), test_user.id)
    
    # This test will check fallback logic. As per current router, it might pick Q1 again based on global stats
    # or if Q1 is the only question, it will be picked for review.
    response = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response.status_code == status.HTTP_200_OK 
    data = response.json()
    assert data["id"] == q1.id # Fallback logic will pick this question for review

def test_update_question(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    question = crud_question.create_question(db_session, schemas.QuestionCreate(**get_sample_question_api_data(test_exam_type.id)))
    update_payload = schemas.QuestionUpdate(problem_statement="Updated Problem Statement via API", correct_answer=3)
    
    response = authenticated_client.put(f"/questions/{question.id}", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["problem_statement"] == "Updated Problem Statement via API"
    assert data["correct_answer"] == 3
    assert data["exam_type_id"] == test_exam_type.id # Should remain unchanged

    db_session.refresh(question)
    assert question.problem_statement == "Updated Problem Statement via API"

def test_update_question_change_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    et_original = test_exam_type
    et_new_data = schemas.ExamTypeCreate(name="New ET for Question Update")
    et_new = crud_exam_type.create_exam_type(db_session, et_new_data)

    question = crud_question.create_question(db_session, schemas.QuestionCreate(**get_sample_question_api_data(et_original.id)))
    update_payload = schemas.QuestionUpdate(exam_type_id=et_new.id)

    response = authenticated_client.put(f"/questions/{question.id}", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["exam_type_id"] == et_new.id

    db_session.refresh(question)
    assert question.exam_type_id == et_new.id

def test_update_question_invalid_new_exam_type_id(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    question = crud_question.create_question(db_session, schemas.QuestionCreate(**get_sample_question_api_data(test_exam_type.id)))
    update_payload = schemas.QuestionUpdate(exam_type_id=99999) # Non-existent
    
    response = authenticated_client.put(f"/questions/{question.id}", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "ExamType with id 99999 not found" in response.json()["detail"]

def test_update_non_existent_question(authenticated_client: TestClient):
    update_payload = schemas.QuestionUpdate(problem_statement="Trying to update non-existent")
    response = authenticated_client.put("/questions/99999", json=update_payload.model_dump(exclude_unset=True))
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_question(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType):
    question_to_delete = crud_question.create_question(db_session, schemas.QuestionCreate(**get_sample_question_api_data(test_exam_type.id)))
    # Create a user answer for this question
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=question_to_delete.id, selected_answer=1), test_user.id)
    
    user_answers_before = db_session.query(models.UserAnswer).filter(models.UserAnswer.question_id == question_to_delete.id).count()
    assert user_answers_before > 0
    
    response = authenticated_client.delete(f"/questions/{question_to_delete.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == question_to_delete.id

    # Verify question is deleted from DB
    db_question_after = db_session.query(models.Question).filter(models.Question.id == question_to_delete.id).first()
    assert db_question_after is None

    # Verify associated UserAnswers are deleted
    user_answers_after = db_session.query(models.UserAnswer).filter(models.UserAnswer.question_id == question_to_delete.id).count()
    assert user_answers_after == 0

def test_delete_non_existent_question(authenticated_client: TestClient):
    response = authenticated_client.delete("/questions/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Test get_next_question behavior when all questions in an exam type are answered,
# and some were answered always correctly, others not.
def test_get_next_question_all_answered_mixed_correctness(
    authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType
):
    # Question 1: User answers correctly
    q1_data = {**get_sample_question_api_data(test_exam_type.id), "problem_statement": "Next Q Mixed Ans 1", "correct_answer": 1}
    q1 = crud_question.create_question(db_session, schemas.QuestionCreate(**q1_data))
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), test_user.id) # Correct

    # Question 2: User answers incorrectly
    q2_data = {**get_sample_question_api_data(test_exam_type.id), "problem_statement": "Next Q Mixed Ans 2", "correct_answer": 1}
    q2 = crud_question.create_question(db_session, schemas.QuestionCreate(**q2_data))
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=2), test_user.id) # Incorrect

    # Another user also answers Q2 incorrectly to give it a higher global incorrect rate
    other_user_data = schemas.UserCreate(username="other_user_mixed", password="pw")
    other_user = crud_exam_type.crud_user.create_user(db_session, other_user_data) # Assuming crud_exam_type has crud_user
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=2), other_user.id) # Incorrect

    # Now, all questions in test_exam_type are answered by test_user.
    # Q1 is in "always_correct_ids" for test_user.
    # Q2 is NOT in "always_correct_ids" for test_user and has a global incorrect rate.
    # /next/ should prioritize Q2.
    response = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == q2.id
    
def test_get_next_question_no_questions_in_db_at_all(authenticated_client: TestClient, db_session: SQLAlchemySession, test_exam_type: models.ExamType):
    # Specific test for when NO questions exist at all for a valid exam_type
    # (differs from test_get_next_question_no_questions_for_exam_type where questions might exist for OTHER exam types)
    
    # Ensure DB is empty of questions for this exam type (and all others for this test's purpose)
    db_session.query(models.UserAnswer).delete() # Clear all answers
    db_session.query(models.Question).delete() # Clear all questions
    db_session.commit()
    
    # Re-fetch or ensure test_exam_type still exists or is recreated if db_session dropped it fully
    # The db_session fixture drops and recreates all tables, so test_exam_type from fixture is valid.
    # However, it won't have questions.

    response = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # The detail message might vary based on how the conditions are checked in the endpoint.
    # Based on current router logic:
    # 1. get_unanswered_question_ids will be empty.
    # 2. get_question_global_stats will be empty.
    # This leads to "No questions available for exam type {exam_type_id}."
    assert f"No questions available for exam type {test_exam_type.id}" in response.json()["detail"]

# Test case where exam_type_id is valid, user has answered all questions correctly.
# The fallback logic should pick one of these for review.
def test_get_next_question_all_answered_correctly_fallback(
    authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType
):
    q1_data = {**get_sample_question_api_data(test_exam_type.id), "problem_statement": "All Correct Fallback Q1", "correct_answer": 1}
    q1 = crud_question.create_question(db_session, schemas.QuestionCreate(**q1_data))
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), test_user.id)

    q2_data = {**get_sample_question_api_data(test_exam_type.id), "problem_statement": "All Correct Fallback Q2", "correct_answer": 2}
    q2 = crud_question.create_question(db_session, schemas.QuestionCreate(**q2_data))
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=2), test_user.id)

    # User has answered all questions in test_exam_type correctly.
    # Global stats might be 0 incorrect for both.
    response = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # It should pick one of them (q1 or q2) for review.
    assert data["id"] in [q1.id, q2.id]

    # If we add another user's answers making Q2 globally more "incorrect", it should still pick from Q1 or Q2
    # for this user, as this user answered both correctly.
    # The prioritization of "global_incorrect_rate" applies to questions *not* in "always_correct_ids".
    # If all are in "always_correct_ids", the current logic is:
    # eligible_for_incorrect_rate_prioritization will be empty.
    # Then it falls to `elif global_stats: selected_question_id = random.choice(global_stats)["question_id"]`
    # This means it will pick randomly from any question in the exam type for review.
    
    other_user_data = schemas.UserCreate(username="other_user_all_correct", password="pw")
    other_user = crud_exam_type.crud_user.create_user(db_session, other_user_data)
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=1), other_user.id) # Q2 incorrect for other_user

    response_after_other_user = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response_after_other_user.status_code == status.HTTP_200_OK
    data_after = response_after_other_user.json()
    assert data_after["id"] in [q1.id, q2.id] # Still picks one for review for test_user.
    
    # If there's only one question and user answered it correctly, it should return that one.
    db_session.query(models.UserAnswer).filter(models.UserAnswer.question_id == q2.id).delete()
    db_session.query(models.Question).filter(models.Question.id == q2.id).delete()
    db_session.commit()
    
    response_one_q = authenticated_client.get(f"/questions/next/?exam_type_id={test_exam_type.id}")
    assert response_one_q.status_code == status.HTTP_200_OK
    data_one_q = response_one_q.json()
    assert data_one_q["id"] == q1.id

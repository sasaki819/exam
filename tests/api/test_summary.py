from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from fastapi import status

from app.schemas import schemas
from app.models import models
from app.crud import crud_question, crud_user_answer # For setting up test scenarios

# Sample question data for reuse
sample_question_summary_data_1 = {
    "problem_statement": "Summary API Q1",
    "option_1": "A1", "option_2": "B1", "option_3": "C1", "option_4": "D1",
    "correct_answer": 1, "explanation": "Expl1."
}
sample_question_summary_data_2 = {
    "problem_statement": "Summary API Q2",
    "option_1": "A2", "option_2": "B2", "option_3": "C2", "option_4": "D2",
    "correct_answer": 2, "explanation": "Expl2."
}

def test_get_summary_no_answers(authenticated_client: TestClient, test_user: models.User):
    response = authenticated_client.get("/summary/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["summary_stats"]["total_unique_questions_attempted"] == 0
    assert data["summary_stats"]["total_answers_submitted"] == 0
    assert data["summary_stats"]["total_correct_answers"] == 0
    assert data["summary_stats"]["total_incorrect_answers"] == 0
    assert data["summary_stats"]["correct_answer_rate"] == 0.0
    assert len(data["question_performance"]) == 0

def test_get_summary_with_answers(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    # Create questions
    q1_data = schemas.QuestionCreate(**sample_question_summary_data_1)
    q2_data = schemas.QuestionCreate(**sample_question_summary_data_2)
    q1 = crud_question.create_question(db_session, q1_data)
    q2 = crud_question.create_question(db_session, q2_data)

    # User answers Q1 correctly
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=q1.correct_answer), test_user.id)
    # User answers Q1 again, incorrectly
    incorrect_q1_answer = q1.correct_answer + 1 if q1.correct_answer < 4 else q1.correct_answer -1
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1.id, selected_answer=incorrect_q1_answer), test_user.id)
    
    # User answers Q2 incorrectly
    incorrect_q2_answer = q2.correct_answer + 1 if q2.correct_answer < 4 else q2.correct_answer -1
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2.id, selected_answer=incorrect_q2_answer), test_user.id)

    response = authenticated_client.get("/summary/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check summary_stats
    stats = data["summary_stats"]
    assert stats["total_unique_questions_attempted"] == 2
    assert stats["total_answers_submitted"] == 3
    assert stats["total_correct_answers"] == 1
    assert stats["total_incorrect_answers"] == 2
    assert stats["correct_answer_rate"] == 1/3 

    # Check question_performance
    perf = data["question_performance"]
    assert len(perf) == 2

    q1_perf = next((p for p in perf if p["question_id"] == q1.id), None)
    assert q1_perf is not None
    assert q1_perf["problem_statement"] == q1.problem_statement
    assert q1_perf["times_answered"] == 2
    assert q1_perf["times_correct"] == 1
    assert q1_perf["times_incorrect"] == 1

    q2_perf = next((p for p in perf if p["question_id"] == q2.id), None)
    assert q2_perf is not None
    assert q2_perf["problem_statement"] == q2.problem_statement
    assert q2_perf["times_answered"] == 1
    assert q2_perf["times_correct"] == 0
    assert q2_perf["times_incorrect"] == 1

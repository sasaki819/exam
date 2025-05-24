from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from fastapi import status

from app.schemas import schemas
from app.models import models
from app.crud import crud_question, crud_user_answer, crud_exam_type # For setting up test scenarios

# Sample question data for reuse, now requires exam_type_id
def get_sample_summary_q_data(exam_type_id: int, suffix: str) -> dict:
    return {
        "problem_statement": f"Summary API Q{suffix} ET{exam_type_id}",
        "option_1": f"A{suffix}", "option_2": f"B{suffix}", "option_3": f"C{suffix}", "option_4": f"D{suffix}",
        "correct_answer": 1, "explanation": f"Expl{suffix}.",
        "exam_type_id": exam_type_id
    }

def test_get_summary_no_answers(authenticated_client: TestClient, test_user: models.User):
    response = authenticated_client.get("/summary/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["summary_stats"]["total_unique_questions_attempted"] == 0
    assert data["summary_stats"]["total_answers_submitted"] == 0
    assert len(data["question_performance"]) == 0

def test_get_summary_with_answers_no_filter(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType):
    et1 = test_exam_type
    et2_data = schemas.ExamTypeCreate(name="Summary Test ET2")
    et2 = crud_exam_type.create_exam_type(db_session, et2_data)

    q1_et1_data = schemas.QuestionCreate(**get_sample_summary_q_data(et1.id, "1_ET1"))
    q1_et1 = crud_question.create_question(db_session, q1_et1_data)
    
    q1_et2_data = schemas.QuestionCreate(**get_sample_summary_q_data(et2.id, "1_ET2"))
    q1_et2 = crud_question.create_question(db_session, q1_et2_data)

    # User answers Q1_ET1 correctly
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1_et1.id, selected_answer=q1_et1.correct_answer), test_user.id)
    # User answers Q1_ET2 incorrectly
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1_et2.id, selected_answer=q1_et2.correct_answer + 1), test_user.id)

    response = authenticated_client.get("/summary/") # No exam_type_id filter
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    stats = data["summary_stats"]
    assert stats["total_unique_questions_attempted"] == 2 # Both questions from different exam types
    assert stats["total_answers_submitted"] == 2
    assert stats["total_correct_answers"] == 1
    assert stats["total_incorrect_answers"] == 1
    assert stats["correct_answer_rate"] == 0.5

    perf = data["question_performance"]
    assert len(perf) == 2
    assert any(p["question_id"] == q1_et1.id for p in perf)
    assert any(p["question_id"] == q1_et2.id for p in perf)

def test_get_summary_with_exam_type_filter(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType):
    et1 = test_exam_type # Default exam type from fixture
    et2_data = schemas.ExamTypeCreate(name="Summary Filter Test ET2")
    et2 = crud_exam_type.create_exam_type(db_session, et2_data)

    # Questions for ET1
    q1_et1_data = schemas.QuestionCreate(**get_sample_summary_q_data(et1.id, "Q1_For_ET1"))
    q1_et1 = crud_question.create_question(db_session, q1_et1_data)
    q2_et1_data = schemas.QuestionCreate(**get_sample_summary_q_data(et1.id, "Q2_For_ET1"))
    q2_et1 = crud_question.create_question(db_session, q2_et1_data)

    # Question for ET2
    q1_et2_data = schemas.QuestionCreate(**get_sample_summary_q_data(et2.id, "Q1_For_ET2"))
    q1_et2 = crud_question.create_question(db_session, q1_et2_data)

    # User answers for ET1
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1_et1.id, selected_answer=q1_et1.correct_answer), test_user.id) # Correct
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q2_et1.id, selected_answer=q2_et1.correct_answer + 1), test_user.id) # Incorrect
    
    # User answer for ET2
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q1_et2.id, selected_answer=q1_et2.correct_answer), test_user.id) # Correct

    # Test summary for ET1
    response_et1 = authenticated_client.get(f"/summary/?exam_type_id={et1.id}")
    assert response_et1.status_code == status.HTTP_200_OK
    data_et1 = response_et1.json()

    stats_et1 = data_et1["summary_stats"]
    assert stats_et1["total_unique_questions_attempted"] == 2 # q1_et1, q2_et1
    assert stats_et1["total_answers_submitted"] == 2
    assert stats_et1["total_correct_answers"] == 1
    assert stats_et1["total_incorrect_answers"] == 1
    assert stats_et1["correct_answer_rate"] == 0.5

    perf_et1 = data_et1["question_performance"]
    assert len(perf_et1) == 2
    assert all(p["question_id"] in [q1_et1.id, q2_et1.id] for p in perf_et1)
    # Verify content of one performance item
    q1_et1_perf = next((p for p in perf_et1 if p["question_id"] == q1_et1.id), None)
    assert q1_et1_perf is not None
    assert q1_et1_perf["times_correct"] == 1
    assert q1_et1_perf["times_incorrect"] == 0


    # Test summary for ET2
    response_et2 = authenticated_client.get(f"/summary/?exam_type_id={et2.id}")
    assert response_et2.status_code == status.HTTP_200_OK
    data_et2 = response_et2.json()

    stats_et2 = data_et2["summary_stats"]
    assert stats_et2["total_unique_questions_attempted"] == 1 # q1_et2
    assert stats_et2["total_answers_submitted"] == 1
    assert stats_et2["total_correct_answers"] == 1
    assert stats_et2["total_incorrect_answers"] == 0
    assert stats_et2["correct_answer_rate"] == 1.0

    perf_et2 = data_et2["question_performance"]
    assert len(perf_et2) == 1
    assert perf_et2[0]["question_id"] == q1_et2.id
    assert perf_et2[0]["times_correct"] == 1

def test_get_summary_non_existent_exam_type_id(authenticated_client: TestClient):
    response = authenticated_client.get("/summary/?exam_type_id=99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "ExamType with id 99999 not found" in response.json()["detail"]

def test_get_summary_exam_type_with_no_user_answers(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    et_no_answers_data = schemas.ExamTypeCreate(name="Summary ET No Answers")
    et_no_answers = crud_exam_type.create_exam_type(db_session, et_no_answers_data)
    
    # Create a question for this exam type, but user does not answer it
    q_data = schemas.QuestionCreate(**get_sample_summary_q_data(et_no_answers.id, "Q_NoAns"))
    crud_question.create_question(db_session, q_data)

    response = authenticated_client.get(f"/summary/?exam_type_id={et_no_answers.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    stats = data["summary_stats"]
    assert stats["total_unique_questions_attempted"] == 0
    assert stats["total_answers_submitted"] == 0
    assert stats["total_correct_answers"] == 0
    assert stats["total_incorrect_answers"] == 0
    assert stats["correct_answer_rate"] == 0.0
    assert len(data["question_performance"]) == 0

def test_get_summary_exam_type_exists_but_no_questions_in_it(authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User):
    et_no_questions_data = schemas.ExamTypeCreate(name="Summary ET No Questions")
    et_no_questions = crud_exam_type.create_exam_type(db_session, et_no_questions_data)
    
    # No questions are created for et_no_questions
    
    response = authenticated_client.get(f"/summary/?exam_type_id={et_no_questions.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    stats = data["summary_stats"]
    assert stats["total_unique_questions_attempted"] == 0
    assert stats["total_answers_submitted"] == 0
    assert stats["total_correct_answers"] == 0
    assert stats["total_incorrect_answers"] == 0
    assert stats["correct_answer_rate"] == 0.0
    assert len(data["question_performance"]) == 0
    
# Test to ensure that if a user has answered questions from other exam types,
# but none from the filtered exam_type_id, the summary is correctly zeroed for that filter.
def test_get_summary_answers_exist_elsewhere_not_in_filtered_exam_type(
    authenticated_client: TestClient, db_session: SQLAlchemySession, test_user: models.User, test_exam_type: models.ExamType
):
    et_answered = test_exam_type # User will answer questions from this exam type
    et_not_answered_data = schemas.ExamTypeCreate(name="Summary ET Not Answered By User")
    et_not_answered = crud_exam_type.create_exam_type(db_session, et_not_answered_data)

    # Question for et_answered, which the user answers
    q_answered_data = schemas.QuestionCreate(**get_sample_summary_q_data(et_answered.id, "Q_Ans_ET1"))
    q_answered = crud_question.create_question(db_session, q_answered_data)
    crud_user_answer.create_user_answer(db_session, schemas.UserAnswerCreate(question_id=q_answered.id, selected_answer=1), test_user.id)

    # Question for et_not_answered, which the user does NOT answer
    q_not_answered_data = schemas.QuestionCreate(**get_sample_summary_q_data(et_not_answered.id, "Q_NotAns_ET2"))
    crud_question.create_question(db_session, q_not_answered_data)
    
    # Fetch summary for et_not_answered
    response = authenticated_client.get(f"/summary/?exam_type_id={et_not_answered.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    stats = data["summary_stats"]
    assert stats["total_unique_questions_attempted"] == 0
    assert stats["total_answers_submitted"] == 0
    assert stats["total_correct_answers"] == 0
    assert stats["total_incorrect_answers"] == 0
    assert stats["correct_answer_rate"] == 0.0
    assert len(data["question_performance"]) == 0
    
    # For sanity, check that the overall summary (no filter) would show the answer from et_answered
    response_overall = authenticated_client.get("/summary/")
    assert response_overall.status_code == status.HTTP_200_OK
    data_overall = response_overall.json()
    assert data_overall["summary_stats"]["total_answers_submitted"] == 1
    assert data_overall["summary_stats"]["total_unique_questions_attempted"] == 1
    assert len(data_overall["question_performance"]) == 1
    assert data_overall["question_performance"][0]["question_id"] == q_answered.id

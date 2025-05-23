from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from app.crud import crud_summary, crud_question, crud_user_answer, crud_user
from app.schemas import schemas
from app.models import models # For type hinting

# Sample data for reuse
sample_question_data_1 = {
    "problem_statement": "Summary Q1: What is 10+10?",
    "option_1": "10", "option_2": "20", "option_3": "30", "option_4": "40",
    "correct_answer": 2, "explanation": "Math."
}
sample_question_data_2 = {
    "problem_statement": "Summary Q2: What is the color of the sky?",
    "option_1": "Green", "option_2": "Blue", "option_3": "Red", "option_4": "Yellow",
    "correct_answer": 2, "explanation": "Observation."
}

def test_get_user_summary_stats_no_answers(db_session: SQLAlchemySession, test_user: models.User):
    stats = crud_summary.get_user_summary_stats(db=db_session, user_id=test_user.id)
    
    assert stats["total_unique_questions_attempted"] == 0
    assert stats["total_answers_submitted"] == 0
    assert stats["total_correct_answers"] == 0
    assert stats["total_incorrect_answers"] == 0

def test_get_user_summary_stats_with_answers(db_session: SQLAlchemySession, test_user: models.User):
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**sample_question_data_1))
    q2 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**sample_question_data_2))

    # User answers Q1 correctly
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=2), user_id=test_user.id)
    # User answers Q1 again, incorrectly
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id)
    # User answers Q2 incorrectly
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q2.id, selected_answer=1), user_id=test_user.id)

    stats = crud_summary.get_user_summary_stats(db=db_session, user_id=test_user.id)
    
    assert stats["total_unique_questions_attempted"] == 2 # q1, q2
    assert stats["total_answers_submitted"] == 3 # Three submissions in total
    assert stats["total_correct_answers"] == 1 # Only the first answer to Q1
    assert stats["total_incorrect_answers"] == 2 # Second answer to Q1, and answer to Q2

def test_get_user_question_performance_no_answers(db_session: SQLAlchemySession, test_user: models.User):
    # Create a question, but user doesn't answer it
    crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**sample_question_data_1))
    
    performance = crud_summary.get_user_question_performance(db=db_session, user_id=test_user.id)
    assert len(performance) == 0 # User hasn't answered any questions

def test_get_user_question_performance_with_answers(db_session: SQLAlchemySession, test_user: models.User):
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**sample_question_data_1))
    q2 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**sample_question_data_2))
    
    # Q1: Answered twice, once correct, once incorrect
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=2), user_id=test_user.id) # Correct
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id) # Incorrect
    
    # Q2: Answered once, incorrectly
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q2.id, selected_answer=3), user_id=test_user.id) # Incorrect

    performance = crud_summary.get_user_question_performance(db=db_session, user_id=test_user.id)
    assert len(performance) == 2 # Two unique questions answered
    
    q1_perf = next((p for p in performance if p["question_id"] == q1.id), None)
    assert q1_perf is not None
    assert q1_perf["problem_statement"] == q1.problem_statement
    assert q1_perf["times_answered"] == 2
    assert q1_perf["times_correct"] == 1
    assert q1_perf["times_incorrect"] == 1
    
    q2_perf = next((p for p in performance if p["question_id"] == q2.id), None)
    assert q2_perf is not None
    assert q2_perf["problem_statement"] == q2.problem_statement
    assert q2_perf["times_answered"] == 1
    assert q2_perf["times_correct"] == 0
    assert q2_perf["times_incorrect"] == 1

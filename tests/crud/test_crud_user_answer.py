from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from app.crud import crud_user_answer, crud_question, crud_user
from app.schemas import schemas
from app.models import models # For type hinting

# Sample data for reuse
sample_question_data = {
    "problem_statement": "What is 1 + 1?",
    "option_1": "1", "option_2": "2", "option_3": "3", "option_4": "4",
    "correct_answer": 2,
    "explanation": "Basic math."
}

def test_create_user_answer(db_session: SQLAlchemySession, test_user: models.User):
    # Create a question first
    question_in = schemas.QuestionCreate(**sample_question_data)
    question = crud_question.create_question(db=db_session, question=question_in)
    
    user_answer_in = schemas.UserAnswerCreate(
        question_id=question.id,
        selected_answer=question.correct_answer # User answers correctly
    )
    
    created_answer = crud_user_answer.create_user_answer(
        db=db_session, 
        user_answer=user_answer_in, 
        user_id=test_user.id
    )
    
    assert created_answer is not None
    assert created_answer.question_id == question.id
    assert created_answer.user_id == test_user.id
    assert created_answer.selected_answer == user_answer_in.selected_answer
    assert created_answer.is_correct is True
    
    db_ua = db_session.query(models.UserAnswer).filter(models.UserAnswer.id == created_answer.id).first()
    assert db_ua is not None
    assert db_ua.is_correct is True

def test_create_user_answer_incorrect(db_session: SQLAlchemySession, test_user: models.User):
    question_in = schemas.QuestionCreate(**{**sample_question_data, "correct_answer": 2})
    question = crud_question.create_question(db=db_session, question=question_in)
    
    incorrect_selected_answer = 1 # Assuming option 2 (value 2) is correct
    if question.correct_answer == incorrect_selected_answer: # Ensure it's actually incorrect
        incorrect_selected_answer = 3

    user_answer_in = schemas.UserAnswerCreate(
        question_id=question.id,
        selected_answer=incorrect_selected_answer 
    )
    
    created_answer = crud_user_answer.create_user_answer(
        db=db_session, 
        user_answer=user_answer_in, 
        user_id=test_user.id
    )
    
    assert created_answer is not None
    assert created_answer.is_correct is False

def test_get_user_answers_by_user(db_session: SQLAlchemySession, test_user: models.User):
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "Q_UA1"}))
    q2 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "Q_UA2"}))
    
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id)
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q2.id, selected_answer=1), user_id=test_user.id)
    
    user_answers = crud_user_answer.get_user_answers_by_user(db=db_session, user_id=test_user.id)
    assert len(user_answers) == 2
    assert user_answers[0].user_id == test_user.id
    assert user_answers[1].user_id == test_user.id

def test_get_answered_question_ids(db_session: SQLAlchemySession, test_user: models.User):
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "AQID1"}))
    q2 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "AQID2"}))
    crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "AQID3_unanswered"})) # Unanswered

    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id)
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=2), user_id=test_user.id) # Answer Q1 again
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q2.id, selected_answer=1), user_id=test_user.id)

    answered_ids = crud_user_answer.get_answered_question_ids(db=db_session, user_id=test_user.id)
    assert q1.id in answered_ids
    assert q2.id in answered_ids
    assert len(answered_ids) == 2 # Should be distinct IDs

def test_get_questions_always_answered_correctly_by_user(db_session: SQLAlchemySession, test_user: models.User):
    q1_data = {**sample_question_data, "problem_statement": "Q_AAC1", "correct_answer": 1}
    q2_data = {**sample_question_data, "problem_statement": "Q_AAC2", "correct_answer": 1}
    q3_data = {**sample_question_data, "problem_statement": "Q_AAC3", "correct_answer": 1} # User will answer this one incorrectly

    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**q1_data))
    q2 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**q2_data))
    q3 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**q3_data))

    # Q1: Always correct
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id)
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id)
    
    # Q2: Always correct (single answer)
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q2.id, selected_answer=1), user_id=test_user.id)

    # Q3: Incorrect once
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q3.id, selected_answer=1), user_id=test_user.id) # Correct
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q3.id, selected_answer=2), user_id=test_user.id) # Incorrect

    always_correct_ids = crud_user_answer.get_questions_always_answered_correctly_by_user(db=db_session, user_id=test_user.id)
    
    assert q1.id in always_correct_ids
    assert q2.id in always_correct_ids
    assert q3.id not in always_correct_ids
    assert len(always_correct_ids) == 2

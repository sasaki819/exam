from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from app.crud import crud_question, crud_user # For creating a user to associate answers
from app.schemas import schemas
from app.models import models # For type hinting and direct model interaction

# Sample question data for reuse
sample_question_data = {
    "problem_statement": "What is the capital of Testland?",
    "option_1": "Testville",
    "option_2": "Testburg",
    "option_3": "Test City",
    "option_4": "Testopolis",
    "correct_answer": 1,
    "explanation": "Testville is the capital of Testland."
}

def test_create_question(db_session: SQLAlchemySession):
    question_in = schemas.QuestionCreate(**sample_question_data)
    created_question = crud_question.create_question(db=db_session, question=question_in)
    
    assert created_question is not None
    assert created_question.problem_statement == question_in.problem_statement
    assert created_question.option_1 == question_in.option_1
    assert created_question.correct_answer == question_in.correct_answer
    
    db_q = db_session.query(models.Question).filter(models.Question.id == created_question.id).first()
    assert db_q is not None
    assert db_q.problem_statement == question_in.problem_statement

def test_get_question(db_session: SQLAlchemySession):
    question_in = schemas.QuestionCreate(**sample_question_data)
    created_question = crud_question.create_question(db=db_session, question=question_in)
    
    fetched_question = crud_question.get_question(db=db_session, question_id=created_question.id)
    assert fetched_question is not None
    assert fetched_question.id == created_question.id
    assert fetched_question.problem_statement == created_question.problem_statement

def test_get_question_nonexistent(db_session: SQLAlchemySession):
    fetched_question = crud_question.get_question(db=db_session, question_id=99999) # Assuming this ID won't exist
    assert fetched_question is None

def test_get_questions(db_session: SQLAlchemySession):
    # Create a couple of questions
    q_data1 = {**sample_question_data, "problem_statement": "Q1"}
    q_data2 = {**sample_question_data, "problem_statement": "Q2"}
    crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**q_data1))
    crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**q_data2))
    
    questions = crud_question.get_questions(db=db_session, skip=0, limit=10)
    assert len(questions) >= 2 # Could be more if other tests left data and scope wasn't function
                               # With function scope for db_session, it should be exactly 2 here

    # Test skip and limit
    questions_limit_1 = crud_question.get_questions(db=db_session, skip=0, limit=1)
    assert len(questions_limit_1) == 1
    
    questions_skip_1 = crud_question.get_questions(db=db_session, skip=1, limit=1)
    assert len(questions_skip_1) == 1
    if len(questions) >= 2: # Ensure there are at least 2 questions for this assertion
        assert questions_limit_1[0].id != questions_skip_1[0].id


def test_get_unanswered_question_ids(db_session: SQLAlchemySession, test_user: models.User):
    # Create some questions
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "UQ1"}))
    q2 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "UQ2"}))
    q3 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "UQ3"}))

    # User answers Q2
    from app.crud import crud_user_answer # Local import to avoid circularity if any
    user_answer_in = schemas.UserAnswerCreate(question_id=q2.id, selected_answer=1)
    crud_user_answer.create_user_answer(db=db_session, user_answer=user_answer_in, user_id=test_user.id)

    unanswered_ids = crud_question.get_unanswered_question_ids(db=db_session, user_id=test_user.id)
    assert q1.id in unanswered_ids
    assert q2.id not in unanswered_ids
    assert q3.id in unanswered_ids
    assert len(unanswered_ids) == 2


def test_get_question_global_stats_no_answers(db_session: SQLAlchemySession):
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "GSQ1"}))
    stats = crud_question.get_question_global_stats(db=db_session)
    
    assert len(stats) >= 1
    q1_stat = next((s for s in stats if s["question_id"] == q1.id), None)
    assert q1_stat is not None
    assert q1_stat["total_answers"] == 0
    assert q1_stat["total_correct_answers"] == 0
    assert q1_stat["total_incorrect_answers"] == 0
    assert q1_stat["global_correct_rate"] == 0
    assert q1_stat["global_incorrect_rate"] == 0


def test_get_question_global_stats_with_answers(db_session: SQLAlchemySession, test_user: models.User):
    q1 = crud_question.create_question(db=db_session, question=schemas.QuestionCreate(**{**sample_question_data, "problem_statement": "GSQ2", "correct_answer": 1}))
    
    # Another user for varied answers
    other_user_data = schemas.UserCreate(username="otheruserstats", password="password")
    other_user = crud_user.create_user(db=db_session, user=other_user_data)

    from app.crud import crud_user_answer
    # Q1: User answers correctly, Other User answers incorrectly
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=1), user_id=test_user.id) # Correct
    crud_user_answer.create_user_answer(db=db_session, user_answer=schemas.UserAnswerCreate(question_id=q1.id, selected_answer=2), user_id=other_user.id) # Incorrect
    
    stats = crud_question.get_question_global_stats(db=db_session)
    q1_stat = next((s for s in stats if s["question_id"] == q1.id), None)
    
    assert q1_stat is not None
    assert q1_stat["total_answers"] == 2
    assert q1_stat["total_correct_answers"] == 1
    assert q1_stat["total_incorrect_answers"] == 1
    assert q1_stat["global_correct_rate"] == 0.5
    assert q1_stat["global_incorrect_rate"] == 0.5

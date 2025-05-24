from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func # Added func

from app.models.models import UserAnswer, Question
from app.schemas import schemas # Assuming schemas are imported as app.schemas

def create_user_answer(db: Session, user_answer: schemas.UserAnswerCreate, user_id: int) -> UserAnswer:
    # We need to fetch the question to determine if the answer is correct.
    question = db.query(Question).filter(Question.id == user_answer.question_id).first()
    if not question:
        # This case should ideally be handled at the API level before calling CRUD
        # Or raise an exception here if question_id is invalid
        raise ValueError(f"Question with id {user_answer.question_id} not found.")

    is_correct = (question.correct_answer == user_answer.selected_answer)
    
    db_user_answer = UserAnswer(
        question_id=user_answer.question_id,
        user_id=user_id,
        selected_answer=user_answer.selected_answer,
        is_correct=is_correct
    )
    db.add(db_user_answer)
    db.commit()
    db.refresh(db_user_answer)
    return db_user_answer

def get_user_answers_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
    return db.query(UserAnswer).filter(UserAnswer.user_id == user_id).offset(skip).limit(limit).all()

def get_user_answers_by_question(db: Session, question_id: int, user_id: int) -> List[UserAnswer]:
    """
    Retrieves all answers a specific user has given for a specific question.
    Typically, a user answers a question once, but this allows for scenarios
    where multiple attempts might be stored or reviewed.
    """
    return db.query(UserAnswer).filter(
        UserAnswer.question_id == question_id,
        UserAnswer.user_id == user_id
    ).all()

def get_specific_user_answer(db: Session, question_id: int, user_id: int) -> Optional[UserAnswer]:
    """
    Retrieves the most recent answer a specific user has given for a specific question.
    This is useful if you only care about the latest attempt.
    """
    return db.query(UserAnswer).filter(
        UserAnswer.question_id == question_id,
        UserAnswer.user_id == user_id
    ).order_by(UserAnswer.answered_at.desc()).first()

def get_answered_question_ids(db: Session, user_id: int) -> List[int]:
    """
    Retrieves a list of question IDs that the user has already answered.
    """
    return [ua.question_id for ua in db.query(UserAnswer.question_id).filter(UserAnswer.user_id == user_id).distinct().all()]


def get_questions_always_answered_correctly_by_user(
    db: Session, 
    user_id: int, 
    exam_type_id: Optional[int] = None
) -> List[int]:
    """
    Returns a list of question IDs that the given user has answered one or more times,
    and all of those answers were correct. Optionally filters by exam_type_id.
    """
    # Subquery to find question IDs that the user has answered incorrectly at least once for the given exam_type
    incorrectly_answered_question_ids_sq = (
        db.query(UserAnswer.question_id)
        .join(Question, Question.id == UserAnswer.question_id)
        .filter(UserAnswer.user_id == user_id)
        .filter(UserAnswer.is_correct == False)
    )
    if exam_type_id is not None:
        incorrectly_answered_question_ids_sq = incorrectly_answered_question_ids_sq.filter(Question.exam_type_id == exam_type_id)
    
    # Must be a subquery to be used with notin_
    incorrectly_answered_question_ids_sq = incorrectly_answered_question_ids_sq.distinct().subquery()

    # Query for question IDs that the user has answered (implies at least one answer exists)
    # and are not in the subquery of incorrectly answered questions.
    always_correct_query = (
        db.query(UserAnswer.question_id)
        .join(Question, Question.id == UserAnswer.question_id)
        .filter(UserAnswer.user_id == user_id)
        # Ensure we only consider questions that the user has answered.
        # And that these questions are NOT in the set of questions they've answered incorrectly.
        .filter(UserAnswer.question_id.notin_(incorrectly_answered_question_ids_sq.select()))
    )
    if exam_type_id is not None:
        always_correct_query = always_correct_query.filter(Question.exam_type_id == exam_type_id)
    
    always_correct_questions = always_correct_query.distinct().all()
    
    return [q.question_id for q in always_correct_questions]

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import UserAnswer, Question

def get_user_summary_stats(db: Session, user_id: int) -> Dict[str, Any]:
    total_unique_questions_attempted = (
        db.query(func.count(func.distinct(UserAnswer.question_id)))
        .filter(UserAnswer.user_id == user_id)
        .scalar() or 0
    )

    total_answers_submitted_by_user = (
        db.query(func.count(UserAnswer.id))
        .filter(UserAnswer.user_id == user_id)
        .scalar() or 0
    )

    total_correct_answers_by_user = (
        db.query(func.count(UserAnswer.id))
        .filter(UserAnswer.user_id == user_id, UserAnswer.is_correct == True)
        .scalar() or 0
    )

    total_incorrect_answers_by_user = (
        db.query(func.count(UserAnswer.id))
        .filter(UserAnswer.user_id == user_id, UserAnswer.is_correct == False)
        .scalar() or 0
    )
    
    # total_questions_answered_by_user is the same as total_unique_questions_attempted in this context
    # as per the definitions provided.

    return {
        "total_unique_questions_attempted": total_unique_questions_attempted,
        "total_answers_submitted": total_answers_submitted_by_user, # Renamed for consistency with schema
        "total_correct_answers": total_correct_answers_by_user, # Renamed for consistency with schema
        "total_incorrect_answers": total_incorrect_answers_by_user, # Renamed for consistency with schema
    }


def get_user_question_performance(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Returns a list of objects, each representing a question the user attempted:
    - question_id
    - problem_statement
    - times_answered_by_user
    - times_correct_by_user
    - times_incorrect_by_user
    """
    # Subquery for total answers per question by user
    total_answers_sub = (
        db.query(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label("times_answered")
        )
        .filter(UserAnswer.user_id == user_id)
        .group_by(UserAnswer.question_id)
        .subquery()
    )

    # Subquery for total correct answers per question by user
    correct_answers_sub = (
        db.query(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label("times_correct")
        )
        .filter(UserAnswer.user_id == user_id, UserAnswer.is_correct == True)
        .group_by(UserAnswer.question_id)
        .subquery()
    )

    query_result = (
        db.query(
            Question.id.label("question_id"),
            Question.problem_statement,
            func.coalesce(total_answers_sub.c.times_answered, 0).label("times_answered"),
            func.coalesce(correct_answers_sub.c.times_correct, 0).label("times_correct")
        )
        .join(total_answers_sub, Question.id == total_answers_sub.c.question_id) # Inner join to only get questions user answered
        .outerjoin(correct_answers_sub, Question.id == correct_answers_sub.c.question_id)
        .order_by(Question.id)
        .all()
    )

    performance_list = []
    for row in query_result:
        times_incorrect = row.times_answered - row.times_correct
        performance_list.append({
            "question_id": row.question_id,
            "problem_statement": row.problem_statement,
            "times_answered": row.times_answered,
            "times_correct": row.times_correct,
            "times_incorrect": times_incorrect,
        })
    return performance_list

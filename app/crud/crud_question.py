from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.models import Question, UserAnswer # Added UserAnswer
from app.schemas import schemas # Assuming schemas are imported as app.schemas

def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()

def get_questions(db: Session, skip: int = 0, limit: int = 100) -> List[Question]:
    return db.query(Question).offset(skip).limit(limit).all()

def create_question(db: Session, question: schemas.QuestionCreate) -> Question:
    db_question = Question(
        problem_statement=question.problem_statement,
        option_1=question.option_1,
        option_2=question.option_2,
        option_3=question.option_3,
        option_4=question.option_4,
        correct_answer=question.correct_answer,
        explanation=question.explanation
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_unanswered_question_ids(db: Session, user_id: int) -> List[int]:
    """
    Returns a list of question IDs that the user has not answered.
    """
    answered_subquery = db.query(UserAnswer.question_id).filter(UserAnswer.user_id == user_id).distinct()
    unanswered_questions = db.query(Question.id).filter(~Question.id.in_(answered_subquery)).all()
    return [q.id for q in unanswered_questions]


def get_question_global_stats(db: Session) -> List[Dict[str, Any]]:
    """
    Calculates global statistics for each question.
    """
    total_answers_sub = (
        db.query(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label("total_answers")
        )
        .group_by(UserAnswer.question_id)
        .subquery()
    )

    total_correct_answers_sub = (
        db.query(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label("total_correct_answers")
        )
        .filter(UserAnswer.is_correct == True)
        .group_by(UserAnswer.question_id)
        .subquery()
    )

    # Select question IDs and their titles/text for context, join with stats
    query_result = (
        db.query(
            Question.id.label("question_id"),
            func.coalesce(total_answers_sub.c.total_answers, 0).label("total_answers"),
            func.coalesce(total_correct_answers_sub.c.total_correct_answers, 0).label("total_correct_answers")
        )
        .outerjoin(total_answers_sub, Question.id == total_answers_sub.c.question_id)
        .outerjoin(total_correct_answers_sub, Question.id == total_correct_answers_sub.c.question_id)
        .group_by(Question.id, total_answers_sub.c.total_answers, total_correct_answers_sub.c.total_correct_answers) # Group by all non-aggregated columns
        .all()
    )
    
    stats_list = []
    for row in query_result:
        total_answers = row.total_answers
        total_correct = row.total_correct_answers
        total_incorrect = total_answers - total_correct
        
        global_correct_rate = (total_correct / total_answers) if total_answers > 0 else 0
        global_incorrect_rate = (total_incorrect / total_answers) if total_answers > 0 else 0
        
        stats_list.append({
            "question_id": row.question_id,
            "total_answers": total_answers,
            "total_correct_answers": total_correct,
            "total_incorrect_answers": total_incorrect,
            "global_correct_rate": global_correct_rate,
            "global_incorrect_rate": global_incorrect_rate,
        })
        
    return stats_list


# Update and Delete functions can be added here if needed later
# def update_question(db: Session, question_id: int, question_update: schemas.QuestionUpdate) -> Optional[Question]:
#     db_question = get_question(db, question_id)
#     if db_question:
#         update_data = question_update.model_dump(exclude_unset=True)
#         for key, value in update_data.items():
#             setattr(db_question, key, value)
#         db.commit()
#         db.refresh(db_question)
#     return db_question

# def delete_question(db: Session, question_id: int) -> Optional[Question]:
#     db_question = get_question(db, question_id)
#     if db_question:
#         db.delete(db_question)
#         db.commit()
#     return db_question

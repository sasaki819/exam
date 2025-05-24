from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

from app.models.models import Question, UserAnswer
from app.schemas import schemas

def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()

def get_questions(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    exam_type_id: Optional[int] = None
) -> List[Question]:
    query = db.query(Question)
    if exam_type_id is not None:
        query = query.filter(Question.exam_type_id == exam_type_id)
    return query.offset(skip).limit(limit).all()

def create_question(db: Session, question: schemas.QuestionCreate) -> Question:
    db_question = Question(
        problem_statement=question.problem_statement,
        option_1=question.option_1,
        option_2=question.option_2,
        option_3=question.option_3,
        option_4=question.option_4,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        exam_type_id=question.exam_type_id # Added exam_type_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_unanswered_question_ids(
    db: Session, 
    user_id: int, 
    exam_type_id: Optional[int] = None
) -> List[int]:
    answered_subquery = db.query(UserAnswer.question_id).filter(UserAnswer.user_id == user_id).distinct()
    
    query = db.query(Question.id).filter(~Question.id.in_(answered_subquery))
    if exam_type_id is not None:
        query = query.filter(Question.exam_type_id == exam_type_id)
        
    unanswered_questions = query.all()
    return [q.id for q in unanswered_questions]

def get_question_global_stats(
    db: Session, 
    exam_type_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    # Base query for questions, filtered by exam_type_id if provided
    question_base_query = db.query(Question.id.label("question_id"))
    if exam_type_id is not None:
        question_base_query = question_base_query.filter(Question.exam_type_id == exam_type_id)
    
    # Alias for subqueries to make them distinct if used multiple times or for clarity
    questions_for_stats = question_base_query.subquery('questions_for_stats')

    # Subquery for total answers
    total_answers_sq = (
        db.query(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label("total_answers")
        )
        .join(questions_for_stats, UserAnswer.question_id == questions_for_stats.c.question_id) # Join to filter by exam_type
        .group_by(UserAnswer.question_id)
        .subquery('total_answers_sq')
    )

    # Subquery for total correct answers
    total_correct_answers_sq = (
        db.query(
            UserAnswer.question_id,
            func.count(UserAnswer.id).label("total_correct_answers")
        )
        .join(questions_for_stats, UserAnswer.question_id == questions_for_stats.c.question_id) # Join to filter by exam_type
        .filter(UserAnswer.is_correct == True)
        .group_by(UserAnswer.question_id)
        .subquery('total_correct_answers_sq')
    )

    # Main query joining questions with their stats
    query_result = (
        db.query(
            questions_for_stats.c.question_id,
            func.coalesce(total_answers_sq.c.total_answers, 0).label("total_answers"),
            func.coalesce(total_correct_answers_sq.c.total_correct_answers, 0).label("total_correct_answers")
        )
        .outerjoin(total_answers_sq, questions_for_stats.c.question_id == total_answers_sq.c.question_id)
        .outerjoin(total_correct_answers_sq, questions_for_stats.c.question_id == total_correct_answers_sq.c.question_id)
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

def update_question(db: Session, question_id: int, question_update: schemas.QuestionUpdate) -> Optional[Question]:
    db_question = get_question(db, question_id)
    if db_question:
        update_data = question_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_question, key, value)
        db.commit()
        db.refresh(db_question)
    return db_question

def delete_question(db: Session, question_id: int) -> Optional[Question]:
    db_question = get_question(db, question_id)
    if db_question:
        # Before deleting the question, consider related UserAnswers.
        # SQLAlchemy by default might try to NULL out question_id in user_answers if there's a relationship
        # and no specific cascade rule like "delete, orphan" on the UserAnswer side for its question FK.
        # For simplicity, we'll delete the question. If UserAnswers should also be deleted,
        # that would require a cascade rule on the Question.user_answers relationship
        # or manual deletion of UserAnswers here.
        # Current model: UserAnswer has a non-nullable question_id. Deleting a Question
        # without handling UserAnswers will cause an IntegrityError if UserAnswers exist for this question.
        # So, we must delete associated UserAnswers first.

        db.query(UserAnswer).filter(UserAnswer.question_id == question_id).delete(synchronize_session=False)
        
        db.delete(db_question)
        db.commit()
    return db_question # Returns the deleted question object (now detached from session) or None

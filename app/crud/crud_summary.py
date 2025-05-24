from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case # Ensure 'and_' and 'case' are imported
from typing import List, Dict, Any, Optional # Ensure Optional is imported

from app.models.models import UserAnswer, Question # Ensure Question is imported
from app.schemas import schemas # Assuming schemas are imported

def get_user_summary_stats(db: Session, user_id: int, exam_type_id: Optional[int] = None) -> schemas.UserSummaryStats:
    # Base query for UserAnswers by the user
    user_answers_query = db.query(UserAnswer).filter(UserAnswer.user_id == user_id)

    if exam_type_id is not None:
        user_answers_query = user_answers_query.join(Question, Question.id == UserAnswer.question_id)\
                                              .filter(Question.exam_type_id == exam_type_id)

    total_answers_submitted = user_answers_query.count()
    
    correct_answers_query = user_answers_query.filter(UserAnswer.is_correct == True)
    total_correct_answers = correct_answers_query.count()
    
    total_incorrect_answers = total_answers_submitted - total_correct_answers

    # For total_unique_questions_attempted, we need to count distinct question_ids from the filtered answers
    # unique_questions_query = user_answers_query.distinct(UserAnswer.question_id) # This was the previous approach
    # total_unique_questions_attempted = unique_questions_query.count() 
                                                                 
    # Correct way to count distinct question_ids from the filtered set of answers
    if exam_type_id is not None:
         count_unique_q = db.query(func.count(func.distinct(UserAnswer.question_id)))\
                            .join(Question, Question.id == UserAnswer.question_id)\
                            .filter(UserAnswer.user_id == user_id, Question.exam_type_id == exam_type_id)\
                            .scalar_one_or_none() or 0
    else:
         count_unique_q = db.query(func.count(func.distinct(UserAnswer.question_id)))\
                            .filter(UserAnswer.user_id == user_id)\
                            .scalar_one_or_none() or 0
    total_unique_questions_attempted = count_unique_q


    correct_answer_rate = (total_correct_answers / total_answers_submitted) if total_answers_submitted > 0 else 0

    return schemas.UserSummaryStats(
        total_unique_questions_attempted=total_unique_questions_attempted,
        total_answers_submitted=total_answers_submitted,
        total_correct_answers=total_correct_answers,
        total_incorrect_answers=total_incorrect_answers,
        correct_answer_rate=correct_answer_rate
    )

def get_user_question_performance_summary(db: Session, user_id: int, exam_type_id: Optional[int] = None) -> List[schemas.UserQuestionPerformance]:
    # Base query for UserAnswers by the user, joined with Question
    base_query = db.query(
            UserAnswer.question_id,
            Question.problem_statement, # Get problem_statement from Question model
            func.count(UserAnswer.id).label("times_answered"),
            func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label("times_correct"),
            func.sum(case((UserAnswer.is_correct == False, 1), else_=0)).label("times_incorrect")
        ).join(Question, Question.id == UserAnswer.question_id)\
         .filter(UserAnswer.user_id == user_id)

    if exam_type_id is not None:
        base_query = base_query.filter(Question.exam_type_id == exam_type_id)
    
    summary_data = base_query.group_by(UserAnswer.question_id, Question.problem_statement).all() # Group by problem_statement too

    performance_list = []
    for item in summary_data:
        performance_list.append(schemas.UserQuestionPerformance(
            question_id=item.question_id,
            problem_statement=item.problem_statement,
            times_answered=item.times_answered,
            times_correct=item.times_correct,
            times_incorrect=item.times_incorrect
        ))
    return performance_list

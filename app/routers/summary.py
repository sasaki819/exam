from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas # Assuming these are importable from app package
from app.db.database import get_db
from app.routers.auth import get_current_user # Import dependency

router = APIRouter()

@router.get("/", response_model=schemas.UserDetailedSummary) # Using UserDetailedSummary
def get_user_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch raw summary stats
    raw_stats = crud.crud_summary.get_user_summary_stats(db, user_id=current_user.id)
    
    # Calculate correct answer rate
    if raw_stats["total_answers_submitted"] > 0:
        correct_rate = raw_stats["total_correct_answers"] / raw_stats["total_answers_submitted"]
    else:
        correct_rate = 0.0

    # Create UserSummaryStats Pydantic model
    summary_stats_model = schemas.UserSummaryStats(
        total_unique_questions_attempted=raw_stats["total_unique_questions_attempted"],
        total_answers_submitted=raw_stats["total_answers_submitted"],
        total_correct_answers=raw_stats["total_correct_answers"],
        total_incorrect_answers=raw_stats["total_incorrect_answers"],
        correct_answer_rate=correct_rate
    )

    # Fetch question performance details
    question_performance_data = crud.crud_summary.get_user_question_performance(db, user_id=current_user.id)
    
    # Convert list of dicts to list of UserQuestionPerformance Pydantic models
    question_performance_models = [
        schemas.UserQuestionPerformance(**item) for item in question_performance_data
    ]

    # Combine into UserDetailedSummary
    return schemas.UserDetailedSummary(
        summary_stats=summary_stats_model,
        question_performance=question_performance_models
    )

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional # Ensure Optional is imported

from app import crud, models, schemas # Assuming these are importable
from app.db.database import get_db
from app.routers.auth import get_current_user # For authentication

router = APIRouter()

@router.get("/", response_model=schemas.UserDetailedSummary)
def get_user_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    exam_type_id: Optional[int] = None # Added optional query parameter
):
    # Optional: Validate exam_type_id if provided
    if exam_type_id is not None:
        exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
        if not exam_type:
            raise HTTPException(status_code=404, detail=f"ExamType with id {exam_type_id} not found.")

    summary_stats = crud.crud_summary.get_user_summary_stats(db, user_id=current_user.id, exam_type_id=exam_type_id)
    question_performance = crud.crud_summary.get_user_question_performance_summary(db, user_id=current_user.id, exam_type_id=exam_type_id)
    
    return schemas.UserDetailedSummary(
        summary_stats=summary_stats,
        question_performance=question_performance
    )

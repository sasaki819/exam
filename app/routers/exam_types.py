from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas # Ensure these are importable
from app.db.database import get_db
from app.routers.auth import get_current_user # For authentication

router = APIRouter(
    prefix="/exam-types",
    tags=["Exam Types"], # Adds a tag in OpenAPI docs
    dependencies=[Depends(get_current_user)] # Secure all endpoints in this router
)

@router.post("/", response_model=schemas.ExamType, status_code=status.HTTP_201_CREATED)
def create_exam_type_endpoint(
    exam_type: schemas.ExamTypeCreate,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user) # Already in router dependencies
):
    db_exam_type = crud.crud_exam_type.get_exam_type_by_name(db, name=exam_type.name)
    if db_exam_type:
        raise HTTPException(status_code=400, detail="Exam type with this name already exists")
    return crud.crud_exam_type.create_exam_type(db=db, exam_type=exam_type)

@router.get("/", response_model=List[schemas.ExamType])
def read_exam_types_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user)
):
    exam_types = crud.crud_exam_type.get_exam_types(db, skip=skip, limit=limit)
    return exam_types

@router.get("/{exam_type_id}", response_model=schemas.ExamType)
def read_exam_type_endpoint(
    exam_type_id: int,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user)
):
    db_exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
    if db_exam_type is None:
        raise HTTPException(status_code=404, detail="Exam type not found")
    return db_exam_type

@router.put("/{exam_type_id}", response_model=schemas.ExamType)
def update_exam_type_endpoint(
    exam_type_id: int,
    exam_type_update: schemas.ExamTypeUpdate,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user)
):
    db_exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
    if db_exam_type is None:
        raise HTTPException(status_code=404, detail="Exam type not found")
    
    # If name is being updated, check if the new name already exists for another exam type
    if exam_type_update.name is not None and exam_type_update.name != db_exam_type.name:
        existing_exam_type_with_new_name = crud.crud_exam_type.get_exam_type_by_name(db, name=exam_type_update.name)
        if existing_exam_type_with_new_name and existing_exam_type_with_new_name.id != exam_type_id:
            raise HTTPException(status_code=400, detail="Another exam type with this name already exists")

    updated_exam_type = crud.crud_exam_type.update_exam_type(db=db, exam_type_id=exam_type_id, exam_type_update=exam_type_update)
    return updated_exam_type

@router.delete("/{exam_type_id}", response_model=schemas.ExamType)
def delete_exam_type_endpoint(
    exam_type_id: int,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user)
):
    db_exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
    if db_exam_type is None:
        raise HTTPException(status_code=404, detail="Exam type not found")
    
    # Note: The foreign key constraint `ondelete='SET NULL'` for `questions.exam_type_id`
    # means that deleting an exam type will set `exam_type_id` to NULL for associated questions.
    # If this is not desired (e.g., prevent deletion if questions are associated),
    # add a check here:
    # if db_exam_type.questions: # Accessing the relationship
    #     raise HTTPException(status_code=400, detail="Cannot delete exam type with associated questions. Reassign questions first.")

    deleted_exam_type = crud.crud_exam_type.delete_exam_type(db=db, exam_type_id=exam_type_id)
    return deleted_exam_type

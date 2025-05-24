from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import ExamType
from app.schemas import schemas # Ensure schemas is accessible like this

def get_exam_type(db: Session, exam_type_id: int) -> Optional[ExamType]:
    return db.query(ExamType).filter(ExamType.id == exam_type_id).first()

def get_exam_type_by_name(db: Session, name: str) -> Optional[ExamType]:
    return db.query(ExamType).filter(ExamType.name == name).first()

def get_exam_types(db: Session, skip: int = 0, limit: int = 100) -> List[ExamType]:
    return db.query(ExamType).offset(skip).limit(limit).all()

def create_exam_type(db: Session, exam_type: schemas.ExamTypeCreate) -> ExamType:
    db_exam_type = ExamType(name=exam_type.name)
    db.add(db_exam_type)
    db.commit()
    db.refresh(db_exam_type)
    return db_exam_type

def update_exam_type(db: Session, exam_type_id: int, exam_type_update: schemas.ExamTypeUpdate) -> Optional[ExamType]:
    db_exam_type = get_exam_type(db, exam_type_id)
    if db_exam_type:
        update_data = exam_type_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_exam_type, key, value)
        db.commit()
        db.refresh(db_exam_type)
    return db_exam_type

def delete_exam_type(db: Session, exam_type_id: int) -> Optional[ExamType]:
    db_exam_type = get_exam_type(db, exam_type_id)
    if db_exam_type:
        # Consider implications: what happens to questions linked to this exam type?
        # The FK constraint in Question model is ON DELETE SET NULL for exam_type_id.
        # This means if an ExamType is deleted, questions associated with it will have their exam_type_id set to NULL.
        # This is acceptable given the current model setup.
        db.delete(db_exam_type)
        db.commit()
    return db_exam_type

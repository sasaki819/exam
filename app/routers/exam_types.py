from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, File, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session
import json

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


@router.get("/{exam_type_id}/export-questions/", response_model=schemas.QuestionsExport)
def export_questions_for_exam_type(
    exam_type_id: int,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user) # Router dependency
):
    # Verify Exam Type
    db_exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
    if db_exam_type is None:
        raise HTTPException(status_code=404, detail="ExamType not found")

    # Fetch Questions
    # Using a large limit to fetch all questions for the exam type.
    # Consider modifying crud.crud_question.get_questions to accept limit=None or limit=-1 for all.
    db_questions = crud.crud_question.get_questions(db, exam_type_id=exam_type_id, limit=10000)

    # Prepare Data for Export
    questions_export_schema_list: List[schemas.QuestionExportItem] = []
    for q_model in db_questions:
        questions_export_schema_list.append(
            schemas.QuestionExportItem(
                problem_statement=q_model.problem_statement,
                option_1=q_model.option_1,
                option_2=q_model.option_2,
                option_3=q_model.option_3,
                option_4=q_model.option_4,
                correct_answer=q_model.correct_answer,
                explanation=q_model.explanation
            )
        )

    # Return JSON File
    filename = f"exam_type_{db_exam_type.name.replace(' ', '_')}_{exam_type_id}_questions.json"
    
    # Convert Pydantic models to a list of dictionaries for JSON serialization
    questions_to_export_dict = [q.model_dump() for q in questions_export_schema_list]
    
    json_content = json.dumps(questions_to_export_dict, indent=4)
    
    response_headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"" # Ensure filename is quoted
    }
    return Response(content=json_content, media_type="application/json", headers=response_headers)


@router.post("/{exam_type_id}/import-questions/", response_model=schemas.ImportSummary)
async def import_questions_for_exam_type(
    exam_type_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user) # Router dependency
) -> schemas.ImportSummary:
    
    db_exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
    if db_exam_type is None:
        raise HTTPException(status_code=404, detail="ExamType not found")

    imported_count = 0
    failed_count = 0
    errors_list: List[schemas.ImportErrorDetail] = []

    contents = await file.read()
    await file.close()

    try:
        # Ensure UTF-8 decoding, as specified in the problem description
        parsed_data = json.loads(contents.decode('utf-8')) 
    except json.JSONDecodeError as e:
        errors_list.append(schemas.ImportErrorDetail(error_message=f"Invalid JSON file: {str(e)}"))
        return schemas.ImportSummary(imported_count=0, failed_count=0, errors=errors_list) # No items to count as failed if JSON is invalid

    if not isinstance(parsed_data, list):
        errors_list.append(schemas.ImportErrorDetail(error_message="JSON content is not a list of questions."))
        # In this case, failed_count could be len(parsed_data) if we knew it, but it's not a list.
        # Or it could be 1, representing the whole file. Let's say 0 imported, 0 failed (items), and 1 file-level error.
        return schemas.ImportSummary(imported_count=0, failed_count=0, errors=errors_list)


    for index, item_data in enumerate(parsed_data):
        try:
            # Validate against QuestionExportItem first (structure of exported file)
            # This ensures all fields expected from export are present.
            question_export_item = schemas.QuestionExportItem(**item_data)

            # Prepare data for QuestionCreate schema
            # (QuestionExportItem does not have exam_type_id, QuestionCreate requires it)
            question_create_data = question_export_item.model_dump()
            question_create_data['exam_type_id'] = exam_type_id
            
            question_to_create_schema = schemas.QuestionCreate(**question_create_data)
            
            # Create question in DB
            crud.crud_question.create_question(db=db, question=question_to_create_schema)
            imported_count += 1

        except ValidationError as e:
            failed_count += 1
            # Pydantic's e.errors() gives a list of error dicts, json.dumps can make it readable
            error_messages = json.dumps(e.errors()) 
            errors_list.append(schemas.ImportErrorDetail(
                row_index=index, 
                error_message=f"Validation Error: {error_messages}", 
                data=item_data
            ))
        except Exception as e:
            failed_count += 1
            errors_list.append(schemas.ImportErrorDetail(
                row_index=index, 
                error_message=f"An unexpected error occurred: {str(e)}", 
                data=item_data
            ))

    return schemas.ImportSummary(
        imported_count=imported_count,
        failed_count=failed_count,
        errors=errors_list
    )

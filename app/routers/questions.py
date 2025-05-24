from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import random

from app import crud, models, schemas
from app.db.database import get_db
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.Question, status_code=status.HTTP_201_CREATED)
def create_new_question(
    question: schemas.QuestionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=question.exam_type_id)
    if not exam_type:
        raise HTTPException(status_code=404, detail=f"ExamType with id {question.exam_type_id} not found.")
    return crud.crud_question.create_question(db=db, question=question)

@router.get("/next/", response_model=schemas.Question)
def get_next_question(
    exam_type_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    selected_question_id: Optional[int] = None

    exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=exam_type_id)
    if not exam_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ExamType with id {exam_type_id} not found.")

    unanswered_ids = crud.crud_question.get_unanswered_question_ids(db, user_id=current_user.id, exam_type_id=exam_type_id)
    if unanswered_ids:
        selected_question_id = random.choice(unanswered_ids)
    
    if not selected_question_id:
        global_stats = crud.crud_question.get_question_global_stats(db, exam_type_id=exam_type_id)
        if not global_stats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No questions available for exam type {exam_type_id}.")

        always_correct_ids = crud.crud_user_answer.get_questions_always_answered_correctly_by_user(
            db, user_id=current_user.id, exam_type_id=exam_type_id
        )
        
        eligible_for_incorrect_rate_prioritization = [
            stat for stat in global_stats if stat["question_id"] not in always_correct_ids
        ]
        
        if eligible_for_incorrect_rate_prioritization:
            eligible_for_incorrect_rate_prioritization.sort(key=lambda x: x["global_incorrect_rate"], reverse=True)
            if eligible_for_incorrect_rate_prioritization[0]["global_incorrect_rate"] > 0:
                selected_question_id = eligible_for_incorrect_rate_prioritization[0]["question_id"]
            else: 
                selected_question_id = random.choice(eligible_for_incorrect_rate_prioritization)["question_id"]
        elif global_stats: # All questions in this exam type are either in always_correct_ids or have no incorrect stats yet
            # Fallback: pick any from global_stats (could be one they always got right, for review)
            selected_question_id = random.choice(global_stats)["question_id"]

    if not selected_question_id: # If still no question selected
        all_questions_in_exam = crud.crud_question.get_questions(db, exam_type_id=exam_type_id, limit=1)
        if all_questions_in_exam:
            selected_question_id = all_questions_in_exam[0].id
        else: 
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No questions found for exam type {exam_type_id} for review.")

    if not selected_question_id: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not determine next question for exam type {exam_type_id}. Please check question availability and user history.")

    question_model = crud.crud_question.get_question(db, question_id=selected_question_id)
    if not question_model: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Selected question not found unexpectedly.")
    
    return question_model

@router.post("/{question_id}/answer/", response_model=schemas.AnswerResult)
def submit_answer(
    question_id: int,
    answer_submission: schemas.UserAnswerSubmit,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    question = crud.crud_question.get_question(db, question_id=question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    user_answer_create_data = schemas.UserAnswerCreate(
        question_id=question_id,
        selected_answer=answer_submission.selected_answer
    )
    
    created_answer = crud.crud_user_answer.create_user_answer(
        db=db,
        user_answer=user_answer_create_data,
        user_id=current_user.id
    )

    return schemas.AnswerResult(
        question_id=question.id,
        submitted_answer=answer_submission.selected_answer,
        is_correct=created_answer.is_correct,
        correct_answer_option=question.correct_answer,
        explanation=question.explanation
    )

@router.get("/{question_id}/", response_model=schemas.Question)
def read_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_question = crud.crud_question.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question

@router.get("/", response_model=List[schemas.Question])
def read_questions(
    skip: int = 0,
    limit: int = 100,
    exam_type_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    questions = crud.crud_question.get_questions(db, skip=skip, limit=limit, exam_type_id=exam_type_id)
    return questions

@router.put("/{question_id}", response_model=schemas.Question)
def update_single_question(
    question_id: int,
    question_update: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Assuming admin/creator rights
):
    db_question = crud.crud_question.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    # If exam_type_id is being updated, verify the new exam_type_id exists
    if question_update.exam_type_id is not None:
        exam_type = crud.crud_exam_type.get_exam_type(db, exam_type_id=question_update.exam_type_id)
        if not exam_type:
            raise HTTPException(status_code=404, detail=f"ExamType with id {question_update.exam_type_id} not found.")

    updated_question = crud.crud_question.update_question(db=db, question_id=question_id, question_update=question_update)
    return updated_question

@router.delete("/{question_id}", response_model=schemas.Question) # Or return a status code like 204 No Content
def delete_single_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Assuming admin/creator rights
):
    db_question = crud.crud_question.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # The CRUD function now handles deleting associated UserAnswers.
    deleted_question = crud.crud_question.delete_question(db=db, question_id=question_id)
    if deleted_question is None: # Should not happen if get_question found it, but as a safeguard
         raise HTTPException(status_code=500, detail="Error deleting question")
    return deleted_question # Returns the deleted item as per response_model

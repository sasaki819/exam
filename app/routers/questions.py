from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import random # For placeholder logic in /next/

from app import crud, models, schemas # Assuming these are importable from app package
from app.db.database import get_db
from app.routers.auth import get_current_user # Import dependency

router = APIRouter()

@router.post("/", response_model=schemas.Question)
def create_new_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Any authenticated user can create
):
    # In a real app, you might add role-based access control here
    return crud.crud_question.create_question(db=db, question=question)

@router.get("/next/", response_model=schemas.Question)
def get_next_question(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    selected_question_id: Optional[int] = None

    # Step 1: Unanswered by User
    unanswered_ids = crud.crud_question.get_unanswered_question_ids(db, user_id=current_user.id)
    if unanswered_ids:
        selected_question_id = random.choice(unanswered_ids)
    
    # Step 2: Highest Global Incorrect Rate (among those not perfectly answered by user)
    if not selected_question_id:
        global_stats = crud.crud_question.get_question_global_stats(db)
        if not global_stats: # No questions in DB at all
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions available in the database.")

        always_correct_ids = crud.crud_user_answer.get_questions_always_answered_correctly_by_user(db, user_id=current_user.id)
        
        # Filter out questions the user always answers correctly
        eligible_for_incorrect_rate_prioritization = [
            stat for stat in global_stats if stat["question_id"] not in always_correct_ids
        ]
        
        if eligible_for_incorrect_rate_prioritization:
            # Sort by global_incorrect_rate (descending)
            eligible_for_incorrect_rate_prioritization.sort(key=lambda x: x["global_incorrect_rate"], reverse=True)
            if eligible_for_incorrect_rate_prioritization[0]["global_incorrect_rate"] > 0: # Prioritize if there's actually an incorrect rate
                selected_question_id = eligible_for_incorrect_rate_prioritization[0]["question_id"]
            else: # If top incorrect rates are all 0, means all remaining are either not answered or always correct globally
                # Fall through to step 3 effectively, or pick randomly from this list if it has items
                # For now, let's pick randomly from this list if it's not empty.
                # This covers cases where questions have answers, but all are correct globally (incorrect_rate = 0)
                # and user hasn't answered them or not always correctly.
                if eligible_for_incorrect_rate_prioritization: # Check again if list is not empty
                     selected_question_id = random.choice(eligible_for_incorrect_rate_prioritization)["question_id"]


    # Step 3: Highest Global Correct Rate (Fallback) or if all answered correctly by user
    if not selected_question_id:
        global_stats = crud.crud_question.get_question_global_stats(db) # Re-fetch or use from above if available
        if not global_stats: # Should have been caught earlier, but as a safeguard
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions available in the database.")

        # At this point, the user has likely answered all questions, or always answered them correctly.
        # Or, questions eligible for incorrect rate prioritization all had 0 incorrect rate.
        # We can offer questions they always got right (for review) or any question if global_stats was empty before.
        # Sort by global_correct_rate (descending) as a general review mechanism.
        global_stats.sort(key=lambda x: x["global_correct_rate"], reverse=True)
        if global_stats: # Ensure list is not empty
            selected_question_id = global_stats[0]["question_id"]

    if not selected_question_id:
        # This case should ideally be covered if global_stats is never empty and has questions.
        # If DB has questions but logic somehow didn't pick one (e.g., all lists ended up empty).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not determine next question based on prioritization.")

    # Fetch and return the selected question
    question_model = crud.crud_question.get_question(db, question_id=selected_question_id)
    if not question_model:
        # This would be unusual if IDs are coming from the DB itself
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Selected question not found.")
    
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

    # Check if user has already answered this specific question (optional, depends on app logic)
    # existing_answer = crud.crud_user_answer.get_specific_user_answer(db, question_id=question_id, user_id=current_user.id)
    # if existing_answer:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already answered this question.")

    is_correct = (question.correct_answer == answer_submission.selected_answer)

    user_answer_create_data = schemas.UserAnswerCreate(
        question_id=question_id,
        selected_answer=answer_submission.selected_answer
        # is_correct will be set by crud_user_answer.create_user_answer based on question.correct_answer
    )
    
    # The crud_user_answer.create_user_answer function will determine 'is_correct'
    # by comparing against the stored Question.correct_answer.
    # So, the 'is_correct' field in UserAnswerCreate is not strictly needed if determined by CRUD.
    # However, our current crud_user_answer.create_user_answer expects it.
    # Let's ensure crud_user_answer.create_user_answer correctly sets is_correct.
    # The current crud_user_answer.create_user_answer already does this.

    created_answer = crud.crud_user_answer.create_user_answer(
        db=db,
        user_answer=user_answer_create_data, # Pass the UserAnswerCreate object
        user_id=current_user.id
    )

    return schemas.AnswerResult(
        question_id=question.id,
        submitted_answer=answer_submission.selected_answer,
        is_correct=created_answer.is_correct, # Use the value from the created UserAnswer
        correct_answer_option=question.correct_answer,
        explanation=question.explanation
    )

@router.get("/{question_id}/", response_model=schemas.Question)
def read_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Ensure user is authenticated
):
    db_question = crud.crud_question.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question

@router.get("/", response_model=List[schemas.Question])
def read_questions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Ensure user is authenticated
):
    questions = crud.crud_question.get_questions(db, skip=skip, limit=limit)
    return questions

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List # Added List

# Schemas for Question
class QuestionBase(BaseModel):
    problem_statement: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    correct_answer: int
    explanation: Optional[str] = None

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int

    class Config:
        orm_mode = True


# Schemas for Summary Statistics
class UserSummaryStats(BaseModel):
    total_unique_questions_attempted: int
    total_answers_submitted: int
    total_correct_answers: int
    total_incorrect_answers: int
    correct_answer_rate: float # Calculated: total_correct_answers / total_answers_submitted

class UserQuestionPerformance(BaseModel):
    question_id: int
    problem_statement: str
    times_answered: int
    times_correct: int
    times_incorrect: int

class UserDetailedSummary(BaseModel):
    summary_stats: UserSummaryStats
    question_performance: List[UserQuestionPerformance]


# Schema for submitting an answer
class UserAnswerSubmit(BaseModel):
    selected_answer: int

# Schema for the result after submitting an answer
class AnswerResult(BaseModel):
    question_id: int
    submitted_answer: int
    is_correct: bool
    correct_answer_option: int # The correct option number (e.g., 1, 2, 3, 4)
    explanation: Optional[str] = None


# Schemas for User
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True


# Schemas for Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# Schemas for UserAnswer
class UserAnswerBase(BaseModel):
    question_id: int
    selected_answer: int
    # user_id will be set by the system using the current authenticated user

class UserAnswerCreate(UserAnswerBase):
    pass # No change here, user_id is not part of creation schema from user input

class UserAnswer(UserAnswerBase):
    id: int
    user_id: int # Added user_id
    is_correct: bool
    answered_at: datetime

    class Config:
        orm_mode = True

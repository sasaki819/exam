from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session
from app.crud import crud_user
from app.schemas import schemas
from app.models import models # For type hinting

def test_create_user(db_session: SQLAlchemySession):
    user_in = schemas.UserCreate(
        username="test_crud_user",
        email="test_crud_user@example.com",
        password="crud_password"
    )
    created_user = crud_user.create_user(db=db_session, user=user_in)
    
    assert created_user is not None
    assert created_user.username == user_in.username
    assert created_user.email == user_in.email
    assert hasattr(created_user, "hashed_password")
    assert created_user.hashed_password is not None
    
    # Verify it's in the DB
    db_user = db_session.query(models.User).filter(models.User.id == created_user.id).first()
    assert db_user is not None
    assert db_user.username == user_in.username

def test_get_user_by_username(db_session: SQLAlchemySession):
    user_in = schemas.UserCreate(
        username="get_user_test",
        email="get_user_test@example.com",
        password="get_password"
    )
    crud_user.create_user(db=db_session, user=user_in) # Create the user first
    
    fetched_user = crud_user.get_user_by_username(db=db_session, username=user_in.username)
    assert fetched_user is not None
    assert fetched_user.username == user_in.username
    assert fetched_user.email == user_in.email

def test_get_user_by_username_nonexistent(db_session: SQLAlchemySession):
    fetched_user = crud_user.get_user_by_username(db=db_session, username="nonexistentuser")
    assert fetched_user is None

def test_get_user_by_email(db_session: SQLAlchemySession):
    user_in = schemas.UserCreate(
        username="get_email_test_user",
        email="get_email_test@example.com",
        password="get_password_email"
    )
    crud_user.create_user(db=db_session, user=user_in)
    
    fetched_user = crud_user.get_user_by_email(db=db_session, email=user_in.email)
    assert fetched_user is not None
    assert fetched_user.username == user_in.username
    assert fetched_user.email == user_in.email

def test_get_user_by_email_nonexistent(db_session: SQLAlchemySession):
    fetched_user = crud_user.get_user_by_email(db=db_session, email="nonexistent_email@example.com")
    assert fetched_user is None

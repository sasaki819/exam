import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict
from sqlalchemy.pool import StaticPool # For SQLite in-memory
import os

# Import your FastAPI app and Base from your models
from app.main import app
from app.db.database import Base, get_db # Assuming get_db is in app.db.database
from app.models import models # Ensure all models are imported for Base.metadata
from app.schemas import schemas # For creating test data
from app.core.security import get_password_hash # For creating test users

# Use SQLite in-memory for testing
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    poolclass=StaticPool, # Use StaticPool for SQLite in-memory
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the override to the app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function") # Changed to function scope for better isolation
def db_session() -> SQLAlchemySession: # Yields a SQLAlchemy session
    Base.metadata.drop_all(bind=engine) # Drop all tables
    Base.metadata.create_all(bind=engine) # Create all tables
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function") # Changed to function scope to ensure clean app state
def client(db_session: SQLAlchemySession) -> TestClient: # Depends on db_session to ensure tables are set up
    # The db_session fixture already handles table creation/dropping.
    # No need to do it here again.
    # The dependency override for get_db is already applied globally.
    
    # If you need to seed data for all tests using this client, do it here using db_session.
    # For example, creating a common test user:
    # user_in = schemas.UserCreate(username="commontestuser", password="testpassword")
    # hashed_password = get_password_hash(user_in.password)
    # db_user = models.User(username=user_in.username, hashed_password=hashed_password)
    # db_session.add(db_user)
    # db_session.commit()
    
    yield TestClient(app)
    # Cleanup (if any specific to client beyond db_session) can go here.


@pytest.fixture(scope="function")
def test_user(db_session: SQLAlchemySession) -> models.User:
    """
    Fixture to create a test user in the database for authentication tests.
    Returns the created User model instance.
    """
    user_data = schemas.UserCreate(
        username="authtestuser", 
        email="authtest@example.com", 
        password="testpassword"
    )
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    return db_user


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, test_user: models.User) -> TestClient:
    """
    Fixture to provide an authenticated TestClient.
    It logs in the test_user and sets the authorization header on the client.
    """
    login_data = {
        "username": test_user.username,
        "password": "testpassword" # The raw password used in the test_user fixture
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200 # Ensure login is successful
    token = response.json()["access_token"]
    
    client.headers = {
        **client.headers, # Preserve other headers if any
        "Authorization": f"Bearer {token}"
    }
    return client


@pytest.fixture(scope="function")
def test_exam_type(db_session: SQLAlchemySession) -> models.ExamType:
    """
    Fixture to create a test exam type in the database.
    Returns the created ExamType model instance.
    """
    exam_type_data = schemas.ExamTypeCreate(name="Default Test Exam Type")
    db_exam_type = models.ExamType(name=exam_type_data.name)
    db_session.add(db_exam_type)
    db_session.commit()
    db_session.refresh(db_exam_type)
    return db_exam_type

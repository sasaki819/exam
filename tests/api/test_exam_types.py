from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Use the renamed Session from conftest
from fastapi import status
from typing import List # For response type hint

from app.schemas import schemas # For request/response validation
from app.models import models # For DB verification
from app.crud import crud_exam_type # For potential direct DB manipulation for setup/cleanup if needed

# Test data
sample_exam_type_data_1 = {"name": "API Test Exam Type Alpha"}
sample_exam_type_data_2 = {"name": "API Test Exam Type Beta"}
sample_exam_type_data_3 = {"name": "API Test Exam Type Gamma"}


def test_create_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession):
    response = authenticated_client.post("/exam-types/", json=sample_exam_type_data_1)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_exam_type_data_1["name"]
    assert "id" in data
    
    # Verify in DB
    exam_type_id = data["id"]
    db_exam_type = db_session.query(models.ExamType).filter(models.ExamType.id == exam_type_id).first()
    assert db_exam_type is not None
    assert db_exam_type.name == sample_exam_type_data_1["name"]
    
    # db_session fixture in conftest handles cleanup (drops and recreates tables)

def test_create_exam_type_duplicate_name(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # Create the first exam type
    initial_response = authenticated_client.post("/exam-types/", json=sample_exam_type_data_2)
    assert initial_response.status_code == status.HTTP_201_CREATED
    
    # Attempt to create another with the same name
    duplicate_response = authenticated_client.post("/exam-types/", json=sample_exam_type_data_2)
    assert duplicate_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in duplicate_response.json()["detail"]

def test_read_exam_types(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # Create a couple of exam types
    crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Read Test ET 1"))
    crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Read Test ET 2"))
    
    response = authenticated_client.get("/exam-types/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Check if the created exam types are in the list (names could vary due to other tests if not isolated,
    # but db_session fixture ensures isolation)
    assert len(data) >= 2 
    assert any(et["name"] == "Read Test ET 1" for et in data)
    assert any(et["name"] == "Read Test ET 2" for et in data)

def test_read_exam_type_by_id(authenticated_client: TestClient, db_session: SQLAlchemySession):
    created_et = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Read Test ET By ID"))
    
    response = authenticated_client.get(f"/exam-types/{created_et.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == created_et.id
    assert data["name"] == created_et.name

def test_read_non_existent_exam_type(authenticated_client: TestClient):
    response = authenticated_client.get("/exam-types/99999") # Non-existent ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Exam type not found"

def test_update_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession):
    created_et = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Update Test ET Original"))
    update_payload = {"name": "Update Test ET Updated Name"}
    
    response = authenticated_client.put(f"/exam-types/{created_et.id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == created_et.id
    assert data["name"] == update_payload["name"]
    
    # Verify in DB
    db_session.refresh(created_et) # Refresh the instance from the DB
    assert created_et.name == update_payload["name"]

def test_update_non_existent_exam_type(authenticated_client: TestClient):
    update_payload = {"name": "Update Non Existent ET"}
    response = authenticated_client.put("/exam-types/99999", json=update_payload) # Non-existent ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Exam type not found"

def test_update_exam_type_to_duplicate_name(authenticated_client: TestClient, db_session: SQLAlchemySession):
    et1 = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Duplicate Update ET Name1"))
    et2 = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Duplicate Update ET Name2"))
    
    update_payload = {"name": et1.name} # Attempt to update et2's name to et1's name
    
    response = authenticated_client.put(f"/exam-types/{et2.id}", json=update_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]

def test_delete_exam_type(authenticated_client: TestClient, db_session: SQLAlchemySession):
    created_et = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Delete Test ET"))
    
    response = authenticated_client.delete(f"/exam-types/{created_et.id}")
    assert response.status_code == status.HTTP_200_OK # Assuming 200 OK is returned
    data = response.json()
    assert data["id"] == created_et.id
    assert data["name"] == created_et.name
    
    # Verify in DB
    db_exam_type_after_delete = db_session.query(models.ExamType).filter(models.ExamType.id == created_et.id).first()
    assert db_exam_type_after_delete is None

    # Verify associated questions have their exam_type_id set to NULL (if any were created and linked)
    # Create a question linked to this exam type
    q_data = {
        "problem_statement": "Test Q for Deleted ET", "option_1": "1", "option_2": "2",
        "option_3": "3", "option_4": "4", "correct_answer": 1, "exam_type_id": created_et.id
    }
    # Need to recreate the ET to link a question, as the previous one is now only in memory (deleted from DB)
    # For this specific test, let's create a new ET, link a question, then delete that ET.
    et_for_cascade_test = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Cascade Delete Test ET"))
    
    from app.crud import crud_question # Local import to avoid circular dependency issues at top level if any
    question_linked = crud_question.create_question(db_session, schemas.QuestionCreate(**q_data, exam_type_id=et_for_cascade_test.id))
    assert question_linked.exam_type_id == et_for_cascade_test.id

    # Delete the new exam type
    authenticated_client.delete(f"/exam-types/{et_for_cascade_test.id}")
    
    # Verify the question's exam_type_id is now None
    db_session.refresh(question_linked) # Refresh from DB
    assert question_linked.exam_type_id is None


def test_delete_non_existent_exam_type(authenticated_client: TestClient):
    response = authenticated_client.delete("/exam-types/99999") # Non-existent ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Exam type not found"

# Test to ensure deleting an exam type with associated questions sets exam_type_id to NULL on questions
def test_delete_exam_type_with_associated_questions(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # 1. Create an Exam Type
    exam_type_to_delete = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="ET With Questions"))
    
    # 2. Create a Question associated with this Exam Type
    from app.crud import crud_question # Ensure crud_question is imported
    question_data = schemas.QuestionCreate(
        problem_statement="Question for ET With Questions",
        option_1="A", option_2="B", option_3="C", option_4="D",
        correct_answer=1,
        exam_type_id=exam_type_to_delete.id
    )
    associated_question = crud_question.create_question(db_session, question_data)
    assert associated_question.exam_type_id == exam_type_to_delete.id

    # 3. Delete the Exam Type via API
    delete_response = authenticated_client.delete(f"/exam-types/{exam_type_to_delete.id}")
    assert delete_response.status_code == status.HTTP_200_OK

    # 4. Verify the Exam Type is deleted from the DB
    db_exam_type = db_session.query(models.ExamType).filter(models.ExamType.id == exam_type_to_delete.id).first()
    assert db_exam_type is None

    # 5. Verify the associated Question's exam_type_id is now NULL
    db_session.refresh(associated_question) # Refresh the question state from the DB
    assert associated_question.exam_type_id is None

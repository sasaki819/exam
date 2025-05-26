import json # For import/export tests
from io import BytesIO # For import tests
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


# --- Tests for Export Questions Endpoint ---

def test_export_questions_success(authenticated_client: TestClient, db_session: SQLAlchemySession):
    from app.crud import crud_question # Local import
    # 1. Create an ExamType
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Export Success ET"))
    
    # 2. Add Questions to it
    q1_data = schemas.QuestionCreate(problem_statement="Q1 Problem", option_1="A", option_2="B", option_3="C", option_4="D", correct_answer=1, exam_type_id=exam_type.id, explanation="Q1 Exp")
    q2_data = schemas.QuestionCreate(problem_statement="Q2 Problem", option_1="1", option_2="2", option_3="3", option_4="4", correct_answer=2, exam_type_id=exam_type.id) # No explanation
    q1 = crud_question.create_question(db_session, q1_data)
    q2 = crud_question.create_question(db_session, q2_data)

    # 3. Make GET request
    response = authenticated_client.get(f"/exam-types/{exam_type.id}/export-questions/")
    
    # 4. Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"].startswith(f"attachment; filename=\"exam_type_{exam_type.name.replace(' ', '_')}_{exam_type.id}_questions.json\"")
    
    exported_data = response.json()
    assert isinstance(exported_data, list)
    assert len(exported_data) == 2
    
    # Verify content of exported questions (order might not be guaranteed, so check for presence)
    exported_q1_data = next((q for q in exported_data if q["problem_statement"] == "Q1 Problem"), None)
    exported_q2_data = next((q for q in exported_data if q["problem_statement"] == "Q2 Problem"), None)
    
    assert exported_q1_data is not None
    assert exported_q1_data["option_1"] == "A"
    assert exported_q1_data["correct_answer"] == 1
    assert exported_q1_data["explanation"] == "Q1 Exp"
    assert "id" not in exported_q1_data
    assert "exam_type_id" not in exported_q1_data
    
    assert exported_q2_data is not None
    assert exported_q2_data["option_1"] == "1"
    assert exported_q2_data["correct_answer"] == 2
    assert exported_q2_data["explanation"] is None # Check for null explanation
    assert "id" not in exported_q2_data
    assert "exam_type_id" not in exported_q2_data

def test_export_questions_no_questions(authenticated_client: TestClient, db_session: SQLAlchemySession):
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Export No Questions ET"))
    
    response = authenticated_client.get(f"/exam-types/{exam_type.id}/export-questions/")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"
    exported_data = response.json()
    assert isinstance(exported_data, list)
    assert len(exported_data) == 0

def test_export_questions_nonexistent_exam_type(authenticated_client: TestClient):
    response = authenticated_client.get("/exam-types/999999/export-questions/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "ExamType not found"

def test_export_questions_unauthenticated(client: TestClient, db_session: SQLAlchemySession):
    # Use unauthenticated client fixture
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Export Unauth ET"))
    response = client.get(f"/exam-types/{exam_type.id}/export-questions/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 


# --- Tests for Import Questions Endpoint ---

def test_import_questions_success(authenticated_client: TestClient, db_session: SQLAlchemySession):
    from app.crud import crud_question # Local import
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Import Success ET"))
    
    questions_to_import = [
        {"problem_statement": "Import Q1", "option_1": "A", "option_2": "B", "option_3": "C", "option_4": "D", "correct_answer": 1, "explanation": "Exp Q1"},
        {"problem_statement": "Import Q2", "option_1": "1", "option_2": "2", "option_3": "3", "option_4": "4", "correct_answer": 2} # No explanation
    ]
    json_string = json.dumps(questions_to_import)
    
    files = {"file": ("test_import.json", BytesIO(json_string.encode('utf-8')), "application/json")}
    response = authenticated_client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    summary = response.json()
    assert summary["imported_count"] == 2
    assert summary["failed_count"] == 0
    assert len(summary["errors"]) == 0
    
    # Verify in DB
    db_questions = db_session.query(models.Question).filter(models.Question.exam_type_id == exam_type.id).all()
    assert len(db_questions) == 2
    
    q1_db = next((q for q in db_questions if q.problem_statement == "Import Q1"), None)
    assert q1_db is not None
    assert q1_db.option_1 == "A"
    assert q1_db.correct_answer == 1
    assert q1_db.explanation == "Exp Q1"
    assert q1_db.exam_type_id == exam_type.id

    q2_db = next((q for q in db_questions if q.problem_statement == "Import Q2"), None)
    assert q2_db is not None
    assert q2_db.option_1 == "1"
    assert q2_db.correct_answer == 2
    assert q2_db.explanation is None
    assert q2_db.exam_type_id == exam_type.id


def test_import_questions_partial_success(authenticated_client: TestClient, db_session: SQLAlchemySession):
    from app.crud import crud_question # Local import
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Import Partial ET"))
    
    questions_to_import = [
        {"problem_statement": "Valid Q1", "option_1": "A", "option_2": "B", "option_3": "C", "option_4": "D", "correct_answer": 1}, # Valid
        {"option_1": "X", "option_2": "Y", "option_3": "Z", "option_4": "W", "correct_answer": 3}, # Invalid - missing problem_statement
        {"problem_statement": "Valid Q2", "option_1": "1", "option_2": "2", "option_3": "3", "option_4": "4", "correct_answer": 4, "explanation": "Exp Q2"} # Valid
    ]
    json_string = json.dumps(questions_to_import)
    
    files = {"file": ("test_import_partial.json", BytesIO(json_string.encode('utf-8')), "application/json")}
    response = authenticated_client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    summary = response.json()
    assert summary["imported_count"] == 2
    assert summary["failed_count"] == 1
    assert len(summary["errors"]) == 1
    assert summary["errors"][0]["row_index"] == 1 # 0-indexed
    assert "problem_statement" in summary["errors"][0]["error_message"] # Check if the error message mentions problem_statement
    assert summary["errors"][0]["data"]["option_1"] == "X" # Check if original data is in error report
    
    # Verify in DB
    db_questions = db_session.query(models.Question).filter(models.Question.exam_type_id == exam_type.id).all()
    assert len(db_questions) == 2
    assert any(q.problem_statement == "Valid Q1" for q in db_questions)
    assert any(q.problem_statement == "Valid Q2" for q in db_questions)


def test_import_questions_all_fail_validation(authenticated_client: TestClient, db_session: SQLAlchemySession):
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Import All Fail ET"))
    
    questions_to_import = [
        {"option_1": "A", "correct_answer": 1}, # Missing problem_statement, options
        {"problem_statement": "Q2", "option_1": "1"} # Missing other options, correct_answer
    ]
    json_string = json.dumps(questions_to_import)
    
    files = {"file": ("test_import_all_fail.json", BytesIO(json_string.encode('utf-8')), "application/json")}
    response = authenticated_client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    summary = response.json()
    assert summary["imported_count"] == 0
    assert summary["failed_count"] == 2
    assert len(summary["errors"]) == 2
    assert summary["errors"][0]["row_index"] == 0
    assert summary["errors"][1]["row_index"] == 1
    
    # Verify no questions added to DB
    db_questions_count = db_session.query(models.Question).filter(models.Question.exam_type_id == exam_type.id).count()
    assert db_questions_count == 0

def test_import_questions_empty_list_in_file(authenticated_client: TestClient, db_session: SQLAlchemySession):
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Import Empty List ET"))
    
    questions_to_import = []
    json_string = json.dumps(questions_to_import)
    
    files = {"file": ("test_import_empty.json", BytesIO(json_string.encode('utf-8')), "application/json")}
    response = authenticated_client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    summary = response.json()
    assert summary["imported_count"] == 0
    assert summary["failed_count"] == 0
    assert len(summary["errors"]) == 0

def test_import_questions_malformed_json_file(authenticated_client: TestClient, db_session: SQLAlchemySession):
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Import Malformed ET"))
    
    # Test 1: Not a list
    malformed_json_string_not_list = json.dumps({"test": "not a list"})
    files_not_list = {"file": ("test_malformed1.json", BytesIO(malformed_json_string_not_list.encode('utf-8')), "application/json")}
    response_not_list = authenticated_client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files_not_list)
    
    assert response_not_list.status_code == status.HTTP_200_OK 
    summary_not_list = response_not_list.json()
    assert summary_not_list["imported_count"] == 0
    assert summary_not_list["failed_count"] == 0 # File level error, not item failure
    assert len(summary_not_list["errors"]) == 1
    assert "JSON content is not a list" in summary_not_list["errors"][0]["error_message"]
    assert summary_not_list["errors"][0]["row_index"] is None # File level error
    
    # Test 2: Invalid JSON string
    invalid_json_string = "this is not json"
    files_invalid_json = {"file": ("test_malformed2.json", BytesIO(invalid_json_string.encode('utf-8')), "application/json")}
    response_invalid_json = authenticated_client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files_invalid_json)
    
    assert response_invalid_json.status_code == status.HTTP_200_OK
    summary_invalid_json = response_invalid_json.json()
    assert summary_invalid_json["imported_count"] == 0
    assert summary_invalid_json["failed_count"] == 0 # File level error
    assert len(summary_invalid_json["errors"]) == 1
    assert "Invalid JSON file" in summary_invalid_json["errors"][0]["error_message"]
    assert summary_invalid_json["errors"][0]["row_index"] is None # File level error

# test_import_questions_not_json_file_content_type is less critical as FastAPI/browser might handle it.
# The backend tries to parse JSON regardless of UploadFile.content_type.
# If strict content-type check was added to backend, this test would be more relevant.

def test_import_questions_nonexistent_exam_type(authenticated_client: TestClient):
    questions_to_import = [{"problem_statement": "Q", "option_1":"A", "option_2":"B", "option_3":"C", "option_4":"D", "correct_answer":1}]
    json_string = json.dumps(questions_to_import)
    files = {"file": ("test_import.json", BytesIO(json_string.encode('utf-8')), "application/json")}
    
    response = authenticated_client.post("/exam-types/999999/import-questions/", files=files)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "ExamType not found"

def test_import_questions_unauthenticated(client: TestClient, db_session: SQLAlchemySession):
    exam_type = crud_exam_type.create_exam_type(db_session, schemas.ExamTypeCreate(name="Import Unauth ET"))
    questions_to_import = [{"problem_statement": "Q", "option_1":"A", "option_2":"B", "option_3":"C", "option_4":"D", "correct_answer":1}]
    json_string = json.dumps(questions_to_import)
    files = {"file": ("test_import.json", BytesIO(json_string.encode('utf-8')), "application/json")}

    response = client.post(f"/exam-types/{exam_type.id}/import-questions/", files=files)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_import_questions_with_duplicates_and_new(authenticated_client: TestClient, db_session: SQLAlchemySession):
    # 1. Create a new ExamType for this test to ensure isolation
    et_payload = {"name": "Import Duplicates Test ET"}
    response_et = authenticated_client.post("/exam-types/", json=et_payload)
    assert response_et.status_code == status.HTTP_201_CREATED
    exam_type_id = response_et.json()["id"]

    # 2. Create an initial question linked to this exam_type_id
    initial_question_payload = {
        "problem_statement": "既存の問題1",
        "option_1": "Initial Opt1", "option_2": "Initial Opt2", "option_3": "Initial Opt3", "option_4": "Initial Opt4",
        "correct_answer": 1, "explanation": "Initial Explanation",
        "exam_type_id": exam_type_id
    }
    response_initial_q = authenticated_client.post("/questions/", json=initial_question_payload)
    assert response_initial_q.status_code == status.HTTP_201_CREATED

    # 3. Prepare the questions_to_import list
    questions_to_import = [
        {
            "problem_statement": "既存の問題1", # Duplicate
            "option_1": "Dup Opt1", "option_2": "Dup Opt2", "option_3": "Dup Opt3", "option_4": "Dup Opt4",
            "correct_answer": 2, "explanation": "Duplicate Explanation"
        },
        {
            "problem_statement": "新しい問題A", # New
            "option_1": "NewA Opt1", "option_2": "NewA Opt2", "option_3": "NewA Opt3", "option_4": "NewA Opt4",
            "correct_answer": 3, "explanation": "NewA Explanation"
        },
        {
            "problem_statement": "新しい問題B", # New
            "option_1": "NewB Opt1", "option_2": "NewB Opt2", "option_3": "NewB Opt3", "option_4": "NewB Opt4",
            "correct_answer": 4, "explanation": "NewB Explanation"
        }
    ]

    # 4. Convert to JSON and BytesIO, then POST for import
    json_data = json.dumps(questions_to_import)
    files = {"file": ("test_import_dup.json", BytesIO(json_data.encode('utf-8')), "application/json")}
    
    response_import = authenticated_client.post(
        f"/exam-types/{exam_type_id}/import-questions/",
        files=files
    )

    # 5. Assert response status code
    assert response_import.status_code == status.HTTP_200_OK

    # 6. Parse response and assert counts
    summary = response_import.json()
    assert summary["imported_count"] == 2, f"Actual summary: {summary}"
    assert summary["skipped_count"] == 1, f"Actual summary: {summary}"
    assert summary["failed_count"] == 0, f"Actual summary: {summary}"
    assert len(summary["errors"]) == 0, f"Actual summary: {summary}"

    # 7. Verify the questions in the database via API
    response_get_all = authenticated_client.get(f"/questions/?exam_type_id={exam_type_id}")
    assert response_get_all.status_code == status.HTTP_200_OK
    
    all_questions_after_import = response_get_all.json()
    assert len(all_questions_after_import) == 3 # Initial (1) + New (2)

    problem_statements_in_db = {q["problem_statement"] for q in all_questions_after_import}
    
    assert "既存の問題1" in problem_statements_in_db
    assert "新しい問題A" in problem_statements_in_db
    assert "新しい問題B" in problem_statements_in_db

    # Additionally, check that the "既存の問題1" was not overwritten by the duplicate import data
    existing_q_after_import = next((q for q in all_questions_after_import if q["problem_statement"] == "既存の問題1"), None)
    assert existing_q_after_import is not None
    assert existing_q_after_import["option_1"] == "Initial Opt1" # Should be the original option
    assert existing_q_after_import["correct_answer"] == 1 # Should be the original answer

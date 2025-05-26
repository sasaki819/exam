document.addEventListener('DOMContentLoaded', async () => {
    const questionsList = document.getElementById('questions-list');
    const createForm = document.getElementById('create-question-form');
    const messageArea = document.getElementById('message-area');
    
    const newExamTypeDropdown = document.getElementById('new-exam-type-id');
    const filterExamTypeDropdown = document.getElementById('filter-exam-type-id');

    const editModal = document.getElementById('edit-question-modal');
    const editForm = document.getElementById('edit-question-form');
    const editQuestionIdInput = document.getElementById('edit-question-id');
    const editExamTypeDropdown = document.getElementById('edit-exam-type-id');
    const closeModalButton = editModal.querySelector('.close-button');

    const exportButton = document.getElementById('export-questions-btn'); // Added for export

    // DOM elements for import functionality
    const importFileIn = document.getElementById('import-questions-file');
    const importButton = document.getElementById('import-questions-btn');
    const importMessageArea = document.getElementById('import-message-area');

    let allExamTypes = []; // To store fetched exam types for reuse

    function getAuthHeaders(isPostOrPut = false) {
        const token = localStorage.getItem('accessToken');
        if (!token) { window.location.href = '/login'; return null; }
        const headers = { 'Authorization': 'Bearer ' + token };
        if (isPostOrPut) { headers['Content-Type'] = 'application/json'; }
        return headers;
    }

    function displayMessage(message, type = 'success') {
        messageArea.textContent = message;
        messageArea.className = `message-area ${type}`;
        setTimeout(() => { messageArea.textContent = ''; messageArea.className = 'message-area'; }, 3000);
    }

    async function fetchExamTypes() {
        const headers = getAuthHeaders();
        if (!headers) return;
        try {
            const response = await fetch('/exam-types/', { headers });
            if (!response.ok) { throw new Error('Failed to load exam types'); }
            allExamTypes = await response.json();
            populateExamTypeDropdown(newExamTypeDropdown, allExamTypes, false); // Don't add "All" option here
            populateExamTypeDropdown(filterExamTypeDropdown, allExamTypes, true); // Add "All" option
            populateExamTypeDropdown(editExamTypeDropdown, allExamTypes, false); // For edit modal
        } catch (error) {
            console.error('Error fetching exam types:', error);
            displayMessage(error.message || 'Error fetching exam types.', 'error');
        }
    }

    function populateExamTypeDropdown(dropdownElement, examTypes, includeAllOption) {
        dropdownElement.innerHTML = ''; // Clear existing options
        if (includeAllOption) {
            const allOption = document.createElement('option');
            allOption.value = "";
            allOption.textContent = "All Exam Types";
            dropdownElement.appendChild(allOption);
        }
        examTypes.forEach(et => {
            const option = document.createElement('option');
            option.value = et.id;
            option.textContent = et.name;
            dropdownElement.appendChild(option);
        });
    }
    
    async function fetchQuestions(examTypeId = '') {
        const headers = getAuthHeaders();
        if (!headers) return;
        let url = '/questions/';
        if (examTypeId) {
            url += `?exam_type_id=${examTypeId}`;
        }
        try {
            const response = await fetch(url, { headers });
            if (!response.ok) { throw new Error('Failed to load questions'); }
            const questions = await response.json();
            renderQuestions(questions);
        } catch (error) {
            console.error('Error fetching questions:', error);
            displayMessage(error.message || 'Error fetching questions.', 'error');
        }
    }

    function renderQuestions(questions) {
        questionsList.innerHTML = '';
        if (questions.length === 0) {
            questionsList.innerHTML = '<li>No questions found for the selected filter.</li>';
            return;
        }
        questions.forEach(q => {
            const listItem = document.createElement('li');
            const examTypeName = allExamTypes.find(et => et.id === q.exam_type_id)?.name || 'N/A';
            listItem.innerHTML = `
                <strong>ID: ${q.id} (Exam: ${examTypeName})</strong><br>
                ${q.problem_statement.substring(0,100)}... <br>
                Options: 1) ${q.option_1}, 2) ${q.option_2}, 3) ${q.option_3}, 4) ${q.option_4} <br>
                Correct: ${q.correct_answer} <br>
                Explanation: ${q.explanation || 'None'}
            `;
            
            const editButton = document.createElement('button');
            editButton.textContent = 'Edit';
            editButton.classList.add('edit-btn');
            editButton.onclick = () => openEditModal(q);

            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.classList.add('delete-btn');
            deleteButton.onclick = () => deleteQuestion(q.id);

            listItem.appendChild(editButton);
            listItem.appendChild(deleteButton);
            questionsList.appendChild(listItem);
        });
    }

    createForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(createForm);
        const data = Object.fromEntries(formData.entries());
        // Ensure numeric fields are numbers
        data.correct_answer = parseInt(data.correct_answer);
        data.exam_type_id = parseInt(data.exam_type_id);

        const headers = getAuthHeaders(true);
        if (!headers) return;

        try {
            const response = await fetch('/questions/', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            });
            if (response.status === 201) {
                displayMessage('Question created successfully!', 'success');
                createForm.reset();
                fetchQuestions(filterExamTypeDropdown.value); // Refresh list
            } else {
                const errorData = await response.json();
                displayMessage(errorData.detail || 'Failed to create question.', 'error');
            }
        } catch (error) {
            displayMessage('Error creating question.', 'error');
        }
    });
    
    filterExamTypeDropdown.addEventListener('change', (event) => {
        fetchQuestions(event.target.value);
    });

    function openEditModal(question) {
        editQuestionIdInput.value = question.id;
        editExamTypeDropdown.value = question.exam_type_id; // Set selected exam type
        // Populate other fields
        document.getElementById('edit-problem-statement').value = question.problem_statement;
        document.getElementById('edit-option-1').value = question.option_1;
        document.getElementById('edit-option-2').value = question.option_2;
        document.getElementById('edit-option-3').value = question.option_3;
        document.getElementById('edit-option-4').value = question.option_4;
        document.getElementById('edit-correct-answer').value = question.correct_answer;
        document.getElementById('edit-explanation').value = question.explanation || '';
        editModal.style.display = 'block';
    }

    if (closeModalButton) { closeModalButton.onclick = () => { editModal.style.display = 'none'; }; }
    window.onclick = (event) => { if (event.target == editModal) { editModal.style.display = "none"; } };

    editForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const id = editQuestionIdInput.value;
        const formData = new FormData(editForm);
        const data = {};
        // Build data object, only include fields that have values or are part of the model.
        // Pydantic's QuestionUpdate schema handles optional fields.
        for (let [key, value] of formData.entries()) {
             if (value || key === 'explanation') { // explanation can be empty string
                 if (key === 'correct_answer' || key === 'exam_type_id') {
                     data[key] = parseInt(value);
                 } else {
                     data[key] = value;
                 }
             }
        }
        
        const headers = getAuthHeaders(true);
        if (!headers) return;

        try {
            const response = await fetch(`/questions/${id}`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(data)
            });
            if (response.ok) {
                displayMessage('Question updated successfully!', 'success');
                editModal.style.display = 'none';
                fetchQuestions(filterExamTypeDropdown.value);
            } else {
                const errorData = await response.json();
                displayMessage(errorData.detail || 'Failed to update question.', 'error');
            }
        } catch (error) {
            displayMessage('Error updating question.', 'error');
        }
    });

    async function deleteQuestion(id) {
        if (!confirm(`Are you sure you want to delete question ID ${id}? This will also delete related answer history.`)) {
            return;
        }
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            const response = await fetch(`/questions/${id}`, { method: 'DELETE', headers: headers });
            if (response.ok) {
                displayMessage('Question deleted successfully!', 'success');
                fetchQuestions(filterExamTypeDropdown.value);
            } else {
                const errorData = await response.json();
                displayMessage(errorData.detail || 'Failed to delete question.', 'error');
            }
        } catch (error) {
            displayMessage('Error deleting question.', 'error');
        }
    }
    
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('accessToken');
            window.location.href = '/login';
        });
    }

    // Initial fetch
    await fetchExamTypes(); // Wait for exam types to load first
    fetchQuestions(); // Then load all questions initially

    // Event listener for the export button
    if (exportButton) {
        exportButton.addEventListener('click', async () => {
            const selectedExamTypeId = filterExamTypeDropdown.value;

            if (!selectedExamTypeId) {
                displayMessage('Please select a specific Exam Type to export questions.', 'error');
                return;
            }

            const exportUrl = `/exam-types/${selectedExamTypeId}/export-questions/`;
            
            try {
                const token = localStorage.getItem('accessToken');
                if (!token) {
                    displayMessage('Authentication token not found. Please log in again.', 'error');
                    window.location.href = '/login'; // Redirect to login
                    return;
                }
                const headers = { 'Authorization': 'Bearer ' + token };

                const response = await fetch(exportUrl, { headers });

                if (response.ok) {
                    const blob = await response.blob();
                    const contentDisposition = response.headers.get('content-disposition');
                    let filename = 'exported_questions.json'; // Default filename
                    if (contentDisposition) {
                        const match = contentDisposition.match(/filename="?([^"]+)"?/i);
                        if (match && match[1]) {
                            filename = match[1];
                        }
                    }

                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    displayMessage('Questions exported successfully. Download has started.', 'success');
                } else {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error during export.' }));
                    displayMessage(`Export failed: ${errorData.detail || response.statusText}`, 'error');
                }
            } catch (error) {
                console.error('Export error:', error);
                displayMessage(`Export failed: ${error.message}`, 'error');
            }
        });
    }

    // Helper function for displaying messages in the import area
    function displayImportMessage(message, type = 'success', errors = []) {
        importMessageArea.innerHTML = ''; // Clear previous messages
        
        const messageP = document.createElement('p');
        messageP.textContent = message;
        messageP.className = `message-area-${type}`; // Use a distinct class if needed, or align with existing
        importMessageArea.appendChild(messageP);

        if (errors.length > 0) {
            const ul = document.createElement('ul');
            ul.style.marginTop = '10px';
            errors.forEach(err => {
                const li = document.createElement('li');
                li.style.fontSize = '0.9em';
                li.style.color = (type === 'error' || type === 'warning') ? 'darkred' : 'black';
                let errorDetail = `Row ${err.row_index !== null ? err.row_index + 1 : 'N/A'}: ${err.error_message}`;
                if (err.data) {
                    errorDetail += ` (Data: ${JSON.stringify(err.data).substring(0, 100)}...)`;
                }
                li.textContent = errorDetail;
                ul.appendChild(li);
            });
            importMessageArea.appendChild(ul);
        }
        // No timeout for import messages as they can be long with error lists
    }

    // Event listener for the import button
    if (importButton) {
        importButton.addEventListener('click', async () => {
            const selectedExamTypeId = filterExamTypeDropdown.value;
            const file = importFileIn.files[0];

            if (!selectedExamTypeId) {
                displayImportMessage('Please select an Exam Type first to import questions into.', 'error');
                return;
            }
            if (!file) {
                displayImportMessage('Please select a file to import.', 'error');
                return;
            }
            if (file.type !== 'application/json') {
                displayImportMessage('Please select a JSON file (.json).', 'error');
                importFileIn.value = ''; // Clear the invalid file
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            const headers = getAuthHeaders(false); // false because browser sets Content-Type for FormData
            if (!headers) {
                 displayImportMessage('Authentication error. Please log in again.', 'error');
                 return; // Should have been redirected by getAuthHeaders, but as a safeguard.
            }
            
            const importUrl = `/exam-types/${selectedExamTypeId}/import-questions/`;

            try {
                const response = await fetch(importUrl, {
                    method: 'POST',
                    body: formData,
                    headers: headers 
                });

                const result = await response.json();

                if (response.ok) {
                    let successMsg = `Successfully imported ${result.imported_count} questions. Failed: ${result.failed_count}.`;
                    if (result.failed_count > 0 || (result.errors && result.errors.length > 0)) {
                         displayImportMessage(successMsg, 'warning', result.errors);
                    } else {
                         displayImportMessage(successMsg, 'success', result.errors);
                    }
                    if (result.imported_count > 0) {
                        fetchQuestions(selectedExamTypeId); // Refresh questions for the current exam type
                    }
                } else {
                    // Handle errors from the server (e.g., 400, 404, 422)
                    let errorMsg = result.detail || 'Import failed. Unknown server error.';
                    if (result.errors && result.errors.length > 0) { // If the backend provides structured errors
                        displayImportMessage(errorMsg, 'error', result.errors);
                    } else if (response.status === 422 && result.detail && Array.isArray(result.detail)) {
                        // Handle FastAPI's default validation error structure if not caught by custom summary
                        const formattedErrors = result.detail.map(err => ({
                            row_index: null, // FastAPI validation errors are not typically row-specific in this context
                            error_message: `${err.loc.join(' -> ')}: ${err.msg}`,
                            data: null
                        }));
                         displayImportMessage('Validation errors occurred:', 'error', formattedErrors);
                    }
                    else {
                        displayImportMessage(errorMsg, 'error');
                    }
                }
            } catch (error) {
                console.error('Error during import:', error);
                displayImportMessage(`An unexpected error occurred during import: ${error.message}`, 'error');
            } finally {
                importFileIn.value = ''; // Clear the file input after attempt
            }
        });
    }
});

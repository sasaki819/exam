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
});

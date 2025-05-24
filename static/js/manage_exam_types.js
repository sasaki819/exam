document.addEventListener('DOMContentLoaded', () => {
    const examTypesList = document.getElementById('exam-types-list');
    const createForm = document.getElementById('create-exam-type-form');
    const newExamTypeNameInput = document.getElementById('new-exam-type-name');
    const messageArea = document.getElementById('message-area');

    const editModal = document.getElementById('edit-modal');
    const editForm = document.getElementById('edit-exam-type-form');
    const editExamTypeIdInput = document.getElementById('edit-exam-type-id');
    const editExamTypeNameInput = document.getElementById('edit-exam-type-name');
    const closeModalButton = editModal.querySelector('.close-button');

    function getAuthHeaders(isPostOrPut = false) {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/login'; // Redirect if no token
            return null;
        }
        const headers = { 'Authorization': 'Bearer ' + token };
        if (isPostOrPut) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    }

    function displayMessage(message, type = 'success') {
        messageArea.textContent = message;
        messageArea.className = `message-area ${type}`; // e.g., message-area success or message-area error
        setTimeout(() => { messageArea.textContent = ''; messageArea.className = 'message-area';}, 3000);
    }

    async function fetchExamTypes() {
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            const response = await fetch('/exam-types/', { headers });
            if (!response.ok) {
                if (response.status === 401) window.location.href = '/login';
                displayMessage('Failed to load exam types.', 'error');
                return;
            }
            const examTypes = await response.json();
            renderExamTypes(examTypes);
        } catch (error) {
            console.error('Error fetching exam types:', error);
            displayMessage('Error fetching exam types.', 'error');
        }
    }

    function renderExamTypes(examTypes) {
        examTypesList.innerHTML = ''; // Clear current list
        if (examTypes.length === 0) {
            examTypesList.innerHTML = '<li>No exam types found.</li>';
            return;
        }
        examTypes.forEach(et => {
            const listItem = document.createElement('li');
            listItem.textContent = `${et.name} (ID: ${et.id})`;
            
            const editButton = document.createElement('button');
            editButton.textContent = 'Edit';
            editButton.classList.add('edit-btn');
            editButton.onclick = () => openEditModal(et);

            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.classList.add('delete-btn');
            deleteButton.onclick = () => deleteExamType(et.id, et.name);

            listItem.appendChild(editButton);
            listItem.appendChild(deleteButton);
            examTypesList.appendChild(listItem);
        });
    }

    createForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const name = newExamTypeNameInput.value.trim();
        if (!name) {
            displayMessage('Name cannot be empty.', 'error');
            return;
        }
        const headers = getAuthHeaders(true);
        if (!headers) return;

        try {
            const response = await fetch('/exam-types/', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ name: name })
            });
            if (response.status === 201) {
                displayMessage('Exam type created successfully!', 'success');
                newExamTypeNameInput.value = ''; // Clear input
                fetchExamTypes(); // Refresh list
            } else {
                const errorData = await response.json();
                displayMessage(errorData.detail || 'Failed to create exam type.', 'error');
            }
        } catch (error) {
            console.error('Error creating exam type:', error);
            displayMessage('Error creating exam type.', 'error');
        }
    });

    function openEditModal(examType) {
        editExamTypeIdInput.value = examType.id;
        editExamTypeNameInput.value = examType.name;
        editModal.style.display = 'block';
    }

    if (closeModalButton) {
         closeModalButton.onclick = () => {
             editModal.style.display = 'none';
         };
    }
    // Close modal if user clicks outside of it
     window.onclick = (event) => {
         if (event.target == editModal) {
             editModal.style.display = "none";
         }
     }


    editForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const id = editExamTypeIdInput.value;
        const name = editExamTypeNameInput.value.trim();
        if (!name) {
            displayMessage('Name cannot be empty for editing.', 'error');
            return;
        }
        const headers = getAuthHeaders(true);
        if (!headers) return;

        try {
            const response = await fetch(`/exam-types/${id}`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ name: name })
            });
            if (response.ok) {
                displayMessage('Exam type updated successfully!', 'success');
                editModal.style.display = 'none';
                fetchExamTypes(); // Refresh list
            } else {
                const errorData = await response.json();
                displayMessage(errorData.detail || 'Failed to update exam type.', 'error');
            }
        } catch (error) {
            console.error('Error updating exam type:', error);
            displayMessage('Error updating exam type.', 'error');
        }
    });

    async function deleteExamType(id, name) {
        if (!confirm(`Are you sure you want to delete exam type "${name}" (ID: ${id})? This might affect existing questions.`)) {
            return;
        }
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            const response = await fetch(`/exam-types/${id}`, {
                method: 'DELETE',
                headers: headers
            });
            if (response.ok) {
                displayMessage('Exam type deleted successfully!', 'success');
                fetchExamTypes(); // Refresh list
            } else {
                const errorData = await response.json();
                // Check if detail is an object with 'msg' (FastAPI validation error) or string
                let detailMsg = 'Failed to delete exam type.';
                if (errorData && errorData.detail) {
                    if (typeof errorData.detail === 'string') {
                        detailMsg = errorData.detail;
                    } else if (Array.isArray(errorData.detail) && errorData.detail[0] && errorData.detail[0].msg) {
                        detailMsg = errorData.detail[0].msg; // Typical for validation errors
                    } else {
                         try { // Attempt to stringify if it's an object/array but not expected format
                             detailMsg = JSON.stringify(errorData.detail);
                         } catch (e) { /* ignore stringify error */ }
                    }
                }
                displayMessage(detailMsg, 'error');
            }
        } catch (error) {
            console.error('Error deleting exam type:', error);
            displayMessage('Error deleting exam type.', 'error');
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
    fetchExamTypes();
});

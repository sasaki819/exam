document.addEventListener('DOMContentLoaded', () => {
    const problemStatementElem = document.getElementById('problem-statement');
    const optionsContainerElem = document.getElementById('options-container');
    const submitAnswerButton = document.getElementById('submit-answer-button');
    const resultContainerElem = document.getElementById('result-container');
    const correctStatusElem = document.getElementById('correct-status');
    const correctOptionElem = document.getElementById('correct-option');
    const explanationTextElem = document.getElementById('explanation-text');
    const nextQuestionButton = document.getElementById('next-question-button');
    const examErrorMessage = document.getElementById('exam-error-message'); // For general exam errors
    const logoutLink = document.getElementById('logout-link');

    const examTypeSelectionArea = document.getElementById('exam-type-selection-area');
    const examTypeDropdown = document.getElementById('exam-type-dropdown');
    const startExamButton = document.getElementById('start-exam-button');
    const examTypeErrorMesssage = document.getElementById('exam-type-error-message');
    const questionArea = document.getElementById('question-area');

    let currentQuestionId = null;
    let selectedExamTypeId = null;

    function getAuthHeaders(isPost = false) {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/login';
            return null;
        }
        const headers = { 'Authorization': 'Bearer ' + token };
        if (isPost) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    }

    async function fetchExamTypes() {
        examTypeErrorMesssage.textContent = '';
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            const response = await fetch('/exam-types/', { method: 'GET', headers: headers });
            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login';
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                examTypeErrorMesssage.textContent = errorData.detail || 'Failed to load exam types.';
                return;
            }
            const examTypes = await response.json();
            if (examTypes.length === 0) {
                examTypeErrorMesssage.textContent = 'No exam types available.';
                return;
            }
            examTypes.forEach(et => {
                const option = document.createElement('option');
                option.value = et.id;
                option.textContent = et.name;
                examTypeDropdown.appendChild(option);
            });
            startExamButton.style.display = 'inline-block'; // Show button once types are loaded

        } catch (error) {
            console.error('Error fetching exam types:', error);
            examTypeErrorMesssage.textContent = 'An error occurred while fetching exam types.';
        }
    }

    async function fetchQuestion() {
        examErrorMessage.textContent = ''; // Clear general exam errors
        if (!selectedExamTypeId) {
            examErrorMessage.textContent = 'Please select an exam type and start the exam.';
            return;
        }
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            // Include exam_type_id as a query parameter
            const response = await fetch(`/questions/next/?exam_type_id=${selectedExamTypeId}`, { method: 'GET', headers: headers });

            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login';
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                problemStatementElem.textContent = errorData.detail || 'Failed to load question.';
                optionsContainerElem.innerHTML = '';
                submitAnswerButton.style.display = 'none';
                nextQuestionButton.style.display = 'none';
                if (response.status === 404) {
                     problemStatementElem.textContent = errorData.detail || "No more questions available for this exam type.";
                }
                return;
            }

            const question = await response.json();
            currentQuestionId = question.id;
            problemStatementElem.textContent = question.problem_statement;
            
            optionsContainerElem.innerHTML = '';
            for (let i = 1; i <= 4; i++) {
                const optionKey = `option_${i}`;
                if (question[optionKey]) {
                    const radioInput = document.createElement('input');
                    radioInput.type = 'radio';
                    radioInput.id = `option${i}`;
                    radioInput.name = 'answer';
                    radioInput.value = i;

                    const label = document.createElement('label');
                    label.htmlFor = `option${i}`;
                    label.textContent = question[optionKey];

                    const div = document.createElement('div');
                    div.appendChild(radioInput);
                    div.appendChild(label);
                    optionsContainerElem.appendChild(div);
                }
            }
            resultContainerElem.style.display = 'none';
            submitAnswerButton.disabled = false;
            submitAnswerButton.style.display = 'block';
            nextQuestionButton.style.display = 'none';
            questionArea.style.display = 'block'; // Show question area

        } catch (error) {
            console.error('Error fetching question:', error);
            problemStatementElem.textContent = 'An error occurred while fetching the question.';
            examErrorMessage.textContent = 'An error occurred. Please try refreshing.';
        }
    }

    async function submitAnswer() {
        examErrorMessage.textContent = '';
        const selectedOption = document.querySelector('input[name="answer"]:checked');
        if (!selectedOption) {
            examErrorMessage.textContent = 'Please select an answer.';
            return;
        }
        const headers = getAuthHeaders(true);
        if (!headers) return;

        const answerData = { selected_answer: parseInt(selectedOption.value) };

        try {
            const response = await fetch(`/questions/${currentQuestionId}/answer/`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(answerData),
            });

            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login';
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                examErrorMessage.textContent = errorData.detail || 'Failed to submit answer.';
                return;
            }

            const result = await response.json();
            correctStatusElem.textContent = result.is_correct ? 'Correct!' : 'Incorrect!';
            correctStatusElem.className = result.is_correct ? 'correct' : 'incorrect';
            correctOptionElem.textContent = result.correct_answer_option;
            explanationTextElem.textContent = result.explanation || 'No explanation provided.';
            
            resultContainerElem.style.display = 'block';
            submitAnswerButton.disabled = true;
            submitAnswerButton.style.display = 'none';
            nextQuestionButton.style.display = 'block';

        } catch (error) {
            console.error('Error submitting answer:', error);
            examErrorMessage.textContent = 'An error occurred while submitting your answer.';
        }
    }

    if (startExamButton) {
        startExamButton.addEventListener('click', () => {
            selectedExamTypeId = examTypeDropdown.value;
            if (!selectedExamTypeId) {
                examTypeErrorMesssage.textContent = 'Please select an exam type.';
                return;
            }
            examTypeErrorMesssage.textContent = ''; // Clear error
            examTypeSelectionArea.style.display = 'none'; // Hide selection area
            questionArea.style.display = 'block'; // Show question area
            fetchQuestion(); // Fetch the first question for the selected exam
        });
    }
    
    if (examTypeDropdown) {
         examTypeDropdown.addEventListener('change', () => {
             // If user changes selection, clear any previous error message.
             examTypeErrorMesssage.textContent = '';
         });
     }

    if (submitAnswerButton) {
        submitAnswerButton.addEventListener('click', submitAnswer);
    }

    if (nextQuestionButton) {
        nextQuestionButton.addEventListener('click', () => {
            resultContainerElem.style.display = 'none';
            fetchQuestion();
        });
    }
    
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('accessToken');
            window.location.href = '/login';
        });
    }

    // Initial actions
    fetchExamTypes(); // Load exam types when page loads
    // Question area is hidden until an exam is started
});

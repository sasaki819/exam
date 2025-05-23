document.addEventListener('DOMContentLoaded', () => {
    const problemStatementElem = document.getElementById('problem-statement');
    const optionsContainerElem = document.getElementById('options-container');
    const submitAnswerButton = document.getElementById('submit-answer-button');
    const resultContainerElem = document.getElementById('result-container');
    const correctStatusElem = document.getElementById('correct-status');
    const correctOptionElem = document.getElementById('correct-option');
    const explanationTextElem = document.getElementById('explanation-text');
    const nextQuestionButton = document.getElementById('next-question-button');
    const examErrorMessage = document.getElementById('exam-error-message');
    const logoutLink = document.getElementById('logout-link');

    let currentQuestionId = null;

    function getAuthHeaders(isPost = false) {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/login'; // Redirect if no token
            return null;
        }
        const headers = { 'Authorization': 'Bearer ' + token };
        if (isPost) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    }

    async function fetchQuestion() {
        examErrorMessage.textContent = '';
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            const response = await fetch('/questions/next/', { method: 'GET', headers: headers });

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
                if (response.status === 404) { // No more questions
                     problemStatementElem.textContent = "Congratulations! No more questions available.";
                }
                return;
            }

            const question = await response.json();
            currentQuestionId = question.id;
            problemStatementElem.textContent = question.problem_statement;
            
            optionsContainerElem.innerHTML = ''; // Clear previous options
            for (let i = 1; i <= 4; i++) {
                const optionKey = `option_${i}`;
                if (question[optionKey]) {
                    const radioInput = document.createElement('input');
                    radioInput.type = 'radio';
                    radioInput.id = `option${i}`;
                    radioInput.name = 'answer';
                    radioInput.value = i; // Value is the option number

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

    if (submitAnswerButton) {
        submitAnswerButton.addEventListener('click', submitAnswer);
    }

    if (nextQuestionButton) {
        nextQuestionButton.addEventListener('click', () => {
            resultContainerElem.style.display = 'none'; // Hide previous result
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

    // Initial question load
    fetchQuestion();
});

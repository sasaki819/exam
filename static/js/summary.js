document.addEventListener('DOMContentLoaded', async () => {
    const summaryErrorMessage = document.getElementById('summary-error-message');
    const totalUniqueQuestionsElem = document.getElementById('total-unique-questions');
    const totalAnswersSubmittedElem = document.getElementById('total-answers-submitted');
    const totalCorrectAnswersElem = document.getElementById('total-correct-answers');
    const totalIncorrectAnswersElem = document.getElementById('total-incorrect-answers');
    const correctAnswerRateElem = document.getElementById('correct-answer-rate');
    const questionPerformanceListElem = document.getElementById('question-performance-list');
    const logoutLink = document.getElementById('logout-link');

    const examTypeDropdown = document.getElementById('summary-exam-type-dropdown');
    const summaryFilterHeading = document.getElementById('summary-filter-heading');
    
    let allExamTypes = [];

    function getAuthHeaders() {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/login';
            return null;
        }
        return { 'Authorization': 'Bearer ' + token };
    }

    async function fetchExamTypesForFilter() {
        const headers = getAuthHeaders();
        if (!headers) return;
        try {
            const response = await fetch('/exam-types/', { headers });
            if (!response.ok) {
                if (response.status === 401) window.location.href = '/login';
                throw new Error('Failed to load exam types for filter.');
            }
            allExamTypes = await response.json();
            populateExamTypeFilterDropdown(allExamTypes);
        } catch (error) {
            console.error('Error fetching exam types for filter:', error);
            summaryErrorMessage.textContent = error.message || 'Could not load exam types for filter.';
        }
    }

    function populateExamTypeFilterDropdown(examTypes) {
        // The "All Exam Types" option is already in HTML
        examTypes.forEach(et => {
            const option = document.createElement('option');
            option.value = et.id;
            option.textContent = et.name;
            examTypeDropdown.appendChild(option);
        });
    }

    async function fetchSummary(examTypeId = '') {
        summaryErrorMessage.textContent = '';
        const headers = getAuthHeaders();
        if (!headers) return;

        let url = '/summary/';
        if (examTypeId) {
            url += `?exam_type_id=${examTypeId}`;
        }

        try {
            const response = await fetch(url, { method: 'GET', headers: headers });

            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login';
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                summaryErrorMessage.textContent = errorData.detail || 'Failed to load summary data.';
                clearSummaryDisplay(); // Clear previous data on error
                return;
            }

            const data = await response.json();
            displaySummary(data);
            
            // Update heading
            if (examTypeId) {
                const selectedExam = allExamTypes.find(et => et.id == examTypeId);
                summaryFilterHeading.textContent = selectedExam ? `Summary for ${selectedExam.name}` : `Summary for Exam ID ${examTypeId}`;
            } else {
                summaryFilterHeading.textContent = 'Overall Summary (All Exam Types)';
            }

        } catch (error) {
            console.error('Error fetching summary:', error);
            summaryErrorMessage.textContent = 'An error occurred while fetching summary data.';
            clearSummaryDisplay();
        }
    }
    
    function clearSummaryDisplay() {
         totalUniqueQuestionsElem.textContent = 'N/A';
         totalAnswersSubmittedElem.textContent = 'N/A';
         totalCorrectAnswersElem.textContent = 'N/A';
         totalIncorrectAnswersElem.textContent = 'N/A';
         correctAnswerRateElem.textContent = 'N/A';
         questionPerformanceListElem.innerHTML = '<li>Error loading data or no data available.</li>';
    }

    function displaySummary(data) {
        const stats = data.summary_stats;
        totalUniqueQuestionsElem.textContent = stats.total_unique_questions_attempted;
        totalAnswersSubmittedElem.textContent = stats.total_answers_submitted;
        totalCorrectAnswersElem.textContent = stats.total_correct_answers;
        totalIncorrectAnswersElem.textContent = stats.total_incorrect_answers;
        correctAnswerRateElem.textContent = (stats.correct_answer_rate * 100).toFixed(2);

        questionPerformanceListElem.innerHTML = ''; // Clear previous list
        if (data.question_performance.length === 0) {
            questionPerformanceListElem.innerHTML = '<li>No question performance data available for this filter.</li>';
            return;
        }
        data.question_performance.forEach(item => {
            const listItem = document.createElement('li');
            listItem.innerHTML = `
                <strong>Question ID ${item.question_id}:</strong> "${item.problem_statement.substring(0, 50)}..."<br>
                Attempted: ${item.times_answered}, Correct: ${item.times_correct}, Incorrect: ${item.times_incorrect}
            `;
            questionPerformanceListElem.appendChild(listItem);
        });
    }

    if (examTypeDropdown) {
        examTypeDropdown.addEventListener('change', (event) => {
            fetchSummary(event.target.value);
        });
    }
    
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('accessToken');
            window.location.href = '/login';
        });
    }

    // Initial Load
    async function initialLoad() {
        await fetchExamTypesForFilter(); // Load exam types for the filter first
        fetchSummary(); // Then load the initial overall summary
    }
    initialLoad();
});

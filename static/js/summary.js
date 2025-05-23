document.addEventListener('DOMContentLoaded', () => {
    const totalUniqueQuestionsAttemptedElem = document.getElementById('total-unique-questions-attempted');
    const totalAnswersSubmittedElem = document.getElementById('total-answers-submitted');
    const totalCorrectAnswersElem = document.getElementById('total-correct-answers');
    const totalIncorrectAnswersElem = document.getElementById('total-incorrect-answers');
    const correctAnswerRateElem = document.getElementById('correct-answer-rate');
    
    const performanceTbody = document.getElementById('question-performance-tbody');
    const performanceLoadingMsg = document.getElementById('performance-loading-message');
    const summaryErrorMessage = document.getElementById('summary-error-message');
    const logoutLinkSummary = document.getElementById('logout-link-summary');

    function getAuthHeaders() {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/login'; // Redirect if no token
            return null;
        }
        return { 'Authorization': 'Bearer ' + token };
    }

    async function fetchSummaryData() {
        summaryErrorMessage.textContent = '';
        const headers = getAuthHeaders();
        if (!headers) return;

        try {
            const response = await fetch('/summary/', { method: 'GET', headers: headers });

            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login';
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                summaryErrorMessage.textContent = errorData.detail || 'Failed to load summary data.';
                performanceLoadingMsg.textContent = 'Could not load performance data.';
                return;
            }

            const data = await response.json();
            
            // Populate summary stats
            const stats = data.summary_stats;
            totalUniqueQuestionsAttemptedElem.textContent = stats.total_unique_questions_attempted;
            totalAnswersSubmittedElem.textContent = stats.total_answers_submitted;
            totalCorrectAnswersElem.textContent = stats.total_correct_answers;
            totalIncorrectAnswersElem.textContent = stats.total_incorrect_answers;
            correctAnswerRateElem.textContent = (stats.correct_answer_rate * 100).toFixed(2);

            // Populate question performance table
            performanceTbody.innerHTML = ''; // Clear previous rows
            if (data.question_performance && data.question_performance.length > 0) {
                data.question_performance.forEach(perf => {
                    const row = performanceTbody.insertRow();
                    row.insertCell().textContent = perf.question_id;
                    row.insertCell().textContent = perf.problem_statement;
                    row.insertCell().textContent = perf.times_answered;
                    row.insertCell().textContent = perf.times_correct;
                    row.insertCell().textContent = perf.times_incorrect;
                });
                performanceLoadingMsg.style.display = 'none';
            } else {
                performanceLoadingMsg.textContent = 'No per-question performance data available.';
            }

        } catch (error) {
            console.error('Error fetching summary data:', error);
            summaryErrorMessage.textContent = 'An error occurred while fetching summary data.';
            performanceLoadingMsg.textContent = 'Error loading performance data.';
        }
    }
    
    if (logoutLinkSummary) {
        logoutLinkSummary.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('accessToken');
            window.location.href = '/login';
        });
    }

    // Initial data load
    fetchSummaryData();
});

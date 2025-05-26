document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const loginErrorMessage = document.getElementById('login-error-message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            loginErrorMessage.textContent = ''; // Clear previous errors
            loginErrorMessage.style.display = 'none'; // Hide error message area

            const username = loginForm.username.value;
            const password = loginForm.password.value;

            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/auth/token', { // Adjusted to /auth/token
                    method: 'POST',
                    body: formData, 
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.access_token) {
                        localStorage.setItem('accessToken', data.access_token);
                        window.location.href = '/exam'; // Adjusted to /exam
                    } else {
                        loginErrorMessage.style.display = 'block'; // Show error
                        loginErrorMessage.textContent = 'Login successful, but no token received.';
                    }
                } else {
                    const errorData = await response.json();
                    loginErrorMessage.style.display = 'block'; // Show error
                    loginErrorMessage.textContent = errorData.detail || 'Login failed. Please check your credentials.';
                }
            } catch (error) {
                console.error('Login error:', error);
                loginErrorMessage.style.display = 'block'; // Show error
                loginErrorMessage.textContent = 'An error occurred during login. Please try again.';
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const registerButton = document.getElementById('registerButton');

    function register() {
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('registerConfirmPassword').value;

        if (password !== confirmPassword) {
            alert("Passwords do not match.");
            return;
        }

        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${username}&password=${password}`,
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Registration failed');
            }
        })
        .then(data => {
            if (data.success) {
                alert('Registration successful! Please log in.');
                window.location.href = '/'; // Redirect to login page
            } else {
                alert(data.message || 'Registration failed');
            }
        })
        .catch(error => {
            console.error('Error during registration:', error);
            alert('Registration failed. Please try again.');
        });
    }

    registerButton.addEventListener('click', register);
});
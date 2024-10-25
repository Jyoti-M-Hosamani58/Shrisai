// loginHandler.js

// Assuming you have a form with an ID of "loginForm"
document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    const email = document.getElementById('emailInput').value; // Get the email input value

    // Perform your AJAX login request
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }), // Send email in request body
    })
    .then(response => {
        if (response.ok) {
            return response.json(); // Assuming response contains user data
        }
        throw new Error('Login failed');
    })
    .then(data => {
        // Call handleLogin to store the email in localStorage
        handleLogin(email);

        // Optionally redirect or update UI based on successful login
        window.location.href = '/branch_home'; // Redirect to branch home
    })
    .catch(error => {
        console.error(error); // Handle error
    });
});

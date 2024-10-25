// On login
function login(email) {
    // Simulate a login
    sessionStorage.setItem('userEmail', email);
    // Additional login logic...
}

// On page load
window.onload = function() {
    const currentUserEmail = sessionStorage.getItem('userEmail');
    if (currentUserEmail) {
        // Display current user information
        console.log("Logged in as: " + currentUserEmail);
    } else {
        // Handle not logged in state
        console.log("No user is logged in.");
    }
}

// Example: Call login with different emails
// login('user1@example.com'); // For Tab 1
// login('user2@example.com'); // For Tab 2


// Function to handle logout
function logout() {
    // Clear the session storage or relevant session data
    const tabId = localStorage.getItem('tabId');
    localStorage.removeItem(`email_${tabId}`); // Remove the email for this tab
    localStorage.removeItem('tabId'); // Clear the tabId as well

    // Redirect to the logout URL
    window.location.href = logoutUrl; // Ensure logoutUrl is defined globally
}



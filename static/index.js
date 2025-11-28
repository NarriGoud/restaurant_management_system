document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('.login-form');
    // Set the base URL for your FastAPI backend
    // FIX: Changed absolute URL to a RELATIVE PATH to prevent hostname/IP mismatch issues
    const API_BASE_URL = '/api/login'; 

    // --- EXISTING LOGIN FORM SUBMISSION LOGIC ---
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            const submitButton = event.submitter;
            // The data-portal attribute gives the portal (e.g., "Admin", "Cashier")
            const portalType = submitButton.getAttribute('data-portal');
            // Get values directly from the input fields
            const emailInput = form.querySelector('input[name="email"]').value;
            const passwordInput = form.querySelector('input[name="password"]').value;

            const loginPayload = {
                // Backend expects lowercase (e.g., "admin")
                portal: portalType.toLowerCase(),
                email: emailInput,
                password: passwordInput
            };

            submitButton.disabled = true;
            submitButton.textContent = 'Logging In...';

            // --- FETCH API CALL TO FASTAPI ---
            fetch(API_BASE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginPayload),
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.detail || 'Login failed due to server error.');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Login successful:', data);
                
                // === NEW CRITICAL LOGIC: Store user info locally for dashboard display ===
                // Data from main.py response: data.name and data.portal
                localStorage.setItem('userName', data.name);
                localStorage.setItem('userPortal', data.portal);

                // === REDIRECTION LOGIC ===
                // Redirects based on the portal returned by the backend (e.g., 'admin_dashboard.html')
                window.location.href = `/${data.portal.toLowerCase()}_dashboard.html`;

            })
            .catch(error => {
                // Handle network errors or specific API error messages
                alert(error.message);
                console.error('Login Error:', error);
            })
            .finally(() => {
                // Re-enable button on error or successful redirection attempt (before actual navigation)
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = `Login as ${portalType}`;
                }
            });
            // --- END FETCH API CALL ---
        });
    });
    // --- END EXISTING LOGIN FORM SUBMISSION LOGIC ---


    // 🔥 Mobile Tab Logic for Switching Portal Cards
    const tabButtons = document.querySelectorAll('.mobile-tab-nav .tab-btn');
    const portalCards = document.querySelectorAll('.portal-card');

    // Attach event listeners only if mobile navigation tabs are present
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Get the data-portal attribute (e.g., 'admin', 'cashier')
                const targetPortal = e.target.getAttribute('data-portal').toLowerCase();

                // 1. Update active tab style
                tabButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');

                // 2. Show/Hide portal cards
                portalCards.forEach(card => {
                    // Check if this card's ID matches the clicked portal
                    const cardId = card.id.replace('-portal-card', '');
                    if (cardId === targetPortal) {
                        card.classList.add('active-mobile-tab');
                    } else {
                        card.classList.remove('active-mobile-tab');
                    }
                });
            });
        });
    }
    // 🔥 END NEW MOBILE TAB LOGIC
    
});
// OTP form is always visible now, no need to manipulate display
document.addEventListener('DOMContentLoaded', function() {
    // Handle "Get OTP" button click
    const getOtpBtn = document.getElementById('getOtpBtn');
    const emailForm = document.querySelector('form[method="post"]:not([action])'); // Form without action (email form)
    
    if (getOtpBtn && emailForm) {
        getOtpBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get email value
            const emailInput = document.getElementById('email');
            if (emailInput && emailInput.value.trim()) {
                // Submit the email form to request OTP
                emailForm.submit();
            } else {
                alert('Please enter your email address first.');
                if (emailInput) emailInput.focus();
            }
        });
    }
    
    // Focus on OTP input when OTP is sent
    const flashMessages = document.querySelector('.flash-messages');
    if (flashMessages && flashMessages.textContent.includes('OTP sent')) {
        const otpInput = document.getElementById('otp');
        if (otpInput) {
            otpInput.focus();
        }
    }
});

// Function for inline OTP button (called from both login and registration)
function getOTPFromEmailForm() {
    const emailForm = document.querySelector('form[method="post"]:not([action])'); // Form without action (email form)
    const emailInput = document.getElementById('email');
    
    if (emailInput && emailInput.value.trim()) {
        // Submit the email form to request OTP
        emailForm.submit();
    } else {
        alert('Please enter your email address first.');
        if (emailInput) emailInput.focus();
    }
}

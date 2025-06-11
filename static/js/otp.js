// OTP form is always visible now, no need to manipulate display
document.addEventListener('DOMContentLoaded', function() {
    // Code is kept simple as the OTP form should always be visible
    // No manipulation of visibility is needed
    
    // We can still respond to flash messages if needed
    const flashMessages = document.querySelector('.flash-messages');
    if (flashMessages && flashMessages.textContent.includes('OTP sent')) {
        // Focus on OTP input for better user experience
        const otpInput = document.getElementById('otp');
        if (otpInput) {
            otpInput.focus();
        }
    }
});

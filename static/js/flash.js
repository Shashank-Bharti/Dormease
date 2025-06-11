// Handle flash messages
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelector('.flash-messages');
    
    if (flashMessages) {
        // Show flash messages
        flashMessages.style.display = 'block';
        
        // Auto-hide flash messages after 5 seconds
        setTimeout(function() {
            flashMessages.classList.add('hide');
            setTimeout(function() {
                flashMessages.style.display = 'none';
            }, 500); // Match this to the animation duration
        }, 5000);
    }
});

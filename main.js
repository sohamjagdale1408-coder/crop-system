document.addEventListener('DOMContentLoaded', () => {
    // Dismiss flash messages
    const closeButtons = document.querySelectorAll('.close-flash');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const flashMessage = this.closest('.flash');
            flashMessage.style.opacity = '0';
            setTimeout(() => {
                flashMessage.remove();
            }, 300);
        });
    });

    // Auto-dismiss flash messages after 5 seconds
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            if (flash.parentNode) {
                flash.style.opacity = '0';
                setTimeout(() => {
                    flash.remove();
                }, 300);
            }
        }, 5000);
    });
});

/**
 * Convert UTC timestamps to local time
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with the data-utc-date attribute
    const utcDateElements = document.querySelectorAll('[data-utc-date]');
    
    utcDateElements.forEach(function(element) {
        const utcDateStr = element.getAttribute('data-utc-date');
        if (utcDateStr) {
            const date = new Date(utcDateStr);
            
            // Get the format from data attribute or use default
            const format = element.getAttribute('data-date-format') || 'full';
            
            let formattedDate;
            if (format === 'date') {
                // Date only: Feb 5, 2023
                formattedDate = date.toLocaleDateString();
            } else if (format === 'time') {
                // Time only: 14:30:45
                formattedDate = date.toLocaleTimeString();
            } else if (format === 'datetime') {
                // Date and time: Feb 5, 2023, 14:30
                formattedDate = date.toLocaleDateString() + ' ' + 
                                date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else {
                // Full date and time (default)
                formattedDate = date.toLocaleString();
            }
            
            // Update the element's text content
            element.textContent = formattedDate;
        }
    });
});
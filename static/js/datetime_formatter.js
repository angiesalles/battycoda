/**
 * Convert UTC timestamps to local time
 */
function formatDateTimeElements(container = document) {
    // Find all elements with the data-utc-date attribute in the given container
    const utcDateElements = container.querySelectorAll('[data-utc-date]');
    
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
}

// Format dates on page load
document.addEventListener('DOMContentLoaded', function() {
    formatDateTimeElements();
});

// Make the function globally available for AJAX content
window.formatDateTimeElements = formatDateTimeElements;
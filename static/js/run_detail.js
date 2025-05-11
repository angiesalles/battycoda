// Run Detail Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh progress information for in-progress runs
    const statusBadge = document.querySelector('.badge');
    
    if (statusBadge && statusBadge.classList.contains('bg-info')) {
        const runId = document.getElementById('run-id').value;
        const progressBar = document.querySelector('.progress-bar');
        
        const refreshInterval = setInterval(function() {
            fetch(`/automation/runs/${runId}/status/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        progressBar.style.width = `${data.progress}%`;
                        progressBar.setAttribute('aria-valuenow', data.progress);
                        progressBar.textContent = `${data.progress.toFixed(1)}%`;
                        
                        if (data.status !== 'in_progress') {
                            clearInterval(refreshInterval);
                            window.location.reload(); // Refresh when status changes
                        }
                    }
                });
        }, 3000); // Check every 3 seconds
    }
    
    // Search functionality for results table
    const searchInput = document.getElementById('resultsSearch');
    const resultsTable = document.getElementById('resultsTable');
    
    if (searchInput && resultsTable) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = resultsTable.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                const display = text.includes(searchTerm) ? '' : 'none';
                row.style.display = display;
            });
        });
    }
    
    // Highlight highest probability in each row
    document.querySelectorAll('tbody tr').forEach(row => {
        let highestValue = 0;
        let highestCell = null;
        
        // Find the highest probability cell
        row.querySelectorAll('.probability-cell').forEach(cell => {
            const value = parseFloat(cell.dataset.value);
            if (value > highestValue) {
                highestValue = value;
                highestCell = cell;
            }
        });
        
        // Apply highlighting to the highest probability cell
        if (highestCell) {
            // Style the progress bar
            const progressBar = highestCell.querySelector('.progress-bar');
            progressBar.classList.remove('bg-info');
            progressBar.classList.add('bg-success');
            
            // Make the value text bold and slightly larger
            highestCell.classList.add('fw-bold');
            
            // Add a highlight effect to the entire cell
            highestCell.style.backgroundColor = 'rgba(40, 167, 69, 0.1)'; // Light green background
            highestCell.style.borderLeft = '3px solid #28a745'; // Green left border
            
            // Make the value more visible
            const valueSpan = highestCell.querySelector('span');
            valueSpan.style.color = '#28a745'; // Green text
            valueSpan.style.fontSize = '1.05em'; // Slightly larger
            
            // Add a "Highest Probability" tooltip
            highestCell.setAttribute('title', 'Highest Probability');
            highestCell.style.cursor = 'help';
        }
    });
});
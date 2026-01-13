// Upload progress tracking
            }
            
            // Check pickle file
            if (pickleFileInput && pickleFileInput.files.length > 0) {
                totalFileSize += pickleFileInput.files[0].size;
                fileCount++;
                filenames.push(pickleFileInput.files[0].name);
            }
        }
        
        // Only show progress if at least one file is selected
        if (fileCount > 0) {
            const totalSizeMB = (totalFileSize / (1024 * 1024)).toFixed(2);
            
            // Show full file list for small number of files, or summary for many files
            let fileListHtml = '';
            const maxDisplayFiles = 10;
            
            if (filenames.length <= maxDisplayFiles) {
                fileListHtml = filenames.map(name => `<span class="badge bg-info mr-2 mb-1">${name}</span>`).join('');
            } else {
                // Show the first few files with a count of remaining
                const displayedFiles = filenames.slice(0, maxDisplayFiles);
                const remainingCount = filenames.length - maxDisplayFiles;
                fileListHtml = displayedFiles.map(name => `<span class="badge bg-info mr-2 mb-1">${name}</span>`).join('') +
                    `<span class="badge bg-secondary">+${remainingCount} more file${remainingCount > 1 ? 's' : ''}</span>`;
            }
            
            statusText.innerHTML = `
                <div class="mb-2">Selected ${fileCount} file${fileCount > 1 ? 's' : ''} (${totalSizeMB} MB total)</div>
                <div class="file-badges-container">${fileListHtml}</div>
            `;
            progressContainer.classList.remove('d-none');
        } else {
            progressContainer.classList.add('d-none');
        }
    }
    
    // Cancel button functionality
    if (cancelButton) {
        cancelButton.addEventListener('click', function() {
            if (xhr && xhr.readyState !== 4) {
                xhr.abort();
                statusText.textContent = 'Upload cancelled';
                progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
                progressBar.classList.add('bg-warning');
            }
        });
    }
    
    form.addEventListener('submit', function(e) {
        // Different validation based on form type
        if (isBatchUpload) {
            // Batch upload form - just need WAV files
            if (!wavFilesInput || wavFilesInput.files.length === 0) {
                // Let the normal form submission handle validation errors
                return;
            }
        } else {
            // Single upload form - need both WAV and pickle files
            if (!wavFileInput || !pickleFileInput || 
                wavFileInput.files.length === 0 || pickleFileInput.files.length === 0) {
                // Let the normal form submission handle validation errors
                return;
            }
        }
        
        e.preventDefault();
        
        // Update UI to show we're starting
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.classList.remove('bg-success', 'bg-danger', 'bg-warning');
        progressBar.classList.add('progress-bar-striped', 'progress-bar-animated', 'bg-primary');
        statusText.textContent = 'Preparing files for upload...';
        
        xhr = new XMLHttpRequest();
        const formData = new FormData(form);
        
        // Setup progress tracking
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressBar.textContent = percentComplete + '%';
                progressBar.setAttribute('aria-valuenow', percentComplete);
                
                if (percentComplete < 100) {
                    statusText.textContent = `Uploading files: ${percentComplete}% (${Math.round(e.loaded / 1048576)}MB / ${Math.round(e.total / 1048576)}MB)`;

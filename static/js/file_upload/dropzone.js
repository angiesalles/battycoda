// Dropzone configuration
        
        // Handle file selection for either file input
        wavFileInput.addEventListener('change', updateFilesInfo);
        pickleFileInput.addEventListener('change', updateFilesInfo);
    }
    
    function setupDropzone(fileInput) {
        const container = fileInput.parentElement;
        const dropArea = document.createElement('div');
        dropArea.className = 'file-dropzone p-4 mb-3 text-center border border-secondary rounded';
        
        // Change wording for multiple files
        const isMultiple = fileInput.multiple;
        const uploadText = isMultiple ? 'Drag & drop your files here or click to browse' : 'Drag & drop your file here or click to browse';
        const selectedText = isMultiple ? 'Selected files:' : 'Selected file:';
        
        dropArea.innerHTML = `
            <div class="file-icon mb-2"><i class="fas fa-file-upload fa-2x"></i></div>
            <p>${uploadText}</p>
            <small class="text-muted">${selectedText} <span class="selected-filename">None</span></small>
        `;
        
        // Insert dropzone before fileInput
        fileInput.parentNode.insertBefore(dropArea, fileInput);
        
        // Hide the original input
        fileInput.style.display = 'none';
        
        // Click on dropzone should trigger file input
        dropArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Update dropzone when file is selected
        fileInput.addEventListener('change', function() {
            const filenameSpan = dropArea.querySelector('.selected-filename');
            if (this.files.length > 0) {
                if (isMultiple && this.files.length > 1) {
                    // Show multiple file count for multiple file inputs
                    const totalSize = Array.from(this.files).reduce((sum, file) => sum + file.size, 0);
                    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
                    filenameSpan.textContent = `${this.files.length} files selected (${totalSizeMB} MB)`;
                } else {
                    // Show single filename for single file input or when only one file is selected
                    const fileName = this.files[0].name;
                    const fileSize = (this.files[0].size / (1024 * 1024)).toFixed(2);
                    filenameSpan.textContent = `${fileName} (${fileSize} MB)`;
                }
                dropArea.classList.add('border-success');
                dropArea.classList.remove('border-secondary');
            } else {
                filenameSpan.textContent = 'None';
                dropArea.classList.remove('border-success');
                dropArea.classList.add('border-secondary');
            }
        });
        
        // Handle drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Handle visual feedback during drag
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropArea.classList.add('border-primary');
            dropArea.classList.add('bg-dark');
        }
        
        function unhighlight() {
            dropArea.classList.remove('border-primary');
            dropArea.classList.remove('bg-dark');
        }
        
        // Handle the actual drop
        dropArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                // Handle multiple files for multiple inputs
                if (fileInput.multiple) {
                    // Create a new DataTransfer object to build the file list
                    const dataTransfer = new DataTransfer();
                    
                    // Add each dropped file to the DataTransfer
                    for (let i = 0; i < files.length; i++) {
                        dataTransfer.items.add(files[i]);
                    }
                    
                    // Assign the files to the input
                    fileInput.files = dataTransfer.files;
                } else {
                    // For single file inputs, just use the first file
                    const singleFileTransfer = new DataTransfer();
                    singleFileTransfer.items.add(files[0]);
                    fileInput.files = singleFileTransfer.files;
                }
                
                // Trigger change event manually
                const event = new Event('change');
                fileInput.dispatchEvent(event);
            }
        });
    }
    
    function updateFilesInfo() {
        // Reset counts
        totalFileSize = 0;
        fileCount = 0;
        filenames = [];
        
        if (isBatchUpload) {
            // Batch upload form - handle multiple files
            // Check WAV files
            if (wavFilesInput && wavFilesInput.files.length > 0) {
                for (let i = 0; i < wavFilesInput.files.length; i++) {
                    totalFileSize += wavFilesInput.files[i].size;
                    fileCount++;
                    filenames.push(wavFilesInput.files[i].name);
                }
            }
            
            // Check pickle files
            if (pickleFilesInput && pickleFilesInput.files.length > 0) {
                for (let i = 0; i < pickleFilesInput.files.length; i++) {
                    totalFileSize += pickleFilesInput.files[i].size;
                    fileCount++;
                    filenames.push(pickleFilesInput.files[i].name);
                }
            }
        } else {
            // Single file upload form
            // Check WAV file
            if (wavFileInput && wavFileInput.files.length > 0) {
                totalFileSize += wavFileInput.files[0].size;
                fileCount++;
                filenames.push(wavFileInput.files[0].name);

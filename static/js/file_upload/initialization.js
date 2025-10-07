// File upload initialization
document.addEventListener('DOMContentLoaded', function() {
    // Set a flag to let other scripts know we've initialized
    window.advancedUploadInitialized = true;
    
    // Setup persistent logging
    const debugLogs = localStorage.getItem('debugLogs') || '';
    if (debugLogs) {
        console.log('PREVIOUS SESSION LOGS:');
        console.log(debugLogs);
        
        // Create debug panel if not exists
        if (!document.getElementById('debug-panel')) {
            const debugPanel = document.createElement('div');
            debugPanel.id = 'debug-panel';
            debugPanel.style.position = 'fixed';
            debugPanel.style.bottom = '10px';
            debugPanel.style.right = '10px';
            debugPanel.style.width = '300px';
            debugPanel.style.maxHeight = '200px';
            debugPanel.style.overflow = 'auto';
            debugPanel.style.backgroundColor = 'rgba(0,0,0,0.8)';
            debugPanel.style.color = '#0f0';
            debugPanel.style.padding = '10px';
            debugPanel.style.borderRadius = '5px';
            debugPanel.style.zIndex = '10000';
            debugPanel.style.fontFamily = 'monospace';
            debugPanel.style.fontSize = '10px';
            debugPanel.innerHTML = `
                <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                    <strong>Debug Log</strong>
                    <button id="clear-logs" style="background:none;border:none;color:red;cursor:pointer;font-size:10px;">Clear</button>
                </div>
                <div id="debug-log-content">${debugLogs.replace(/\n/g, '<br>')}</div>
            `;
            document.body.appendChild(debugPanel);
            
            // Add clear logs handler
            document.getElementById('clear-logs').addEventListener('click', function() {
                localStorage.removeItem('debugLogs');
                document.getElementById('debug-log-content').innerHTML = '';
            });
        }
    }
    
    // Override console.log
    const originalLog = console.log;
    console.log = function() {
        // Call original console.log
        originalLog.apply(console, arguments);
        
        // Format the log message
        const msg = Array.from(arguments).map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
        
        // Add to localStorage
        const logs = localStorage.getItem('debugLogs') || '';
        localStorage.setItem('debugLogs', logs + '\n' + msg);
        
        // Update debug panel if exists
        const logContent = document.getElementById('debug-log-content');
        if (logContent) {
            logContent.innerHTML += '<br>' + msg;
            logContent.scrollTop = logContent.scrollHeight;
        }
    };
    
    console.log('File upload script initialized');
    
    const form = document.querySelector('form[enctype="multipart/form-data"]');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressContainer = document.getElementById('upload-progress-container');
    const statusText = document.getElementById('upload-status');
    
    // Support both single file and multiple files upload forms
    // For single file uploads (task batch form)
    const wavFileInput = document.querySelector('input[type="file"][name="wav_file"]');
    const pickleFileInput = document.querySelector('input[type="file"][name="pickle_file"]');
    
    // For batch uploads (recordings batch upload)
    const wavFilesInput = document.querySelector('input[type="file"][name="wav_files"]');
    const pickleFilesInput = document.querySelector('input[type="file"][name="pickle_files"]');
    
    const cancelButton = document.getElementById('cancel-upload');
    let xhr;
    
    // If we don't have the necessary elements, skip initialization
    if (!form || !progressBar) {
        console.log("File upload initialization skipped - missing elements");
        return;
    }
    
    // Determine which form we're on - batch or single
    const isBatchUpload = wavFilesInput !== null;
    
    // Track total file size for both files
    let totalFileSize = 0;
    let fileCount = 0;
    let filenames = [];
    
    // Initialize dropzone styling for file inputs based on which form we're on
    if (isBatchUpload) {
        // For batch upload form
        setupDropzone(wavFilesInput);
        setupDropzone(pickleFilesInput);
        
        // Handle file selection for either file input
        wavFilesInput.addEventListener('change', updateFilesInfo);
        pickleFilesInput.addEventListener('change', updateFilesInfo);
    } else if (wavFileInput && pickleFileInput) {
        // For single file upload form
        setupDropzone(wavFileInput);
        setupDropzone(pickleFileInput);

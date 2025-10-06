/**
 * Task Annotation JavaScript
 * 
 * This file contains all the JavaScript functionality for the task annotation interface,
 * including spectrogram switching, channel toggling, form handling, and notifications.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize spectrogram viewer functionality
    initSpectrogramViewer();
    
    // Initialize form behavior
    initFormBehavior();
    
    // Check for batch switch notification
    checkBatchSwitchNotification();
});

/**
 * Initialize the spectrogram viewer with channel and view switching
 */
function initSpectrogramViewer() {
    // Find all UI elements needed
    const mainSpectrogram = document.getElementById('main-spectrogram');
    const detailViewBtn = document.getElementById('detail-view-btn');
    const overviewBtn = document.getElementById('overview-btn');
    const detailTicks = document.getElementById('detail-ticks');
    const overviewTicks = document.getElementById('overview-ticks');
    
    // Channel switching elements
    const channel1Btn = document.getElementById('channel-1-btn');
    const channel2Btn = document.getElementById('channel-2-btn');
    const channelToggle = document.getElementById('channel-toggle');
    const channelLabel = document.getElementById('channel-label');
    
    // Check for critical elements
    if (!mainSpectrogram || !detailViewBtn || !overviewBtn || !detailTicks || !overviewTicks) {
        console.error("Critical elements for spectrogram viewing are missing.");
        return;
    }
    
    let currentChannel = 0;
    // Determine initial state from which button is active
    let isOverview = overviewBtn.classList.contains('active');

    // Function to update spectrogram based on current settings
    function updateSpectrogram() {
        const key = `channel_${currentChannel}_${isOverview ? 'overview' : 'detail'}`;
        
        if (taskConfig.spectrogramUrls[key]) {
            // Update the image source
            mainSpectrogram.src = taskConfig.spectrogramUrls[key];
            
            // Update audio player
            updateAudioPlayer();
            
            // Update x-axis ticks
            if (isOverview) {
                detailTicks.classList.remove('active');
                overviewTicks.classList.add('active');
            } else {
                detailTicks.classList.add('active');
                overviewTicks.classList.remove('active');
            }
        } else {
            console.error("Spectrogram URL not found for key:", key);
        }
    }
    
    // Function to update audio player URL
    function updateAudioPlayer() {
        const audioPlayer = document.getElementById('audio-player');
        if (audioPlayer) {
            const overviewParam = isOverview ? 'True' : 'False';
            const cacheBuster = new Date().getTime();
            
            // Build audio URL with configuration variables
            audioPlayer.src = `${taskConfig.audioSnippetUrl}?wav_path=${encodeURIComponent(taskConfig.wavPath)}&call=0&channel=${currentChannel}&hash=${taskConfig.fileHash}&overview=${overviewParam}&onset=${taskConfig.onset}&offset=${taskConfig.offset}&loudness=1.0&t=${cacheBuster}`;
        }
    }
    
    // Set up event listeners
    detailViewBtn.addEventListener('click', function() {
        isOverview = false;
        // Update button styles
        detailViewBtn.classList.add('active');
        detailViewBtn.classList.remove('btn-outline-primary');
        detailViewBtn.classList.add('btn-primary');
        overviewBtn.classList.remove('active');
        overviewBtn.classList.remove('btn-primary');
        overviewBtn.classList.add('btn-outline-secondary');
        updateSpectrogram();
    });
    
    overviewBtn.addEventListener('click', function() {
        isOverview = true;
        // Update button styles
        overviewBtn.classList.add('active');
        overviewBtn.classList.remove('btn-outline-secondary');
        overviewBtn.classList.add('btn-primary');
        detailViewBtn.classList.remove('active');
        detailViewBtn.classList.remove('btn-primary');
        detailViewBtn.classList.add('btn-outline-secondary');
        updateSpectrogram();
    });
    
    // Set up channel buttons if they exist
    if (channel1Btn && channel2Btn) {
        channel1Btn.addEventListener('click', function() {
            currentChannel = 0;
            // Update button styles
            channel1Btn.classList.add('active', 'btn-primary');
            channel1Btn.classList.remove('btn-outline-secondary');
            channel2Btn.classList.remove('active', 'btn-primary');
            channel2Btn.classList.add('btn-outline-secondary');
            updateSpectrogram();
        });
        
        channel2Btn.addEventListener('click', function() {
            currentChannel = 1;
            // Update button styles
            channel2Btn.classList.add('active', 'btn-primary');
            channel2Btn.classList.remove('btn-outline-secondary');
            channel1Btn.classList.remove('active', 'btn-primary');
            channel1Btn.classList.add('btn-outline-secondary');
            updateSpectrogram();
        });
    }
    // Use the legacy toggle if it exists (we don't have it anymore)
    else if (channelToggle && channelLabel) {
        channelToggle.addEventListener('change', function() {
            currentChannel = this.checked ? 1 : 0;
            channelLabel.textContent = `Channel ${currentChannel + 1}`;
            updateSpectrogram();
        });
    }
    
    // Initialize on page load
    updateSpectrogram();
}

/**
 * Initialize form behavior for the task annotation
 */
function initFormBehavior() {
    // Previously handled the "Other" option which has been removed
    
    // Add any other form-related behavior here
}

/**
 * Check if we need to show a notification about switching batches
 */
function checkBatchSwitchNotification() {
    // Check if toastr is available
    if (typeof toastr !== 'undefined') {
        // Configure toastr
        toastr.options = {
            "closeButton": true,
            "positionClass": "toast-top-right",
            "preventDuplicates": true,
            "timeOut": "6000",
            "extendedTimeOut": "2000",
        };
        
        // Check if there's batch switch data in sessionStorage
        if (typeof batchSwitchData !== 'undefined' && batchSwitchData) {
            const fromBatchName = batchSwitchData.from_batch_name;
            const toBatchName = batchSwitchData.to_batch_name;
            const toBatchId = batchSwitchData.to_batch_id;
            
            // Create message with link to batch
            const batchLink = `<a href="/tasks/batches/${toBatchId}/" class="text-white text-decoration-underline">view batch</a>`;
            const message = `You completed all tasks in batch "${fromBatchName}" and are now working on "${toBatchName}" (${batchLink})`;
            
            // Show success notification
            toastr.success(message, 'Batch Completed!');
        }
    }
}
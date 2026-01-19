/**
 * Task Annotation JavaScript
 *
 * This file contains all the JavaScript functionality for the task annotation interface,
 * including spectrogram switching, channel toggling, form handling, and notifications.
 */

import { getJsonData } from './utils/page-data.js';
import { escapeHtml, validateUrl } from './utils/html.js';

// Get configuration from JSON script tags
const taskConfig = getJsonData('task-config-data');
const batchSwitchData = getJsonData('batch-switch-data');

/**
 * Initialize all task annotation functionality
 */
export function initialize() {
  // Initialize spectrogram viewer functionality
  initSpectrogramViewer();

  // Initialize form behavior
  initFormBehavior();

  // Check for batch switch notification
  checkBatchSwitchNotification();
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

/**
 * Initialize the spectrogram viewer with channel and view switching
 */
export function initSpectrogramViewer() {
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
    console.error('Critical elements for spectrogram viewing are missing.');
    return;
  }

  // Check that taskConfig was loaded
  if (!taskConfig) {
    console.error('Task configuration data not found.');
    return;
  }

  let currentChannel = 0;

  // Load user's saved view preference from localStorage
  const savedViewPreference = localStorage.getItem('taskAnnotationViewPreference');
  let isOverview;

  if (savedViewPreference !== null) {
    // Use saved preference
    isOverview = savedViewPreference === 'overview';
    // Update buttons to match saved preference
    if (isOverview) {
      overviewBtn.classList.add('active', 'btn-primary');
      overviewBtn.classList.remove('btn-outline-secondary');
      detailViewBtn.classList.remove('active', 'btn-primary');
      detailViewBtn.classList.add('btn-outline-primary');
    } else {
      detailViewBtn.classList.add('active', 'btn-primary');
      detailViewBtn.classList.remove('btn-outline-primary');
      overviewBtn.classList.remove('active', 'btn-primary');
      overviewBtn.classList.add('btn-outline-secondary');
    }
  } else {
    // Determine initial state from which button is active (template default)
    isOverview = overviewBtn.classList.contains('active');
  }

  // Function to update spectrogram based on current settings
  function updateSpectrogram() {
    // Build spectrogram URL with task ID and overview parameter
    const overviewParam = isOverview ? '1' : '0';
    const spectrogramUrl = `${taskConfig.spectrogramBaseUrl}?overview=${overviewParam}`;

    // Update the image source
    mainSpectrogram.src = spectrogramUrl;

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
  }

  // Function to update audio player URL
  function updateAudioPlayer() {
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
      const cacheBuster = new Date().getTime();

      // Build audio URL with configuration variables - always use False for overview (detail view audio)
      audioPlayer.src = `${taskConfig.audioSnippetUrl}?wav_path=${encodeURIComponent(taskConfig.wavPath)}&call=0&channel=${currentChannel}&hash=${taskConfig.fileHash}&overview=False&onset=${taskConfig.onset}&offset=${taskConfig.offset}&loudness=1.0&t=${cacheBuster}`;
    }
  }

  // Set up event listeners
  detailViewBtn.addEventListener('click', function () {
    isOverview = false;
    // Save preference to localStorage
    localStorage.setItem('taskAnnotationViewPreference', 'detail');
    // Update button styles
    detailViewBtn.classList.add('active');
    detailViewBtn.classList.remove('btn-outline-primary');
    detailViewBtn.classList.add('btn-primary');
    overviewBtn.classList.remove('active');
    overviewBtn.classList.remove('btn-primary');
    overviewBtn.classList.add('btn-outline-secondary');
    updateSpectrogram();
  });

  overviewBtn.addEventListener('click', function () {
    isOverview = true;
    // Save preference to localStorage
    localStorage.setItem('taskAnnotationViewPreference', 'overview');
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
    channel1Btn.addEventListener('click', function () {
      currentChannel = 0;
      // Update button styles
      channel1Btn.classList.add('active', 'btn-primary');
      channel1Btn.classList.remove('btn-outline-secondary');
      channel2Btn.classList.remove('active', 'btn-primary');
      channel2Btn.classList.add('btn-outline-secondary');
      updateSpectrogram();
    });

    channel2Btn.addEventListener('click', function () {
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
    channelToggle.addEventListener('change', function () {
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
export function initFormBehavior() {
  // Previously handled the "Other" option which has been removed
  // Add any other form-related behavior here
}

/**
 * Check if we need to show a notification about switching batches
 */
export function checkBatchSwitchNotification() {
  // Check if toastr is available
  if (typeof toastr !== 'undefined') {
    // Configure toastr
    toastr.options = {
      closeButton: true,
      positionClass: 'toast-top-right',
      preventDuplicates: true,
      timeOut: '6000',
      extendedTimeOut: '2000',
    };

    // Check if there's batch switch data
    if (batchSwitchData) {
      const fromBatchName = batchSwitchData.fromBatchName;
      const toBatchName = batchSwitchData.toBatchName;
      const toBatchUrl = batchSwitchData.toBatchUrl;
      const sameProject = batchSwitchData.sameProject;
      const projectName = batchSwitchData.projectName;

      // Validate URL and escape text content for XSS protection
      const safeUrl = validateUrl(toBatchUrl);
      const safeFromName = escapeHtml(fromBatchName);
      const safeToName = escapeHtml(toBatchName);

      // Create message with link to batch (only if URL is valid)
      const batchLink = safeUrl
        ? `<a href="${safeUrl}" class="text-white text-decoration-underline">view batch</a>`
        : '';
      let message = `You completed all tasks in batch "${safeFromName}" and are now working on "${safeToName}"`;
      if (batchLink) {
        message += ` (${batchLink})`;
      }

      // Add project context if switching within same project
      if (sameProject && projectName) {
        message += `<br><small>Continuing with project: ${escapeHtml(projectName)}</small>`;
      }

      // Show success notification
      toastr.success(message, 'Batch Completed!');
    }
  }
}

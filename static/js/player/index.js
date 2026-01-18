/**
 * BattyCoda Waveform Player - Main Entry Point
 *
 * This is the main entry point for the waveform player that exports the public API
 * and imports all required modules.
 */

import { WaveformPlayer } from './player.js';

// Global registry to expose player instances outside this module
if (window.players === undefined) {
  window.players = {};
}

/**
 * Initializes a waveform player for a recording
 * @param {string} containerId - ID of the container element
 * @param {number} recordingId - ID of the recording
 * @param {boolean} allowSelection - Whether to allow selecting regions
 * @param {boolean} showZoom - Whether to show zoom controls
 * @param {Array} [segmentsData] - Optional array of segments to display in the waveform
 * @param {Object} [urls] - URL templates for API endpoints
 * @param {string} [urls.waveformData] - URL template for waveform data
 * @param {string} [urls.spectrogramData] - URL template for spectrogram data
 */
export function initWaveformPlayer(
  containerId,
  recordingId,
  allowSelection,
  showZoom,
  segmentsData,
  urls
) {
  // Debug: Log what we receive
  console.log('initWaveformPlayer called with:', {
    containerId,
    recordingId,
    allowSelection,
    showZoom,
    segmentsData: segmentsData ? segmentsData.length : 'null',
    urls: urls || 'default',
  });

  // Create a new WaveformPlayer instance
  const player = new WaveformPlayer(
    containerId,
    recordingId,
    allowSelection,
    showZoom,
    segmentsData,
    urls
  );

  // Try to initialize spectrogram data from HDF5
  console.log('Attempting to load spectrogram data from HDF5');
  player.viewManager.initializeSpectrogramData().then((success) => {
    if (success) {
      console.log('Spectrogram data initialized successfully');
    } else {
      console.log('No spectrogram data available');
    }
  });

  // Register the player instance in the global registry
  window.players[containerId] = {
    getSelection: function () {
      return player.getSelection();
    },
    setSegments: function (newSegments) {
      player.setSegments(newSegments || []);
    },
    redrawSegments: function () {
      player.redrawSegments();
    },
    // View management functions
    setViewMode: function (mode) {
      player.viewManager.setViewMode(mode);
    },
    getViewMode: function () {
      return player.viewManager.getViewMode();
    },
    isSpectrogramAvailable: function () {
      return player.viewManager.isSpectrogramAvailable();
    },
    spectrogramDataRenderer: player.spectrogramDataRenderer, // Expose spectrogram data renderer for controls
    player: player, // Expose the underlying player directly
  };

  // Initialize the player
  player.initialize();
}

// Expose to window for Django template usage
window.initWaveformPlayer = initWaveformPlayer;

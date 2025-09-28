/**
 * BattyCoda Waveform Player - Main Entry Point
 * 
 * This is the main entry point for the waveform player that exports the public API
 * and imports all required modules.
 */

import { WaveformPlayer } from './player.js';

// Global registry to expose player instances outside this module
if (window.waveformPlayers === undefined) {
    window.waveformPlayers = {};
}

/**
 * Initializes a waveform player for a recording
 * @param {string} containerId - ID of the container element
 * @param {number} recordingId - ID of the recording
 * @param {boolean} allowSelection - Whether to allow selecting regions
 * @param {boolean} showZoom - Whether to show zoom controls
 * @param {Array} [segmentsData] - Optional array of segments to display in the waveform
 * @param {string} [spectrogramUrl] - Optional URL of the spectrogram image
 */
export function initWaveformPlayer(containerId, recordingId, allowSelection, showZoom, segmentsData, spectrogramUrl) {
    // Debug: Log what we receive
    console.log('initWaveformPlayer called with:', {
        containerId, 
        recordingId, 
        allowSelection, 
        showZoom, 
        segmentsData: segmentsData ? segmentsData.length : 'null',
        spectrogramUrl
    });
    
    // Create a new WaveformPlayer instance
    const player = new WaveformPlayer(containerId, recordingId, allowSelection, showZoom, segmentsData);
    
    // Initialize spectrogram if URL provided
    if (spectrogramUrl) {
        console.log('Initializing spectrogram with URL:', spectrogramUrl);
        player.viewManager.initializeSpectrogram(spectrogramUrl);
    } else {
        console.log('No spectrogram URL provided - spectrogramUrl is:', spectrogramUrl);
    }
    
    // Register the player instance in the global registry
    window.waveformPlayers[containerId] = {
        getSelection: function() {
            return player.getSelection();
        },
        setSegments: function(newSegments) {
            player.setSegments(newSegments || []);
        },
        redrawSegments: function() {
            player.redrawSegments();
        },
        // View management functions
        setViewMode: function(mode) {
            player.viewManager.setViewMode(mode);
        },
        getViewMode: function() {
            return player.viewManager.getViewMode();
        },
        isSpectrogramAvailable: function() {
            return player.viewManager.isSpectrogramAvailable();
        },
        initializeSpectrogram: function(url) {
            player.viewManager.initializeSpectrogram(url);
        },
        player: player // Expose the underlying player directly
    };
    
    // Initialize the player
    player.initialize();
}

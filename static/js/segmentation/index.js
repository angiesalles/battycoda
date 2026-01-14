/**
 * Segmentation module initialization
 *
 * This is the main entry point for the segmentation functionality.
 */

import { SegmentManager } from './segment_manager_simple.js';

// Initialize segmentation functionality
export function initSegmentation(options) {
  // Create a new SegmentManager instance
  const manager = new SegmentManager(options);

  // Expose the manager globally if needed
  if (typeof window !== 'undefined') {
    if (!window.battycoda) {
      window.battycoda = {};
    }
    if (!window.battycoda.segmentation) {
      window.battycoda.segmentation = {};
    }
    // Store by waveformId (the player ID) for consistency with onclick handlers
    const playerId = options.waveformId || 'segment-waveform';
    window.battycoda.segmentation[playerId] = manager;
  }

  return manager;
}

// Expose to window for Django template usage
window.initSegmentation = initSegmentation;

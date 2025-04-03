/**
 * Segmentation module initialization
 * 
 * This is the main entry point for the segmentation functionality.
 */

import { SegmentManager } from './segment_manager.js';

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
        window.battycoda.segmentation[options.containerId] = manager;
    }
    
    return manager;
}
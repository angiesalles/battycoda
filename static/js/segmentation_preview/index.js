/**
 * Segmentation Preview - Main Entry Point
 * Initializes the segmentation preview functionality
 */

import { initializePreviewHandler } from './preview_handler.js';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing segmentation preview...');
    initializePreviewHandler();
});
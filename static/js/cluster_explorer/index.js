/**
 * Cluster Explorer Module
 *
 * Interactive visualization and exploration of audio segment clusters using D3.js.
 * Allows users to explore clustering results, view segment details, and update labels.
 *
 * Dependencies:
 * - D3.js (loaded via CDN)
 * - jQuery (loaded via CDN)
 *
 * Components (to be converted to ES6 modules):
 * - visualization.js : Main D3 visualization rendering
 * - controls.js      : UI controls (point size, opacity, zoom)
 * - data_loader.js   : AJAX data loading for cluster/segment details
 * - interactions.js  : Click, hover, and selection handlers
 *
 * Usage:
 * Include this module on cluster exploration pages. The visualization
 * initializes automatically when the DOM is ready if the expected
 * elements are present (#cluster-visualization, etc).
 *
 * Global data expected:
 * - window.clusters: Array of cluster objects from Django template
 *
 * Note: The component files currently use global functions for compatibility
 * with Django templates. They will be converted to ES6 modules as part
 * of the module migration task. For now, they are loaded via script tags.
 */

// Placeholder for future ES6 module exports
// Once the component files are converted to ES6 modules, this file will:
// import { initializeVisualization } from './visualization.js';
// export { initializeVisualization };

console.log('Cluster explorer module entry point loaded');

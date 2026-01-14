/**
 * Cluster Mapping Module
 *
 * Interface for mapping audio clusters to call types. Enables drag-and-drop
 * assignment of clusters to known call types with confidence scores.
 *
 * Dependencies:
 * - jQuery (loaded via CDN)
 * - jQuery UI Sortable (for drag-and-drop)
 *
 * Components (to be converted to ES6 modules):
 * - initialization.js : Setup and existing mapping restoration
 * - drag_drop.js      : Drag-and-drop handling for cluster-to-call mapping
 * - filtering.js      : Call type filtering and search
 * - modal_handlers.js : Modal dialogs for confirmation and details
 *
 * Usage:
 * Include this module on cluster mapping pages. Initializes when DOM is ready
 * if the expected elements are present (.cluster-box, .mapping-container, etc).
 *
 * Global namespace:
 * - window.ClusterMapping: Contains mapping functions and state
 *
 * Note: The component files use IIFE pattern and attach to window.ClusterMapping.
 * They will be converted to proper ES6 modules as part of the module migration task.
 * For now, they are loaded via script tags in Django templates.
 */

// Placeholder for future ES6 module exports
// Once the component files are converted to ES6 modules, this file will:
// import { ClusterMapping } from './initialization.js';
// export { ClusterMapping };

console.log('Cluster mapping module entry point loaded');

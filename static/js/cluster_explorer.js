/**
 * Cluster Explorer - Module Loader
 *
 * This file has been refactored into smaller modules for better maintainability.
 * The modules are located in the cluster_explorer/ subdirectory:
 * - visualization.js: Main visualization rendering logic
 * - interactions.js: User interaction handlers
 * - data_loader.js: Data loading and processing
 * - controls.js: UI controls and AJAX operations
 *
 * This loader loads all modules in the correct order.
 */

(function() {
    const modules = [
        'cluster_explorer/visualization.js',
        'cluster_explorer/data_loader.js',
        'cluster_explorer/interactions.js',
        'cluster_explorer/controls.js'
    ];

    const basePath = document.currentScript.src.replace(/[^\/]*$/, '');

    modules.forEach(function(module) {
        const script = document.createElement('script');
        script.src = basePath + module;
        script.async = false; // Maintain order
        document.head.appendChild(script);
    });
})();

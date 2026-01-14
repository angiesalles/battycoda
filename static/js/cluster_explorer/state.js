/**
 * Cluster Explorer State Module
 *
 * Manages shared state for the cluster explorer.
 */

// Currently selected cluster ID
let selectedClusterId = null;

/**
 * Get the currently selected cluster ID
 * @returns {number|null} Selected cluster ID
 */
export function getSelectedClusterId() {
    return selectedClusterId;
}

/**
 * Set the selected cluster ID
 * @param {number|null} id - Cluster ID to select
 */
export function setSelectedClusterId(id) {
    selectedClusterId = id;
}

// D3 color scale for clusters
export const colorScale = window.d3 ? window.d3.scaleOrdinal(window.d3.schemeCategory10) : null;

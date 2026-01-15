/**
 * Cluster Explorer State Module
 *
 * Manages shared state for the cluster explorer.
 */

import { scaleOrdinal, schemeCategory10 } from 'd3';

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

// D3 color scale for clusters (now imported from npm module)
export const colorScale = scaleOrdinal(schemeCategory10);

/**
 * Cluster Explorer State Module
 *
 * Manages shared state for the cluster explorer.
 * All mutable state is encapsulated here to avoid polluting the global namespace.
 */

import { scaleOrdinal, schemeCategory10 } from 'd3';

// Currently selected cluster ID
let selectedClusterId = null;

// Cluster data array
let clusters = null;

// Whether this is a project-scoped clustering run
let isProjectScope = false;

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

/**
 * Get the clusters array
 * @returns {Array|null} Array of cluster objects
 */
export function getClusters() {
  return clusters;
}

/**
 * Set the clusters array
 * @param {Array} data - Array of cluster objects
 */
export function setClusters(data) {
  clusters = data;
}

/**
 * Get whether this is a project-scoped clustering run
 * @returns {boolean} True if project scope
 */
export function getIsProjectScope() {
  return isProjectScope;
}

/**
 * Set whether this is a project-scoped clustering run
 * @param {boolean} value - True if project scope
 */
export function setIsProjectScope(value) {
  isProjectScope = !!value;
}

/**
 * Reset all state (useful for testing and re-initialization)
 */
export function resetState() {
  selectedClusterId = null;
  clusters = null;
  isProjectScope = false;
}

// D3 color scale for clusters (now imported from npm module)
export const colorScale = scaleOrdinal(schemeCategory10);

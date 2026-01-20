/**
 * Cluster Explorer State Module
 *
 * Manages shared state for the cluster explorer using centralized state utilities.
 * All mutable state is encapsulated here to avoid polluting the global namespace.
 */

import { scaleOrdinal, schemeCategory10 } from 'd3';
import { createStateModule } from '../clustering/shared/create-state.js';
import {
  getJQuery as sharedGetJQuery,
  setJQuery as sharedSetJQuery,
  resetJQuery,
} from '../clustering/shared/jquery-utils.js';

/**
 * Cluster Explorer state configuration
 * Uses createStateModule for consistent getter/setter generation
 */
const state = createStateModule({
  selectedClusterId: null,
  clusters: null,
  isProjectScope: { value: false, boolean: true },
});

// Export generated getters/setters
export const {
  getSelectedClusterId,
  setSelectedClusterId,
  getClusters,
  setClusters,
  getIsProjectScope,
  setIsProjectScope,
} = state;

// Re-export shared jQuery utilities for backward compatibility
export const getJQuery = sharedGetJQuery;
export const setJQuery = sharedSetJQuery;

/**
 * Reset all state (useful for testing and re-initialization)
 */
export function resetState() {
  state.resetAll();
  resetJQuery();
}

// D3 color scale for clusters (now imported from npm module)
export const colorScale = scaleOrdinal(schemeCategory10);

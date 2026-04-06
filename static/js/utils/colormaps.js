/**
 * Colormap definitions for BattyCoda spectrograms.
 *
 * Single source of truth is static/data/colormaps.json which is consumed
 * by both Python (battycoda_app/audio/colormaps.py) and JavaScript (here).
 */

import colormaps from '../../data/colormaps.json';

export const ROSEUS_COLORMAP = colormaps.roseus;

/**
 * Get a colormap by name. Falls back to roseus if not found.
 * @param {string} name - Colormap name (e.g. 'roseus', 'viridis', 'classic')
 * @returns {Array} 256-entry array of [r, g, b] tuples
 */
export function getColormap(name) {
  return colormaps[name] || colormaps.roseus;
}

/**
 * Get the user's preferred colormap from page data.
 * @returns {Array} 256-entry array of [r, g, b] tuples
 */
export function getUserColormap() {
  const pageData = document.getElementById('page-data');
  const name = pageData?.dataset?.spectrogramColormap || 'roseus';
  return getColormap(name);
}

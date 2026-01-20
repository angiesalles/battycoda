/**
 * Cluster Explorer Keyboard Navigation Module
 *
 * Enables keyboard navigation through clusters using arrow keys,
 * Enter to select, and Escape to deselect.
 */

import { selectAll } from 'd3-selection';
import {
  getClusters,
  getSelectedClusterId,
  getFocusedClusterIndex,
  setFocusedClusterIndex,
  getJQuery,
} from './state.js';
import { selectCluster, deselectCluster } from './interactions.js';

// Track whether keyboard navigation is initialized
let isInitialized = false;
let keydownHandler = null;

/**
 * Initialize keyboard navigation for the cluster explorer
 */
export function initializeKeyboardNavigation() {
  if (isInitialized) {
    console.warn('[ClusterExplorer] Keyboard navigation already initialized.');
    return;
  }

  // Create the keydown handler
  keydownHandler = handleKeyDown;

  // Attach keydown handler to document
  document.addEventListener('keydown', keydownHandler);

  isInitialized = true;
  console.debug('[ClusterExplorer] Keyboard navigation initialized.');
}

/**
 * Clean up keyboard navigation event listeners
 */
export function cleanupKeyboardNavigation() {
  if (keydownHandler) {
    document.removeEventListener('keydown', keydownHandler);
    keydownHandler = null;
  }
  isInitialized = false;
}

/**
 * Handle keyboard events for cluster navigation
 * @param {KeyboardEvent} event - The keyboard event
 */
function handleKeyDown(event) {
  // Ignore keyboard events when typing in input fields
  const target = event.target;
  if (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.tagName === 'SELECT' ||
    target.isContentEditable
  ) {
    return;
  }

  const clusters = getClusters();
  if (!clusters || clusters.length === 0) {
    return;
  }

  let focusedIndex = getFocusedClusterIndex();

  switch (event.key) {
    case 'ArrowRight':
    case 'ArrowDown':
      event.preventDefault();
      focusedIndex = Math.min(focusedIndex + 1, clusters.length - 1);
      setFocusedClusterIndex(focusedIndex);
      highlightFocusedCluster(focusedIndex);
      break;

    case 'ArrowLeft':
    case 'ArrowUp':
      event.preventDefault();
      focusedIndex = Math.max(focusedIndex - 1, 0);
      setFocusedClusterIndex(focusedIndex);
      highlightFocusedCluster(focusedIndex);
      break;

    case 'Enter':
    case ' ': // Space key
      event.preventDefault();
      if (focusedIndex >= 0 && focusedIndex < clusters.length) {
        selectCluster(clusters[focusedIndex].id);
      }
      break;

    case 'Escape':
      event.preventDefault();
      deselectCluster();
      break;

    case 'Home':
      event.preventDefault();
      focusedIndex = 0;
      setFocusedClusterIndex(focusedIndex);
      highlightFocusedCluster(focusedIndex);
      break;

    case 'End':
      event.preventDefault();
      focusedIndex = clusters.length - 1;
      setFocusedClusterIndex(focusedIndex);
      highlightFocusedCluster(focusedIndex);
      break;

    default:
      // Ignore other keys
      break;
  }
}

/**
 * Highlight the focused cluster with a visual indicator
 * @param {number} index - Index of the cluster to highlight
 */
function highlightFocusedCluster(index) {
  const $ = getJQuery();
  if (!$) {
    return;
  }

  const clusters = getClusters();
  if (!clusters || index < 0 || index >= clusters.length) {
    return;
  }

  const cluster = clusters[index];
  const selectedId = getSelectedClusterId();
  const pointSize = parseInt($('#point-size').val()) || 8;

  const points = selectAll('.cluster-point');
  if (points.empty()) {
    return;
  }

  try {
    // Reset all points first, then apply focused styling
    points.each(function () {
      const point = selectAll([this]);
      const d = point.datum();

      // Determine the visual state
      const isSelected = d.id === selectedId;
      const isFocused = d.id === cluster.id;

      if (isSelected) {
        // Selected state takes precedence
        point
          .attr('stroke-width', 3)
          .attr('stroke', '#fff')
          .attr('r', pointSize * 1.5)
          .classed('focused', isFocused);
      } else if (isFocused) {
        // Focused but not selected - dashed outline
        point
          .attr('stroke-width', 2)
          .attr('stroke', '#007bff')
          .attr('r', pointSize * 1.2)
          .classed('focused', true);
      } else {
        // Default state
        point
          .attr('stroke-width', 1)
          .attr('stroke', '#000')
          .attr('r', pointSize)
          .classed('focused', false);
      }
    });
  } catch (error) {
    console.error('[ClusterExplorer] Failed to highlight focused cluster:', error);
  }
}

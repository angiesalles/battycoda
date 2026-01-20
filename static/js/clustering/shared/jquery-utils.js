/**
 * jQuery Utilities for Clustering Modules
 *
 * Provides a shared jQuery dependency injection pattern for testability.
 */

// Private jQuery instance (for dependency injection)
let jQueryInstance = null;

/**
 * Get the jQuery instance
 * Falls back to window.jQuery if not explicitly set
 * @returns {Function|null} jQuery function
 */
export function getJQuery() {
  return jQueryInstance || (typeof window !== 'undefined' ? window.jQuery : null);
}

/**
 * Set the jQuery instance (for dependency injection in tests)
 * @param {Function} $ - jQuery function
 */
export function setJQuery($) {
  jQueryInstance = $;
}

/**
 * Reset the jQuery instance to default (window.jQuery fallback)
 */
export function resetJQuery() {
  jQueryInstance = null;
}

/**
 * Check if jQuery is available
 * @returns {boolean} True if jQuery is available
 */
export function isJQueryAvailable() {
  return getJQuery() !== null;
}

/**
 * Run a function with jQuery, logging an error if unavailable
 * @param {Function} fn - Function to run with jQuery as first argument
 * @param {string} context - Context string for error message
 * @returns {*} Result of fn, or undefined if jQuery unavailable
 */
export function withJQuery(fn, context = 'Unknown') {
  const $ = getJQuery();
  if (!$) {
    console.error(`[${context}] jQuery is not available`);
    return undefined;
  }
  return fn($);
}

/**
 * Debounce utilities for rate-limiting function calls
 */

/**
 * Create a debounced version of a function that delays execution
 * until after a specified delay has passed since the last call.
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in milliseconds (default: 300)
 * @returns {Function} Debounced function
 */
export function debounce(fn, delay = 300) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

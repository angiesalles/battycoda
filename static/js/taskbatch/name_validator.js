/**
 * Task Batch Name Validator
 *
 * Provides functionality to check if a task batch name already exists
 * and warn the user, without preventing them from using the name.
 */

/**
 * Check if a name exists via AJAX
 * @param {string} name - The name to check
 * @param {string} checkUrl - The URL to check against
 * @param {HTMLElement} warningElement - The element to show/hide based on result
 * @returns {Promise<boolean>} - Whether the name exists
 */
export async function checkNameExists(name, checkUrl, warningElement) {
  if (!checkUrl) return false;

  try {
    const response = await fetch(`${checkUrl}?name=${encodeURIComponent(name)}`);
    const data = await response.json();

    if (warningElement) {
      warningElement.style.display = data.exists ? 'block' : 'none';
    }

    return data.exists;
  } catch (error) {
    console.error('Error checking name:', error);
    if (warningElement) {
      warningElement.style.display = 'none';
    }
    return false;
  }
}

/**
 * Create a debounced version of a function
 * @param {Function} fn - The function to debounce
 * @param {number} delay - The debounce delay in ms
 * @returns {Function} - The debounced function
 */
export function debounce(fn, delay) {
  let timeoutId;
  return function (...args) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

/**
 * Initialize the name validator for a form
 * @param {Object} options - Configuration options
 * @param {HTMLInputElement} options.nameInput - The name input element
 * @param {HTMLElement} options.warningElement - The warning element to show/hide
 * @param {number} [options.debounceDelay=300] - Debounce delay in ms
 */
export function initialize(options = {}) {
  const { nameInput, warningElement, debounceDelay = 300 } = options;

  // Use provided elements or find by ID
  const input = nameInput || document.getElementById('name');
  const warning = warningElement || document.getElementById('name-warning');

  // Exit if elements don't exist on this page
  if (!input || !warning) return;

  const checkUrl = input.getAttribute('data-check-url');

  // Create debounced check function
  const debouncedCheck = debounce((name) => {
    checkNameExists(name, checkUrl, warning);
  }, debounceDelay);

  // Add input event listener
  input.addEventListener('input', function () {
    const name = this.value.trim();

    if (name) {
      debouncedCheck(name);
    } else {
      warning.style.display = 'none';
    }
  });

  // Check initial value
  if (input.value.trim()) {
    checkNameExists(input.value.trim(), checkUrl, warning);
  }
}

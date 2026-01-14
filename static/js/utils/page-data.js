/**
 * Page Data Utility
 *
 * Provides a clean pattern for reading Django template data in ES6 modules.
 * Instead of using global variables defined in inline scripts, data is passed
 * via data attributes on a hidden container element or JSON script tags.
 *
 * Usage in Django templates:
 *
 * For simple values (strings, numbers, booleans):
 * ```html
 * <div id="page-data"
 *      data-recording-id="{{ recording.id }}"
 *      data-api-url="{% url 'battycoda_app:api_endpoint' %}"
 *      data-is-active="{{ is_active|yesno:'true,false' }}"
 *      hidden>
 * </div>
 * ```
 *
 * For complex data (objects, arrays):
 * ```html
 * <script id="config-data" type="application/json">
 * {{ config_json|safe }}
 * </script>
 * ```
 *
 * Usage in JavaScript:
 * ```javascript
 * import { getPageData, getJsonData } from './utils/page-data.js';
 *
 * const data = getPageData();
 * console.log(data.recordingId);  // kebab-case converted to camelCase
 * console.log(data.apiUrl);
 * console.log(data.isActive);     // boolean true/false
 *
 * const config = getJsonData('config-data');
 * console.log(config.someProperty);
 * ```
 */

/**
 * Parse a string value to its appropriate type
 * @param {string} value - The string value to parse
 * @returns {string|number|boolean|null} The parsed value
 */
function parseValue(value) {
  // Handle null/undefined
  if (value === null || value === undefined || value === 'null' || value === 'undefined') {
    return null;
  }

  // Handle booleans
  if (value === 'true') return true;
  if (value === 'false') return false;

  // Handle numbers (integers and floats)
  if (/^-?\d+$/.test(value)) {
    return parseInt(value, 10);
  }
  if (/^-?\d*\.?\d+$/.test(value)) {
    return parseFloat(value);
  }

  // Return as string
  return value;
}

/**
 * Convert kebab-case to camelCase
 * @param {string} str - The kebab-case string (e.g., "recording-id")
 * @returns {string} The camelCase string (e.g., "recordingId")
 */
function kebabToCamel(str) {
  return str.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Get page data from the hidden data container element
 * @param {string} [containerId='page-data'] - The ID of the data container element
 * @returns {Object} An object with all data attributes (kebab-case converted to camelCase)
 */
export function getPageData(containerId = 'page-data') {
  const container = document.getElementById(containerId);
  if (!container) {
    return {};
  }

  const data = {};
  for (const attr of container.attributes) {
    if (attr.name.startsWith('data-')) {
      const key = kebabToCamel(attr.name.slice(5)); // Remove 'data-' prefix
      data[key] = parseValue(attr.value);
    }
  }
  return data;
}

/**
 * Get a single value from the page data container
 * @param {string} key - The data attribute name (without 'data-' prefix, in kebab-case)
 * @param {*} [defaultValue=null] - Default value if the attribute doesn't exist
 * @param {string} [containerId='page-data'] - The ID of the data container element
 * @returns {*} The parsed value or default
 */
export function getPageDataValue(key, defaultValue = null, containerId = 'page-data') {
  const container = document.getElementById(containerId);
  if (!container) {
    return defaultValue;
  }

  const value = container.dataset[kebabToCamel(key)];
  if (value === undefined) {
    return defaultValue;
  }
  return parseValue(value);
}

/**
 * Get complex JSON data from a script tag
 * @param {string} scriptId - The ID of the script element containing JSON
 * @returns {*} The parsed JSON data, or null if not found or invalid
 */
export function getJsonData(scriptId) {
  const script = document.getElementById(scriptId);
  if (!script) {
    console.warn(`JSON data script with id "${scriptId}" not found`);
    return null;
  }

  try {
    return JSON.parse(script.textContent);
  } catch (e) {
    console.error(`Failed to parse JSON data from script "${scriptId}":`, e);
    return null;
  }
}

/**
 * Check if page data container exists
 * @param {string} [containerId='page-data'] - The ID of the data container element
 * @returns {boolean} True if the container exists
 */
export function hasPageData(containerId = 'page-data') {
  return document.getElementById(containerId) !== null;
}

/**
 * Get CSRF token from the page
 * Looks for it in multiple locations:
 * 1. Hidden input with name 'csrfmiddlewaretoken'
 * 2. Meta tag with name 'csrf-token'
 * 3. Page data container with data-csrf-token attribute
 * @returns {string|null} The CSRF token or null if not found
 */
export function getCsrfToken() {
  // Try hidden input first (most common in Django forms)
  const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (input) {
    return input.value;
  }

  // Try meta tag
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) {
    return meta.getAttribute('content');
  }

  // Try page data container
  const container = document.getElementById('page-data');
  if (container && container.dataset.csrfToken) {
    return container.dataset.csrfToken;
  }

  return null;
}

/**
 * Set up jQuery AJAX with CSRF token
 * Call this once when your page loads if you're using jQuery for AJAX requests
 */
export function setupJQueryCsrf() {
  if (typeof $ === 'undefined' && typeof jQuery === 'undefined') {
    console.warn('jQuery not available for CSRF setup');
    return;
  }

  const jq = $ || jQuery;
  const csrfToken = getCsrfToken();

  if (!csrfToken) {
    console.warn('No CSRF token found for jQuery AJAX setup');
    return;
  }

  jq.ajaxSetup({
    beforeSend: function (xhr) {
      if (!this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
      }
    },
  });
}

/**
 * Unified API Configuration for Clustering Modules
 *
 * Provides consistent API URL handling across cluster_explorer and cluster_mapping.
 * URLs are read from data attributes in the template, with fallbacks for testing.
 */

/**
 * Create an API config reader for a specific config element
 * @param {string} elementId - ID of the config element
 * @param {Object} urlMapping - Maps friendly names to data attribute names
 * @param {Object} fallbacks - Fallback URLs for testing
 * @returns {Object} Lazy-loading proxy for API URLs
 */
export function createApiConfig(elementId, urlMapping, fallbacks) {
  let cachedUrls = null;

  function loadUrls() {
    if (cachedUrls) return cachedUrls;

    const configElement = document.getElementById(elementId);

    if (configElement) {
      cachedUrls = {};
      for (const [name, dataAttr] of Object.entries(urlMapping)) {
        cachedUrls[name] = configElement.dataset[dataAttr];
      }
    } else {
      console.warn(`${elementId} element not found, using fallback URLs`);
      cachedUrls = { ...fallbacks };
    }

    return cachedUrls;
  }

  // Return a proxy that lazily loads URLs on first access
  return new Proxy(
    {},
    {
      get(target, prop) {
        const urls = loadUrls();
        return urls[prop];
      },
      ownKeys() {
        const urls = loadUrls();
        return Object.keys(urls);
      },
      getOwnPropertyDescriptor(target, prop) {
        const urls = loadUrls();
        if (prop in urls) {
          return { enumerable: true, configurable: true, value: urls[prop] };
        }
        return undefined;
      },
    }
  );
}

/**
 * Build a URL with query parameters
 * @param {string} endpoint - Base endpoint URL
 * @param {Object} params - Query parameters as key-value pairs
 * @returns {string} Full URL with query string
 */
export function buildUrl(endpoint, params = {}) {
  const queryString = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');

  return queryString ? `${endpoint}?${queryString}` : endpoint;
}

/**
 * Reset cached URLs (for testing)
 * Note: Since we use closures, each createApiConfig call has its own cache.
 * This function is provided for modules that expose their cache reset.
 */
export function createResettableApiConfig(elementId, urlMapping, fallbacks) {
  let cachedUrls = null;

  function loadUrls() {
    if (cachedUrls) return cachedUrls;

    const configElement = document.getElementById(elementId);

    if (configElement) {
      cachedUrls = {};
      for (const [name, dataAttr] of Object.entries(urlMapping)) {
        cachedUrls[name] = configElement.dataset[dataAttr];
      }
    } else {
      console.warn(`${elementId} element not found, using fallback URLs`);
      cachedUrls = { ...fallbacks };
    }

    return cachedUrls;
  }

  function reset() {
    cachedUrls = null;
  }

  const proxy = new Proxy(
    {},
    {
      get(target, prop) {
        if (prop === 'reset') return reset;
        const urls = loadUrls();
        return urls[prop];
      },
      ownKeys() {
        const urls = loadUrls();
        return Object.keys(urls);
      },
      getOwnPropertyDescriptor(target, prop) {
        const urls = loadUrls();
        if (prop in urls) {
          return { enumerable: true, configurable: true, value: urls[prop] };
        }
        return undefined;
      },
    }
  );

  return proxy;
}

/**
 * HTML utilities for safe content rendering
 */

/**
 * Escape HTML special characters to prevent XSS attacks
 * @param {string} str - String to escape
 * @returns {string} HTML-escaped string safe for innerHTML
 */
export function escapeHtml(str) {
  if (str == null) {
    return '';
  }
  const string = String(str);
  const htmlEscapes = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };
  return string.replace(/[&<>"']/g, (char) => htmlEscapes[char]);
}

/**
 * Validate a URL for safe loading of dynamic resources (defense-in-depth)
 * @param {string} url - URL to validate
 * @returns {string} The URL if safe, or empty string if potentially dangerous
 */
export function validateUrl(url) {
  if (url == null || typeof url !== 'string') {
    return '';
  }
  const trimmedUrl = url.trim();
  if (trimmedUrl === '') {
    return '';
  }

  // Allow relative URLs starting with /
  if (trimmedUrl.startsWith('/')) {
    return trimmedUrl;
  }

  // Allow HTTPS URLs
  if (trimmedUrl.startsWith('https://')) {
    return trimmedUrl;
  }

  // Allow HTTP only for localhost (development)
  if (trimmedUrl.startsWith('http://localhost') || trimmedUrl.startsWith('http://127.0.0.1')) {
    return trimmedUrl;
  }

  // Reject everything else (javascript:, data:, vbscript:, ftp:, etc.)
  console.warn('validateUrl rejected potentially unsafe URL:', url);
  return '';
}

/**
 * Security utilities for XSS prevention and URL validation.
 *
 * These functions provide defense-in-depth against XSS attacks:
 * - escapeHtml: Safely escapes HTML entities in user-provided content
 * - validateUrl: Validates URLs before dynamic resource loading
 *
 * @module utils/security
 */

/**
 * Escape HTML entities in a string to prevent XSS attacks.
 *
 * Uses the browser's built-in text encoding by creating a text node
 * and reading its innerHTML. This is more reliable than regex-based
 * approaches as it handles all edge cases correctly.
 *
 * @param {*} str - The string to escape (null/undefined returns empty string)
 * @returns {string} The escaped HTML string
 *
 * @example
 * escapeHtml('<script>alert("xss")</script>')
 * // Returns: '&lt;script&gt;alert("xss")&lt;/script&gt;'
 */
export function escapeHtml(str) {
  if (str == null) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

/**
 * Validate a URL for safe dynamic resource loading.
 *
 * Returns the URL if it passes safety checks, or an empty string if
 * the URL is potentially dangerous. This provides defense-in-depth
 * against injection of malicious URLs.
 *
 * Allowed URL patterns:
 * - Relative URLs starting with /
 * - HTTPS URLs
 * - HTTP URLs only for localhost (development)
 *
 * Rejected URL patterns:
 * - javascript: URLs
 * - data: URLs
 * - vbscript: URLs
 * - ftp: and other protocols
 *
 * @param {*} url - The URL to validate
 * @returns {string} The validated URL or empty string if unsafe
 *
 * @example
 * validateUrl('/api/data') // Returns: '/api/data'
 * validateUrl('https://example.com') // Returns: 'https://example.com'
 * validateUrl('javascript:alert(1)') // Returns: '' (logs warning)
 */
export function validateUrl(url) {
  // Handle null/undefined/non-string values
  if (url == null || typeof url !== 'string') return '';
  url = url.trim();
  if (url === '') return '';

  // Allow relative URLs starting with /
  if (url.startsWith('/')) return url;

  // Allow HTTPS URLs
  if (url.startsWith('https://')) return url;

  // Allow HTTP only for localhost (development)
  if (url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1')) return url;

  // Reject everything else (javascript:, data:, vbscript:, ftp:, etc.)
  console.warn('validateUrl rejected potentially unsafe URL:', url);
  return '';
}

// Also expose as globals for backwards compatibility with inline scripts
// that may reference window.escapeHtml or window.validateUrl
if (typeof window !== 'undefined') {
  window.escapeHtml = escapeHtml;
  window.validateUrl = validateUrl;
}

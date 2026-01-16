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

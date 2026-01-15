/**
 * Validation - File validation utilities
 *
 * Validates file types and sizes for upload forms.
 */

/**
 * Allowed file extensions for WAV files
 */
const WAV_EXTENSIONS = ['.wav', '.wave'];

/**
 * Allowed file extensions for pickle files
 */
const PICKLE_EXTENSIONS = ['.pickle', '.pkl'];

/**
 * Check if a file has a valid WAV extension
 * @param {File} file - File to check
 * @returns {boolean} True if valid WAV file
 */
export function isValidWavFile(file) {
  const name = file.name.toLowerCase();
  return WAV_EXTENSIONS.some((ext) => name.endsWith(ext));
}

/**
 * Check if a file has a valid pickle extension
 * @param {File} file - File to check
 * @returns {boolean} True if valid pickle file
 */
export function isValidPickleFile(file) {
  const name = file.name.toLowerCase();
  return PICKLE_EXTENSIONS.some((ext) => name.endsWith(ext));
}

/**
 * Validate files in a file input
 * @param {FileList} files - Files to validate
 * @param {function} validator - Validation function
 * @returns {Object} Validation result with valid/invalid files
 */
export function validateFiles(files, validator) {
  const valid = [];
  const invalid = [];

  for (const file of files) {
    if (validator(file)) {
      valid.push(file);
    } else {
      invalid.push(file);
    }
  }

  return { valid, invalid };
}

/**
 * Get human-readable file size
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

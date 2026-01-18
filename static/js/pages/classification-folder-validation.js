/**
 * Classification Folder Validation Script
 *
 * Handles species selection redirect for training data folder validation.
 * When a species is selected, redirects to the same page with the species_id
 * query parameter to trigger server-side validation.
 *
 * Expected elements:
 * - #species_id: The species select dropdown
 *
 * @module pages/classification-folder-validation
 */

/**
 * Redirect to current page with selected species ID as query parameter.
 * This triggers server-side validation of the training folder for the selected species.
 */
function validateFolder() {
  const speciesSelect = document.getElementById('species_id');
  if (!speciesSelect) {
    return;
  }

  const speciesId = speciesSelect.value;
  if (speciesId) {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('species_id', speciesId);
    window.location.href = currentUrl.toString();
  }
}

/**
 * Initialize folder validation functionality.
 * Attaches the validateFolder function to the species select dropdown.
 */
function initFolderValidation() {
  const speciesSelect = document.getElementById('species_id');
  if (!speciesSelect) {
    return;
  }

  // Attach change handler
  speciesSelect.addEventListener('change', validateFolder);
}

// Export for potential external use
window.validateFolder = validateFolder;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFolderValidation);
} else {
  initFolderValidation();
}

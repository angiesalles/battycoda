/**
 * Profile Management Module
 *
 * Handles profile editing functionality including:
 * - Profile image upload and removal
 * - Email updates
 * - Management features toggle
 * - API key copy
 *
 * Usage:
 * Include this module on the edit profile page with required data attributes:
 *
 * ```html
 * <div id="profile-page-data"
 *      data-update-profile-url="/api/profile/update/"
 *      hidden>
 * </div>
 * ```
 */

import { getCsrfToken } from '../utils/page-data.js';
import { escapeHtml, validateUrl } from '../utils/html.js';

/**
 * Show a status message in the specified element
 * @param {HTMLElement} element - Container element for the message
 * @param {string} message - Message to display
 * @param {boolean} isSuccess - Whether this is a success (true) or error (false) message
 */
function showStatus(element, message, isSuccess) {
  if (!element) return;
  element.innerHTML = `<div class="alert alert-${isSuccess ? 'success' : 'danger'} py-2">${escapeHtml(message)}</div>`;

  // Clear message after 5 seconds
  setTimeout(() => {
    if (element) {
      element.innerHTML = '';
    }
  }, 5000);
}

/**
 * Handle profile image upload
 * @param {string} updateUrl - The URL to POST to
 */
function setupImageUpload(updateUrl) {
  const profileImageUpload = document.getElementById('profile_image_upload');
  const uploadImageBtn = document.getElementById('upload-image-btn');
  const imageUploadStatus = document.getElementById('image-upload-status');

  if (!uploadImageBtn || !profileImageUpload) return;

  uploadImageBtn.addEventListener('click', function () {
    if (!profileImageUpload.files.length) {
      showStatus(imageUploadStatus, 'Please select an image file first.', false);
      return;
    }

    const file = profileImageUpload.files[0];

    // Validate file type
    if (!file.type.match('image.*')) {
      showStatus(imageUploadStatus, 'Please select a valid image file.', false);
      return;
    }

    // Create FormData object and append the file
    const formData = new FormData();
    formData.append('profile_image', file);
    formData.append('action', 'upload_image');

    // Show loading state
    uploadImageBtn.disabled = true;
    uploadImageBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Uploading...';

    // Send AJAX request
    fetch(updateUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showStatus(imageUploadStatus, data.message, true);

          // Update the profile image on the page
          const imageDisplay = document.getElementById('profile-image-display');
          const validatedImageUrl = validateUrl(data.image_url);
          if (validatedImageUrl && imageDisplay) {
            imageDisplay.innerHTML = `<img src="${escapeHtml(validatedImageUrl)}?v=${new Date().getTime()}" alt="Profile Image" class="img-fluid rounded-circle" style="width: 150px; height: 150px; object-fit: cover;">`;
          }

          // Add remove button if it doesn't exist
          const removeImageBtn = document.getElementById('remove-image-btn');
          if (!removeImageBtn && data.has_image) {
            const removeBtn = document.createElement('button');
            removeBtn.id = 'remove-image-btn';
            removeBtn.className = 'btn btn-sm btn-outline-danger ms-2';
            removeBtn.innerHTML = '<i class="fas fa-trash me-1"></i> Remove Image';
            const buttonContainer = document.querySelector('.mt-2');
            if (buttonContainer) {
              buttonContainer.appendChild(removeBtn);
            }

            // Add event listener to newly created button
            removeBtn.addEventListener('click', () => handleRemoveImage(updateUrl));
          }

          // Update navbar profile image if it exists
          const navbarProfileImage = document.querySelector('.nav.navbar-nav a.dropdown-toggle img');
          if (navbarProfileImage && validatedImageUrl) {
            navbarProfileImage.src = validatedImageUrl + '?v=' + new Date().getTime();
          }

          // Clear the file input
          profileImageUpload.value = '';
        } else {
          showStatus(imageUploadStatus, data.message || 'An error occurred.', false);
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        showStatus(imageUploadStatus, 'An error occurred while uploading the image.', false);
      })
      .finally(() => {
        // Reset button state
        uploadImageBtn.disabled = false;
        uploadImageBtn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload Image';
      });
  });
}

/**
 * Handle profile image removal
 * @param {string} updateUrl - The URL to POST to
 */
function handleRemoveImage(updateUrl) {
  if (!confirm('Are you sure you want to remove your profile image?')) {
    return;
  }

  const removeImageBtn = document.getElementById('remove-image-btn');
  const imageUploadStatus = document.getElementById('image-upload-status');

  // Create FormData and append action
  const formData = new FormData();
  formData.append('action', 'remove_image');

  // Show loading state
  if (removeImageBtn) {
    removeImageBtn.disabled = true;
    removeImageBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Removing...';
  }

  // Send AJAX request
  fetch(updateUrl, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
    },
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showStatus(imageUploadStatus, data.message, true);

        // Update the profile image display
        const imageDisplay = document.getElementById('profile-image-display');
        if (imageDisplay) {
          imageDisplay.innerHTML = `
            <div class="profile-placeholder rounded-circle d-flex align-items-center justify-content-center bg-primary" style="width: 150px; height: 150px; margin: 0 auto;">
                <span class="fas fa-user text-white" style="font-size: 4rem;"></span>
            </div>
          `;
        }

        // Remove the remove button
        if (removeImageBtn) {
          removeImageBtn.remove();
        }

        // Update navbar image
        const navbarProfileImage = document.querySelector('.nav.navbar-nav a.dropdown-toggle img');
        if (navbarProfileImage) {
          const navbarUserIcon = navbarProfileImage.parentNode;
          if (navbarUserIcon) {
            navbarUserIcon.innerHTML = '<span class="icon fas fa-user"></span>';
          }
        }
      } else {
        showStatus(imageUploadStatus, data.message || 'An error occurred.', false);
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      showStatus(imageUploadStatus, 'An error occurred while removing the image.', false);
    });
}

/**
 * Setup remove image button event listener
 * @param {string} updateUrl - The URL to POST to
 */
function setupImageRemove(updateUrl) {
  const removeImageBtn = document.getElementById('remove-image-btn');
  if (removeImageBtn) {
    removeImageBtn.addEventListener('click', () => handleRemoveImage(updateUrl));
  }
}

/**
 * Handle email update
 * @param {string} updateUrl - The URL to POST to
 */
function setupEmailUpdate(updateUrl) {
  const updateEmailBtn = document.getElementById('update-email-btn');
  const emailInput = document.getElementById('id_email');
  const emailUpdateStatus = document.getElementById('email-update-status');

  if (!updateEmailBtn || !emailInput) return;

  updateEmailBtn.addEventListener('click', function () {
    const email = emailInput.value.trim();

    if (!email) {
      showStatus(emailUpdateStatus, 'Please enter a valid email address.', false);
      return;
    }

    // Create FormData and append email
    const formData = new FormData();
    formData.append('email', email);
    formData.append('action', 'update_email');

    // Show loading state
    updateEmailBtn.disabled = true;
    updateEmailBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Updating...';

    // Send AJAX request
    fetch(updateUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showStatus(emailUpdateStatus, data.message, true);
        } else {
          showStatus(emailUpdateStatus, data.message || 'An error occurred.', false);
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        showStatus(emailUpdateStatus, 'An error occurred while updating email.', false);
      })
      .finally(() => {
        // Reset button state
        updateEmailBtn.disabled = false;
        updateEmailBtn.innerHTML = '<i class="fas fa-save me-1"></i> Update Email';
      });
  });
}

/**
 * Handle management features toggle
 * @param {string} updateUrl - The URL to POST to
 */
function setupManagementFeaturesUpdate(updateUrl) {
  const updateManagementFeaturesBtn = document.getElementById('update-management-features-btn');
  const managementFeaturesCheckbox = document.getElementById('id_management_features_enabled');
  const managementFeaturesStatus = document.getElementById('management-features-status');

  if (!updateManagementFeaturesBtn || !managementFeaturesCheckbox) return;

  updateManagementFeaturesBtn.addEventListener('click', function () {
    const isEnabled = managementFeaturesCheckbox.checked;

    // Create FormData and append management features setting
    const formData = new FormData();
    formData.append('management_features_enabled', isEnabled);
    formData.append('action', 'update_management_features');

    // Show loading state
    updateManagementFeaturesBtn.disabled = true;
    updateManagementFeaturesBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Updating...';

    // Send AJAX request
    fetch(updateUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showStatus(managementFeaturesStatus, data.message, true);
        } else {
          showStatus(managementFeaturesStatus, data.message || 'An error occurred.', false);
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        showStatus(managementFeaturesStatus, 'An error occurred while updating management features.', false);
      })
      .finally(() => {
        // Reset button state
        updateManagementFeaturesBtn.disabled = false;
        updateManagementFeaturesBtn.innerHTML =
          '<i class="fas fa-save me-1"></i> Update Management Features';
      });
  });
}

/**
 * Setup API key copy functionality
 */
function setupApiKeyCopy() {
  // Expose copyApiKey globally for onclick handlers
  window.copyApiKey = function () {
    const apiKeyInput = document.getElementById('api-key-display');
    if (!apiKeyInput) return;

    apiKeyInput.select();
    apiKeyInput.setSelectionRange(0, 99999); // For mobile devices

    try {
      document.execCommand('copy');

      // Show success message
      const statusDiv = document.getElementById('api-key-status');
      if (statusDiv) {
        statusDiv.innerHTML = '<div class="alert alert-success py-2">API key copied to clipboard!</div>';

        // Clear message after 3 seconds
        setTimeout(() => {
          statusDiv.innerHTML = '';
        }, 3000);
      }
    } catch (err) {
      console.error('Failed to copy: ', err);

      // Show error message
      const statusDiv = document.getElementById('api-key-status');
      if (statusDiv) {
        statusDiv.innerHTML =
          '<div class="alert alert-warning py-2">Please manually copy the API key.</div>';

        // Clear message after 3 seconds
        setTimeout(() => {
          statusDiv.innerHTML = '';
        }, 3000);
      }
    }
  };
}

/**
 * Initialize the profile page functionality
 */
export function initProfile() {
  // Get the update URL from page data
  const pageData = document.getElementById('profile-page-data');
  if (!pageData) {
    console.warn('Profile page data element not found');
    return;
  }

  const updateUrl = pageData.dataset.updateProfileUrl;
  if (!updateUrl) {
    console.error('Update profile URL not found in page data');
    return;
  }

  // Setup all profile functionality
  setupImageUpload(updateUrl);
  setupImageRemove(updateUrl);
  setupEmailUpdate(updateUrl);
  setupManagementFeaturesUpdate(updateUrl);
  setupApiKeyCopy();
}

/**
 * Auto-initialize when DOM is ready
 */
export function autoInit() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProfile);
  } else {
    initProfile();
  }
}

// Auto-initialize when this module is loaded
autoInit();

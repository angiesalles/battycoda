/**
 * Species Management Module
 *
 * Handles species create and edit form functionality including:
 * - Managing call types (add, delete, parse from file)
 * - Species name validation against existing names (create mode)
 * - Form submission handling with JSON call types
 *
 * Usage:
 * Include this module on the species page with required data:
 *
 * ```html
 * <script id="species-page-data" type="application/json">
 * {
 *   "mode": "create" | "edit",
 *   "existingSpeciesNames": ["Species 1", "Species 2"],  // for create mode
 *   "currentSpeciesName": "My Species",                  // for edit mode
 *   "existingCalls": [{"short_name": "FM", "long_name": "Frequency Modulated"}],  // for edit mode
 *   "canModifyCalls": true  // for edit mode - false if species has classifiers
 * }
 * </script>
 * ```
 */

import { getJsonData } from '../utils/page-data.js';
import { escapeHtml } from '../utils/html.js';

// Module state
let callTypes = [];
let canModifyCalls = true;

/**
 * Show a message in the specified element
 * @param {HTMLElement} element - Container element for the message
 * @param {string} message - Message to display
 * @param {string} type - Message type: 'success' or 'error'
 */
function showMessage(element, message, type = 'success') {
  if (!element) return;

  element.innerHTML = `
    <div style="margin-top: 8px; margin-bottom: 8px; padding: 8px 12px; border-radius: 4px; background-color: ${type === 'success' ? '#2e7d32' : '#c62828'}; color: white;">
      ${escapeHtml(message)}
    </div>
  `;

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    if (element && element.firstChild) {
      element.innerHTML = '';
    }
  }, 5000);
}

/**
 * Update the hidden JSON field with current call types
 * @returns {string} The JSON string
 */
function updateCallTypesJson() {
  const callTypesJsonInput = document.getElementById('call_types_json');
  if (!callTypesJsonInput) return '';

  const jsonString = JSON.stringify(callTypes);
  callTypesJsonInput.value = jsonString;
  return jsonString;
}

/**
 * Render the calls table with current call types
 */
function renderCallsTable() {
  const callsTableContainer = document.getElementById('calls-table-container');
  if (!callsTableContainer) return;

  if (callTypes.length === 0) {
    callsTableContainer.innerHTML =
      '<p style="font-style: italic; color: #999; text-align: center;">No call types added yet.</p>';
    return;
  }

  // Create table HTML using Bootstrap styles for consistency
  let tableHtml = `
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Short Name</th>
            <th>Long Name</th>
            <th class="text-center" style="width: 100px;">Actions</th>
          </tr>
        </thead>
        <tbody>
  `;

  // Add rows for each call type
  callTypes.forEach((call, index) => {
    const deleteButton = canModifyCalls
      ? `<button type="button" class="btn btn-sm btn-danger delete-call-btn" data-index="${index}">
           <i class="fas fa-trash"></i> Delete
         </button>`
      : `<button type="button" class="btn btn-sm btn-secondary" disabled title="Cannot delete call types when species is used by classifiers">
           <i class="fas fa-lock"></i> Locked
         </button>`;

    tableHtml += `
      <tr class="call-item" data-index="${index}">
        <td>${escapeHtml(call.short_name)}</td>
        <td>${escapeHtml(call.long_name || '')}</td>
        <td class="text-center">${deleteButton}</td>
      </tr>
    `;
  });

  tableHtml += `
        </tbody>
      </table>
    </div>
  `;

  callsTableContainer.innerHTML = tableHtml;

  // Add event listeners to delete buttons (only if modification is allowed)
  if (canModifyCalls) {
    document.querySelectorAll('.delete-call-btn').forEach((button) => {
      button.addEventListener('click', function () {
        const index = parseInt(this.dataset.index, 10);
        deleteCall(index);
      });
    });
  }
}

/**
 * Add a new call type
 * @param {string} shortName - Short name of the call
 * @param {string} longName - Long name of the call
 * @returns {boolean} True if added successfully
 */
function addCall(shortName, longName) {
  const addCallMessages = document.getElementById('add-call-messages');

  // Check if modifications are allowed
  if (!canModifyCalls) {
    showMessage(
      addCallMessages,
      'Cannot modify call types because this species is used by classifiers.',
      'error'
    );
    return false;
  }

  // Check if a call with this short name already exists
  const existing = callTypes.find(
    (call) => call.short_name.toLowerCase() === shortName.toLowerCase()
  );
  if (existing) {
    showMessage(addCallMessages, `A call with short name '${shortName}' already exists.`, 'error');
    return false;
  }

  // Add to the call types array
  callTypes.push({
    short_name: shortName,
    long_name: longName,
  });

  // Update the JSON field and re-render the table
  updateCallTypesJson();
  renderCallsTable();

  return true;
}

/**
 * Delete a call type by index
 * @param {number} index - Index of the call to delete
 */
function deleteCall(index) {
  // Check if modifications are allowed
  if (!canModifyCalls) {
    const addCallMessages = document.getElementById('add-call-messages');
    showMessage(
      addCallMessages,
      'Cannot modify call types because this species is used by classifiers.',
      'error'
    );
    return;
  }

  // Remove from the array
  callTypes.splice(index, 1);

  // Update the JSON field and re-render the table
  updateCallTypesJson();
  renderCallsTable();
}

/**
 * Handle adding a new call from the input fields
 * @returns {boolean} True if added successfully
 */
function handleAddCall() {
  const newCallShortName = document.getElementById('new-call-short-name');
  const newCallLongName = document.getElementById('new-call-long-name');
  const addCallMessages = document.getElementById('add-call-messages');

  if (!newCallShortName) return false;

  // Get the values
  const shortName = newCallShortName.value.trim();
  const longName = newCallLongName ? newCallLongName.value.trim() : '';

  // Validate
  if (!shortName) {
    showMessage(addCallMessages, 'Short name is required', 'error');
    newCallShortName.focus();
    return false;
  }

  // Add the call
  const added = addCall(shortName, longName);

  if (added) {
    // Show success message
    showMessage(addCallMessages, `Call '${shortName}' added successfully.`);

    // Clear the inputs
    newCallShortName.value = '';
    if (newCallLongName) newCallLongName.value = '';
    newCallShortName.focus();
    return true;
  }

  return false;
}

/**
 * Setup call type management (add/delete buttons, Enter key handling)
 */
function setupCallTypeManagement() {
  const addCallButton = document.getElementById('add-call-btn');
  const newCallShortName = document.getElementById('new-call-short-name');
  const newCallLongName = document.getElementById('new-call-long-name');

  // Add new call when button is clicked
  if (addCallButton) {
    addCallButton.addEventListener('click', function (event) {
      event.preventDefault();
      handleAddCall();
    });
  }

  // Handle Enter key in call input fields
  if (newCallShortName) {
    newCallShortName.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault(); // Prevent form submission
        handleAddCall();
      }
    });
  }

  if (newCallLongName) {
    newCallLongName.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault(); // Prevent form submission
        handleAddCall();
      }
    });
  }
}

/**
 * Setup file parsing for call types
 */
function setupFileParsing() {
  const parseFileButton = document.getElementById('parse_file_btn');
  const fileLoadStatus = document.getElementById('file-load-status');

  if (!parseFileButton) return;

  parseFileButton.addEventListener('click', function () {
    const fileInput = document.getElementById('calls_file_input');
    const files = fileInput ? fileInput.files : null;

    if (!files || files.length === 0) {
      showMessage(fileLoadStatus, 'Please select a file first', 'error');
      return;
    }

    const file = files[0];
    if (file.type !== 'text/plain' && !file.name.endsWith('.txt')) {
      showMessage(fileLoadStatus, 'Please select a text file (.txt)', 'error');
      return;
    }

    // Show loading message
    showMessage(fileLoadStatus, 'Reading file...', 'success');

    // Read the file
    const reader = new FileReader();
    reader.onload = function (e) {
      const content = e.target.result;
      const lines = content.split(/\r?\n/);
      const calls = [];

      // Process each line
      lines.forEach((line) => {
        line = line.trim();
        if (!line) return; // Skip empty lines

        let shortName,
          longName = '';

        if (line.includes(',')) {
          [shortName, longName] = line.split(',', 2);
        } else if (line.includes('|')) {
          [shortName, longName] = line.split('|', 2);
        } else if (line.includes('\t')) {
          [shortName, longName] = line.split('\t', 2);
        } else {
          shortName = line;
        }

        shortName = shortName.trim();
        longName = longName ? longName.trim() : '';

        if (shortName) {
          calls.push({
            short_name: shortName,
            long_name: longName,
          });
        }
      });

      if (calls.length === 0) {
        showMessage(fileLoadStatus, 'No valid call types found in the file', 'error');
        return;
      }

      // Replace all existing calls with the ones from the file
      callTypes = calls;
      updateCallTypesJson();
      renderCallsTable();

      showMessage(
        fileLoadStatus,
        `Successfully loaded ${calls.length} call types from file`,
        'success'
      );
    };

    reader.onerror = function () {
      showMessage(fileLoadStatus, 'Error reading file', 'error');
    };

    reader.readAsText(file);
  });
}

/**
 * Setup species name validation
 * @param {string[]} existingSpeciesNames - Array of existing species names
 */
function setupNameValidation(existingSpeciesNames) {
  const speciesNameInput = document.getElementById('id_name');
  const submitButton = document.getElementById('submit-button');
  const nameErrorDiv = document.getElementById('name-error-field');

  if (!speciesNameInput || !submitButton || !nameErrorDiv) return;

  /**
   * Validate species name
   * @returns {boolean} True if valid
   */
  function validateSpeciesName() {
    const speciesName = speciesNameInput.value.trim();

    // Check if empty
    if (!speciesName) {
      nameErrorDiv.textContent = 'Please enter a species name.';
      nameErrorDiv.style.display = 'block';
      submitButton.disabled = true;
      return false;
    }

    // Check for duplicates
    if (existingSpeciesNames.includes(speciesName)) {
      nameErrorDiv.textContent = `A species with the name "${speciesName}" already exists in your group.`;
      nameErrorDiv.style.display = 'block';
      submitButton.disabled = true;
      return false;
    }

    // If we get here, name is valid
    nameErrorDiv.style.display = 'none';
    submitButton.disabled = false;
    return true;
  }

  // Check name as soon as the page loads (in case there's a default value)
  validateSpeciesName();

  // Check name as user types
  speciesNameInput.addEventListener('input', validateSpeciesName);

  // Return the validate function for form submission
  return validateSpeciesName;
}

/**
 * Setup form submission handling
 * @param {Function} validateSpeciesName - Validation function for species name
 */
function setupFormSubmission(validateSpeciesName) {
  const form = document.querySelector('form');
  const newCallShortName = document.getElementById('new-call-short-name');
  const newCallLongName = document.getElementById('new-call-long-name');

  if (!form) return;

  // Prevent form submission on Enter key press in text fields
  form.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && event.target.tagName === 'INPUT' && event.target.type === 'text') {
      // Let the call inputs handle their own Enter key
      if (event.target === newCallShortName || event.target === newCallLongName) {
        return;
      }

      // For other text inputs, prevent form submission
      event.preventDefault();
    }
  });

  // Handle form submission
  form.addEventListener('submit', function (event) {
    // Stop the form submission temporarily
    event.preventDefault();

    // Validate name one more time
    if (validateSpeciesName && !validateSpeciesName()) {
      return;
    }

    // Make sure the JSON field is up to date - this must happen BEFORE form submission
    updateCallTypesJson();

    // Continue with form submission after ensuring data is set
    this.submit();
  });
}

/**
 * Initialize the species creation page functionality
 */
export function initSpeciesCreate() {
  // Get existing species names from JSON data
  const pageData = getJsonData('species-page-data');
  const existingSpeciesNames = pageData?.existingSpeciesNames || [];

  // Set module state
  canModifyCalls = true;
  callTypes = [];

  // Initialize the table
  renderCallsTable();

  // Setup all functionality
  setupCallTypeManagement();
  setupFileParsing();
  const validateSpeciesName = setupNameValidation(existingSpeciesNames);
  setupFormSubmission(validateSpeciesName);
}

/**
 * Initialize the species edit page functionality
 */
export function initSpeciesEdit() {
  // Get page data from JSON
  const pageData = getJsonData('species-page-data');
  const existingCalls = pageData?.existingCalls || [];
  canModifyCalls = pageData?.canModifyCalls !== false; // default to true if not specified

  // Set module state
  callTypes = existingCalls.map((call) => ({
    short_name: call.short_name,
    long_name: call.long_name || '',
  }));

  // Initialize the table with existing calls
  renderCallsTable();

  // Setup functionality if modification is allowed
  if (canModifyCalls) {
    setupCallTypeManagement();
    setupFileParsing();
  } else {
    // Show a message that calls are locked
    const addCallSection = document.getElementById('add-call-section');
    if (addCallSection) {
      addCallSection.innerHTML = `
        <div class="alert alert-warning">
          <i class="fas fa-lock"></i> Call types cannot be modified because this species is used by one or more classifiers.
          Classifiers are tied to the call types of their species.
        </div>
      `;
    }
    // Hide file import section if it exists
    const fileImportSection = document.getElementById('file-import-section');
    if (fileImportSection) {
      fileImportSection.style.display = 'none';
    }
  }

  // Setup form submission (no name validation needed for edit mode)
  setupFormSubmission(null);
}

/**
 * Auto-initialize when DOM is ready
 */
export function autoInit() {
  // Only initialize if we're on a species page
  const speciesPageData = document.getElementById('species-page-data');
  if (!speciesPageData) return;

  const pageData = getJsonData('species-page-data');
  const mode = pageData?.mode || 'create';

  const initFn = mode === 'edit' ? initSpeciesEdit : initSpeciesCreate;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFn);
  } else {
    initFn();
  }
}

// Auto-initialize when this module is loaded
autoInit();

/**
 * Task Batch Name Validator
 *
 * Provides functionality to check if a task batch name already exists
 * and warn the user, without preventing them from using the name.
 */
document.addEventListener('DOMContentLoaded', function () {
  const nameInput = document.getElementById('name');
  const nameWarning = document.getElementById('name-warning');
  let checkTimeout;

  // Exit if elements don't exist on this page
  if (!nameInput || !nameWarning) return;

  // Function to check if name exists via AJAX
  function checkNameExists(name) {
    // Get the URL from the data attribute
    const checkUrl = nameInput.getAttribute('data-check-url');
    if (!checkUrl) return;

    fetch(`${checkUrl}?name=${encodeURIComponent(name)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.exists) {
          nameWarning.style.display = 'block';
        } else {
          nameWarning.style.display = 'none';
        }
      })
      .catch((error) => {
        console.error('Error checking name:', error);
        nameWarning.style.display = 'none';
      });
  }

  // Add input event listener with debounce
  nameInput.addEventListener('input', function () {
    const name = this.value.trim();

    // Clear any existing timeout
    if (checkTimeout) {
      clearTimeout(checkTimeout);
    }

    // Only check if name has content
    if (name) {
      // Set a timeout to reduce number of requests
      checkTimeout = setTimeout(() => {
        checkNameExists(name);
      }, 300); // 300ms debounce
    } else {
      nameWarning.style.display = 'none';
    }
  });

  // Check initial value
  if (nameInput.value.trim()) {
    checkNameExists(nameInput.value.trim());
  }
});

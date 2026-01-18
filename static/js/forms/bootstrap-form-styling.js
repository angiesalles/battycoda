/**
 * Bootstrap Form Styling Module
 *
 * Automatically adds Bootstrap classes to form inputs that don't have them.
 * Useful for Django-rendered forms that need Bootstrap styling.
 *
 * Usage:
 * Include this script on any page with Django forms:
 * <script src="{% static 'js/forms/bootstrap-form-styling.js' %}"></script>
 */

/**
 * Add Bootstrap form-control class to inputs that don't have it
 */
function applyBootstrapFormClasses() {
  const formInputs = document.querySelectorAll('input, select, textarea');
  formInputs.forEach((input) => {
    // Skip checkboxes, radios, and inputs that already have form-control
    if (
      !input.classList.contains('form-check-input') &&
      !input.classList.contains('form-control') &&
      input.type !== 'hidden' &&
      input.type !== 'file'
    ) {
      input.classList.add('form-control');
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', applyBootstrapFormClasses);
} else {
  applyBootstrapFormClasses();
}

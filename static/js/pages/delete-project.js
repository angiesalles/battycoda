/**
 * Delete Project Page Module
 *
 * Handles the force delete checkbox that enables the delete button
 * when the project has dependencies.
 *
 * Usage:
 * Include this script on the delete project page:
 * <script src="{% static 'js/pages/delete-project.js' %}"></script>
 */

function setupForceDeleteCheckbox() {
  const forceDeleteCheck = document.getElementById('forceDeleteCheck');
  const deleteBtn = document.getElementById('deleteBtn');

  if (forceDeleteCheck && deleteBtn) {
    forceDeleteCheck.addEventListener('change', function () {
      deleteBtn.disabled = !this.checked;
    });
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupForceDeleteCheckbox);
} else {
  setupForceDeleteCheckbox();
}

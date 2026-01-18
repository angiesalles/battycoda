/**
 * Batch Detail Page Module
 *
 * Handles the delete batch modal functionality.
 *
 * Usage:
 * Include this script on the batch detail page with data attributes on the delete button:
 * <button id="delete-batch-btn"
 *         data-batch-name="{{ batch.name }}"
 *         data-delete-url="{% url 'battycoda_app:delete_task_batch' batch.id %}">
 * <script src="{% static 'js/pages/batch-detail.js' %}"></script>
 */

function setupDeleteBatchModal() {
  const deleteBtn = document.getElementById('delete-batch-btn');
  const modalElement = document.getElementById('deleteBatchModal');
  const batchNameDisplay = document.getElementById('batch-name-display');
  const deleteForm = document.getElementById('delete-batch-form');

  if (!deleteBtn || !modalElement || !deleteForm) return;

  const modal = new bootstrap.Modal(modalElement);

  deleteBtn.addEventListener('click', function () {
    const batchName = this.getAttribute('data-batch-name');
    const deleteUrl = this.getAttribute('data-delete-url');

    // Update modal content and form action
    if (batchNameDisplay) {
      batchNameDisplay.textContent = batchName;
    }
    deleteForm.action = deleteUrl;

    modal.show();
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupDeleteBatchModal);
} else {
  setupDeleteBatchModal();
}

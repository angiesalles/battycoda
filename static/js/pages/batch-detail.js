/**
 * Batch Detail Page Module
 *
 * Handles the delete batch modal functionality.
 *
 * Usage:
 * Include this script on the batch detail page:
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
    const batchId = this.getAttribute('data-batch-id');
    const batchName = this.getAttribute('data-batch-name');

    // Update modal content and form action
    if (batchNameDisplay) {
      batchNameDisplay.textContent = batchName;
    }
    deleteForm.action = `/tasks/batches/${batchId}/delete/`;

    modal.show();
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupDeleteBatchModal);
} else {
  setupDeleteBatchModal();
}

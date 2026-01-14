function filterByCallType() {
  const select = document.getElementById('call-type-filter');
  const selectedCallType = select.value;

  // Update URL with the selected call type
  const url = new URL(window.location);
  url.searchParams.set('call_type', selectedCallType);
  window.location.href = url.toString();
}

function relabelTask(selectElement) {
  const taskId = selectElement.getAttribute('data-task-id');
  const newLabel = selectElement.value;

  if (!newLabel) {
    return;
  }

  // Show loading
  document.getElementById('loading-overlay').style.display = 'flex';

  // Prepare form data
  const formData = new FormData();
  formData.append('task_id', taskId);
  formData.append('new_label', newLabel);
  formData.append(
    'csrfmiddlewaretoken',
    document.querySelector('[name=csrfmiddlewaretoken]').value
  );

  fetch(relabelTaskUrl, {
    method: 'POST',
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      document.getElementById('loading-overlay').style.display = 'none';

      if (data.success) {
        // Show success message
        showToast('Task relabeled successfully', 'success');

        // Reload the page to reflect changes
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showToast('Error: ' + data.error, 'error');
        selectElement.value = ''; // Reset dropdown
      }
    })
    .catch((error) => {
      document.getElementById('loading-overlay').style.display = 'none';
      showToast('Error relabeling task: ' + error, 'error');
      selectElement.value = ''; // Reset dropdown
    });
}

function showToast(message, type) {
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
  toast.style.cssText = 'top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
  toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

  document.body.appendChild(toast);

  // Remove toast after 5 seconds
  setTimeout(() => {
    if (toast && toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 5000);
}

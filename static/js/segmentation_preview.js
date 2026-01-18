document.addEventListener('DOMContentLoaded', function () {
  console.log('Segmentation preview script loaded');
  const previewBtn = document.getElementById('previewBtn');
  console.log('Preview button found:', previewBtn);

  if (!previewBtn) {
    console.log('Preview button not found, exiting');
    return;
  }

  previewBtn.addEventListener('click', function () {
    const selectedAlgorithm = document.querySelector('input[name="algorithm"]:checked');
    if (!selectedAlgorithm) {
      alert('Please select an algorithm first.');
      return;
    }

    const startTime = document.getElementById('preview_start_time').value || 0;
    const minDuration = document.getElementById('min_duration_ms')?.value || 5;
    const smoothWindow = document.getElementById('smooth_window')?.value || 10;
    const thresholdFactor = document.getElementById('threshold_factor')?.value || 2.0;
    const lowFreq = document.getElementById('low_freq')?.value || '';
    const highFreq = document.getElementById('high_freq')?.value || '';

    const formData = new FormData();
    formData.append('algorithm', selectedAlgorithm.value);
    formData.append('start_time', startTime);
    formData.append('duration', '2.0');
    formData.append('min_duration_ms', minDuration);
    formData.append('smooth_window', smoothWindow);
    formData.append('threshold_factor', thresholdFactor);
    if (lowFreq) formData.append('low_freq', lowFreq);
    if (highFreq) formData.append('high_freq', highFreq);
    formData.append(
      'csrfmiddlewaretoken',
      document.querySelector('[name=csrfmiddlewaretoken]').value
    );

    const previewUrl = previewBtn.dataset.previewUrl;
    if (!previewUrl) {
      console.error('Preview URL not found in data attributes');
      return;
    }

    previewBtn.disabled = true;
    previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Preview...';

    fetch(previewUrl, {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          window.location.href = data.preview_url;
        } else {
          alert('Preview failed: ' + data.error);
          previewBtn.disabled = false;
          previewBtn.innerHTML = '<i class="fas fa-search"></i> Preview Segmentation';
        }
      })
      .catch((error) => {
        console.error('Error:', error);
        alert('An error occurred while creating preview.');
        previewBtn.disabled = false;
        previewBtn.innerHTML = '<i class="fas fa-search"></i> Preview Segmentation';
      });
  });
});

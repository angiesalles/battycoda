/**
 * Cluster Explorer Data Loader Module
 *
 * Handles saving cluster labels and descriptions.
 */

import { getSelectedClusterId } from './state.js';
import { getCsrfToken } from '../utils/page-data.js';
import { API_ENDPOINTS } from './api.js';

/**
 * Save the cluster label and description
 * @param {Function} onSuccess - Callback on successful save
 */
export function saveClusterLabel(onSuccess) {
  const $ = window.jQuery;
  if (!$) return;

  const selectedId = getSelectedClusterId();
  if (!selectedId) return;

  const label = $('#cluster-label').val();
  const description = $('#cluster-description').val();

  // Show a loading indicator
  const saveBtn = $('#save-cluster-label');
  const originalText = saveBtn.html();
  saveBtn.html('<span class="spinner-border spinner-border-sm"></span> Saving...');
  saveBtn.attr('disabled', true);

  // Make an AJAX request to update the label
  $.ajax({
    url: API_ENDPOINTS.UPDATE_CLUSTER_LABEL,
    type: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() },
    data: {
      cluster_id: selectedId,
      label: label,
      description: description,
    },
    success: function (data) {
      if (data.status === 'success') {
        // Update the local data if clusters array exists
        if (typeof window.clusters !== 'undefined') {
          const cluster = window.clusters.find((c) => c.id === selectedId);
          if (cluster) {
            cluster.label = label;
            cluster.description = description;
            cluster.is_labeled = !!label;
          }
        }

        // Show a success message
        if (typeof window.toastr !== 'undefined') {
          window.toastr.success('Cluster label updated successfully');
        } else {
          alert('Cluster label updated successfully');
        }

        // Call the success callback
        if (onSuccess) onSuccess(selectedId);
      } else {
        if (typeof window.toastr !== 'undefined') {
          window.toastr.error(`Failed to update label: ${data.message}`);
        } else {
          alert(`Failed to update label: ${data.message}`);
        }
      }
    },
    error: function () {
      if (typeof window.toastr !== 'undefined') {
        window.toastr.error('Failed to update cluster label. Please try again.');
      } else {
        alert('Failed to update cluster label. Please try again.');
      }
    },
    complete: function () {
      saveBtn.html(originalText);
      saveBtn.attr('disabled', false);
    },
  });
}

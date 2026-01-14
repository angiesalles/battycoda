/**
 * Cluster Explorer Controls Module
 *
 * Handles UI controls and segment detail loading.
 */

import { getSelectedClusterId } from './state.js';

/**
 * Load segment details into the modal
 * @param {number} segmentId - Segment ID to load
 */
export function loadSegmentDetails(segmentId) {
  const $ = window.jQuery;
  if (!$) return;

  // Show a loading indicator in the modal
  $('.segment-spectrogram').html('<div class="spinner-border text-primary"></div>');
  $('.segment-audio-player').attr('src', '');
  $('.segment-id').text('Loading...');
  $('.segment-recording').text('Loading...');
  $('.segment-onset').text('Loading...');
  $('.segment-offset').text('Loading...');
  $('.segment-duration').text('Loading...');

  // Load the segment details from the API
  $.getJSON(`/clustering/get-segment-data/?segment_id=${segmentId}`, function (data) {
    if (data.status === 'success') {
      $('.segment-id').text(data.segment_id);
      $('.segment-recording').text(data.recording_name);
      $('.segment-onset').text(data.onset.toFixed(4));
      $('.segment-offset').text(data.offset.toFixed(4));
      $('.segment-duration').text(data.duration.toFixed(4));

      $('.segment-spectrogram').html(`
                <img src="${data.spectrogram_url}" class="img-fluid" alt="Segment Spectrogram">
            `);

      $('.segment-audio-player').attr('src', data.audio_url);
    } else {
      $('.segment-spectrogram').html(
        `<div class="alert alert-danger">Failed to load segment: ${data.message}</div>`
      );
    }
  }).fail(function () {
    $('.segment-spectrogram').html(
      '<div class="alert alert-danger">Failed to load segment. Please try again.</div>'
    );
  });
}

/**
 * Initialize control event handlers
 * @param {Function} onPointSizeChange - Callback when point size changes
 * @param {Function} onOpacityChange - Callback when opacity changes
 */
export function initializeControls(onPointSizeChange, onOpacityChange) {
  const $ = window.jQuery;
  const d3 = window.d3;
  if (!$ || !d3) return;

  $('#point-size').on('input', function () {
    const size = parseInt($(this).val());
    const selectedId = getSelectedClusterId();
    d3.selectAll('.cluster-point').attr('r', (d) => (d.id === selectedId ? size * 1.5 : size));
    if (onPointSizeChange) onPointSizeChange(size);
  });

  $('#cluster-opacity').on('input', function () {
    const opacity = parseFloat($(this).val());
    d3.selectAll('.cluster-point').attr('opacity', opacity);
    if (onOpacityChange) onOpacityChange(opacity);
  });
}

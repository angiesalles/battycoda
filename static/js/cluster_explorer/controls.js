/**
 * Cluster Explorer Controls Module
 *
 * Handles UI controls and segment detail loading.
 * D3 is now bundled via npm for tree-shaking benefits.
 */

import { selectAll } from 'd3-selection';
import { getSelectedClusterId } from './state.js';
import { escapeHtml } from '../utils/html.js';

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
        `<div class="alert alert-danger">Failed to load segment: ${escapeHtml(data.message)}</div>`
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
  if (!$) return;

  // Clean up existing handlers to prevent duplicates on re-initialization
  $('#point-size').off('input');
  $('#cluster-opacity').off('input');

  $('#point-size').on('input', function () {
    const size = parseInt($(this).val());
    const selectedId = getSelectedClusterId();
    selectAll('.cluster-point').attr('r', (d) => (d.id === selectedId ? size * 1.5 : size));
    if (onPointSizeChange) onPointSizeChange(size);
  });

  $('#cluster-opacity').on('input', function () {
    const opacity = parseFloat($(this).val());
    selectAll('.cluster-point').attr('opacity', opacity);
    if (onOpacityChange) onOpacityChange(opacity);
  });
}

/**
 * Segment Display Manager - Handles UI display of segments
 */

import { escapeHtml } from '../utils/html.js';

export class SegmentDisplay {
  constructor(playerId, readOnly = false) {
    this.playerId = playerId;
    this.readOnly = readOnly;
    this.paginationInfo = null;
  }

  // Get segments that are visible in current viewport
  getVisibleSegments(allSegments) {
    console.log('getVisibleSegments called with', allSegments.length, 'segments');

    if (!window.players || !window.players[this.playerId]) {
      console.log('No player found, returning all segments');
      return allSegments; // Return all if no player
    }

    const playerWrapper = window.players[this.playerId];
    const player = playerWrapper.player;
    console.log('Player zoom level:', player?.zoomLevel);

    if (!player || player.zoomLevel <= 1) {
      console.log('Not zoomed in, returning all segments');
      return allSegments; // Return all if not zoomed
    }

    // Calculate visible time range
    const visibleDuration = player.duration / player.zoomLevel;
    const visibleStartTime = player.zoomOffset * player.duration;
    const visibleEndTime = Math.min(visibleStartTime + visibleDuration, player.duration);

    // Filter segments that overlap with visible range
    return allSegments
      .filter((segment) => {
        return segment.offset >= visibleStartTime && segment.onset <= visibleEndTime;
      })
      .sort((a, b) => a.onset - b.onset);
  }

  // Update segments count display
  updateSegmentsCount(count) {
    const countElement = document.getElementById('segments-count');
    if (countElement) {
      countElement.textContent = count;
    }
  }

  // Render the segments list in the table with pagination
  renderSegmentsList(segments, paginationInfo = null) {
    this.paginationInfo = paginationInfo;

    const segmentsList = document.getElementById('segments-list');
    if (!segmentsList) return;

    // Clear existing rows
    segmentsList.innerHTML = '';

    // Add new rows
    segments.forEach((segment) => {
      const row = document.createElement('tr');
      row.id = `segment-row-${segment.id}`;
      row.dataset.segmentId = segment.id;
      row.style.cursor = 'pointer';

      const durationMs = ((segment.offset - segment.onset) * 1000).toFixed(1);

      row.innerHTML = `
                <td>${segment.id}</td>
                <td>${segment.onset.toFixed(2)}s - ${segment.offset.toFixed(2)}s</td>
                <td>${durationMs}ms</td>
                <td>
                    <div class="segment-actions" data-segment-id="${segment.id}"
                         data-onset="${segment.onset}" data-offset="${segment.offset}"
                         data-name="${escapeHtml(segment.name || '')}"
                         data-notes="${escapeHtml(segment.notes || '')}"></div>
                </td>
            `;

      // Make row clickable to seek to segment position
      row.addEventListener('click', (e) => {
        // Don't trigger if clicking on action buttons
        if (e.target.closest('.segment-actions')) return;

        const player = window.players?.[this.playerId];
        if (player?.player) {
          player.player.seek(segment.onset);
        }
      });

      segmentsList.appendChild(row);
    });

    // Re-render action buttons for each segment
    const actionContainers = segmentsList.querySelectorAll('.segment-actions');
    actionContainers.forEach((container) => {
      this.renderSegmentActionButtons(container);
    });

    // Show/hide the table and no-segments message
    this.toggleTableVisibility(segments.length > 0);

    // Render pagination controls if pagination info provided
    if (paginationInfo) {
      this.renderPaginationControls(paginationInfo);
    }
  }

  // Toggle table visibility based on whether there are segments
  toggleTableVisibility(hasSegments) {
    const tableContainer = document.querySelector('#segments-list')?.closest('.table-responsive');
    const noSegmentsMessage = document.getElementById('no-segments-message');

    if (hasSegments) {
      if (tableContainer) tableContainer.style.display = 'block';
      if (noSegmentsMessage) noSegmentsMessage.style.display = 'none';
    } else {
      if (tableContainer) tableContainer.style.display = 'none';
      if (noSegmentsMessage) noSegmentsMessage.style.display = 'block';
    }
  }

  // Render action buttons for a segment
  renderSegmentActionButtons(container) {
    if (!container) return;

    const segmentId = container.dataset.segmentId;
    const onset = parseFloat(container.dataset.onset);
    const offset = parseFloat(container.dataset.offset);

    if (this.readOnly) {
      container.innerHTML = `
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-success btn-sm" onclick="window.battycoda?.segmentation?.['${this.playerId}']?.playSegment(${onset}, ${offset})">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
            `;
    } else {
      container.innerHTML = `
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-success btn-sm" onclick="window.battycoda?.segmentation?.['${this.playerId}']?.playSegment(${onset}, ${offset})">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="window.battycoda?.segmentation?.['${this.playerId}']?.deleteSegment(${segmentId})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
    }
  }

  // Render pagination controls
  renderPaginationControls(paginationInfo) {
    const container = document.getElementById('segment-pagination-controls');
    if (!container) return;

    if (paginationInfo.totalPages <= 1) {
      container.style.display = 'none';
      return;
    }

    container.style.display = 'block';

    // Generate page numbers to display (max 7 pages)
    const pages = this.calculatePageNumbers(paginationInfo.currentPage, paginationInfo.totalPages);

    let html =
      '<nav aria-label="Segments pagination"><ul class="pagination pagination-sm mb-0 justify-content-center">';

    // First and Previous buttons
    if (paginationInfo.hasPrevious) {
      html += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="1" aria-label="First">
                        <span aria-hidden="true">&laquo;&laquo;</span>
                    </a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${paginationInfo.currentPage - 1}" aria-label="Previous">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
            `;
    }

    // Page numbers
    pages.forEach((page) => {
      if (page === '...') {
        html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
      } else if (page === paginationInfo.currentPage) {
        html += `<li class="page-item active"><span class="page-link">${page}</span></li>`;
      } else {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${page}">${page}</a></li>`;
      }
    });

    // Next and Last buttons
    if (paginationInfo.hasNext) {
      html += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${paginationInfo.currentPage + 1}" aria-label="Next">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${paginationInfo.totalPages}" aria-label="Last">
                        <span aria-hidden="true">&raquo;&raquo;</span>
                    </a>
                </li>
            `;
    }

    html += '</ul></nav>';

    // Pagination info text
    html += `<div class="text-center mt-2"><small class="text-muted">
            Showing ${paginationInfo.startIdx}-${paginationInfo.endIdx} of ${paginationInfo.totalSegments} segments
        </small></div>`;

    container.innerHTML = html;

    // Add click handlers
    container.querySelectorAll('a.page-link').forEach((link) => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = parseInt(e.currentTarget.dataset.page);
        this.onPageChange?.(page);
      });
    });
  }

  // Calculate which page numbers to show
  calculatePageNumbers(currentPage, totalPages) {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const pages = [];

    // Always show first page
    pages.push(1);

    if (currentPage > 3) {
      pages.push('...');
    }

    // Show pages around current page
    for (
      let i = Math.max(2, currentPage - 1);
      i <= Math.min(totalPages - 1, currentPage + 1);
      i++
    ) {
      pages.push(i);
    }

    if (currentPage < totalPages - 2) {
      pages.push('...');
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  }

  // Set page change callback
  setPageChangeHandler(callback) {
    this.onPageChange = callback;
  }
}

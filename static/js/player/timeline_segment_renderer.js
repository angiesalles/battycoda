/**
 * Timeline Segment Renderer - Handles rendering segments on the timeline
 */

export class SegmentRenderer {
  constructor(dragHandler, effectsHandler) {
    this.dragHandler = dragHandler;
    this.effectsHandler = effectsHandler;
  }

  /**
   * Calculate segment position in pixels
   */
  calculateSegmentPosition(segment, startTime, visibleDuration, width) {
    const segmentStartTime = segment.onset;
    const segmentEndTime = segment.offset;

    // Convert to pixel positions
    const segmentStart = ((segmentStartTime - startTime) / visibleDuration) * width;
    const segmentEnd = ((segmentEndTime - startTime) / visibleDuration) * width;

    // Clip to visible area
    const visibleStart = Math.max(0, segmentStart);
    const visibleEnd = Math.min(width, segmentEnd);
    const visibleWidth = visibleEnd - visibleStart;

    return {
      segmentStartTime,
      segmentEndTime,
      segmentStart,
      segmentEnd,
      visibleStart,
      visibleEnd,
      visibleWidth,
    };
  }

  /**
   * Create segment marker DOM element
   */
  createSegmentMarker(segment, positions) {
    const segmentMarker = document.createElement('div');
    segmentMarker.className = 'position-absolute';
    segmentMarker.style.left = positions.visibleStart + 'px';
    segmentMarker.style.width = positions.visibleWidth + 'px';
    segmentMarker.style.top = '5px';
    segmentMarker.style.height = '20px';
    segmentMarker.style.backgroundColor = '#007bff';
    segmentMarker.style.opacity = '0.7';
    segmentMarker.style.borderRadius = '2px';
    segmentMarker.style.cursor = 'move';
    segmentMarker.title = `Segment ${segment.id}: ${segment.onset.toFixed(2)}s - ${segment.offset.toFixed(2)}s`;

    segmentMarker.dataset.segmentId = segment.id;
    segmentMarker.dataset.segmentStart = positions.segmentStartTime;
    segmentMarker.dataset.segmentEnd = positions.segmentEndTime;

    return segmentMarker;
  }

  /**
   * Add clipping indicators for segments partially outside view
   */
  addClippingIndicators(segmentMarker, positions, width) {
    if (positions.segmentStart < 0) {
      segmentMarker.style.borderLeftWidth = '3px';
      segmentMarker.style.borderLeftStyle = 'dashed';
      segmentMarker.style.borderLeftColor = '#ff9800';
    }

    if (positions.segmentEnd > width) {
      segmentMarker.style.borderRightWidth = '3px';
      segmentMarker.style.borderRightStyle = 'dashed';
      segmentMarker.style.borderRightColor = '#ff9800';
    }
  }

  /**
   * Scroll to a segment in the segment list
   */
  scrollToSegmentInList(segmentId) {
    // Clear previous selection
    const prev = document.querySelector('tr.segment-row-selected');
    if (prev) prev.classList.remove('segment-row-selected');

    const segmentRow = document.getElementById(`segment-row-${segmentId}`);

    if (segmentRow) {
      segmentRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
      segmentRow.classList.add('segment-row-selected');
    } else {
      // Segment not visible in current page/filter - try to navigate to it
      const segmentManager = window.battycoda?.segmentation;
      if (segmentManager) {
        const managerInstance = Object.values(segmentManager)[0];
        if (managerInstance) {
          this.navigateToSegmentInList(managerInstance, segmentId);
        }
      }
    }
  }

  /**
   * Navigate to a segment in the paginated/filtered list
   */
  navigateToSegmentInList(segmentManager, segmentId) {
    // Find the segment in the full segments array
    const segment = segmentManager.segments.find((s) => s.id === segmentId);
    if (!segment) {
      return;
    }

    // Clear any filters that might be hiding the segment
    const searchIdInput = document.getElementById('segment-search-id');
    const minDurationInput = document.getElementById('segment-search-min-duration');
    const maxDurationInput = document.getElementById('segment-search-max-duration');

    if (searchIdInput) searchIdInput.value = '';
    if (minDurationInput) minDurationInput.value = '';
    if (maxDurationInput) maxDurationInput.value = '';

    segmentManager.searchPagination.clearFilters();

    // Filter segments and find which page the segment is on
    const filteredSegments = segmentManager.searchPagination.filterSegments(
      segmentManager.segments
    );
    const segmentIndex = filteredSegments.findIndex((s) => s.id === segmentId);

    if (segmentIndex >= 0) {
      const pageSize = segmentManager.searchPagination.pageSize;
      const targetPage = Math.floor(segmentIndex / pageSize) + 1;

      // Navigate to the page containing the segment
      segmentManager.searchPagination.setPage(targetPage);
      segmentManager.updateSegmentsList();

      // Wait for the list to render, then scroll to the segment
      setTimeout(() => {
        const segmentRow = document.getElementById(`segment-row-${segmentId}`);
        if (segmentRow) {
          segmentRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
          segmentRow.classList.add('segment-row-selected');
        }
      }, 100);
    }
  }

  /**
   * Draw all segments on the timeline
   */
  draw(container, segments, width, startTime, visibleDuration, waveformContainer) {
    segments.forEach((segment) => {
      const positions = this.calculateSegmentPosition(segment, startTime, visibleDuration, width);

      // Skip segments outside the visible range
      if (positions.segmentEnd < 0 || positions.segmentStart > width) {
        return;
      }

      // Create segment marker
      if (positions.visibleWidth > 0) {
        const segmentMarker = this.createSegmentMarker(segment, positions);

        // Add click handler to scroll to segment in list
        segmentMarker.addEventListener('click', () => {
          this.scrollToSegmentInList(segment.id);
        });

        // Add hover effects
        this.effectsHandler.addSegmentHoverEffects(segmentMarker, positions, waveformContainer);

        // Add clipping indicators
        this.addClippingIndicators(segmentMarker, positions, width);

        // Add draggable handles if segment is fully visible
        if (positions.segmentStart >= 0 && positions.segmentEnd <= width) {
          this.dragHandler.addDraggableHandles(segmentMarker, segment, startTime, visibleDuration);
        }

        container.appendChild(segmentMarker);
      }
    });
  }
}

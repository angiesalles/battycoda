/**
 * BattyCoda Waveform Player - Timeline Renderer
 *
 * Responsible for drawing the timeline below the waveform
 */

import { SegmentDragHandler } from './segment_drag_handler.js';
import { TimeMarkers } from './timeline_time_markers.js';
import { SegmentRenderer } from './timeline_segment_renderer.js';
import { SegmentEffects } from './timeline_segment_effects.js';

export class TimelineRenderer {
  /**
   * Create a new TimelineRenderer
   * @param {Object} player - The parent WaveformPlayer instance
   */
  constructor(player) {
    this.player = player;
    this.dragHandler = new SegmentDragHandler(player);
    this.effectsHandler = new SegmentEffects();
    this.timeMarkers = new TimeMarkers();
    this.segmentRenderer = new SegmentRenderer(this.dragHandler, this.effectsHandler);
  }

  /**
   * Draw the timeline
   */
  draw() {
    const player = this.player;
    if (!player.timelineContainer) return;

    // Remove any existing hover lines from the waveform container
    if (player.waveformContainer) {
      const hoverLines = player.waveformContainer.querySelectorAll('.segment-hover-line');
      hoverLines.forEach((line) => line.remove());
    }

    // Clear timeline
    player.timelineContainer.innerHTML = '';

    // If no duration, draw a simple timeline
    if (!player.duration) {
      this.drawSimpleTimeline();
      return;
    }

    // Calculate visible range based on zoom
    const visibleDuration = player.duration / player.zoomLevel;
    const startTime = player.zoomOffset * player.duration;
    const endTime = Math.min(startTime + visibleDuration, player.duration);
    const width = player.timelineContainer.clientWidth;

    // Draw time markers
    this.timeMarkers.draw(
      player.timelineContainer,
      width,
      player.duration,
      startTime,
      endTime,
      visibleDuration
    );

    // Draw segments if available
    this.segmentRenderer.draw(
      player.timelineContainer,
      player.segments,
      width,
      startTime,
      visibleDuration,
      player.waveformContainer
    );
  }

  /**
   * Draw a simple timeline when no duration is available
   */
  drawSimpleTimeline() {
    const player = this.player;

    // Draw a simple timeline with 0 and duration markers
    const simpleDuration = 60; // Default 60 seconds if no duration available
    const width = player.timelineContainer.clientWidth;

    // Start marker (0s)
    const startMarker = document.createElement('div');
    startMarker.className = 'position-absolute';
    startMarker.style.left = '0px';
    startMarker.style.top = '0';
    startMarker.style.bottom = '0';
    startMarker.style.width = '1px';
    startMarker.style.backgroundColor = '#6c757d';

    const startLabel = document.createElement('div');
    startLabel.className = 'position-absolute text-light small';
    startLabel.style.left = '0px';
    startLabel.style.bottom = '0';
    startLabel.textContent = '0.0s';

    // End marker
    const endMarker = document.createElement('div');
    endMarker.className = 'position-absolute';
    endMarker.style.left = width - 1 + 'px';
    endMarker.style.top = '0';
    endMarker.style.bottom = '0';
    endMarker.style.width = '1px';
    endMarker.style.backgroundColor = '#6c757d';

    const endLabel = document.createElement('div');
    endLabel.className = 'position-absolute text-light small';
    endLabel.style.left = width - 30 + 'px';
    endLabel.style.bottom = '0';
    endLabel.textContent = simpleDuration.toFixed(1) + 's';

    player.timelineContainer.appendChild(startMarker);
    player.timelineContainer.appendChild(startLabel);
    player.timelineContainer.appendChild(endMarker);
    player.timelineContainer.appendChild(endLabel);
  }
}

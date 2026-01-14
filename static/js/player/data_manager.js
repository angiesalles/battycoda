/**
 * BattyCoda Waveform Player - Data Management
 *
 * Handles segments, selection, and time calculations
 */

export class DataManager {
  constructor(player) {
    this.player = player;
  }

  /**
   * Get the current selection
   * @returns {Object} Selection object with start and end times
   */
  getSelection() {
    return {
      start: this.player.selectionStart,
      end: this.player.selectionEnd,
    };
  }

  /**
   * Check if a given time is within any existing segment
   * @param {number} time - Time to check
   * @returns {boolean} True if time is within a segment
   */
  isTimeInSegment(time) {
    if (!this.player.segments || !this.player.segments.length) return false;

    return this.player.segments.some((segment) => {
      const onset = segment.onset;
      const offset = segment.offset;
      return time >= onset && time <= offset;
    });
  }

  /**
   * Find the nearest segment boundary from a given time
   * @param {number} time - Starting time
   * @param {string} direction - 'forward' or 'backward'
   * @returns {number|null} Time of nearest boundary, or null if none found
   */
  findNearestSegmentBoundary(time, direction = 'forward') {
    if (!this.player.segments || !this.player.segments.length) return null;

    let nearestBoundary = null;
    let nearestDistance = Infinity;

    this.player.segments.forEach((segment) => {
      const boundaries = [segment.onset, segment.offset];
      boundaries.forEach((boundary) => {
        const distance = direction === 'forward' ? boundary - time : time - boundary;
        if (distance > 0 && distance < nearestDistance) {
          nearestDistance = distance;
          nearestBoundary = boundary;
        }
      });
    });

    if (direction === 'forward') {
      return nearestBoundary;
    } else {
      return nearestBoundary;
    }
  }

  /**
   * Set segments for the waveform
   * @param {Array} newSegments - Array of segment objects
   */
  setSegments(newSegments) {
    this.player.segments = newSegments || [];
    this.player.redrawCurrentView();
    this.player.drawTimeline();
  }

  /**
   * Redraw segments on the waveform
   * Called when a new segment is added
   */
  redrawSegments() {
    this.player.redrawCurrentView();
  }
}

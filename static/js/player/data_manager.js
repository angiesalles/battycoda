/**
 * BattyCoda Waveform Player - Data Management
 *
 * Handles segments, selection, and time calculations
 *
 * Dependencies (injected via constructor):
 * - getSelectionStart: () => number - Returns current selection start time
 * - getSelectionEnd: () => number - Returns current selection end time
 * - getSegments: () => Array - Returns current segments array
 * - setSegmentsData: (segments: Array) => void - Sets segments array
 * - redrawCurrentView: () => void - Callback to redraw the view
 * - drawTimeline: () => void - Callback to redraw the timeline
 */

export class DataManager {
  /**
   * Create a DataManager instance
   * @param {Object} deps - Dependencies object or legacy player object
   * @param {Function} [deps.getSelectionStart] - Returns selection start time
   * @param {Function} [deps.getSelectionEnd] - Returns selection end time
   * @param {Function} [deps.getSegments] - Returns segments array
   * @param {Function} [deps.setSegmentsData] - Sets segments array
   * @param {Function} [deps.redrawCurrentView] - Callback to redraw view
   * @param {Function} [deps.drawTimeline] - Callback to redraw timeline
   */
  constructor(deps) {
    // Detect if this is the new dependency injection style or legacy player object
    const isLegacy = deps && typeof deps.redrawCurrentView === 'function' && !deps.getSegments;

    if (isLegacy) {
      // Legacy mode: deps is actually a player object
      const player = deps;
      this._getSelectionStart = () => player.selectionStart;
      this._getSelectionEnd = () => player.selectionEnd;
      this._getSegments = () => player.segments;
      this._setSegmentsData = (segments) => {
        player.segments = segments;
      };
      this._redrawCurrentView = () => player.redrawCurrentView();
      this._drawTimeline = () => player.drawTimeline();
      // Keep player reference for backward compatibility in tests
      this.player = player;
    } else {
      // New dependency injection style
      this._getSelectionStart = deps.getSelectionStart;
      this._getSelectionEnd = deps.getSelectionEnd;
      this._getSegments = deps.getSegments;
      this._setSegmentsData = deps.setSegmentsData;
      this._redrawCurrentView = deps.redrawCurrentView;
      this._drawTimeline = deps.drawTimeline;
    }
  }

  /**
   * Get the current selection
   * @returns {Object} Selection object with start and end times
   */
  getSelection() {
    return {
      start: this._getSelectionStart(),
      end: this._getSelectionEnd(),
    };
  }

  /**
   * Check if a given time is within any existing segment
   * @param {number} time - Time to check
   * @returns {boolean} True if time is within a segment
   */
  isTimeInSegment(time) {
    const segments = this._getSegments();
    if (!segments || !segments.length) return false;

    return segments.some((segment) => {
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
    const segments = this._getSegments();
    if (!segments || !segments.length) return null;

    let nearestBoundary = null;
    let nearestDistance = Infinity;

    segments.forEach((segment) => {
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
    this._setSegmentsData(newSegments || []);
    this._redrawCurrentView();
    this._drawTimeline();
  }

  /**
   * Redraw segments on the waveform
   * Called when a new segment is added
   */
  redrawSegments() {
    this._redrawCurrentView();
  }
}

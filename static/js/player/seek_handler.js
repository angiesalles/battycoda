/**
 * BattyCoda Waveform Player - Seek Handler
 *
 * Handles seeking to specific times and ensuring playhead visibility
 *
 * Required dependencies (injected via constructor):
 * - audioPlayer: HTMLAudioElement - The audio element to control
 * - getDuration: () => number - Returns audio duration
 * - getZoomLevel: () => number - Returns current zoom level
 * - setCurrentTime: (time: number) => void - Sets internal current time
 * - setZoomOffset: (offset: number) => void - Sets zoom offset
 * - updateTimeDisplay: () => void - Callback to update time display
 * - redrawCurrentView: () => void - Callback to redraw view
 * - drawTimeline: () => void - Callback to redraw timeline
 */

export class SeekHandler {
  /**
   * Create a SeekHandler instance
   * @param {Object} deps - Dependencies object
   * @param {HTMLAudioElement} deps.audioPlayer - Audio element
   * @param {Function} deps.getDuration - Returns audio duration
   * @param {Function} deps.getZoomLevel - Returns zoom level
   * @param {Function} deps.setCurrentTime - Sets current time
   * @param {Function} deps.setZoomOffset - Sets zoom offset
   * @param {Function} deps.updateTimeDisplay - Update time display callback
   * @param {Function} deps.redrawCurrentView - Redraw view callback
   * @param {Function} deps.drawTimeline - Draw timeline callback
   */
  constructor(deps) {
    this._audioPlayer = deps.audioPlayer;
    this._getDuration = deps.getDuration;
    this._getZoomLevel = deps.getZoomLevel;
    this._setCurrentTime = deps.setCurrentTime;
    this._setZoomOffset = deps.setZoomOffset;
    this._updateTimeDisplay = deps.updateTimeDisplay;
    this._redrawCurrentView = deps.redrawCurrentView;
    this._drawTimeline = deps.drawTimeline;
  }

  /**
   * Seek to a specific time and ensure it's visible in the viewport
   * @param {number} time - Time in seconds to seek to
   */
  seek(time) {
    const duration = this._getDuration();

    // Clamp to valid range
    time = Math.max(0, Math.min(time, duration));

    // Update audio player and internal time
    if (this._audioPlayer) {
      this._audioPlayer.currentTime = time;
    }
    this._setCurrentTime(time);

    // If zoomed in, center the view on this time
    const zoomLevel = this._getZoomLevel();
    if (zoomLevel > 1) {
      const timeRatio = time / duration;
      const visibleDuration = 1 / zoomLevel;

      // Center the view on the seek position
      this._setZoomOffset(Math.max(0, Math.min(timeRatio - visibleDuration / 2, 1 - visibleDuration)));
    }

    // Update displays
    this._updateTimeDisplay();
    this._redrawCurrentView();
    this._drawTimeline();
  }
}

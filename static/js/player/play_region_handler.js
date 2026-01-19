/**
 * BattyCoda Waveform Player - Play Region Handler
 *
 * Handles playing a specific region (start to end time) of audio
 *
 * Dependencies (injected via constructor):
 * - audioPlayer: HTMLAudioElement - The audio element to control
 * - getDuration: () => number - Returns audio duration
 * - getZoomLevel: () => number - Returns current zoom level
 * - setZoomLevel: (level: number) => void - Sets zoom level
 * - setZoomOffset: (offset: number) => void - Sets zoom offset
 * - seek: (time: number) => void - Seek to a specific time
 * - redrawCurrentView: () => void - Callback to redraw view
 * - drawTimeline: () => void - Callback to redraw timeline
 * - updateTimeDisplay: () => void - Callback to update time display
 */

export class PlayRegionHandler {
  /**
   * Create a PlayRegionHandler instance
   * @param {Object} deps - Dependencies object or legacy player object
   * @param {HTMLAudioElement} [deps.audioPlayer] - Audio element
   * @param {Function} [deps.getDuration] - Returns audio duration
   * @param {Function} [deps.getZoomLevel] - Returns zoom level
   * @param {Function} [deps.setZoomLevel] - Sets zoom level
   * @param {Function} [deps.setZoomOffset] - Sets zoom offset
   * @param {Function} [deps.seek] - Seek to time
   * @param {Function} [deps.redrawCurrentView] - Redraw view callback
   * @param {Function} [deps.drawTimeline] - Draw timeline callback
   * @param {Function} [deps.updateTimeDisplay] - Update time display callback
   */
  constructor(deps) {
    // Detect if this is the new dependency injection style or legacy player object
    const isLegacy = deps && typeof deps.redrawCurrentView === 'function' && !deps.getDuration;

    if (isLegacy) {
      // Legacy mode: deps is actually a player object
      const player = deps;
      // Use getter to access audioPlayer dynamically (allows tests to modify it)
      this._getAudioPlayer = () => player.audioPlayer;
      this._getDuration = () => player.duration;
      this._getZoomLevel = () => player.zoomLevel;
      this._setZoomLevel = (level) => {
        player.zoomLevel = level;
      };
      this._setZoomOffset = (offset) => {
        player.zoomOffset = offset;
      };
      this._seek = (time) => player.seek(time);
      this._redrawCurrentView = () => player.redrawCurrentView();
      this._drawTimeline = () => player.drawTimeline();
      this._updateTimeDisplay = () => player.updateTimeDisplay();
      // Keep player reference for backward compatibility in tests
      this.player = player;
    } else {
      // New dependency injection style
      this._getAudioPlayer = () => deps.audioPlayer;
      this._getDuration = deps.getDuration;
      this._getZoomLevel = deps.getZoomLevel;
      this._setZoomLevel = deps.setZoomLevel;
      this._setZoomOffset = deps.setZoomOffset;
      this._seek = deps.seek;
      this._redrawCurrentView = deps.redrawCurrentView;
      this._drawTimeline = deps.drawTimeline;
      this._updateTimeDisplay = deps.updateTimeDisplay;
    }

    this._stopAtEndListener = null;
  }

  /**
   * Play a region of audio from start to end time
   * @param {number} start - Start time in seconds
   * @param {number} end - End time in seconds
   */
  playRegion(start, end) {
    const audioPlayer = this._getAudioPlayer();
    if (!audioPlayer) return;

    // Remove any existing listener from previous playRegion call
    this._cleanupListener();

    // Seek to start position
    this._seek(start);

    // Start playback
    audioPlayer.play();

    // Set up a one-time event listener to stop playback at end time
    this._stopAtEndListener = () => {
      if (audioPlayer.currentTime >= end) {
        audioPlayer.pause();
        this._cleanupListener();
      }
    };

    audioPlayer.addEventListener('timeupdate', this._stopAtEndListener);

    // If the region is completely zoomed out, zoom in on it
    this._zoomToRegionIfNeeded(start, end);
  }

  /**
   * Zoom to show a region if needed
   * @param {number} start - Start time in seconds
   * @param {number} end - End time in seconds
   */
  _zoomToRegionIfNeeded(start, end) {
    const duration = this._getDuration();
    const zoomLevel = this._getZoomLevel();

    // Only zoom if currently at default zoom level and region is less than half the duration
    if (zoomLevel === 1 && end - start < duration / 2) {
      // Calculate needed zoom level to show the segment with padding
      const padding = 0.2; // 20% padding on each side
      const segmentDuration = end - start;
      const desiredDuration = segmentDuration * (1 + 2 * padding);
      const newZoomLevel = Math.min(duration / desiredDuration, 10);

      // Set zoom level
      this._setZoomLevel(newZoomLevel);

      // Center the segment in the view
      const segmentCenter = (start + end) / 2;
      const visibleDuration = duration / newZoomLevel;
      this._setZoomOffset(
        Math.max(0, Math.min(segmentCenter / duration - visibleDuration / duration / 2, 1 - visibleDuration / duration))
      );

      // Update displays
      this._redrawCurrentView();
      this._drawTimeline();
      this._updateTimeDisplay();
    }
  }

  /**
   * Clean up the timeupdate listener
   */
  _cleanupListener() {
    const audioPlayer = this._getAudioPlayer();
    if (this._stopAtEndListener && audioPlayer) {
      audioPlayer.removeEventListener('timeupdate', this._stopAtEndListener);
      this._stopAtEndListener = null;
    }
  }

  /**
   * Stop region playback and clean up
   */
  stop() {
    this._cleanupListener();
    const audioPlayer = this._getAudioPlayer();
    if (audioPlayer) {
      audioPlayer.pause();
    }
  }
}

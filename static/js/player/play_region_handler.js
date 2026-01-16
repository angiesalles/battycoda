/**
 * BattyCoda Waveform Player - Play Region Handler
 *
 * Handles playing a specific region (start to end time) of audio
 */

export class PlayRegionHandler {
  constructor(player) {
    this.player = player;
    this._stopAtEndListener = null;
  }

  /**
   * Play a region of audio from start to end time
   * @param {number} start - Start time in seconds
   * @param {number} end - End time in seconds
   */
  playRegion(start, end) {
    if (!this.player.audioPlayer) return;

    // Remove any existing listener from previous playRegion call
    this._cleanupListener();

    // Seek to start position
    this.player.seek(start);

    // Start playback
    this.player.audioPlayer.play();

    // Set up a one-time event listener to stop playback at end time
    this._stopAtEndListener = () => {
      if (this.player.audioPlayer.currentTime >= end) {
        this.player.audioPlayer.pause();
        this._cleanupListener();
      }
    };

    this.player.audioPlayer.addEventListener('timeupdate', this._stopAtEndListener);

    // If the region is completely zoomed out, zoom in on it
    this._zoomToRegionIfNeeded(start, end);
  }

  /**
   * Zoom to show a region if needed
   * @param {number} start - Start time in seconds
   * @param {number} end - End time in seconds
   */
  _zoomToRegionIfNeeded(start, end) {
    const player = this.player;

    // Only zoom if currently at default zoom level and region is less than half the duration
    if (player.zoomLevel === 1 && end - start < player.duration / 2) {
      // Calculate needed zoom level to show the segment with padding
      const padding = 0.2; // 20% padding on each side
      const segmentDuration = end - start;
      const desiredDuration = segmentDuration * (1 + 2 * padding);
      const newZoomLevel = Math.min(player.duration / desiredDuration, 10);

      // Set zoom level
      player.zoomLevel = newZoomLevel;

      // Center the segment in the view
      const segmentCenter = (start + end) / 2;
      const visibleDuration = player.duration / player.zoomLevel;
      player.zoomOffset = Math.max(
        0,
        Math.min(
          segmentCenter / player.duration - visibleDuration / player.duration / 2,
          1 - visibleDuration / player.duration
        )
      );

      // Update displays
      player.redrawCurrentView();
      player.drawTimeline();
      player.updateTimeDisplay();
    }
  }

  /**
   * Clean up the timeupdate listener
   */
  _cleanupListener() {
    if (this._stopAtEndListener && this.player.audioPlayer) {
      this.player.audioPlayer.removeEventListener('timeupdate', this._stopAtEndListener);
      this._stopAtEndListener = null;
    }
  }

  /**
   * Stop region playback and clean up
   */
  stop() {
    this._cleanupListener();
    if (this.player.audioPlayer) {
      this.player.audioPlayer.pause();
    }
  }
}

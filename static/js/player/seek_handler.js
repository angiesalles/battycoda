/**
 * BattyCoda Waveform Player - Seek Handler
 *
 * Handles seeking to specific times and ensuring playhead visibility
 */

export class SeekHandler {
  constructor(player) {
    this.player = player;
  }

  /**
   * Seek to a specific time and ensure it's visible in the viewport
   * @param {number} time - Time in seconds to seek to
   */
  seek(time) {
    // Clamp to valid range
    time = Math.max(0, Math.min(time, this.player.duration));

    // Update audio player and internal time
    this.player.audioPlayer.currentTime = time;
    this.player.currentTime = time;

    // If zoomed in, center the view on this time
    if (this.player.zoomLevel > 1) {
      const timeRatio = time / this.player.duration;
      const visibleDuration = 1 / this.player.zoomLevel;

      // Center the view on the seek position
      this.player.zoomOffset = Math.max(
        0,
        Math.min(timeRatio - visibleDuration / 2, 1 - visibleDuration)
      );
    }

    // Update displays
    this.player.updateTimeDisplay();
    this.player.redrawCurrentView();
    this.player.drawTimeline();
  }
}

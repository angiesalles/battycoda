/**
 * BattyCoda Waveform Player - Audio Event Handlers
 *
 * Handles audio player event listeners (play, pause, timeupdate, etc.)
 */

export class AudioEvents {
  constructor(player) {
    this.player = player;
  }

  /**
   * Set up audio player event listeners
   */
  setup() {
    if (!this.player.audioPlayer) return;

    let lastScrollUpdateTime = 0;

    this.player.audioPlayer.addEventListener('timeupdate', () => {
      this.player.currentTime = this.player.audioPlayer.currentTime;
      this.player.updateTimeDisplay();

      // Redraw the current view to update the playback cursor
      this.player.redrawCurrentView();

      const now = performance.now();

      // Check if we're in a recording selection process
      if (
        this.player.allowSelection &&
        this.player.selectionStart !== null &&
        this.player.selectionEnd === null
      ) {
        // If we're playing and hit a segment boundary, stop the selection process
        if (this.player.isPlaying) {
          if (this.player.isTimeInSegment(this.player.currentTime)) {
            // We've entered an existing segment - can't make selection here
            this.player.selectionStart = null;
            this.player.updateSelectionDisplay();
            this.player.redrawCurrentView();
            if (this.player.setStartBtn) this.player.setStartBtn.disabled = false;
            if (this.player.setEndBtn) this.player.setEndBtn.disabled = true;
          }
        }
      }

      // Smooth scrolling when zoomed in during playback
      if (this.player.zoomLevel > 1 && this.player.isPlaying) {
        const currentRatio = this.player.currentTime / this.player.duration;
        const visibleDuration = 1 / this.player.zoomLevel;
        const currentCenter = this.player.zoomOffset + visibleDuration / 2;
        const distanceFromCenter = Math.abs(currentRatio - currentCenter);

        // Only scroll if the playhead is getting close to the edge of the visible area
        const scrollThreshold = visibleDuration * 0.3; // Start scrolling when 30% from edge

        if (distanceFromCenter > scrollThreshold) {
          // Smoothly update the target zoom offset
          this.player.targetZoomOffset = Math.max(
            0,
            Math.min(currentRatio - visibleDuration / 2, 1 - visibleDuration)
          );

          // Only update if enough time has passed or if we're significantly off target
          if (
            Math.abs(this.player.targetZoomOffset - this.player.zoomOffset) > 0.01 ||
            now - lastScrollUpdateTime > 250
          ) {
            this.player.animateScroll();
            lastScrollUpdateTime = now;
          }
        }
      }
    });

    this.player.audioPlayer.addEventListener('play', () => {
      this.player.isPlaying = true;
      this.player.updatePlayButtons();
    });

    this.player.audioPlayer.addEventListener('pause', () => {
      this.player.isPlaying = false;
      this.player.updatePlayButtons();
    });

    this.player.audioPlayer.addEventListener('ended', () => {
      this.player.isPlaying = false;
      this.player.updatePlayButtons();
    });

    this.player.audioPlayer.addEventListener('loadedmetadata', () => {
      this.player.duration = this.player.audioPlayer.duration;
      if (this.player.totalTimeEl)
        this.player.totalTimeEl.textContent = this.player.duration.toFixed(2) + 's';
    });

    this.player.audioPlayer.addEventListener('canplay', () => {
      if (this.player.loadingEl) this.player.loadingEl.style.display = 'none';
    });
  }
}

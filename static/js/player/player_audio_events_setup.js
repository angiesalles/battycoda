/**
 * Audio Event Listeners Setup
 * Extracted from player.js for maintainability
 */

export function setupAudioEventListeners(player) {
  if (!player.audioPlayer) return;

  let lastScrollUpdateTime = 0;

  player.audioPlayer.addEventListener('timeupdate', () => {
    player.currentTime = player.audioPlayer.currentTime;
    player.updateTimeDisplay();

    const now = performance.now();

    // Check if we're in a recording selection process
    if (player.allowSelection && player.selectionStart !== null && player.selectionEnd === null) {
      // If we're playing through segments while making a selection, handle segment collisions
      if (player.isPlaying) {
        // Check if current position is inside any existing segment
        if (player.isTimeInSegment(player.currentTime)) {
          // Stop the selection at the segment boundary we just entered
          player.selectionEnd = player.findNearestSegmentBoundary(player.currentTime, 'backward');
          player.updateSelectionDisplay();
          player.drawWaveform();

          // Reset selection buttons state
          if (player.setStartBtn) player.setStartBtn.disabled = false;
          if (player.setEndBtn) player.setEndBtn.disabled = true;
        }
      }
    }

    // For more reliable playback following, start recentering sooner
    // Also track if the cursor is near the edge of the visible area
    if (player.zoomLevel > 1 && player.isPlaying) {
      const visibleDuration = player.duration / player.zoomLevel;

      // Center the view on current time, with bounds checking
      const targetCenter = player.currentTime / player.duration;
      const halfVisibleDuration = visibleDuration / 2 / player.duration;

      // Calculate new offset (start of visible window)
      // This centers the playhead in the visible area
      player.targetZoomOffset = Math.max(
        0,
        Math.min(targetCenter - halfVisibleDuration, 1 - visibleDuration / player.duration)
      );

      // Only update if significant change or enough time has passed
      if (
        Math.abs(player.targetZoomOffset - player.zoomOffset) > 0.01 ||
        now - lastScrollUpdateTime > 250
      ) {
        // Move gradually toward the target position to create a smooth scrolling effect
        // Apply a step toward the target position (easing)
        const step = 0.3; // Adjusted for faster centering during playback
        player.zoomOffset += (player.targetZoomOffset - player.zoomOffset) * step;

        player.drawWaveform();
        player.drawTimeline();
        lastScrollUpdateTime = now;
        return; // Skip the drawWaveform below to avoid double draws
      }
    }

    // Just update waveform (for cursor) if we didn't do a full redraw above
    player.drawWaveform();
  });

  player.audioPlayer.addEventListener('play', () => {
    player.isPlaying = true;
    player.updatePlayButtons();
  });

  player.audioPlayer.addEventListener('pause', () => {
    player.isPlaying = false;
    player.updatePlayButtons();
  });

  player.audioPlayer.addEventListener('ended', () => {
    player.isPlaying = false;
    player.updatePlayButtons();
  });
}

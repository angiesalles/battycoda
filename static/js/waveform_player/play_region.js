/**
 * BattyCoda Waveform Player - playRegion Extension
 * 
 * This file adds the playRegion functionality to the WaveformPlayer class.
 * Import this file after the main player has been initialized.
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Add the playRegion method to all waveform players
  setTimeout(function() {
    if (window.waveformPlayers) {
      // Extend each player with the playRegion method
      for (const id in window.waveformPlayers) {
        if (window.waveformPlayers.hasOwnProperty(id)) {
          const playerWrapper = window.waveformPlayers[id];
          const player = playerWrapper.player;
          
          // Add the playRegion method to the player instance
          if (player && !player.playRegion) {
            player.playRegion = function(start, end) {
              if (!this.audioPlayer) return;
              
              // Set the current time to the start position
              this.audioPlayer.currentTime = start;
              this.currentTime = start;
              
              // Start playback
              this.audioPlayer.play();
              
              // Set up a one-time event listener to stop playback at end time
              const stopAtEnd = () => {
                if (this.audioPlayer.currentTime >= end) {
                  this.audioPlayer.pause();
                  this.audioPlayer.removeEventListener('timeupdate', stopAtEnd);
                }
              };
              
              this.audioPlayer.addEventListener('timeupdate', stopAtEnd);
              
              // If the region is completely zoomed out, zoom in on it
              if (this.zoomLevel === 1 && end - start < this.duration / 2) {
                // Calculate needed zoom level to show the segment with padding
                const padding = 0.2; // 20% padding on each side
                const segmentDuration = end - start;
                const desiredDuration = segmentDuration * (1 + 2 * padding);
                const newZoomLevel = Math.min(this.duration / desiredDuration, 10);
                
                // Set zoom level
                this.zoomLevel = newZoomLevel;
                
                // Center the segment in the view
                const segmentCenter = (start + end) / 2;
                const visibleDuration = this.duration / this.zoomLevel;
                this.zoomOffset = Math.max(0, Math.min(
                  segmentCenter / this.duration - (visibleDuration / this.duration / 2),
                  1 - visibleDuration / this.duration
                ));
                
                // Update displays
                this.drawWaveform();
                this.drawTimeline();
                this.updateTimeDisplay();
              }
            };
          }
        }
      }
    }
  }, 1000); // Delay to ensure all players are initialized
});
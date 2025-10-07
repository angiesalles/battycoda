/**
 * Control Event Listeners Setup
 * Extracted from player.js for maintainability
 */

export function setupControlEventListeners(player) {
        if (player.playBtn) {
            player.playBtn.addEventListener('click', () => {
                player.audioPlayer.play();
            });
        }
        
        // Pause button
        if (player.pauseBtn) {
            player.pauseBtn.addEventListener('click', () => {
                player.audioPlayer.pause();
            });
        }
        
        // Stop button
        if (player.stopBtn) {
            player.stopBtn.addEventListener('click', () => {
                player.audioPlayer.pause();
                player.audioPlayer.currentTime = 0;
                player.currentTime = 0;
                player.updateTimeDisplay();
                player.drawWaveform();
            });
        }
        
        // Progress container click
        if (player.progressContainer) {
            player.progressContainer.addEventListener('click', (e) => {
                const rect = player.progressContainer.getBoundingClientRect();
                const offsetX = e.clientX - rect.left;
                const clickPosition = offsetX / rect.width;
                
                // Set current time based on click position (progress bar always shows full duration)
                player.currentTime = clickPosition * player.duration;
                player.audioPlayer.currentTime = player.currentTime;
                
                // We no longer immediately center on clicked position
                // Let the timeupdate handler handle this gradually during playback
                
                player.updateTimeDisplay();
                player.drawWaveform();
            });
        }
}

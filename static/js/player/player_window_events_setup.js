/**
 * Window Event Listeners Setup
 * Extracted from player.js for maintainability
 */

export function setupWindowEventListeners(player) {
    window.addEventListener('resize', () => {
        player.drawWaveform();
        player.drawTimeline();
    });
}
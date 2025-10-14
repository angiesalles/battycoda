/**
 * BattyCoda Waveform Player - Event Handlers Module
 *
 * Coordinates all event listener setup and management for the waveform player
 */

import { AudioEvents } from './audio_events.js';
import { ControlEvents } from './control_events.js';
import { SelectionEvents } from './selection_events.js';

export class EventHandlers {
    constructor(player) {
        this.player = player;
        this.audioEvents = new AudioEvents(player);
        this.controlEvents = new ControlEvents(player);
        this.selectionEvents = new SelectionEvents(player);
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        this.audioEvents.setup();
        this.controlEvents.setup();
        this.selectionEvents.setup();
    }

    /**
     * Animate smooth scrolling when zoomed in
     */
    animateScroll() {
        // Cancel any existing animation
        if (this.player.animationFrameId) {
            cancelAnimationFrame(this.player.animationFrameId);
        }

        const startOffset = this.player.zoomOffset;
        const targetOffset = this.player.targetZoomOffset;
        const offsetDiff = targetOffset - startOffset;
        const startTime = performance.now();
        const duration = 150; // Animation duration in ms

        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Use easing function for smooth animation
            const eased = 1 - Math.pow(1 - progress, 3); // Ease-out cubic

            // Update zoom offset
            this.player.zoomOffset = startOffset + (offsetDiff * eased);

            // Redraw
            this.player.redrawCurrentView();
            this.player.drawTimeline();
            this.player.updateTimeDisplay();

            // Continue animation if not complete
            if (progress < 1) {
                this.player.animationFrameId = requestAnimationFrame(step);
            }
        };

        this.player.animationFrameId = requestAnimationFrame(step);
    }
}

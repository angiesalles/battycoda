/**
 * Timeline Time Markers - Handles drawing time markers and labels
 */

export class TimeMarkers {
    /**
     * Calculate appropriate time step based on visible duration
     */
    calculateTimeStep(visibleDuration) {
        if (visibleDuration <= 2) {
            return 0.1; // Show 0.1 second intervals for very zoomed view
        } else if (visibleDuration <= 5) {
            return 0.5; // Show 0.5 second intervals
        } else if (visibleDuration <= 10) {
            return 1; // Show 1 second intervals
        } else if (visibleDuration <= 30) {
            return 2; // Show 2 second intervals
        } else if (visibleDuration <= 60) {
            return 5; // Show 5 second intervals
        } else if (visibleDuration <= 300) {
            return 30; // Show 30 second intervals
        } else {
            return 60; // Show 1 minute intervals
        }
    }

    /**
     * Format time label based on duration
     */
    formatTimeLabel(time, visibleDuration) {
        if (visibleDuration > 60) {
            // Show minutes:seconds for longer durations
            const minutes = Math.floor(time / 60);
            const seconds = time % 60;
            return `${minutes}:${seconds.toFixed(0).padStart(2, '0')}`;
        } else if (visibleDuration <= 3) {
            // Show more precision for short durations
            return time.toFixed(2) + 's';
        } else {
            return time.toFixed(1) + 's';
        }
    }

    /**
     * Draw time markers on the timeline
     */
    draw(container, width, duration, startTime, endTime, visibleDuration) {
        const timeStep = this.calculateTimeStep(visibleDuration);

        // Calculate start time aligned with time step
        const firstMarkerTime = Math.ceil(startTime / timeStep) * timeStep;

        // Draw time markers
        for (let time = firstMarkerTime; time <= endTime; time += timeStep) {
            // Skip if we're at exactly duration (edge case)
            if (time > duration) break;

            // Calculate x position for the marker
            const markerX = ((time - startTime) / visibleDuration) * width;

            // Only draw if in the visible area
            if (markerX >= 0 && markerX <= width) {
                const marker = document.createElement('div');
                marker.className = 'position-absolute';
                marker.style.left = markerX + 'px';
                marker.style.top = '0';
                marker.style.bottom = '0';
                marker.style.width = '1px';
                marker.style.backgroundColor = '#6c757d';

                const label = document.createElement('div');
                label.className = 'position-absolute text-light small';
                label.style.left = (markerX - 12) + 'px';
                label.style.bottom = '0';
                label.textContent = this.formatTimeLabel(time, visibleDuration);

                container.appendChild(marker);
                container.appendChild(label);
            }
        }
    }
}

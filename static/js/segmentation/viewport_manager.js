/**
 * Viewport Manager - Handles viewport-based segment loading
 */

export class ViewportManager {
    constructor(segmentLoader) {
        this.segmentLoader = segmentLoader;
        this.lastLoadedRange = null;
        this.loadTimeout = null;
    }
    
    // Load segments for the current visible viewport
    loadSegmentsForCurrentView(playerWrapper, onSegmentsLoaded) {
        if (!playerWrapper || !playerWrapper.player) return;
        
        const player = playerWrapper.player;
        if (!player || player.zoomLevel <= 1) return; // Only load when zoomed in
        
        // Calculate visible time range
        const visibleDuration = player.duration / player.zoomLevel;
        const visibleStartTime = player.zoomOffset * player.duration;
        const visibleEndTime = Math.min(visibleStartTime + visibleDuration, player.duration);
        
        // Add some padding to load segments slightly outside visible area
        const padding = visibleDuration * 0.2; // 20% padding on each side
        const startTime = Math.max(0, visibleStartTime - padding);
        const endTime = Math.min(player.duration, visibleEndTime + padding);
        
        // Check if we already loaded this range recently
        if (this.lastLoadedRange && 
            Math.abs(this.lastLoadedRange.start - startTime) < visibleDuration * 0.1 &&
            Math.abs(this.lastLoadedRange.end - endTime) < visibleDuration * 0.1) {
            return; // Skip loading if range is very similar to last loaded range
        }
        
        // Throttle loading requests
        if (this.loadTimeout) {
            clearTimeout(this.loadTimeout);
        }
        
        this.loadTimeout = setTimeout(async () => {
            try {
                console.log(`Loading segments for viewport: ${startTime.toFixed(2)}s - ${endTime.toFixed(2)}s (zoom: ${player.zoomLevel}x)`);
                
                const newSegments = await this.segmentLoader.loadSegmentsInRange(startTime, endTime);
                
                // Update last loaded range
                this.lastLoadedRange = { start: startTime, end: endTime };
                
                // Notify callback with new segments
                if (onSegmentsLoaded) {
                    onSegmentsLoaded(newSegments);
                }
                
            } catch (error) {
                console.error('Failed to load viewport segments:', error);
            }
        }, 300); // 300ms delay to throttle requests
    }
    
    // Clear any pending load operations
    clearPendingLoads() {
        if (this.loadTimeout) {
            clearTimeout(this.loadTimeout);
            this.loadTimeout = null;
        }
    }
}
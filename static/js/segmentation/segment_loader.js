/**
 * Segment Loader - Handles dynamic loading of segments
 */

export class SegmentLoader {
    constructor(recordingId) {
        this.recordingId = recordingId;
        this.loadedSegments = new Map(); // Cache loaded segments by time range
    }
    
    // Load segments dynamically within a time range
    async loadSegmentsInRange(startTime, endTime) {
        const cacheKey = `${startTime}-${endTime}`;
        
        // Return cached segments if already loaded
        if (this.loadedSegments.has(cacheKey)) {
            return this.loadedSegments.get(cacheKey);
        }
        
        try {
            const url = `/segments/${this.recordingId}/load-ajax/?start_time=${startTime}&end_time=${endTime}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Cache the loaded segments
                this.loadedSegments.set(cacheKey, data.segments);
                console.log(`Loaded ${data.segments.length} segments in range ${startTime}-${endTime}s`);
                return data.segments;
            } else {
                throw new Error(data.error || 'Failed to load segments');
            }
        } catch (error) {
            console.error('Error loading segments:', error);
            throw error;
        }
    }
    
    // Clear the cache
    clearCache() {
        this.loadedSegments.clear();
    }
    
    // Get all cached segments
    getAllCachedSegments() {
        const allSegments = [];
        for (const segments of this.loadedSegments.values()) {
            allSegments.push(...segments);
        }
        
        // Remove duplicates and sort by onset
        const uniqueSegments = allSegments.filter((segment, index, self) =>
            index === self.findIndex(s => s.id === segment.id)
        );
        
        return uniqueSegments.sort((a, b) => a.onset - b.onset);
    }
}
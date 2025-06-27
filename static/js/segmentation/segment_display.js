/**
 * Segment Display Manager - Handles UI display of segments
 */

export class SegmentDisplay {
    constructor(waveformId) {
        this.waveformId = waveformId;
    }
    
    // Get segments that are visible in current viewport
    getVisibleSegments(allSegments) {
        console.log('getVisibleSegments called with', allSegments.length, 'segments');
        
        if (!window.waveformPlayers || !window.waveformPlayers[this.waveformId]) {
            console.log('No waveform player found, returning all segments');
            return allSegments; // Return all if no player
        }
        
        const playerWrapper = window.waveformPlayers[this.waveformId];
        const player = playerWrapper.player;
        console.log('Player zoom level:', player?.zoomLevel);
        
        if (!player || player.zoomLevel <= 1) {
            console.log('Not zoomed in, returning all segments');
            return allSegments; // Return all if not zoomed
        }
        
        // Calculate visible time range
        const visibleDuration = player.duration / player.zoomLevel;
        const visibleStartTime = player.zoomOffset * player.duration;
        const visibleEndTime = Math.min(visibleStartTime + visibleDuration, player.duration);
        
        // Filter segments that overlap with visible range
        return allSegments.filter(segment => {
            return segment.offset >= visibleStartTime && segment.onset <= visibleEndTime;
        }).sort((a, b) => a.onset - b.onset);
    }
    
    // Update segments count display
    updateSegmentsCount(count) {
        const countElement = document.getElementById('segments-count');
        if (countElement) {
            countElement.textContent = count;
        }
    }
    
    // Render the segments list in the table
    renderSegmentsList(segments) {
        const segmentsList = document.getElementById('segments-list');
        if (!segmentsList) return;
        
        // Clear existing rows
        segmentsList.innerHTML = '';
        
        // Add new rows
        segments.forEach(segment => {
            const row = document.createElement('tr');
            row.id = `segment-row-${segment.id}`;
            row.dataset.segmentId = segment.id;
            
            const duration = (segment.offset - segment.onset).toFixed(2);
            
            row.innerHTML = `
                <td>${segment.id}</td>
                <td>${segment.onset.toFixed(2)}s - ${segment.offset.toFixed(2)}s</td>
                <td>${duration}s</td>
                <td>
                    <div class="segment-actions" data-segment-id="${segment.id}" 
                         data-onset="${segment.onset}" data-offset="${segment.offset}"
                         data-name="${segment.name || ''}" 
                         data-notes="${segment.notes || ''}"></div>
                </td>
            `;
            
            segmentsList.appendChild(row);
        });
        
        // Re-render action buttons for each segment
        const actionContainers = segmentsList.querySelectorAll('.segment-actions');
        actionContainers.forEach(container => {
            this.renderSegmentActionButtons(container);
        });
        
        // Show/hide the table and no-segments message
        this.toggleTableVisibility(segments.length > 0);
    }
    
    // Toggle table visibility based on whether there are segments
    toggleTableVisibility(hasSegments) {
        const tableContainer = document.querySelector('#segments-list')?.closest('.table-responsive');
        const noSegmentsMessage = document.getElementById('no-segments-message');
        
        if (hasSegments) {
            if (tableContainer) tableContainer.style.display = 'block';
            if (noSegmentsMessage) noSegmentsMessage.style.display = 'none';
        } else {
            if (tableContainer) tableContainer.style.display = 'none';
            if (noSegmentsMessage) noSegmentsMessage.style.display = 'block';
        }
    }
    
    // Render action buttons for a segment
    renderSegmentActionButtons(container) {
        if (!container) return;
        
        const segmentId = container.dataset.segmentId;
        const onset = parseFloat(container.dataset.onset);
        const offset = parseFloat(container.dataset.offset);
        
        container.innerHTML = `
            <div class="btn-group btn-group-sm">
                <button class="btn btn-success btn-sm" onclick="window.battycoda?.segmentation?.['${this.waveformId}']?.playSegment(${onset}, ${offset})">
                    <i class="fas fa-play"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="window.battycoda?.segmentation?.['${this.waveformId}']?.deleteSegment(${segmentId})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
    }
}
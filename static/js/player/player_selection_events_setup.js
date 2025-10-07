/**
 * Selection Event Listeners Setup
 * Extracted from player.js for maintainability
 */

export function setupSelectionEventListeners(player) {
        if (player.setStartBtn) {
            player.setStartBtn.addEventListener('click', () => {
                // Check if current position overlaps with any existing segments
                if (player.isTimeInSegment(player.currentTime)) {
                    console.log('Cannot start selection inside an existing segment');
                    return; // Don't allow setting start point inside existing segment
                }
                
                // Start a new selection - clear any existing selection
                player.selectionStart = player.currentTime;
                player.selectionEnd = null;
                player.updateSelectionDisplay();
                player.drawWaveform();
                
                // Update button states
                player.setStartBtn.disabled = false;  // Allow changing start point
            });
            
            // Regularly check if we're inside a segment and update button state
            setInterval(() => {
                if (player.setStartBtn) {
                    player.setStartBtn.disabled = player.isTimeInSegment(player.currentTime);
                }
            }, 200);
        }
        
        // Set end button
        if (player.setEndBtn) {
            // Disable end button initially until start is set
            player.setEndBtn.disabled = true;
            
            player.setEndBtn.addEventListener('click', () => {
                // Only set end if there's a start point and current time is after it
                if (player.selectionStart !== null && player.currentTime > player.selectionStart) {
                    // Check if there's an existing segment between start and current time
                    const segmentBetween = player.segments.some(segment => {
                        const segStart = segment.start || segment.onset;
                        const segEnd = segment.end || segment.offset;
                        
                        // Check if any segment overlaps with our selection
                        return (segStart <= player.currentTime && segEnd >= player.selectionStart) ||
                               (segStart >= player.selectionStart && segStart <= player.currentTime);
                    });
                    
                    if (segmentBetween) {
                        // Find nearest segment boundary before current position
                        const boundaryTime = player.findNearestSegmentBoundary(player.currentTime, 'backward');
                        if (boundaryTime !== null && boundaryTime > player.selectionStart) {
                            // Use the segment boundary as our end point
                            player.selectionEnd = boundaryTime;
                        } else {
                            console.log('Cannot end selection - overlaps with existing segment');
                            return;
                        }
                    } else {
                        // Normal case - no overlap
                        player.selectionEnd = player.currentTime;
                    }
                    
                    player.updateSelectionDisplay();
                    player.drawWaveform();
                    
                    // Reset button states after completing a selection
                    player.setStartBtn.disabled = player.isTimeInSegment(player.currentTime);
                    player.setEndBtn.disabled = true;
                }
            });
            
            // We need to regularly update end button state based on playhead position
            player.audioPlayer.addEventListener('timeupdate', () => {
                if (player.selectionStart !== null && player.selectionEnd === null) {
                    // Check two conditions:
                    // 1. If we're to the right of the start point
                    // 2. If current position is inside any existing segment
                    const afterStart = player.currentTime > player.selectionStart;
                    const insideSegment = player.isTimeInSegment(player.currentTime);
                    
                    // Check if there's an overlap between our selection start and current time
                    const hasOverlap = player.segments.some(segment => {
                        const segStart = segment.start || segment.onset;
                        const segEnd = segment.end || segment.offset;
                        return (segStart <= player.currentTime && segEnd >= player.selectionStart) ||
                               (segStart >= player.selectionStart && segStart <= player.currentTime);
                    });
                    
                    // Only enable if we're after start, not inside a segment, and no segment overlap
                    player.setEndBtn.disabled = !afterStart || insideSegment || hasOverlap;
                } else {
                    // Disable end button if no start point or already have end point
                    player.setEndBtn.disabled = true;
                }
            });
        }
}

/**
 * Segment Drag Handler - Handles dragging segment boundaries on the timeline
 */

export class SegmentDragHandler {
    constructor(player) {
        this.player = player;
    }

    /**
     * Add draggable handles to a segment marker
     */
    addDraggableHandles(segmentMarker, segment, startTime, visibleDuration) {
        const leftHandle = this.createHandle('left');
        const rightHandle = this.createHandle('right');

        // Show handles on hover
        segmentMarker.addEventListener('mouseenter', () => {
            leftHandle.style.opacity = '0.8';
            rightHandle.style.opacity = '0.8';
        });

        segmentMarker.addEventListener('mouseleave', () => {
            leftHandle.style.opacity = '0';
            rightHandle.style.opacity = '0';
        });

        // Add drag handlers
        leftHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            e.preventDefault(); // Prevent click event from firing
            this.startDrag(e, segment, 'start', startTime, visibleDuration);
        });

        rightHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            e.preventDefault(); // Prevent click event from firing
            this.startDrag(e, segment, 'end', startTime, visibleDuration);
        });

        segmentMarker.appendChild(leftHandle);
        segmentMarker.appendChild(rightHandle);
    }

    /**
     * Create a draggable handle element
     */
    createHandle(side) {
        const handle = document.createElement('div');
        handle.className = `segment-handle segment-handle-${side}`;
        handle.style.position = 'absolute';
        handle.style.top = '0';
        handle.style.width = '10px';
        handle.style.height = '100%';
        handle.style.cursor = 'ew-resize';
        handle.style.backgroundColor = '#ffffff';
        handle.style.borderRadius = '2px';
        handle.style.opacity = '0';
        handle.style.transition = 'opacity 0.2s';
        handle.style.zIndex = '20';

        if (side === 'left') {
            handle.style.left = '-5px';
        } else {
            handle.style.right = '-5px';
        }

        return handle;
    }

    /**
     * Start dragging a segment boundary
     */
    startDrag(e, segment, boundary, startTime, visibleDuration) {
        e.preventDefault();

        const player = this.player;
        const width = player.timelineContainer.clientWidth;
        const timelineRect = player.timelineContainer.getBoundingClientRect();

        let isDragging = true;
        let originalOnset = segment.onset;
        let originalOffset = segment.offset;

        const onMouseMove = (moveEvent) => {
            if (!isDragging) return;

            // Calculate new time from mouse position
            const mouseX = moveEvent.clientX - timelineRect.left;
            const timeFromMouse = startTime + (mouseX / width) * visibleDuration;

            // Clamp to valid range
            const clampedTime = Math.max(0, Math.min(player.duration, timeFromMouse));

            // Update segment boundary
            if (boundary === 'start') {
                segment.onset = Math.min(clampedTime, segment.offset - 0.001);
            } else {
                segment.offset = Math.max(clampedTime, segment.onset + 0.001);
            }

            // Redraw timeline to show updated position
            player.drawTimeline();
        };

        const onMouseUp = async () => {
            if (!isDragging) return;
            isDragging = false;

            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);

            // Check if segment actually changed
            if (segment.onset === originalOnset && segment.offset === originalOffset) {
                return;
            }

            // Get segmentation ID from the segment manager
            const segmentManager = window.battycoda?.segmentation?.[player.containerId];
            if (!segmentManager?.segmentationId) {
                throw new Error('Segmentation ID not found');
            }

            // Update segment via API
            try {
                const response = await fetch(`/segmentations/${segmentManager.segmentationId}/segments/${segment.id}/edit/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: new URLSearchParams({
                        onset: segment.onset.toFixed(6),
                        offset: segment.offset.toFixed(6)
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to update segment');
                }

                const result = await response.json();

                if (result.success) {
                    segment.onset = result.segment.onset;
                    segment.offset = result.segment.offset;

                    player.drawTimeline();
                    player.redrawCurrentView();

                    // Update segment in the segment manager's array and refresh list
                    const segmentManager = window.battycoda?.segmentation?.[player.containerId];
                    if (segmentManager) {
                        const managerSegment = segmentManager.segments.find(s => s.id === segment.id);
                        if (managerSegment) {
                            managerSegment.onset = segment.onset;
                            managerSegment.offset = segment.offset;
                        }
                        segmentManager.refreshSegmentsList();
                    }
                } else {
                    throw new Error(result.error || 'Failed to update segment');
                }
            } catch (error) {
                console.error('Error updating segment:', error);

                // Revert changes
                segment.onset = originalOnset;
                segment.offset = originalOffset;
                player.drawTimeline();
                player.redrawCurrentView();

                alert('Failed to update segment: ' + error.message);
            }
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    /**
     * Get CSRF token from cookie
     */
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

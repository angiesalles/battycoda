/**
 * BattyCoda Waveform Player - Canvas Interaction Handler
 *
 * Handles mouse interactions with the waveform canvas including:
 * - Click to seek
 * - Drag to pan (when zoomed in)
 */

export class CanvasInteractions {
  constructor(player) {
    this.player = player;
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartOffset = 0;
    this.dragStartTime = 0;
  }

  /**
   * Add interaction handlers to a canvas
   */
  setupCanvasHandlers(canvas, width, visibleStartTime, visibleDuration) {
    // Store canvas reference
    this.canvas = canvas;

    // Remove existing listeners to prevent duplicates
    this.removeCanvasHandlers(canvas);

    // Bind methods to preserve 'this' context
    this.handleMouseDown = this.handleMouseDown.bind(this);
    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleMouseUp = this.handleMouseUp.bind(this);
    this.handleMouseLeave = this.handleMouseLeave.bind(this);

    // Store canvas properties for use in handlers
    this.updateViewParameters(width, visibleStartTime, visibleDuration);

    // Add event listeners
    canvas.addEventListener('mousedown', this.handleMouseDown);
    canvas.addEventListener('mousemove', this.handleMouseMove);
    canvas.addEventListener('mouseup', this.handleMouseUp);
    canvas.addEventListener('mouseleave', this.handleMouseLeave);

    // Set initial cursor based on zoom level
    this.updateCursor(canvas);
  }

  /**
   * Update view parameters without re-adding event listeners
   */
  updateViewParameters(width, visibleStartTime, visibleDuration) {
    this.canvasWidth = width;
    this.visibleStartTime = visibleStartTime;
    this.visibleDuration = visibleDuration;

    // Update cursor if canvas exists
    if (this.canvas) {
      this.updateCursor(this.canvas);
    }
  }

  /**
   * Remove interaction handlers from a canvas
   */
  removeCanvasHandlers(canvas) {
    if (this.handleMouseDown) {
      canvas.removeEventListener('mousedown', this.handleMouseDown);
      canvas.removeEventListener('mousemove', this.handleMouseMove);
      canvas.removeEventListener('mouseup', this.handleMouseUp);
      canvas.removeEventListener('mouseleave', this.handleMouseLeave);
    }
  }

  /**
   * Handle mouse down event
   */
  handleMouseDown(e) {
    const rect = e.target.getBoundingClientRect();
    this.dragStartX = e.clientX - rect.left;
    this.dragStartOffset = this.player.zoomOffset;
    this.dragStartTime = Date.now();
    this.isDragging = false;

    // Change cursor to indicate drag is active when zoomed in
    if (this.player.zoomLevel > 1) {
      e.target.style.cursor = 'grabbing';
    }
  }

  /**
   * Handle mouse move event
   */
  handleMouseMove(e) {
    if (this.dragStartTime === 0) return;

    const rect = e.target.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const deltaX = currentX - this.dragStartX;

    // Only start dragging if we've moved more than 5 pixels
    if (!this.isDragging && Math.abs(deltaX) > 5) {
      this.isDragging = true;
    }

    // If dragging and zoomed in, pan the view
    if (this.isDragging && this.player.zoomLevel > 1) {
      this.panView(deltaX);
    }
  }

  /**
   * Handle mouse up event
   */
  handleMouseUp(e) {
    if (this.dragStartTime === 0) return;

    const timeSinceDragStart = Date.now() - this.dragStartTime;

    // If we didn't drag (or dragged very briefly), treat as a click
    if (!this.isDragging || timeSinceDragStart < 150) {
      this.seekToPosition(e);
    }

    this.resetDragState(e.target);
  }

  /**
   * Handle mouse leave event
   */
  handleMouseLeave(e) {
    if (this.isDragging) {
      this.resetDragState(e.target);
    }
  }

  /**
   * Pan the view based on drag distance
   */
  panView(deltaX) {
    const pixelsPerSecond = this.canvasWidth / this.visibleDuration;
    const deltaTime = -deltaX / pixelsPerSecond; // Negative for natural drag feel
    const deltaOffset = deltaTime / this.player.duration;

    // Apply the offset change, clamping to valid range
    const visibleDurationRatio = 1 / this.player.zoomLevel;
    const newOffset = Math.max(
      0,
      Math.min(1 - visibleDurationRatio, this.dragStartOffset + deltaOffset)
    );

    this.player.zoomOffset = newOffset;

    // Redraw the view
    this.player.redrawCurrentView();
    this.player.drawTimeline();
    this.player.updateTimeDisplay();
  }

  /**
   * Seek to a specific position based on mouse click
   */
  seekToPosition(e) {
    const rect = e.target.getBoundingClientRect();
    const x = Math.max(0, Math.min(this.canvasWidth, e.clientX - rect.left));

    // Calculate time position considering zoom
    const visibleProportion = x / this.canvasWidth;
    const timePos = this.visibleStartTime + visibleProportion * this.visibleDuration;

    // Use centralized seek method
    this.player.seek(timePos);
  }

  /**
   * Reset drag state
   */
  resetDragState(canvas) {
    this.isDragging = false;
    this.dragStartTime = 0;
    this.updateCursor(canvas);
  }

  /**
   * Update cursor based on zoom level and interaction state
   */
  updateCursor(canvas) {
    canvas.style.cursor = this.player.zoomLevel > 1 ? 'grab' : 'pointer';
  }
}

/**
 * Overlay Renderer - Handles UI elements that should appear on top of both waveform and spectrogram views
 *
 * This includes:
 * - Playback cursor
 * - Selection highlights
 * - Any other UI overlays
 */

export class OverlayRenderer {
  constructor(player) {
    this.player = player;
    this.canvas = null;
    this.ctx = null;

    this.setupCanvas();
  }

  setupCanvas() {
    const container = this.player.waveformContainer;
    if (!container) {
      console.error('Waveform container not found for overlay');
      return;
    }

    // Create overlay canvas
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'overlay-canvas';
    this.canvas.style.position = 'absolute';
    this.canvas.style.top = '0';
    this.canvas.style.left = '0';
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
    this.canvas.style.pointerEvents = 'none'; // Allow clicks to pass through
    this.canvas.style.zIndex = '10'; // Above both waveform and spectrogram

    container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');

    console.log('Overlay canvas created');
  }

  /**
   * Draw all overlay elements
   */
  draw() {
    if (!this.canvas || !this.ctx) return;

    const player = this.player;
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;

    // Set canvas resolution to match display size
    if (this.canvas.width !== width || this.canvas.height !== height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }

    // Clear canvas
    this.ctx.clearRect(0, 0, width, height);

    // Calculate visible time range
    const visibleDuration = player.duration / player.zoomLevel;
    const visibleStartTime = player.zoomOffset * player.duration;

    // Draw selection if allowed
    if (player.allowSelection) {
      this.drawSelection(width, height, visibleStartTime, visibleDuration);
    }

    // Draw playback cursor
    this.drawPlaybackCursor(width, height, visibleStartTime, visibleDuration);
  }

  /**
   * Draw the selection highlight
   */
  drawSelection(width, height, visibleStartTime, visibleDuration) {
    const player = this.player;
    const ctx = this.ctx;

    // If only start is set, draw a single marker
    if (player.selectionStart !== null && player.selectionEnd === null) {
      const startX = ((player.selectionStart - visibleStartTime) / visibleDuration) * width;

      if (startX >= 0 && startX <= width) {
        ctx.beginPath();
        ctx.strokeStyle = '#007bff';
        ctx.lineWidth = 2;
        ctx.moveTo(startX, 0);
        ctx.lineTo(startX, height);
        ctx.stroke();
      }
      return;
    }

    // If neither or only end is set, don't draw anything
    if (player.selectionStart === null || player.selectionEnd === null) return;

    // Both start and end are set - draw full selection
    const selStart = Math.min(player.selectionStart, player.selectionEnd);
    const selEnd = Math.max(player.selectionStart, player.selectionEnd);

    // Convert to pixel positions
    const startX = ((selStart - visibleStartTime) / visibleDuration) * width;
    const endX = ((selEnd - visibleStartTime) / visibleDuration) * width;

    // Draw selection highlight
    ctx.fillStyle = 'rgba(0, 123, 255, 0.2)';
    ctx.fillRect(Math.max(0, startX), 0, Math.min(width, endX) - Math.max(0, startX), height);

    // Draw selection boundaries
    if (startX >= 0 && startX <= width) {
      ctx.beginPath();
      ctx.strokeStyle = '#007bff';
      ctx.lineWidth = 2;
      ctx.moveTo(startX, 0);
      ctx.lineTo(startX, height);
      ctx.stroke();
    }

    if (endX >= 0 && endX <= width) {
      ctx.beginPath();
      ctx.strokeStyle = '#dc3545';
      ctx.lineWidth = 3;
      ctx.moveTo(endX, 0);
      ctx.lineTo(endX, height);
      ctx.stroke();
    }
  }

  /**
   * Draw the playback cursor
   */
  drawPlaybackCursor(width, height, visibleStartTime, visibleDuration) {
    const player = this.player;
    const ctx = this.ctx;

    // Calculate cursor position relative to visible window
    const cursorX = ((player.currentTime - visibleStartTime) / visibleDuration) * width;

    // Only draw if cursor is in visible range
    if (cursorX >= 0 && cursorX <= width) {
      ctx.beginPath();
      ctx.strokeStyle = '#fd7e14';
      ctx.lineWidth = 2;
      ctx.moveTo(cursorX, 0);
      ctx.lineTo(cursorX, height);
      ctx.stroke();
    }
  }

  /**
   * Destroy the overlay canvas
   */
  destroy() {
    if (this.canvas && this.canvas.parentNode) {
      this.canvas.parentNode.removeChild(this.canvas);
    }
    this.canvas = null;
    this.ctx = null;
  }
}

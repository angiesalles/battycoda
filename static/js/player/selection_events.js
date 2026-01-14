/**
 * BattyCoda Waveform Player - Selection Event Handlers
 *
 * Handles segment selection event listeners
 */

export class SelectionEvents {
  constructor(player) {
    this.player = player;
  }

  /**
   * Set up selection button event listeners
   */
  setup() {
    if (!this.player.allowSelection) return;

    // Set start button
    if (this.player.setStartBtn) {
      this.player.setStartBtn.addEventListener('click', () => {
        // Only allow setting start if not in a segment
        if (this.player.isTimeInSegment(this.player.currentTime)) {
          return;
        }

        this.player.selectionStart = this.player.currentTime;
        this.player.selectionEnd = null;
        this.player.updateSelectionDisplay();
        this.player.redrawCurrentView();

        // Update button states
        this.player.setStartBtn.disabled = false; // Allow changing start point
      });

      // Regularly check if we're inside a segment and update button state
      setInterval(() => {
        if (this.player.setStartBtn) {
          this.player.setStartBtn.disabled = this.player.isTimeInSegment(this.player.currentTime);
        }
      }, 100);
    }

    // Set end button
    if (this.player.setEndBtn) {
      this.player.setEndBtn.addEventListener('click', () => {
        // Only proceed if we have a start time
        if (
          this.player.selectionStart !== null &&
          this.player.currentTime > this.player.selectionStart
        ) {
          // Check if there are any segments between start and current time
          const segmentBetween = this.player.segments.some((segment) => {
            const segStart = segment.onset;
            const segEnd = segment.offset;
            // Return true if this segment overlaps with our proposed selection
            return (
              (segStart <= this.player.currentTime && segEnd >= this.player.selectionStart) ||
              (segStart >= this.player.selectionStart && segStart <= this.player.currentTime)
            );
          });

          if (segmentBetween) {
            // Find the nearest segment boundary after our start time
            const boundaryTime = this.player.findNearestSegmentBoundary(
              this.player.selectionStart,
              'forward'
            );
            if (boundaryTime !== null && boundaryTime > this.player.selectionStart) {
              this.player.selectionEnd = Math.min(boundaryTime - 0.001, this.player.currentTime);
            } else {
              // No safe boundary found, can't complete selection
              return;
            }
          } else {
            this.player.selectionEnd = this.player.currentTime;
          }

          this.player.updateSelectionDisplay();
          this.player.redrawCurrentView();

          // Reset button states after completing a selection
          this.player.setStartBtn.disabled = this.player.isTimeInSegment(this.player.currentTime);
          this.player.setEndBtn.disabled = true;
        }
      });
    }

    // Set end button state based on selection progress
    setInterval(() => {
      if (this.player.setEndBtn) {
        if (this.player.selectionStart !== null && this.player.selectionEnd === null) {
          // We have a start time but no end time
          // Check if current time is valid for ending selection
          const hasValidEnd = this.player.currentTime > this.player.selectionStart;

          // Check if there are any segments between start and current time
          const segmentBetween = this.player.segments.some((segment) => {
            const segStart = segment.onset;
            const segEnd = segment.offset;
            // Return true if this segment overlaps with our proposed selection
            return (
              (segStart <= this.player.currentTime && segEnd >= this.player.selectionStart) ||
              (segStart >= this.player.selectionStart && segStart <= this.player.currentTime)
            );
          });

          this.player.setEndBtn.disabled = !hasValidEnd || segmentBetween;
        } else {
          this.player.setEndBtn.disabled = true;
        }
      }
    }, 100);
  }
}

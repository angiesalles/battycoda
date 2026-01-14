/**
 * Timeline Segment Effects - Handles visual effects for segments (hover, highlights)
 */

export class SegmentEffects {
  /**
   * Create hover lines that extend from timeline to top of waveform
   */
  createSegmentHoverLines(positions, waveformContainer) {
    const lines = [];

    if (!waveformContainer) return lines;

    // Create start line
    const startLine = document.createElement('div');
    startLine.style.position = 'absolute';
    startLine.style.left = positions.visibleStart + 'px';
    startLine.style.top = '0px';
    startLine.style.width = '2px';
    startLine.style.height = waveformContainer.clientHeight + 'px';
    startLine.style.backgroundColor = '#ff6b35';
    startLine.style.opacity = '0.8';
    startLine.style.pointerEvents = 'none';
    startLine.style.zIndex = '10';
    startLine.className = 'segment-hover-line';

    // Create end line
    const endLine = document.createElement('div');
    endLine.style.position = 'absolute';
    endLine.style.left = positions.visibleEnd + 'px';
    endLine.style.top = '0px';
    endLine.style.width = '2px';
    endLine.style.height = waveformContainer.clientHeight + 'px';
    endLine.style.backgroundColor = '#ff6b35';
    endLine.style.opacity = '0.8';
    endLine.style.pointerEvents = 'none';
    endLine.style.zIndex = '10';
    endLine.className = 'segment-hover-line';

    // Add lines to waveform container
    waveformContainer.appendChild(startLine);
    waveformContainer.appendChild(endLine);

    lines.push(startLine, endLine);
    return lines;
  }

  /**
   * Remove hover lines
   */
  removeSegmentHoverLines(lines) {
    if (lines) {
      lines.forEach((line) => line.remove());
    }
  }

  /**
   * Add hover effects to segment markers
   */
  addSegmentHoverEffects(segmentMarker, positions, waveformContainer) {
    let hoverLines = null;

    // Mouse enter handler
    segmentMarker.addEventListener('mouseenter', () => {
      // Create hover lines that extend to the top of the waveform
      hoverLines = this.createSegmentHoverLines(positions, waveformContainer);

      // Highlight the segment marker
      segmentMarker.style.opacity = '1.0';
      segmentMarker.style.backgroundColor = '#ff6b35';
    });

    // Mouse leave handler
    segmentMarker.addEventListener('mouseleave', () => {
      // Remove hover lines
      this.removeSegmentHoverLines(hoverLines);
      hoverLines = null;

      // Restore segment marker appearance
      segmentMarker.style.opacity = '0.7';
      segmentMarker.style.backgroundColor = '#007bff';
    });
  }
}

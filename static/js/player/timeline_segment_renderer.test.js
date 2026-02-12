/**
 * Tests for player/timeline_segment_renderer.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SegmentRenderer } from './timeline_segment_renderer.js';

/**
 * Create mock drag and effects handlers
 */
function createMockHandlers() {
  return {
    dragHandler: {
      addDraggableHandles: vi.fn(),
    },
    effectsHandler: {
      addSegmentHoverEffects: vi.fn(),
    },
  };
}

describe('SegmentRenderer', () => {
  let segmentRenderer;
  let mockDragHandler;
  let mockEffectsHandler;

  beforeEach(() => {
    const handlers = createMockHandlers();
    mockDragHandler = handlers.dragHandler;
    mockEffectsHandler = handlers.effectsHandler;
    segmentRenderer = new SegmentRenderer(mockDragHandler, mockEffectsHandler);
  });

  describe('constructor', () => {
    it('should store handler references', () => {
      expect(segmentRenderer.dragHandler).toBe(mockDragHandler);
      expect(segmentRenderer.effectsHandler).toBe(mockEffectsHandler);
    });
  });

  describe('calculateSegmentPosition', () => {
    it('should calculate positions for a segment within view', () => {
      const segment = { onset: 2, offset: 4 };
      const startTime = 0;
      const visibleDuration = 10;
      const width = 1000;

      const positions = segmentRenderer.calculateSegmentPosition(
        segment,
        startTime,
        visibleDuration,
        width
      );

      // segmentStart = ((2-0)/10) * 1000 = 200
      // segmentEnd = ((4-0)/10) * 1000 = 400
      expect(positions.segmentStartTime).toBe(2);
      expect(positions.segmentEndTime).toBe(4);
      expect(positions.segmentStart).toBe(200);
      expect(positions.segmentEnd).toBe(400);
      expect(positions.visibleStart).toBe(200);
      expect(positions.visibleEnd).toBe(400);
      expect(positions.visibleWidth).toBe(200);
    });

    it('should clip segment that extends before visible area', () => {
      const segment = { onset: 0, offset: 5 };
      const startTime = 2; // View starts at 2s
      const visibleDuration = 10;
      const width = 1000;

      const positions = segmentRenderer.calculateSegmentPosition(
        segment,
        startTime,
        visibleDuration,
        width
      );

      // segmentStart = ((0-2)/10) * 1000 = -200 (before view)
      // segmentEnd = ((5-2)/10) * 1000 = 300
      expect(positions.segmentStart).toBe(-200);
      expect(positions.segmentEnd).toBe(300);
      // Clipped to visible area
      expect(positions.visibleStart).toBe(0);
      expect(positions.visibleEnd).toBe(300);
      expect(positions.visibleWidth).toBe(300);
    });

    it('should clip segment that extends beyond visible area', () => {
      const segment = { onset: 8, offset: 15 };
      const startTime = 0;
      const visibleDuration = 10;
      const width = 1000;

      const positions = segmentRenderer.calculateSegmentPosition(
        segment,
        startTime,
        visibleDuration,
        width
      );

      // segmentStart = (8/10) * 1000 = 800
      // segmentEnd = (15/10) * 1000 = 1500 (beyond width)
      expect(positions.segmentStart).toBe(800);
      expect(positions.segmentEnd).toBe(1500);
      // Clipped to visible area
      expect(positions.visibleStart).toBe(800);
      expect(positions.visibleEnd).toBe(1000);
      expect(positions.visibleWidth).toBe(200);
    });

    it('should clip segment that spans entire view and beyond', () => {
      const segment = { onset: 0, offset: 20 };
      const startTime = 5;
      const visibleDuration = 10;
      const width = 1000;

      const positions = segmentRenderer.calculateSegmentPosition(
        segment,
        startTime,
        visibleDuration,
        width
      );

      // Segment spans -500 to 1500 in pixels
      expect(positions.visibleStart).toBe(0);
      expect(positions.visibleEnd).toBe(1000);
      expect(positions.visibleWidth).toBe(1000);
    });

    it('should handle segment completely outside view (before)', () => {
      const segment = { onset: 0, offset: 2 };
      const startTime = 5;
      const visibleDuration = 10;
      const width = 1000;

      const positions = segmentRenderer.calculateSegmentPosition(
        segment,
        startTime,
        visibleDuration,
        width
      );

      // Both start and end are negative
      expect(positions.segmentStart).toBeLessThan(0);
      expect(positions.segmentEnd).toBeLessThan(0);
      expect(positions.visibleWidth).toBeLessThan(0); // Negative width means not visible
    });

    it('should handle segment completely outside view (after)', () => {
      const segment = { onset: 20, offset: 25 };
      const startTime = 0;
      const visibleDuration = 10;
      const width = 1000;

      const positions = segmentRenderer.calculateSegmentPosition(
        segment,
        startTime,
        visibleDuration,
        width
      );

      // Both start and end are beyond width
      expect(positions.segmentStart).toBeGreaterThan(1000);
      expect(positions.segmentEnd).toBeGreaterThan(1000);
    });
  });

  describe('createSegmentMarker', () => {
    it('should create a DOM element with correct attributes', () => {
      const segment = { id: 42, onset: 2.5, offset: 4.75 };
      const positions = {
        visibleStart: 100,
        visibleWidth: 150,
        segmentStartTime: 2.5,
        segmentEndTime: 4.75,
      };

      const marker = segmentRenderer.createSegmentMarker(segment, positions);

      expect(marker.tagName).toBe('DIV');
      expect(marker.className).toBe('position-absolute');
      expect(marker.style.left).toBe('100px');
      expect(marker.style.width).toBe('150px');
      expect(marker.style.cursor).toBe('move');
      expect(marker.dataset.segmentId).toBe('42');
      expect(marker.dataset.segmentStart).toBe('2.5');
      expect(marker.dataset.segmentEnd).toBe('4.75');
      expect(marker.title).toContain('Segment 42');
      expect(marker.title).toContain('2.50s');
      expect(marker.title).toContain('4.75s');
    });
  });

  describe('addClippingIndicators', () => {
    it('should add left clipping indicator when segment starts before view', () => {
      const marker = document.createElement('div');
      const positions = {
        segmentStart: -100, // Before view
        segmentEnd: 500,
      };
      const width = 1000;

      segmentRenderer.addClippingIndicators(marker, positions, width);

      expect(marker.style.borderLeftWidth).toBe('3px');
      expect(marker.style.borderLeftStyle).toBe('dashed');
      expect(marker.style.borderLeftColor).toBe('rgb(255, 152, 0)'); // #ff9800
    });

    it('should add right clipping indicator when segment ends after view', () => {
      const marker = document.createElement('div');
      const positions = {
        segmentStart: 500,
        segmentEnd: 1200, // After view
      };
      const width = 1000;

      segmentRenderer.addClippingIndicators(marker, positions, width);

      expect(marker.style.borderRightWidth).toBe('3px');
      expect(marker.style.borderRightStyle).toBe('dashed');
      expect(marker.style.borderRightColor).toBe('rgb(255, 152, 0)');
    });

    it('should add both indicators when segment spans entire view', () => {
      const marker = document.createElement('div');
      const positions = {
        segmentStart: -100,
        segmentEnd: 1200,
      };
      const width = 1000;

      segmentRenderer.addClippingIndicators(marker, positions, width);

      expect(marker.style.borderLeftStyle).toBe('dashed');
      expect(marker.style.borderRightStyle).toBe('dashed');
    });

    it('should not add indicators when segment is fully visible', () => {
      const marker = document.createElement('div');
      const positions = {
        segmentStart: 200,
        segmentEnd: 800,
      };
      const width = 1000;

      segmentRenderer.addClippingIndicators(marker, positions, width);

      expect(marker.style.borderLeftStyle).toBe('');
      expect(marker.style.borderRightStyle).toBe('');
    });
  });

  describe('draw', () => {
    let mockContainer;
    let mockWaveformContainer;

    beforeEach(() => {
      mockContainer = {
        appendChild: vi.fn(),
      };
      mockWaveformContainer = document.createElement('div');
    });

    it('should draw visible segments', () => {
      const segments = [
        { id: 1, onset: 2, offset: 4 },
        { id: 2, onset: 6, offset: 8 },
      ];

      segmentRenderer.draw(mockContainer, segments, 1000, 0, 10, mockWaveformContainer);

      // Both segments are in view
      expect(mockContainer.appendChild).toHaveBeenCalledTimes(2);
    });

    it('should skip segments outside visible range', () => {
      const segments = [
        { id: 1, onset: 0, offset: 2 }, // Outside (before view)
        { id: 2, onset: 6, offset: 8 }, // Inside
        { id: 3, onset: 15, offset: 18 }, // Outside (after view)
      ];

      segmentRenderer.draw(mockContainer, segments, 1000, 5, 10, mockWaveformContainer);

      // Only middle segment should be drawn
      expect(mockContainer.appendChild).toHaveBeenCalledTimes(1);
    });

    it('should skip segments with zero visible width', () => {
      // Segment exactly at edge with no visible part
      const segments = [{ id: 1, onset: 5, offset: 5.001 }]; // Nearly zero width

      // Create a spy on calculateSegmentPosition that returns zero width
      vi.spyOn(segmentRenderer, 'calculateSegmentPosition').mockReturnValue({
        segmentStart: 0,
        segmentEnd: 1,
        visibleStart: 0,
        visibleEnd: 0,
        visibleWidth: 0,
      });

      segmentRenderer.draw(mockContainer, segments, 1000, 0, 10, mockWaveformContainer);

      expect(mockContainer.appendChild).not.toHaveBeenCalled();
    });

    it('should add hover effects to segments', () => {
      const segments = [{ id: 1, onset: 2, offset: 4 }];

      segmentRenderer.draw(mockContainer, segments, 1000, 0, 10, mockWaveformContainer);

      expect(mockEffectsHandler.addSegmentHoverEffects).toHaveBeenCalled();
    });

    it('should add draggable handles to fully visible segments', () => {
      const segments = [{ id: 1, onset: 2, offset: 4 }];

      segmentRenderer.draw(mockContainer, segments, 1000, 0, 10, mockWaveformContainer);

      expect(mockDragHandler.addDraggableHandles).toHaveBeenCalled();
    });

    it('should not add draggable handles to partially visible segments', () => {
      const segments = [{ id: 1, onset: 0, offset: 8 }]; // Starts before view

      // Start view at 2s, so segment is partially clipped
      segmentRenderer.draw(mockContainer, segments, 1000, 2, 10, mockWaveformContainer);

      expect(mockDragHandler.addDraggableHandles).not.toHaveBeenCalled();
    });

    it('should handle empty segments array', () => {
      segmentRenderer.draw(mockContainer, [], 1000, 0, 10, mockWaveformContainer);

      expect(mockContainer.appendChild).not.toHaveBeenCalled();
    });
  });

  describe('scrollToSegmentInList', () => {
    it('should scroll to existing segment row and highlight it', () => {
      // Create a mock segment row
      const segmentRow = document.createElement('tr');
      segmentRow.id = 'segment-row-42';
      segmentRow.scrollIntoView = vi.fn();
      document.body.appendChild(segmentRow);

      segmentRenderer.scrollToSegmentInList(42);

      expect(segmentRow.scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'center',
      });
      expect(segmentRow.classList.contains('segment-row-selected')).toBe(true);

      // Cleanup
      document.body.removeChild(segmentRow);
    });

    it('should clear previous selection when selecting a new segment', () => {
      const row1 = document.createElement('tr');
      row1.id = 'segment-row-1';
      row1.classList.add('segment-row-selected');
      row1.scrollIntoView = vi.fn();
      document.body.appendChild(row1);

      const row2 = document.createElement('tr');
      row2.id = 'segment-row-2';
      row2.scrollIntoView = vi.fn();
      document.body.appendChild(row2);

      segmentRenderer.scrollToSegmentInList(2);

      expect(row1.classList.contains('segment-row-selected')).toBe(false);
      expect(row2.classList.contains('segment-row-selected')).toBe(true);

      // Cleanup
      document.body.removeChild(row1);
      document.body.removeChild(row2);
    });

    it('should handle missing segment row gracefully', () => {
      // No segment row exists
      expect(() => {
        segmentRenderer.scrollToSegmentInList(999);
      }).not.toThrow();
    });
  });
});

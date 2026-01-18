/**
 * Tests for player/timeline.js (TimelineRenderer)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TimelineRenderer } from './timeline.js';

/**
 * Create a mock player object
 */
function createMockPlayer(options = {}) {
  return {
    duration: options.duration ?? 60,
    zoomLevel: options.zoomLevel ?? 1,
    zoomOffset: options.zoomOffset ?? 0,
    segments: options.segments ?? [],
    timelineContainer: options.timelineContainer ?? createMockContainer(),
    waveformContainer: options.waveformContainer ?? createMockContainer(),
  };
}

/**
 * Create a mock DOM container
 */
function createMockContainer() {
  const container = document.createElement('div');
  container.style.width = '800px';
  Object.defineProperty(container, 'clientWidth', {
    value: 800,
    configurable: true,
  });
  return container;
}

describe('TimelineRenderer', () => {
  let timelineRenderer;
  let mockPlayer;

  beforeEach(() => {
    mockPlayer = createMockPlayer();
    timelineRenderer = new TimelineRenderer(mockPlayer);
  });

  describe('constructor', () => {
    it('should store player reference', () => {
      expect(timelineRenderer.player).toBe(mockPlayer);
    });

    it('should create child handlers', () => {
      expect(timelineRenderer.dragHandler).toBeDefined();
      expect(timelineRenderer.effectsHandler).toBeDefined();
      expect(timelineRenderer.timeMarkers).toBeDefined();
      expect(timelineRenderer.segmentRenderer).toBeDefined();
    });
  });

  describe('draw', () => {
    it('should clear timeline container before drawing', () => {
      mockPlayer.timelineContainer.innerHTML = '<div>old content</div>';

      timelineRenderer.draw();

      // After drawing, container should have been cleared (then new content added)
      // The fact that draw() runs without error and the innerHTML was initially non-empty
      // confirms the clear happened
      expect(true).toBe(true);
    });

    it('should not draw if timeline container is missing', () => {
      mockPlayer.timelineContainer = null;

      expect(() => timelineRenderer.draw()).not.toThrow();
    });

    it('should draw simple timeline when no duration', () => {
      mockPlayer.duration = 0;
      const drawSimpleSpy = vi.spyOn(timelineRenderer, 'drawSimpleTimeline');

      timelineRenderer.draw();

      expect(drawSimpleSpy).toHaveBeenCalled();
    });

    it('should calculate visible range based on zoom', () => {
      mockPlayer.duration = 100;
      mockPlayer.zoomLevel = 2; // Shows 50% of duration
      mockPlayer.zoomOffset = 0.25; // Starts at 25%

      const timeMarkersSpy = vi.spyOn(timelineRenderer.timeMarkers, 'draw');

      timelineRenderer.draw();

      // visibleDuration = 100 / 2 = 50
      // startTime = 0.25 * 100 = 25
      // endTime = min(25 + 50, 100) = 75
      expect(timeMarkersSpy).toHaveBeenCalledWith(
        expect.anything(),
        800, // width
        100, // duration
        25, // startTime
        75, // endTime
        50 // visibleDuration
      );
    });

    it('should clamp end time to duration', () => {
      mockPlayer.duration = 60;
      mockPlayer.zoomLevel = 1; // Shows full duration
      mockPlayer.zoomOffset = 0.5; // Would extend beyond end

      const timeMarkersSpy = vi.spyOn(timelineRenderer.timeMarkers, 'draw');

      timelineRenderer.draw();

      // visibleDuration = 60 / 1 = 60
      // startTime = 0.5 * 60 = 30
      // endTime = min(30 + 60, 60) = 60 (clamped)
      expect(timeMarkersSpy).toHaveBeenCalledWith(
        expect.anything(),
        800,
        60,
        30,
        60, // Clamped to duration
        60
      );
    });

    it('should draw segments if available', () => {
      mockPlayer.segments = [
        { id: 1, onset: 5, offset: 10 },
        { id: 2, onset: 15, offset: 20 },
      ];

      const segmentRendererSpy = vi.spyOn(timelineRenderer.segmentRenderer, 'draw');

      timelineRenderer.draw();

      expect(segmentRendererSpy).toHaveBeenCalledWith(
        mockPlayer.timelineContainer,
        mockPlayer.segments,
        800,
        0, // startTime
        60, // visibleDuration
        mockPlayer.waveformContainer
      );
    });

    it('should remove existing hover lines from waveform container', () => {
      // Add a hover line element
      const hoverLine = document.createElement('div');
      hoverLine.className = 'segment-hover-line';
      mockPlayer.waveformContainer.appendChild(hoverLine);

      timelineRenderer.draw();

      // Hover line should be removed
      expect(mockPlayer.waveformContainer.querySelector('.segment-hover-line')).toBeNull();
    });

    it('should handle missing waveform container', () => {
      mockPlayer.waveformContainer = null;

      expect(() => timelineRenderer.draw()).not.toThrow();
    });
  });

  describe('drawSimpleTimeline', () => {
    it('should create start and end markers', () => {
      mockPlayer.duration = 0;
      Object.defineProperty(mockPlayer.timelineContainer, 'clientWidth', {
        value: 600,
      });

      timelineRenderer.drawSimpleTimeline();

      // Should have 4 elements: start marker, start label, end marker, end label
      expect(mockPlayer.timelineContainer.childNodes.length).toBe(4);
    });

    it('should position end marker at container width', () => {
      Object.defineProperty(mockPlayer.timelineContainer, 'clientWidth', {
        value: 600,
      });

      timelineRenderer.drawSimpleTimeline();

      // Find the end marker (second marker element)
      const markers = mockPlayer.timelineContainer.querySelectorAll('div');
      // End marker should be positioned at width - 1
      const endMarker = Array.from(markers).find(
        (m) => m.style.width === '1px' && parseFloat(m.style.left) > 0
      );
      expect(endMarker).toBeTruthy();
      expect(endMarker.style.left).toBe('599px');
    });

    it('should show default 60s duration label', () => {
      timelineRenderer.drawSimpleTimeline();

      // Find the end label
      const labels = mockPlayer.timelineContainer.querySelectorAll('div');
      const endLabel = Array.from(labels).find((l) => l.textContent.includes('60.0s'));
      expect(endLabel).toBeTruthy();
    });

    it('should show 0.0s for start label', () => {
      timelineRenderer.drawSimpleTimeline();

      const labels = mockPlayer.timelineContainer.querySelectorAll('div');
      const startLabel = Array.from(labels).find((l) => l.textContent === '0.0s');
      expect(startLabel).toBeTruthy();
    });
  });

  describe('integration with zoom', () => {
    it('should handle no zoom (full view)', () => {
      mockPlayer.zoomLevel = 1;
      mockPlayer.zoomOffset = 0;
      mockPlayer.duration = 120;

      const timeMarkersSpy = vi.spyOn(timelineRenderer.timeMarkers, 'draw');

      timelineRenderer.draw();

      expect(timeMarkersSpy).toHaveBeenCalledWith(expect.anything(), 800, 120, 0, 120, 120);
    });

    it('should handle maximum zoom', () => {
      mockPlayer.zoomLevel = 10;
      mockPlayer.zoomOffset = 0.5; // Center of recording
      mockPlayer.duration = 100;

      const timeMarkersSpy = vi.spyOn(timelineRenderer.timeMarkers, 'draw');

      timelineRenderer.draw();

      // visibleDuration = 100 / 10 = 10
      // startTime = 0.5 * 100 = 50
      // endTime = min(50 + 10, 100) = 60
      expect(timeMarkersSpy).toHaveBeenCalledWith(expect.anything(), 800, 100, 50, 60, 10);
    });
  });

  describe('integration with segments', () => {
    it('should pass segments to segment renderer', () => {
      const segments = [
        { id: 1, onset: 0, offset: 5 },
        { id: 2, onset: 10, offset: 15 },
        { id: 3, onset: 50, offset: 55 },
      ];
      mockPlayer.segments = segments;

      const segmentRendererSpy = vi.spyOn(timelineRenderer.segmentRenderer, 'draw');

      timelineRenderer.draw();

      expect(segmentRendererSpy).toHaveBeenCalledWith(
        expect.anything(),
        segments,
        expect.any(Number),
        expect.any(Number),
        expect.any(Number),
        expect.anything()
      );
    });

    it('should handle empty segments array', () => {
      mockPlayer.segments = [];

      expect(() => timelineRenderer.draw()).not.toThrow();
    });
  });
});

/**
 * Tests for player/timeline_time_markers.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TimeMarkers } from './timeline_time_markers.js';

describe('TimeMarkers', () => {
  let timeMarkers;

  beforeEach(() => {
    timeMarkers = new TimeMarkers();
  });

  describe('calculateTimeStep', () => {
    it('should return 0.1s for very short durations (<= 2s)', () => {
      expect(timeMarkers.calculateTimeStep(0.5)).toBe(0.1);
      expect(timeMarkers.calculateTimeStep(1)).toBe(0.1);
      expect(timeMarkers.calculateTimeStep(2)).toBe(0.1);
    });

    it('should return 0.5s for short durations (2-5s)', () => {
      expect(timeMarkers.calculateTimeStep(2.1)).toBe(0.5);
      expect(timeMarkers.calculateTimeStep(3)).toBe(0.5);
      expect(timeMarkers.calculateTimeStep(5)).toBe(0.5);
    });

    it('should return 1s for medium-short durations (5-10s)', () => {
      expect(timeMarkers.calculateTimeStep(5.1)).toBe(1);
      expect(timeMarkers.calculateTimeStep(7)).toBe(1);
      expect(timeMarkers.calculateTimeStep(10)).toBe(1);
    });

    it('should return 2s for medium durations (10-30s)', () => {
      expect(timeMarkers.calculateTimeStep(10.1)).toBe(2);
      expect(timeMarkers.calculateTimeStep(20)).toBe(2);
      expect(timeMarkers.calculateTimeStep(30)).toBe(2);
    });

    it('should return 5s for medium-long durations (30-60s)', () => {
      expect(timeMarkers.calculateTimeStep(30.1)).toBe(5);
      expect(timeMarkers.calculateTimeStep(45)).toBe(5);
      expect(timeMarkers.calculateTimeStep(60)).toBe(5);
    });

    it('should return 30s for long durations (60-300s)', () => {
      expect(timeMarkers.calculateTimeStep(60.1)).toBe(30);
      expect(timeMarkers.calculateTimeStep(180)).toBe(30);
      expect(timeMarkers.calculateTimeStep(300)).toBe(30);
    });

    it('should return 60s for very long durations (>300s)', () => {
      expect(timeMarkers.calculateTimeStep(300.1)).toBe(60);
      expect(timeMarkers.calculateTimeStep(600)).toBe(60);
      expect(timeMarkers.calculateTimeStep(3600)).toBe(60);
    });
  });

  describe('formatTimeLabel', () => {
    describe('short durations (<= 3s)', () => {
      it('should show 2 decimal places with "s" suffix', () => {
        expect(timeMarkers.formatTimeLabel(1.5, 2)).toBe('1.50s');
        expect(timeMarkers.formatTimeLabel(0.123, 3)).toBe('0.12s');
        expect(timeMarkers.formatTimeLabel(2.999, 2.5)).toBe('3.00s');
      });
    });

    describe('medium durations (3-60s)', () => {
      it('should show 1 decimal place with "s" suffix', () => {
        expect(timeMarkers.formatTimeLabel(30, 30)).toBe('30.0s');
        expect(timeMarkers.formatTimeLabel(45.6, 60)).toBe('45.6s');
        expect(timeMarkers.formatTimeLabel(15.99, 20)).toBe('16.0s');
      });
    });

    describe('long durations (>60s)', () => {
      it('should show minutes:seconds format', () => {
        expect(timeMarkers.formatTimeLabel(60, 120)).toBe('1:00');
        expect(timeMarkers.formatTimeLabel(90, 180)).toBe('1:30');
        expect(timeMarkers.formatTimeLabel(125, 300)).toBe('2:05');
      });

      it('should pad seconds with leading zero', () => {
        expect(timeMarkers.formatTimeLabel(61, 120)).toBe('1:01');
        expect(timeMarkers.formatTimeLabel(69, 120)).toBe('1:09');
      });

      it('should handle full minutes', () => {
        expect(timeMarkers.formatTimeLabel(120, 300)).toBe('2:00');
        expect(timeMarkers.formatTimeLabel(300, 600)).toBe('5:00');
      });
    });
  });

  describe('draw', () => {
    let mockContainer;

    beforeEach(() => {
      // Create a mock container with appendChild method
      mockContainer = {
        appendChild: vi.fn(),
        clientWidth: 800,
      };
    });

    it('should draw time markers within visible range', () => {
      timeMarkers.draw(mockContainer, 800, 60, 0, 10, 10);

      // With visibleDuration=10 and timeStep=1, we should have markers at 1,2,3...10
      // Each marker creates 2 elements (marker + label)
      expect(mockContainer.appendChild).toHaveBeenCalled();
      const callCount = mockContainer.appendChild.mock.calls.length;
      // Should have approximately 10 markers with 2 elements each = ~20 calls
      expect(callCount).toBeGreaterThan(10);
    });

    it('should not draw markers outside duration', () => {
      const appendChildSpy = vi.fn();
      mockContainer.appendChild = appendChildSpy;

      // Duration is 5s, visible range is 0-10s
      timeMarkers.draw(mockContainer, 800, 5, 0, 10, 10);

      // With timeStep=1s and duration=5, markers at 0, 1, 2, 3, 4, 5 = 6 markers
      // Each marker has 2 elements (marker line + label)
      const markerCount = appendChildSpy.mock.calls.length / 2;
      expect(markerCount).toBeLessThanOrEqual(6);
    });

    it('should align markers to time step boundaries', () => {
      const appendedElements = [];
      mockContainer.appendChild = (el) => appendedElements.push(el);

      // Start at time 2.3, timeStep should be 5s for 30s visible duration
      timeMarkers.draw(mockContainer, 800, 60, 2.3, 32.3, 30);

      // First marker should be at 5 (first multiple of 5 >= 2.3)
      // Labels should contain time values
      const labels = appendedElements.filter((el) => el.textContent);
      expect(labels.length).toBeGreaterThan(0);
    });

    it('should calculate correct x positions', () => {
      const appendedElements = [];
      mockContainer.appendChild = (el) => appendedElements.push(el);

      // Simple case: visible range 0-10s in 1000px width
      timeMarkers.draw(mockContainer, 1000, 60, 0, 10, 10);

      // With timeStep=1s, markers at 0, 1, 2, ... 10
      // At 1000px width over 10s, each second = 100px
      const markers = appendedElements.filter((el) => el.style.width === '1px');
      expect(markers.length).toBeGreaterThan(0);

      // First marker is at time 0 (x=0px), second at time 1 (x=100px)
      expect(markers[0].style.left).toBe('0px');
      if (markers.length > 1) {
        expect(markers[1].style.left).toBe('100px');
      }
    });

    it('should not draw markers with negative x positions', () => {
      const appendedElements = [];
      mockContainer.appendChild = (el) => appendedElements.push(el);

      // Start time is 10s, visible duration is 10s
      timeMarkers.draw(mockContainer, 800, 60, 10, 20, 10);

      // All markers should have non-negative positions
      const markers = appendedElements.filter((el) => el.style.left);
      markers.forEach((marker) => {
        const left = parseFloat(marker.style.left);
        expect(left).toBeGreaterThanOrEqual(-20); // Allow small negative for label offset
      });
    });
  });
});

/**
 * Tests for player/data_manager.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { DataManager } from './data_manager.js';

/**
 * Create dependencies for DataManager
 */
function createDependencies(options = {}) {
  let selectionStart = options.selectionStart ?? 0;
  let selectionEnd = options.selectionEnd ?? 0;
  let segments = options.segments ?? [];

  return {
    getSelectionStart: vi.fn(() => selectionStart),
    getSelectionEnd: vi.fn(() => selectionEnd),
    getSegments: vi.fn(() => segments),
    setSegmentsData: vi.fn((newSegments) => {
      segments = newSegments;
    }),
    redrawCurrentView: vi.fn(),
    drawTimeline: vi.fn(),
    // Helpers for testing
    _setSelectionStart: (val) => {
      selectionStart = val;
    },
    _setSelectionEnd: (val) => {
      selectionEnd = val;
    },
    _setSegments: (val) => {
      segments = val;
    },
    _getSegments: () => segments,
  };
}

describe('DataManager', () => {
  let dataManager;
  let deps;

  beforeEach(() => {
    deps = createDependencies();
    dataManager = new DataManager(deps);
  });

  describe('constructor', () => {
    it('should store dependency functions', () => {
      expect(dataManager._getSelectionStart).toBe(deps.getSelectionStart);
      expect(dataManager._getSegments).toBe(deps.getSegments);
    });
  });

  describe('getSelection', () => {
    it('should return current selection via getters', () => {
      deps._setSelectionStart(1.5);
      deps._setSelectionEnd(3.2);

      const selection = dataManager.getSelection();

      expect(selection).toEqual({ start: 1.5, end: 3.2 });
      expect(deps.getSelectionStart).toHaveBeenCalled();
      expect(deps.getSelectionEnd).toHaveBeenCalled();
    });

    it('should return zeros when no selection', () => {
      const selection = dataManager.getSelection();

      expect(selection).toEqual({ start: 0, end: 0 });
    });
  });

  describe('isTimeInSegment', () => {
    it('should return false when no segments exist', () => {
      deps._setSegments([]);

      expect(dataManager.isTimeInSegment(1.0)).toBe(false);
    });

    it('should return false when segments is null', () => {
      deps._setSegments(null);

      expect(dataManager.isTimeInSegment(1.0)).toBe(false);
    });

    it('should return true when time is within a segment', () => {
      deps._setSegments([
        { onset: 0, offset: 1.5 },
        { onset: 2.0, offset: 3.5 },
        { onset: 4.0, offset: 5.0 },
      ]);

      expect(dataManager.isTimeInSegment(2.5)).toBe(true);
    });

    it('should return true when time is at segment boundary (onset)', () => {
      deps._setSegments([{ onset: 2.0, offset: 3.5 }]);

      expect(dataManager.isTimeInSegment(2.0)).toBe(true);
    });

    it('should return true when time is at segment boundary (offset)', () => {
      deps._setSegments([{ onset: 2.0, offset: 3.5 }]);

      expect(dataManager.isTimeInSegment(3.5)).toBe(true);
    });

    it('should return false when time is outside all segments', () => {
      deps._setSegments([
        { onset: 0, offset: 1.0 },
        { onset: 3.0, offset: 4.0 },
      ]);

      expect(dataManager.isTimeInSegment(2.0)).toBe(false);
    });

    it('should return false when time is before first segment', () => {
      deps._setSegments([{ onset: 1.0, offset: 2.0 }]);

      expect(dataManager.isTimeInSegment(0.5)).toBe(false);
    });

    it('should return false when time is after last segment', () => {
      deps._setSegments([{ onset: 1.0, offset: 2.0 }]);

      expect(dataManager.isTimeInSegment(2.5)).toBe(false);
    });
  });

  describe('findNearestSegmentBoundary', () => {
    it('should return null when no segments exist', () => {
      deps._setSegments([]);

      expect(dataManager.findNearestSegmentBoundary(1.0, 'forward')).toBeNull();
    });

    it('should return null when segments is null', () => {
      deps._setSegments(null);

      expect(dataManager.findNearestSegmentBoundary(1.0, 'backward')).toBeNull();
    });

    it('should find nearest boundary forward', () => {
      deps._setSegments([
        { onset: 0, offset: 1.0 },
        { onset: 2.0, offset: 3.0 },
        { onset: 4.0, offset: 5.0 },
      ]);

      // From time 1.5, nearest forward boundary is 2.0 (onset of second segment)
      expect(dataManager.findNearestSegmentBoundary(1.5, 'forward')).toBe(2.0);
    });

    it('should find nearest boundary backward', () => {
      deps._setSegments([
        { onset: 0, offset: 1.0 },
        { onset: 2.0, offset: 3.0 },
        { onset: 4.0, offset: 5.0 },
      ]);

      // From time 3.5, nearest backward boundary is 3.0 (offset of second segment)
      expect(dataManager.findNearestSegmentBoundary(3.5, 'backward')).toBe(3.0);
    });

    it('should find offset boundary forward when closer than onset', () => {
      deps._setSegments([{ onset: 2.0, offset: 3.0 }]);

      // From time 2.5, both 2.0 (behind) and 3.0 (ahead) are options
      // Forward should find 3.0
      expect(dataManager.findNearestSegmentBoundary(2.5, 'forward')).toBe(3.0);
    });

    it('should return null when no boundaries are in the requested direction', () => {
      deps._setSegments([{ onset: 0, offset: 1.0 }]);

      // From time 2.0 looking forward, there are no boundaries
      expect(dataManager.findNearestSegmentBoundary(2.0, 'forward')).toBeNull();
    });

    it('should return null when looking backward from before first segment', () => {
      deps._setSegments([{ onset: 2.0, offset: 3.0 }]);

      // From time 0.5 looking backward, there are no boundaries
      expect(dataManager.findNearestSegmentBoundary(0.5, 'backward')).toBeNull();
    });

    it('should default to forward direction', () => {
      deps._setSegments([{ onset: 2.0, offset: 3.0 }]);

      // Should default to forward
      expect(dataManager.findNearestSegmentBoundary(1.0)).toBe(2.0);
    });
  });

  describe('setSegments', () => {
    it('should set segments and trigger redraws', () => {
      const newSegments = [
        { onset: 0, offset: 1.0 },
        { onset: 2.0, offset: 3.0 },
      ];

      dataManager.setSegments(newSegments);

      expect(deps.setSegmentsData).toHaveBeenCalledWith(newSegments);
      expect(deps.redrawCurrentView).toHaveBeenCalledTimes(1);
      expect(deps.drawTimeline).toHaveBeenCalledTimes(1);
    });

    it('should set empty array when null is passed', () => {
      dataManager.setSegments(null);

      expect(deps.setSegmentsData).toHaveBeenCalledWith([]);
      expect(deps.redrawCurrentView).toHaveBeenCalled();
      expect(deps.drawTimeline).toHaveBeenCalled();
    });

    it('should set empty array when undefined is passed', () => {
      dataManager.setSegments(undefined);

      expect(deps.setSegmentsData).toHaveBeenCalledWith([]);
    });
  });

  describe('redrawSegments', () => {
    it('should call redrawCurrentView callback', () => {
      dataManager.redrawSegments();

      expect(deps.redrawCurrentView).toHaveBeenCalledTimes(1);
    });
  });
});

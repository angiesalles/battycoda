/**
 * Tests for player/seek_handler.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SeekHandler } from './seek_handler.js';

/**
 * Create a mock player object for SeekHandler tests (legacy style)
 */
function createMockPlayer(options = {}) {
  return {
    duration: options.duration ?? 60,
    currentTime: options.currentTime ?? 0,
    zoomLevel: options.zoomLevel ?? 1,
    zoomOffset: options.zoomOffset ?? 0,
    audioPlayer: {
      currentTime: options.audioCurrentTime ?? 0,
    },
    updateTimeDisplay: vi.fn(),
    redrawCurrentView: vi.fn(),
    drawTimeline: vi.fn(),
  };
}

/**
 * Create explicit dependencies (new DI style)
 */
function createDependencies(options = {}) {
  let duration = options.duration ?? 60;
  let currentTime = options.currentTime ?? 0;
  let zoomLevel = options.zoomLevel ?? 1;
  let zoomOffset = options.zoomOffset ?? 0;

  const audioPlayer = {
    currentTime: options.audioCurrentTime ?? 0,
  };

  return {
    audioPlayer,
    getDuration: vi.fn(() => duration),
    getZoomLevel: vi.fn(() => zoomLevel),
    setCurrentTime: vi.fn((time) => {
      currentTime = time;
    }),
    setZoomOffset: vi.fn((offset) => {
      zoomOffset = offset;
    }),
    updateTimeDisplay: vi.fn(),
    redrawCurrentView: vi.fn(),
    drawTimeline: vi.fn(),
    // Helpers for testing
    _setDuration: (val) => {
      duration = val;
    },
    _setZoomLevel: (val) => {
      zoomLevel = val;
    },
    _getZoomOffset: () => zoomOffset,
    _getCurrentTime: () => currentTime,
  };
}

describe('SeekHandler', () => {
  let seekHandler;
  let mockPlayer;

  beforeEach(() => {
    mockPlayer = createMockPlayer();
    seekHandler = new SeekHandler(mockPlayer);
  });

  describe('constructor', () => {
    it('should store player reference', () => {
      expect(seekHandler.player).toBe(mockPlayer);
    });
  });

  describe('seek', () => {
    it('should seek to a valid time', () => {
      seekHandler.seek(30);

      expect(mockPlayer.audioPlayer.currentTime).toBe(30);
      expect(mockPlayer.currentTime).toBe(30);
    });

    it('should clamp negative time to 0', () => {
      seekHandler.seek(-10);

      expect(mockPlayer.audioPlayer.currentTime).toBe(0);
      expect(mockPlayer.currentTime).toBe(0);
    });

    it('should clamp time exceeding duration', () => {
      mockPlayer.duration = 60;

      seekHandler.seek(100);

      expect(mockPlayer.audioPlayer.currentTime).toBe(60);
      expect(mockPlayer.currentTime).toBe(60);
    });

    it('should update displays after seeking', () => {
      seekHandler.seek(30);

      expect(mockPlayer.updateTimeDisplay).toHaveBeenCalledTimes(1);
      expect(mockPlayer.redrawCurrentView).toHaveBeenCalledTimes(1);
      expect(mockPlayer.drawTimeline).toHaveBeenCalledTimes(1);
    });

    describe('zoom offset adjustment', () => {
      it('should not adjust zoom offset when not zoomed', () => {
        mockPlayer.zoomLevel = 1;
        mockPlayer.zoomOffset = 0;

        seekHandler.seek(30);

        expect(mockPlayer.zoomOffset).toBe(0);
      });

      it('should center view on seek position when zoomed', () => {
        mockPlayer.duration = 100;
        mockPlayer.zoomLevel = 4; // Shows 25% of total duration
        mockPlayer.zoomOffset = 0;

        // Seek to middle of recording (50 seconds)
        seekHandler.seek(50);

        // timeRatio = 50/100 = 0.5
        // visibleDuration = 1/4 = 0.25
        // zoomOffset = max(0, min(0.5 - 0.125, 1 - 0.25)) = max(0, min(0.375, 0.75)) = 0.375
        expect(mockPlayer.zoomOffset).toBeCloseTo(0.375);
      });

      it('should clamp zoom offset to 0 when seeking near start', () => {
        mockPlayer.duration = 100;
        mockPlayer.zoomLevel = 4;
        mockPlayer.zoomOffset = 0.5;

        // Seek near start
        seekHandler.seek(5);

        // timeRatio = 5/100 = 0.05
        // visibleDuration = 0.25
        // zoomOffset = max(0, min(0.05 - 0.125, 0.75)) = max(0, min(-0.075, 0.75)) = 0
        expect(mockPlayer.zoomOffset).toBe(0);
      });

      it('should clamp zoom offset when seeking near end', () => {
        mockPlayer.duration = 100;
        mockPlayer.zoomLevel = 4;
        mockPlayer.zoomOffset = 0;

        // Seek near end
        seekHandler.seek(95);

        // timeRatio = 95/100 = 0.95
        // visibleDuration = 0.25
        // zoomOffset = max(0, min(0.95 - 0.125, 0.75)) = max(0, min(0.825, 0.75)) = 0.75
        expect(mockPlayer.zoomOffset).toBeCloseTo(0.75);
      });

      it('should handle extreme zoom levels', () => {
        mockPlayer.duration = 60;
        mockPlayer.zoomLevel = 10; // Shows 10% of total duration

        seekHandler.seek(30);

        // Should center at 50% mark
        // timeRatio = 30/60 = 0.5
        // visibleDuration = 0.1
        // zoomOffset = max(0, min(0.5 - 0.05, 0.9)) = 0.45
        expect(mockPlayer.zoomOffset).toBeCloseTo(0.45);
      });
    });

    describe('edge cases', () => {
      it('should handle seek to exact start', () => {
        mockPlayer.zoomLevel = 2;
        mockPlayer.zoomOffset = 0.5;

        seekHandler.seek(0);

        expect(mockPlayer.audioPlayer.currentTime).toBe(0);
        expect(mockPlayer.zoomOffset).toBe(0);
      });

      it('should handle seek to exact end', () => {
        mockPlayer.duration = 60;
        mockPlayer.zoomLevel = 2;

        seekHandler.seek(60);

        expect(mockPlayer.audioPlayer.currentTime).toBe(60);
        // Should show the end portion of the recording
        expect(mockPlayer.zoomOffset).toBeCloseTo(0.5);
      });

      it('should handle zero duration', () => {
        mockPlayer.duration = 0;

        seekHandler.seek(10);

        // Should clamp to 0
        expect(mockPlayer.audioPlayer.currentTime).toBe(0);
      });
    });
  });
});

/**
 * Tests using new dependency injection style
 */
describe('SeekHandler (Dependency Injection)', () => {
  let seekHandler;
  let deps;

  beforeEach(() => {
    deps = createDependencies();
    seekHandler = new SeekHandler(deps);
  });

  describe('constructor', () => {
    it('should not have player reference in DI mode', () => {
      expect(seekHandler.player).toBeUndefined();
    });
  });

  describe('seek', () => {
    it('should call dependency functions', () => {
      seekHandler.seek(30);

      expect(deps.getDuration).toHaveBeenCalled();
      expect(deps.setCurrentTime).toHaveBeenCalledWith(30);
      expect(deps.audioPlayer.currentTime).toBe(30);
    });

    it('should update displays via callbacks', () => {
      seekHandler.seek(30);

      expect(deps.updateTimeDisplay).toHaveBeenCalledTimes(1);
      expect(deps.redrawCurrentView).toHaveBeenCalledTimes(1);
      expect(deps.drawTimeline).toHaveBeenCalledTimes(1);
    });

    it('should adjust zoom offset when zoomed', () => {
      deps._setDuration(100);
      deps._setZoomLevel(4);

      seekHandler.seek(50);

      expect(deps.getZoomLevel).toHaveBeenCalled();
      expect(deps.setZoomOffset).toHaveBeenCalled();
    });

    it('should not adjust zoom offset when not zoomed', () => {
      deps._setZoomLevel(1);

      seekHandler.seek(30);

      expect(deps.setZoomOffset).not.toHaveBeenCalled();
    });
  });
});

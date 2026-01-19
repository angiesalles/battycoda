/**
 * Tests for player/play_region_handler.js
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { PlayRegionHandler } from './play_region_handler.js';

/**
 * Create dependencies for PlayRegionHandler
 */
function createDependencies(options = {}) {
  let duration = options.duration ?? 60;
  let zoomLevel = options.zoomLevel ?? 1;
  let zoomOffset = options.zoomOffset ?? 0;

  let audioPlayer = options.audioPlayer ?? {
    currentTime: options.audioCurrentTime ?? 0,
    play: vi.fn(),
    pause: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };

  return {
    getAudioPlayer: vi.fn(() => audioPlayer),
    getDuration: vi.fn(() => duration),
    getZoomLevel: vi.fn(() => zoomLevel),
    setZoomLevel: vi.fn((level) => {
      zoomLevel = level;
    }),
    setZoomOffset: vi.fn((offset) => {
      zoomOffset = offset;
    }),
    seek: vi.fn(),
    redrawCurrentView: vi.fn(),
    drawTimeline: vi.fn(),
    updateTimeDisplay: vi.fn(),
    // Helpers for testing
    _setDuration: (val) => {
      duration = val;
    },
    _setZoomLevel: (val) => {
      zoomLevel = val;
    },
    _getZoomOffset: () => zoomOffset,
    _getZoomLevel: () => zoomLevel,
    _setAudioPlayer: (ap) => {
      audioPlayer = ap;
    },
    _getAudioPlayer: () => audioPlayer,
  };
}

describe('PlayRegionHandler', () => {
  let playRegionHandler;
  let deps;

  beforeEach(() => {
    deps = createDependencies();
    playRegionHandler = new PlayRegionHandler(deps);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('constructor', () => {
    it('should store dependency functions', () => {
      expect(playRegionHandler._getAudioPlayer).toBe(deps.getAudioPlayer);
      expect(playRegionHandler._getDuration).toBe(deps.getDuration);
    });

    it('should initialize _stopAtEndListener as null', () => {
      expect(playRegionHandler._stopAtEndListener).toBeNull();
    });
  });

  describe('playRegion', () => {
    it('should seek to start position', () => {
      playRegionHandler.playRegion(10, 20);

      expect(deps.seek).toHaveBeenCalledWith(10);
    });

    it('should start playback', () => {
      playRegionHandler.playRegion(10, 20);

      expect(deps._getAudioPlayer().play).toHaveBeenCalledTimes(1);
    });

    it('should add timeupdate listener to stop at end', () => {
      playRegionHandler.playRegion(10, 20);

      expect(deps._getAudioPlayer().addEventListener).toHaveBeenCalledWith(
        'timeupdate',
        expect.any(Function)
      );
    });

    it('should do nothing if audioPlayer is null', () => {
      deps._setAudioPlayer(null);

      playRegionHandler.playRegion(10, 20);

      expect(deps.seek).not.toHaveBeenCalled();
    });

    it('should clean up existing listener before adding new one', () => {
      // Set up a pre-existing listener
      const existingListener = vi.fn();
      playRegionHandler._stopAtEndListener = existingListener;
      const audioPlayer = deps._getAudioPlayer();

      playRegionHandler.playRegion(10, 20);

      // Should have removed the old listener
      expect(audioPlayer.removeEventListener).toHaveBeenCalledWith('timeupdate', existingListener);
    });

    describe('timeupdate listener behavior', () => {
      it('should pause when currentTime reaches end', () => {
        playRegionHandler.playRegion(10, 20);

        // Get the listener that was added
        const listener = deps._getAudioPlayer().addEventListener.mock.calls[0][1];

        // Simulate currentTime reaching end
        deps._getAudioPlayer().currentTime = 20;
        listener();

        expect(deps._getAudioPlayer().pause).toHaveBeenCalled();
      });

      it('should not pause when currentTime is before end', () => {
        playRegionHandler.playRegion(10, 20);

        // Get the listener that was added
        const listener = deps._getAudioPlayer().addEventListener.mock.calls[0][1];

        // Simulate currentTime before end
        deps._getAudioPlayer().currentTime = 15;
        listener();

        expect(deps._getAudioPlayer().pause).not.toHaveBeenCalled();
      });
    });
  });

  describe('_zoomToRegionIfNeeded', () => {
    it('should not zoom if already zoomed in', () => {
      deps._setZoomLevel(2);
      deps._setDuration(100);

      playRegionHandler._zoomToRegionIfNeeded(10, 20);

      expect(deps.setZoomLevel).not.toHaveBeenCalled();
    });

    it('should not zoom if region is more than half the duration', () => {
      deps._setZoomLevel(1);
      deps._setDuration(100);

      // Region is 60 seconds, which is > half of 100
      playRegionHandler._zoomToRegionIfNeeded(10, 70);

      expect(deps.setZoomLevel).not.toHaveBeenCalled();
    });

    it('should zoom in when at default zoom and region is small', () => {
      deps._setZoomLevel(1);
      deps._setDuration(100);

      // Region is 10 seconds, which is < half of 100
      playRegionHandler._zoomToRegionIfNeeded(10, 20);

      expect(deps.setZoomLevel).toHaveBeenCalled();
    });

    it('should cap zoom level at 10', () => {
      deps._setZoomLevel(1);
      deps._setDuration(100);

      // Very small region that would result in zoom > 10
      playRegionHandler._zoomToRegionIfNeeded(10, 11);

      expect(deps.setZoomLevel).toHaveBeenCalled();
      const calledZoom = deps.setZoomLevel.mock.calls[0][0];
      expect(calledZoom).toBeLessThanOrEqual(10);
    });

    it('should center the view on the segment', () => {
      deps._setZoomLevel(1);
      deps._setDuration(100);

      playRegionHandler._zoomToRegionIfNeeded(40, 60);

      expect(deps.setZoomOffset).toHaveBeenCalled();
    });

    it('should update displays after zooming', () => {
      deps._setZoomLevel(1);
      deps._setDuration(100);

      playRegionHandler._zoomToRegionIfNeeded(10, 20);

      expect(deps.redrawCurrentView).toHaveBeenCalledTimes(1);
      expect(deps.drawTimeline).toHaveBeenCalledTimes(1);
      expect(deps.updateTimeDisplay).toHaveBeenCalledTimes(1);
    });

    it('should clamp zoomOffset to valid range (0 to 1-visible)', () => {
      deps._setZoomLevel(1);
      deps._setDuration(100);

      // Region near the start
      playRegionHandler._zoomToRegionIfNeeded(0, 10);

      expect(deps.setZoomOffset).toHaveBeenCalled();
      const calledOffset = deps.setZoomOffset.mock.calls[0][0];
      expect(calledOffset).toBeGreaterThanOrEqual(0);

      // Reset and test region near the end
      deps._setZoomLevel(1);
      vi.clearAllMocks();
      playRegionHandler._zoomToRegionIfNeeded(90, 100);

      expect(deps.setZoomOffset).toHaveBeenCalled();
      const calledOffset2 = deps.setZoomOffset.mock.calls[0][0];
      expect(calledOffset2).toBeLessThanOrEqual(1);
    });
  });

  describe('_cleanupListener', () => {
    it('should remove listener and set to null', () => {
      const listener = vi.fn();
      playRegionHandler._stopAtEndListener = listener;
      const audioPlayer = deps._getAudioPlayer();

      playRegionHandler._cleanupListener();

      expect(audioPlayer.removeEventListener).toHaveBeenCalledWith('timeupdate', listener);
      expect(playRegionHandler._stopAtEndListener).toBeNull();
    });

    it('should do nothing if no listener exists', () => {
      playRegionHandler._stopAtEndListener = null;

      playRegionHandler._cleanupListener();

      expect(deps._getAudioPlayer().removeEventListener).not.toHaveBeenCalled();
    });

    it('should do nothing if audioPlayer is null', () => {
      playRegionHandler._stopAtEndListener = vi.fn();
      deps._setAudioPlayer(null);

      // Should not throw
      expect(() => playRegionHandler._cleanupListener()).not.toThrow();
    });
  });

  describe('stop', () => {
    it('should clean up listener and pause playback', () => {
      const listener = vi.fn();
      playRegionHandler._stopAtEndListener = listener;
      const audioPlayer = deps._getAudioPlayer();

      playRegionHandler.stop();

      expect(audioPlayer.removeEventListener).toHaveBeenCalledWith('timeupdate', listener);
      expect(audioPlayer.pause).toHaveBeenCalled();
    });

    it('should handle null audioPlayer gracefully', () => {
      deps._setAudioPlayer(null);

      // Should not throw
      expect(() => playRegionHandler.stop()).not.toThrow();
    });
  });

  describe('integration scenarios', () => {
    it('should handle multiple consecutive playRegion calls', () => {
      // First call
      playRegionHandler.playRegion(0, 10);
      const firstListener = playRegionHandler._stopAtEndListener;

      // Second call should clean up first
      playRegionHandler.playRegion(20, 30);

      expect(deps._getAudioPlayer().removeEventListener).toHaveBeenCalledWith(
        'timeupdate',
        firstListener
      );
      expect(deps.seek).toHaveBeenLastCalledWith(20);
    });

    it('should work with edge case times', () => {
      deps._setDuration(60);

      // Start at 0
      playRegionHandler.playRegion(0, 5);
      expect(deps.seek).toHaveBeenCalledWith(0);

      // End at duration
      playRegionHandler.playRegion(55, 60);
      expect(deps.seek).toHaveBeenCalledWith(55);
    });
  });
});

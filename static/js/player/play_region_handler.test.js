/**
 * Tests for player/play_region_handler.js
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { PlayRegionHandler } from './play_region_handler.js';

/**
 * Create a mock player object for PlayRegionHandler tests
 */
function createMockPlayer(options = {}) {
  return {
    duration: options.duration ?? 60,
    currentTime: options.currentTime ?? 0,
    zoomLevel: options.zoomLevel ?? 1,
    zoomOffset: options.zoomOffset ?? 0,
    audioPlayer: {
      currentTime: options.audioCurrentTime ?? 0,
      play: vi.fn(),
      pause: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    },
    seek: vi.fn(),
    updateTimeDisplay: vi.fn(),
    redrawCurrentView: vi.fn(),
    drawTimeline: vi.fn(),
  };
}

describe('PlayRegionHandler', () => {
  let playRegionHandler;
  let mockPlayer;

  beforeEach(() => {
    mockPlayer = createMockPlayer();
    playRegionHandler = new PlayRegionHandler(mockPlayer);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('constructor', () => {
    it('should store player reference', () => {
      expect(playRegionHandler.player).toBe(mockPlayer);
    });

    it('should initialize _stopAtEndListener as null', () => {
      expect(playRegionHandler._stopAtEndListener).toBeNull();
    });
  });

  describe('playRegion', () => {
    it('should seek to start position', () => {
      playRegionHandler.playRegion(10, 20);

      expect(mockPlayer.seek).toHaveBeenCalledWith(10);
    });

    it('should start playback', () => {
      playRegionHandler.playRegion(10, 20);

      expect(mockPlayer.audioPlayer.play).toHaveBeenCalledTimes(1);
    });

    it('should add timeupdate listener to stop at end', () => {
      playRegionHandler.playRegion(10, 20);

      expect(mockPlayer.audioPlayer.addEventListener).toHaveBeenCalledWith(
        'timeupdate',
        expect.any(Function)
      );
    });

    it('should do nothing if audioPlayer is null', () => {
      mockPlayer.audioPlayer = null;

      playRegionHandler.playRegion(10, 20);

      expect(mockPlayer.seek).not.toHaveBeenCalled();
    });

    it('should clean up existing listener before adding new one', () => {
      // Set up a pre-existing listener
      const existingListener = vi.fn();
      playRegionHandler._stopAtEndListener = existingListener;
      mockPlayer.audioPlayer = createMockPlayer().audioPlayer;

      playRegionHandler.playRegion(10, 20);

      // Should have removed the old listener
      expect(mockPlayer.audioPlayer.removeEventListener).toHaveBeenCalledWith(
        'timeupdate',
        existingListener
      );
    });

    describe('timeupdate listener behavior', () => {
      it('should pause when currentTime reaches end', () => {
        let capturedListener;
        mockPlayer.audioPlayer.addEventListener.mockImplementation((event, listener) => {
          if (event === 'timeupdate') {
            capturedListener = listener;
          }
        });

        playRegionHandler.playRegion(10, 20);

        // Simulate time reaching end
        mockPlayer.audioPlayer.currentTime = 20;
        capturedListener();

        expect(mockPlayer.audioPlayer.pause).toHaveBeenCalledTimes(1);
        expect(mockPlayer.audioPlayer.removeEventListener).toHaveBeenCalledWith(
          'timeupdate',
          capturedListener
        );
      });

      it('should not pause when currentTime is before end', () => {
        let capturedListener;
        mockPlayer.audioPlayer.addEventListener.mockImplementation((event, listener) => {
          if (event === 'timeupdate') {
            capturedListener = listener;
          }
        });

        playRegionHandler.playRegion(10, 20);

        // Simulate time before end
        mockPlayer.audioPlayer.currentTime = 15;
        capturedListener();

        expect(mockPlayer.audioPlayer.pause).not.toHaveBeenCalled();
      });
    });
  });

  describe('_zoomToRegionIfNeeded', () => {
    it('should not zoom if already zoomed in', () => {
      mockPlayer.zoomLevel = 2;
      const initialZoomLevel = mockPlayer.zoomLevel;

      playRegionHandler._zoomToRegionIfNeeded(10, 20);

      expect(mockPlayer.zoomLevel).toBe(initialZoomLevel);
    });

    it('should not zoom if region is more than half the duration', () => {
      mockPlayer.duration = 60;
      mockPlayer.zoomLevel = 1;

      // Region is 40 seconds, which is more than half of 60
      playRegionHandler._zoomToRegionIfNeeded(10, 50);

      expect(mockPlayer.zoomLevel).toBe(1);
    });

    it('should zoom in when at default zoom and region is small', () => {
      mockPlayer.duration = 60;
      mockPlayer.zoomLevel = 1;

      // Region is 10 seconds (less than half of 60)
      playRegionHandler._zoomToRegionIfNeeded(20, 30);

      expect(mockPlayer.zoomLevel).toBeGreaterThan(1);
    });

    it('should cap zoom level at 10', () => {
      mockPlayer.duration = 100;
      mockPlayer.zoomLevel = 1;

      // Very small region that would require extreme zoom
      playRegionHandler._zoomToRegionIfNeeded(10, 10.5);

      expect(mockPlayer.zoomLevel).toBeLessThanOrEqual(10);
    });

    it('should center the view on the segment', () => {
      mockPlayer.duration = 100;
      mockPlayer.zoomLevel = 1;

      // Region in the middle
      playRegionHandler._zoomToRegionIfNeeded(45, 55);

      // zoomOffset should be set to center the region
      expect(mockPlayer.zoomOffset).toBeGreaterThanOrEqual(0);
      expect(mockPlayer.zoomOffset).toBeLessThanOrEqual(1);
    });

    it('should update displays after zooming', () => {
      mockPlayer.duration = 60;
      mockPlayer.zoomLevel = 1;

      playRegionHandler._zoomToRegionIfNeeded(10, 20);

      expect(mockPlayer.redrawCurrentView).toHaveBeenCalledTimes(1);
      expect(mockPlayer.drawTimeline).toHaveBeenCalledTimes(1);
      expect(mockPlayer.updateTimeDisplay).toHaveBeenCalledTimes(1);
    });

    it('should clamp zoomOffset to valid range (0 to 1-visible)', () => {
      mockPlayer.duration = 100;
      mockPlayer.zoomLevel = 1;

      // Region near the start
      playRegionHandler._zoomToRegionIfNeeded(0, 10);

      expect(mockPlayer.zoomOffset).toBeGreaterThanOrEqual(0);

      // Reset and test region near the end
      mockPlayer.zoomLevel = 1;
      playRegionHandler._zoomToRegionIfNeeded(90, 100);

      expect(mockPlayer.zoomOffset).toBeLessThanOrEqual(1);
    });
  });

  describe('_cleanupListener', () => {
    it('should remove listener and set to null', () => {
      const listener = vi.fn();
      playRegionHandler._stopAtEndListener = listener;

      playRegionHandler._cleanupListener();

      expect(mockPlayer.audioPlayer.removeEventListener).toHaveBeenCalledWith(
        'timeupdate',
        listener
      );
      expect(playRegionHandler._stopAtEndListener).toBeNull();
    });

    it('should do nothing if no listener exists', () => {
      playRegionHandler._stopAtEndListener = null;

      playRegionHandler._cleanupListener();

      expect(mockPlayer.audioPlayer.removeEventListener).not.toHaveBeenCalled();
    });

    it('should do nothing if audioPlayer is null', () => {
      playRegionHandler._stopAtEndListener = vi.fn();
      mockPlayer.audioPlayer = null;

      // Should not throw
      expect(() => playRegionHandler._cleanupListener()).not.toThrow();
    });
  });

  describe('stop', () => {
    it('should clean up listener and pause playback', () => {
      const listener = vi.fn();
      playRegionHandler._stopAtEndListener = listener;

      playRegionHandler.stop();

      expect(mockPlayer.audioPlayer.removeEventListener).toHaveBeenCalledWith(
        'timeupdate',
        listener
      );
      expect(mockPlayer.audioPlayer.pause).toHaveBeenCalledTimes(1);
    });

    it('should handle null audioPlayer gracefully', () => {
      mockPlayer.audioPlayer = null;

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

      expect(mockPlayer.audioPlayer.removeEventListener).toHaveBeenCalledWith(
        'timeupdate',
        firstListener
      );
      expect(mockPlayer.seek).toHaveBeenLastCalledWith(20);
    });

    it('should work with edge case times', () => {
      mockPlayer.duration = 60;

      // Start at 0
      playRegionHandler.playRegion(0, 5);
      expect(mockPlayer.seek).toHaveBeenCalledWith(0);

      // End at duration
      playRegionHandler.playRegion(55, 60);
      expect(mockPlayer.seek).toHaveBeenCalledWith(55);
    });
  });
});

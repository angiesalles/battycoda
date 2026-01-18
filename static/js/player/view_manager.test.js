/**
 * Tests for player/view_manager.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ViewManager } from './view_manager.js';

/**
 * Create a mock player object for ViewManager tests
 */
function createMockPlayer(options = {}) {
  return {
    duration: options.duration ?? 60,
    zoomLevel: options.zoomLevel ?? 1,
    zoomOffset: options.zoomOffset ?? 0,
    waveformContainer: options.waveformContainer ?? {
      style: { display: 'block' },
      clientWidth: 800,
      clientHeight: 200,
    },
    waveformRenderer: {
      show: vi.fn(),
      hide: vi.fn(),
    },
    spectrogramDataRenderer: {
      initialize: vi.fn().mockResolvedValue(true),
      show: vi.fn(),
      hide: vi.fn(),
      updateView: vi.fn(),
      render: vi.fn(),
    },
    overlayRenderer: {
      draw: vi.fn(),
    },
    drawWaveform: vi.fn(),
    drawTimeline: vi.fn(),
    updateSelectionDisplay: vi.fn(),
    updateTimeDisplay: vi.fn(),
  };
}

describe('ViewManager', () => {
  let viewManager;
  let mockPlayer;

  beforeEach(() => {
    mockPlayer = createMockPlayer();
    viewManager = new ViewManager(mockPlayer);
  });

  describe('constructor', () => {
    it('should store player reference', () => {
      expect(viewManager.player).toBe(mockPlayer);
    });

    it('should initialize with waveform view mode', () => {
      expect(viewManager.viewMode).toBe('waveform');
    });

    it('should initialize spectrogram as not initialized', () => {
      expect(viewManager.spectrogramInitialized).toBe(false);
    });
  });

  describe('getViewMode', () => {
    it('should return current view mode', () => {
      expect(viewManager.getViewMode()).toBe('waveform');

      viewManager.viewMode = 'spectrogram';
      expect(viewManager.getViewMode()).toBe('spectrogram');
    });
  });

  describe('isSpectrogramAvailable', () => {
    it('should return false when spectrogram not initialized', () => {
      expect(viewManager.isSpectrogramAvailable()).toBe(false);
    });

    it('should return true when spectrogram initialized', () => {
      viewManager.spectrogramInitialized = true;
      expect(viewManager.isSpectrogramAvailable()).toBe(true);
    });
  });

  describe('initializeSpectrogramData', () => {
    it('should initialize spectrogram successfully', async () => {
      const success = await viewManager.initializeSpectrogramData();

      expect(success).toBe(true);
      expect(viewManager.spectrogramInitialized).toBe(true);
      expect(mockPlayer.spectrogramDataRenderer.initialize).toHaveBeenCalled();
    });

    it('should handle initialization failure', async () => {
      mockPlayer.spectrogramDataRenderer.initialize.mockResolvedValue(false);

      const success = await viewManager.initializeSpectrogramData();

      expect(success).toBe(false);
      expect(viewManager.spectrogramInitialized).toBe(false);
    });

    it('should handle initialization error', async () => {
      mockPlayer.spectrogramDataRenderer.initialize.mockRejectedValue(new Error('Init failed'));

      const success = await viewManager.initializeSpectrogramData();

      expect(success).toBe(false);
      expect(viewManager.spectrogramInitialized).toBe(false);
    });
  });

  describe('setViewMode', () => {
    it('should not change mode if already in that mode', () => {
      viewManager.viewMode = 'waveform';
      const hideWaveformSpy = vi.spyOn(viewManager, 'hideWaveform');

      viewManager.setViewMode('waveform');

      expect(hideWaveformSpy).not.toHaveBeenCalled();
    });

    it('should not switch to spectrogram if not initialized', () => {
      viewManager.spectrogramInitialized = false;

      viewManager.setViewMode('spectrogram');

      expect(viewManager.viewMode).toBe('waveform');
    });

    it('should switch to spectrogram when initialized', () => {
      viewManager.spectrogramInitialized = true;

      viewManager.setViewMode('spectrogram');

      expect(viewManager.viewMode).toBe('spectrogram');
      expect(mockPlayer.spectrogramDataRenderer.show).toHaveBeenCalled();
    });

    it('should switch from spectrogram to waveform', () => {
      viewManager.spectrogramInitialized = true;
      viewManager.viewMode = 'spectrogram';

      viewManager.setViewMode('waveform');

      expect(viewManager.viewMode).toBe('waveform');
      expect(mockPlayer.waveformRenderer.show).toHaveBeenCalled();
    });

    it('should call redraw after mode change', () => {
      viewManager.spectrogramInitialized = true;
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.setViewMode('spectrogram');

      expect(redrawSpy).toHaveBeenCalled();
    });
  });

  describe('showWaveform', () => {
    it('should show waveform container and renderer', () => {
      viewManager.showWaveform();

      expect(mockPlayer.waveformContainer.style.display).toBe('block');
      expect(mockPlayer.waveformRenderer.show).toHaveBeenCalled();
    });

    it('should handle missing waveform container', () => {
      mockPlayer.waveformContainer = null;

      expect(() => viewManager.showWaveform()).not.toThrow();
      expect(mockPlayer.waveformRenderer.show).toHaveBeenCalled();
    });
  });

  describe('hideWaveform', () => {
    it('should hide waveform renderer', () => {
      viewManager.hideWaveform();

      expect(mockPlayer.waveformRenderer.hide).toHaveBeenCalled();
    });

    it('should handle missing waveform renderer', () => {
      mockPlayer.waveformRenderer = null;

      expect(() => viewManager.hideWaveform()).not.toThrow();
    });
  });

  describe('showSpectrogram', () => {
    it('should show spectrogram when initialized', () => {
      viewManager.spectrogramInitialized = true;

      viewManager.showSpectrogram();

      expect(mockPlayer.spectrogramDataRenderer.show).toHaveBeenCalled();
    });

    it('should not show spectrogram when not initialized', () => {
      viewManager.spectrogramInitialized = false;

      viewManager.showSpectrogram();

      expect(mockPlayer.spectrogramDataRenderer.show).not.toHaveBeenCalled();
    });
  });

  describe('hideSpectrogram', () => {
    it('should hide spectrogram when initialized', () => {
      viewManager.spectrogramInitialized = true;

      viewManager.hideSpectrogram();

      expect(mockPlayer.spectrogramDataRenderer.hide).toHaveBeenCalled();
    });

    it('should not hide spectrogram when not initialized', () => {
      viewManager.spectrogramInitialized = false;

      viewManager.hideSpectrogram();

      expect(mockPlayer.spectrogramDataRenderer.hide).not.toHaveBeenCalled();
    });
  });

  describe('redraw', () => {
    it('should redraw waveform when in waveform mode', () => {
      viewManager.viewMode = 'waveform';

      viewManager.redraw();

      expect(mockPlayer.drawWaveform).toHaveBeenCalled();
      expect(mockPlayer.drawTimeline).toHaveBeenCalled();
      expect(mockPlayer.overlayRenderer.draw).toHaveBeenCalled();
    });

    it('should update spectrogram view when in spectrogram mode', () => {
      viewManager.viewMode = 'spectrogram';
      viewManager.spectrogramInitialized = true;

      viewManager.redraw();

      expect(mockPlayer.spectrogramDataRenderer.updateView).toHaveBeenCalled();
      expect(mockPlayer.drawTimeline).toHaveBeenCalled();
      expect(mockPlayer.overlayRenderer.draw).toHaveBeenCalled();
    });

    it('should calculate visible time range for spectrogram', () => {
      viewManager.viewMode = 'spectrogram';
      viewManager.spectrogramInitialized = true;
      mockPlayer.duration = 120;
      mockPlayer.zoomLevel = 2;
      mockPlayer.zoomOffset = 0.25;

      viewManager.redraw();

      // visibleDuration = 120 / 2 = 60
      // visibleStartTime = 0.25 * 120 = 30
      // visibleEndTime = min(30 + 60, 120) = 90
      expect(mockPlayer.spectrogramDataRenderer.updateView).toHaveBeenCalledWith(30, 90, 800, 200);
    });
  });

  describe('handleZoomChange', () => {
    it('should update player zoom and redraw', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleZoomChange(4, 0.5);

      expect(mockPlayer.zoomLevel).toBe(4);
      expect(mockPlayer.zoomOffset).toBe(0.5);
      expect(redrawSpy).toHaveBeenCalled();
    });
  });

  describe('handleSelectionChange', () => {
    it('should redraw and update selection display', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleSelectionChange();

      expect(redrawSpy).toHaveBeenCalled();
      expect(mockPlayer.updateSelectionDisplay).toHaveBeenCalled();
    });
  });

  describe('handlePlaybackUpdate', () => {
    it('should redraw and update time display', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handlePlaybackUpdate();

      expect(redrawSpy).toHaveBeenCalled();
      expect(mockPlayer.updateTimeDisplay).toHaveBeenCalled();
    });
  });

  describe('handleResize', () => {
    it('should render spectrogram and redraw when spectrogram initialized', () => {
      viewManager.spectrogramInitialized = true;
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleResize();

      expect(mockPlayer.spectrogramDataRenderer.render).toHaveBeenCalled();
      expect(redrawSpy).toHaveBeenCalled();
    });

    it('should only redraw when spectrogram not initialized', () => {
      viewManager.spectrogramInitialized = false;
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleResize();

      expect(mockPlayer.spectrogramDataRenderer.render).not.toHaveBeenCalled();
      expect(redrawSpy).toHaveBeenCalled();
    });
  });
});

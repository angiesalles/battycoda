/**
 * Tests for player/view_manager.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ViewManager } from './view_manager.js';

/**
 * Create dependencies for ViewManager
 */
function createDependencies(options = {}) {
  let duration = options.duration ?? 60;
  let zoomLevel = options.zoomLevel ?? 1;
  let zoomOffset = options.zoomOffset ?? 0;

  const waveformContainer = options.waveformContainer ?? {
    style: { display: 'block' },
    clientWidth: 800,
    clientHeight: 200,
  };

  return {
    spectrogramDataRenderer: {
      initialize: vi.fn().mockResolvedValue(true),
      show: vi.fn(),
      hide: vi.fn(),
      updateView: vi.fn(),
      render: vi.fn(),
    },
    waveformRenderer: {
      show: vi.fn(),
      hide: vi.fn(),
    },
    overlayRenderer: {
      draw: vi.fn(),
    },
    getWaveformContainer: vi.fn(() => waveformContainer),
    getDuration: vi.fn(() => duration),
    getZoomLevel: vi.fn(() => zoomLevel),
    getZoomOffset: vi.fn(() => zoomOffset),
    setZoomLevel: vi.fn((level) => {
      zoomLevel = level;
    }),
    setZoomOffset: vi.fn((offset) => {
      zoomOffset = offset;
    }),
    drawWaveform: vi.fn(),
    drawTimeline: vi.fn(),
    updateSelectionDisplay: vi.fn(),
    updateTimeDisplay: vi.fn(),
    // Helpers for testing
    _setDuration: (val) => {
      duration = val;
    },
    _setZoomLevel: (val) => {
      zoomLevel = val;
    },
    _setZoomOffset: (val) => {
      zoomOffset = val;
    },
    _waveformContainer: waveformContainer,
  };
}

describe('ViewManager', () => {
  let viewManager;
  let deps;

  beforeEach(() => {
    deps = createDependencies();
    viewManager = new ViewManager(deps);
  });

  describe('constructor', () => {
    it('should store dependency functions', () => {
      expect(viewManager._getDuration).toBe(deps.getDuration);
      expect(viewManager._spectrogramDataRenderer).toBe(deps.spectrogramDataRenderer);
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
      const result = await viewManager.initializeSpectrogramData();

      expect(result).toBe(true);
      expect(viewManager.spectrogramInitialized).toBe(true);
      expect(deps.spectrogramDataRenderer.initialize).toHaveBeenCalled();
    });

    it('should handle initialization failure', async () => {
      deps.spectrogramDataRenderer.initialize.mockResolvedValue(false);

      const result = await viewManager.initializeSpectrogramData();

      expect(result).toBe(false);
      expect(viewManager.spectrogramInitialized).toBe(false);
    });

    it('should handle initialization error', async () => {
      deps.spectrogramDataRenderer.initialize.mockRejectedValue(new Error('Init failed'));

      const result = await viewManager.initializeSpectrogramData();

      expect(result).toBe(false);
      expect(viewManager.spectrogramInitialized).toBe(false);
    });
  });

  describe('setViewMode', () => {
    it('should not change mode if already in that mode', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.setViewMode('waveform');

      expect(redrawSpy).not.toHaveBeenCalled();
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
      expect(deps.waveformRenderer.hide).toHaveBeenCalled();
      expect(deps.spectrogramDataRenderer.show).toHaveBeenCalled();
    });

    it('should switch from spectrogram to waveform', () => {
      viewManager.spectrogramInitialized = true;
      viewManager.viewMode = 'spectrogram';

      viewManager.setViewMode('waveform');

      expect(viewManager.viewMode).toBe('waveform');
      expect(deps.spectrogramDataRenderer.hide).toHaveBeenCalled();
      expect(deps.waveformRenderer.show).toHaveBeenCalled();
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

      expect(deps._waveformContainer.style.display).toBe('block');
      expect(deps.waveformRenderer.show).toHaveBeenCalled();
    });

    it('should handle missing waveform container', () => {
      const depsNoContainer = createDependencies();
      depsNoContainer.getWaveformContainer = vi.fn(() => null);
      const vm = new ViewManager(depsNoContainer);

      // Should not throw
      expect(() => vm.showWaveform()).not.toThrow();
    });
  });

  describe('hideWaveform', () => {
    it('should hide waveform renderer', () => {
      viewManager.hideWaveform();

      expect(deps.waveformRenderer.hide).toHaveBeenCalled();
    });

    it('should handle missing waveform renderer', () => {
      const depsNoRenderer = createDependencies();
      depsNoRenderer.waveformRenderer = null;
      const vm = new ViewManager(depsNoRenderer);

      // Should not throw
      expect(() => vm.hideWaveform()).not.toThrow();
    });
  });

  describe('showSpectrogram', () => {
    it('should show spectrogram when initialized', () => {
      viewManager.spectrogramInitialized = true;

      viewManager.showSpectrogram();

      expect(deps.spectrogramDataRenderer.show).toHaveBeenCalled();
    });

    it('should not show spectrogram when not initialized', () => {
      viewManager.spectrogramInitialized = false;

      viewManager.showSpectrogram();

      expect(deps.spectrogramDataRenderer.show).not.toHaveBeenCalled();
    });
  });

  describe('hideSpectrogram', () => {
    it('should hide spectrogram when initialized', () => {
      viewManager.spectrogramInitialized = true;

      viewManager.hideSpectrogram();

      expect(deps.spectrogramDataRenderer.hide).toHaveBeenCalled();
    });

    it('should not hide spectrogram when not initialized', () => {
      viewManager.spectrogramInitialized = false;

      viewManager.hideSpectrogram();

      expect(deps.spectrogramDataRenderer.hide).not.toHaveBeenCalled();
    });
  });

  describe('redraw', () => {
    it('should redraw waveform when in waveform mode', () => {
      viewManager.viewMode = 'waveform';

      viewManager.redraw();

      expect(deps.drawWaveform).toHaveBeenCalled();
      expect(deps.drawTimeline).toHaveBeenCalled();
      expect(deps.overlayRenderer.draw).toHaveBeenCalled();
    });

    it('should update spectrogram view when in spectrogram mode', () => {
      viewManager.viewMode = 'spectrogram';
      viewManager.spectrogramInitialized = true;

      viewManager.redraw();

      expect(deps.spectrogramDataRenderer.updateView).toHaveBeenCalled();
      expect(deps.drawTimeline).toHaveBeenCalled();
    });

    it('should calculate visible time range for spectrogram', () => {
      viewManager.viewMode = 'spectrogram';
      viewManager.spectrogramInitialized = true;
      deps._setDuration(100);
      deps._setZoomLevel(2);
      deps._setZoomOffset(0.25);

      viewManager.redraw();

      // visibleDuration = 100 / 2 = 50
      // visibleStartTime = 0.25 * 100 = 25
      // visibleEndTime = min(25 + 50, 100) = 75
      expect(deps.spectrogramDataRenderer.updateView).toHaveBeenCalledWith(25, 75, 800, 200);
    });
  });

  describe('handleZoomChange', () => {
    it('should update zoom and redraw', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleZoomChange(4, 0.5);

      expect(deps.setZoomLevel).toHaveBeenCalledWith(4);
      expect(deps.setZoomOffset).toHaveBeenCalledWith(0.5);
      expect(redrawSpy).toHaveBeenCalled();
    });
  });

  describe('handleSelectionChange', () => {
    it('should redraw and update selection display', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleSelectionChange();

      expect(redrawSpy).toHaveBeenCalled();
      expect(deps.updateSelectionDisplay).toHaveBeenCalled();
    });
  });

  describe('handlePlaybackUpdate', () => {
    it('should redraw and update time display', () => {
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handlePlaybackUpdate();

      expect(redrawSpy).toHaveBeenCalled();
      expect(deps.updateTimeDisplay).toHaveBeenCalled();
    });
  });

  describe('handleResize', () => {
    it('should render spectrogram and redraw when spectrogram initialized', () => {
      viewManager.spectrogramInitialized = true;
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleResize();

      expect(deps.spectrogramDataRenderer.render).toHaveBeenCalled();
      expect(redrawSpy).toHaveBeenCalled();
    });

    it('should only redraw when spectrogram not initialized', () => {
      viewManager.spectrogramInitialized = false;
      const redrawSpy = vi.spyOn(viewManager, 'redraw');

      viewManager.handleResize();

      expect(deps.spectrogramDataRenderer.render).not.toHaveBeenCalled();
      expect(redrawSpy).toHaveBeenCalled();
    });
  });
});

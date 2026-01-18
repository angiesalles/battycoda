/**
 * Tests for cluster_explorer/controls.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { loadSegmentDetails, initializeControls } from './controls.js';
import { setJQuery, resetState } from './state.js';
import { API_ENDPOINTS, buildUrl } from './api.js';

// Mock d3-selection
vi.mock('d3-selection', () => ({
  selectAll: vi.fn(() => ({
    attr: vi.fn().mockReturnThis(),
    empty: vi.fn(() => false),
  })),
}));

describe('cluster_explorer/controls', () => {
  let mockJQuery;
  let mockElement;
  let mockGetJSON;
  let eventHandlers;

  beforeEach(() => {
    // Reset all state
    resetState();
    eventHandlers = {};

    // Create mock element
    mockElement = {
      html: vi.fn().mockReturnThis(),
      text: vi.fn().mockReturnThis(),
      attr: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      off: vi.fn().mockReturnThis(),
      on: vi.fn((event, handler) => {
        eventHandlers[event] = handler;
        return mockElement;
      }),
    };

    // Create mock getJSON with promise-like behavior
    mockGetJSON = vi.fn().mockReturnValue({
      fail: vi.fn().mockReturnThis(),
    });

    // Create mock jQuery function
    mockJQuery = vi.fn(() => mockElement);
    mockJQuery.getJSON = mockGetJSON;

    // Inject mock jQuery via state (instead of window.jQuery)
    setJQuery(mockJQuery);
  });

  describe('loadSegmentDetails', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      loadSegmentDetails(123);

      expect(mockGetJSON).not.toHaveBeenCalled();
    });

    it('should show loading state in UI elements', () => {
      loadSegmentDetails(123);

      // Check that loading indicators are shown
      expect(mockElement.html).toHaveBeenCalled();
      expect(mockElement.text).toHaveBeenCalledWith('Loading...');
    });

    it('should fetch segment data from correct URL', () => {
      loadSegmentDetails(456);

      expect(mockGetJSON).toHaveBeenCalledWith(
        buildUrl(API_ENDPOINTS.GET_SEGMENT_DATA, { segment_id: 456 }),
        expect.any(Function)
      );
    });

    it('should update UI with segment details on success', () => {
      loadSegmentDetails(101);

      // Get the success callback
      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        segment_id: 101,
        recording_name: 'Recording 1',
        onset: 0.5,
        offset: 1.2,
        duration: 0.7,
        spectrogram_url: '/media/spectrograms/seg_101.png',
        audio_url: '/media/audio/seg_101.wav',
      });

      expect(mockElement.text).toHaveBeenCalledWith(101);
      expect(mockElement.text).toHaveBeenCalledWith('Recording 1');
      expect(mockElement.text).toHaveBeenCalledWith('0.5000');
      expect(mockElement.text).toHaveBeenCalledWith('1.2000');
      expect(mockElement.text).toHaveBeenCalledWith('0.7000');
    });

    it('should set spectrogram image on success', () => {
      loadSegmentDetails(101);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        segment_id: 101,
        recording_name: 'Recording 1',
        onset: 0.5,
        offset: 1.2,
        duration: 0.7,
        spectrogram_url: '/media/spectrograms/seg_101.png',
        audio_url: '/media/audio/seg_101.wav',
      });

      // Check that html was called with img tag
      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('<img src="/media/spectrograms/seg_101.png"')
      );
    });

    it('should set audio player source on success', () => {
      loadSegmentDetails(101);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        segment_id: 101,
        recording_name: 'Recording 1',
        onset: 0.5,
        offset: 1.2,
        duration: 0.7,
        spectrogram_url: '/media/spectrograms/seg_101.png',
        audio_url: '/media/audio/seg_101.wav',
      });

      expect(mockElement.attr).toHaveBeenCalledWith('src', '/media/audio/seg_101.wav');
    });

    it('should show error message on API failure response', () => {
      loadSegmentDetails(101);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'error',
        message: 'Segment not found',
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load segment: Segment not found')
      );
    });

    it('should show error message on AJAX failure', () => {
      const failMock = vi.fn();
      mockGetJSON.mockReturnValue({ fail: failMock });

      loadSegmentDetails(101);

      // Get the fail callback
      const failCallback = failMock.mock.calls[0][0];
      failCallback();

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load segment. Please try again.')
      );
    });
  });

  describe('initializeControls', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      initializeControls(
        () => {},
        () => {}
      );

      // No error should be thrown
      expect(mockElement.on).not.toHaveBeenCalled();
    });

    it('should set up point size slider event handler', () => {
      initializeControls(
        () => {},
        () => {}
      );

      // Check that event handler was registered
      expect(mockJQuery).toHaveBeenCalledWith('#point-size');
      expect(mockElement.on).toHaveBeenCalledWith('input', expect.any(Function));
    });

    it('should set up opacity slider event handler', () => {
      initializeControls(
        () => {},
        () => {}
      );

      expect(mockJQuery).toHaveBeenCalledWith('#cluster-opacity');
      expect(mockElement.on).toHaveBeenCalledWith('input', expect.any(Function));
    });

    it('should call onPointSizeChange callback when slider changes', () => {
      const onPointSizeChange = vi.fn();
      initializeControls(onPointSizeChange, () => {});

      // Get the input handler from the first on() call
      const inputHandler = mockElement.on.mock.calls[0][1];

      // Simulate slider change
      inputHandler.call({ val: () => '10' });

      expect(onPointSizeChange).toHaveBeenCalledWith(8); // Uses parsed value from mockElement.val
    });

    it('should call onOpacityChange callback when slider changes', () => {
      const onOpacityChange = vi.fn();
      mockElement.val.mockReturnValue('0.5');
      initializeControls(() => {}, onOpacityChange);

      // Get the input handler from the second on() call
      const inputHandler = mockElement.on.mock.calls[1][1];

      // Simulate slider change
      inputHandler.call({ val: () => '0.5' });

      expect(onOpacityChange).toHaveBeenCalledWith(0.5);
    });
  });
});

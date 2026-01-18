/**
 * Tests for cluster_explorer/interactions.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { selectCluster, loadClusterDetails, loadClusterMembers } from './interactions.js';
import { getSelectedClusterId, setIsProjectScope, setJQuery, resetState } from './state.js';
import { API_ENDPOINTS, buildUrl } from './api.js';

// Mock d3-selection
vi.mock('d3-selection', () => ({
  selectAll: vi.fn(() => ({
    attr: vi.fn().mockReturnThis(),
    empty: vi.fn(() => false),
  })),
}));

describe('cluster_explorer/interactions', () => {
  let mockJQuery;
  let mockElement;
  let mockGetJSON;

  beforeEach(() => {
    // Reset all state
    resetState();

    // Create mock element
    mockElement = {
      html: vi.fn().mockReturnThis(),
      text: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      attr: vi.fn().mockReturnThis(),
      addClass: vi.fn().mockReturnThis(),
      removeClass: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      append: vi.fn().mockReturnThis(),
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

  describe('selectCluster', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      selectCluster(1);

      expect(mockGetJSON).not.toHaveBeenCalled();
    });

    it('should update selected cluster ID in state', () => {
      selectCluster(42);

      expect(getSelectedClusterId()).toBe(42);
    });

    it('should load cluster details', () => {
      selectCluster(1);

      // Check that getJSON was called for cluster details
      expect(mockGetJSON).toHaveBeenCalledWith(
        buildUrl(API_ENDPOINTS.GET_CLUSTER_DATA, { cluster_id: 1 }),
        expect.any(Function)
      );
    });

    it('should load cluster members', () => {
      selectCluster(1);

      // Check that getJSON was called for cluster members
      expect(mockGetJSON).toHaveBeenCalledWith(
        buildUrl(API_ENDPOINTS.GET_CLUSTER_MEMBERS, { cluster_id: 1, limit: 50 }),
        expect.any(Function)
      );
    });
  });

  describe('loadClusterDetails', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      loadClusterDetails(1);

      expect(mockGetJSON).not.toHaveBeenCalled();
    });

    it('should show and hide appropriate UI sections', () => {
      loadClusterDetails(1);

      expect(mockJQuery).toHaveBeenCalledWith('.initial-message');
      expect(mockJQuery).toHaveBeenCalledWith('.cluster-details');
      expect(mockElement.addClass).toHaveBeenCalledWith('d-none');
      expect(mockElement.removeClass).toHaveBeenCalledWith('d-none');
    });

    it('should show loading indicator', () => {
      loadClusterDetails(1);

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Loading cluster details')
      );
    });

    it('should fetch cluster data from correct URL', () => {
      loadClusterDetails(456);

      expect(mockGetJSON).toHaveBeenCalledWith(
        buildUrl(API_ENDPOINTS.GET_CLUSTER_DATA, { cluster_id: 456 }),
        expect.any(Function)
      );
    });

    it('should populate UI with cluster details on success', () => {
      loadClusterDetails(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        cluster_id: 1,
        label: 'Echolocation',
        description: 'Test description',
        size: 15,
        coherence: 0.85,
        representative_spectrogram_url: '/media/spectrograms/seg_1.png',
        representative_audio_url: '/media/audio/seg_1.wav',
        mappings: [],
      });

      expect(mockElement.text).toHaveBeenCalledWith('Cluster 1');
      expect(mockElement.val).toHaveBeenCalled();
      expect(mockElement.text).toHaveBeenCalledWith(15);
      expect(mockElement.text).toHaveBeenCalledWith('0.8500');
    });

    it('should display spectrogram when available', () => {
      loadClusterDetails(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        cluster_id: 1,
        label: 'Test',
        description: '',
        size: 10,
        coherence: 0.9,
        representative_spectrogram_url: '/media/spectrograms/seg_1.png',
        representative_audio_url: '/media/audio/seg_1.wav',
        mappings: [],
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('<img src="/media/spectrograms/seg_1.png"')
      );
    });

    it('should show message when no spectrogram available', () => {
      loadClusterDetails(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        cluster_id: 1,
        label: 'Test',
        description: '',
        size: 10,
        coherence: 0.9,
        representative_spectrogram_url: null,
        representative_audio_url: null,
        mappings: [],
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('No representative sample available')
      );
    });

    it('should display mappings when present', () => {
      loadClusterDetails(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        cluster_id: 1,
        label: 'Test',
        description: '',
        size: 10,
        coherence: 0.9,
        representative_spectrogram_url: null,
        representative_audio_url: null,
        mappings: [{ species_name: 'Eptesicus fuscus', call_name: 'Echo', confidence: 0.95 }],
      });

      expect(mockElement.addClass).toHaveBeenCalledWith('d-none');
      expect(mockElement.empty).toHaveBeenCalled();
      expect(mockElement.append).toHaveBeenCalled();
    });

    it('should show error message on API failure response', () => {
      loadClusterDetails(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'error',
        message: 'Cluster not found',
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load cluster details: Cluster not found')
      );
    });

    it('should show error message on AJAX failure', () => {
      const failMock = vi.fn();
      mockGetJSON.mockReturnValue({ fail: failMock });

      loadClusterDetails(1);

      const failCallback = failMock.mock.calls[0][0];
      failCallback();

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load cluster details. Please try again.')
      );
    });
  });

  describe('loadClusterMembers', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      loadClusterMembers(1);

      expect(mockGetJSON).not.toHaveBeenCalled();
    });

    it('should show and hide appropriate UI sections', () => {
      loadClusterMembers(1);

      expect(mockJQuery).toHaveBeenCalledWith('.initial-members-message');
      expect(mockJQuery).toHaveBeenCalledWith('.cluster-members');
      expect(mockElement.addClass).toHaveBeenCalledWith('d-none');
      expect(mockElement.removeClass).toHaveBeenCalledWith('d-none');
    });

    it('should show loading indicator', () => {
      loadClusterMembers(1);

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Loading cluster members')
      );
    });

    it('should fetch cluster members from correct URL', () => {
      loadClusterMembers(456);

      expect(mockGetJSON).toHaveBeenCalledWith(
        buildUrl(API_ENDPOINTS.GET_CLUSTER_MEMBERS, { cluster_id: 456, limit: 50 }),
        expect.any(Function)
      );
    });

    it('should populate table with member data on success', () => {
      loadClusterMembers(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        members: [
          {
            segment_id: 101,
            onset: 0.5,
            offset: 1.2,
            duration: 0.7,
            confidence: 0.92,
            recording_name: 'Recording 1',
          },
        ],
        total_size: 15,
        has_more: false,
        is_project_scope: false,
      });

      // Check that HTML was set for the table body
      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('101'));
      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('0.500'));
      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('1.200'));
      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('0.700'));
      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('0.92'));
    });

    it('should include recording name column for project scope', () => {
      loadClusterMembers(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        members: [
          {
            segment_id: 101,
            onset: 0.5,
            offset: 1.2,
            duration: 0.7,
            confidence: 0.92,
            recording_name: 'Recording 1',
          },
        ],
        total_size: 15,
        has_more: false,
        is_project_scope: true,
      });

      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('Recording 1'));
    });

    it('should show "has more" message when results are truncated', () => {
      loadClusterMembers(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        members: [
          {
            segment_id: 101,
            onset: 0.5,
            offset: 1.2,
            duration: 0.7,
            confidence: 0.92,
          },
        ],
        total_size: 100,
        has_more: true,
        is_project_scope: false,
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Showing 1 of 100 segments')
      );
    });

    it('should show message when cluster has no members', () => {
      loadClusterMembers(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        members: [],
        total_size: 0,
        has_more: false,
        is_project_scope: false,
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('No segments in this cluster')
      );
    });

    it('should handle N/A confidence values', () => {
      loadClusterMembers(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'success',
        members: [
          {
            segment_id: 101,
            onset: 0.5,
            offset: 1.2,
            duration: 0.7,
            confidence: null,
          },
        ],
        total_size: 1,
        has_more: false,
        is_project_scope: false,
      });

      expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('N/A'));
    });

    it('should show error message on API failure response', () => {
      loadClusterMembers(1);

      const successCallback = mockGetJSON.mock.calls[0][1];
      successCallback({
        status: 'error',
        message: 'Cluster not found',
      });

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load members: Cluster not found')
      );
    });

    it('should show error message on AJAX failure', () => {
      const failMock = vi.fn();
      mockGetJSON.mockReturnValue({ fail: failMock });

      loadClusterMembers(1);

      const failCallback = failMock.mock.calls[0][0];
      failCallback();

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load cluster members. Please try again.')
      );
    });

    it('should use correct column count for project scope', () => {
      // Use setIsProjectScope to set the state (code now uses getIsProjectScope() internally)
      setIsProjectScope(true);

      loadClusterMembers(1);

      // Loading indicator should use 7 columns for project scope
      const htmlCalls = mockElement.html.mock.calls;
      expect(htmlCalls.some((call) => call[0].includes('colspan="7"'))).toBe(true);
    });
  });
});

/**
 * Tests for cluster_explorer/data_loader.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { saveClusterLabel } from './data_loader.js';
import { setSelectedClusterId, setClusters, getClusters, resetState } from './state.js';
import { API_ENDPOINTS } from './api.js';

// Mock getCsrfToken
vi.mock('../utils/page-data.js', () => ({
  getCsrfToken: vi.fn(() => 'test-csrf-token'),
}));

describe('cluster_explorer/data_loader', () => {
  let mockJQuery;
  let mockAjax;
  let mockElement;

  beforeEach(() => {
    // Reset all state
    resetState();

    // Create mock element that jQuery selector returns
    mockElement = {
      val: vi.fn(() => ''),
      html: vi.fn().mockReturnThis(),
      attr: vi.fn().mockReturnThis(),
    };

    // Create mock ajax that returns a promise-like object
    mockAjax = vi.fn().mockImplementation((options) => {
      // Store the options for later assertions
      mockAjax.lastOptions = options;
      return {
        done: vi.fn(),
        fail: vi.fn(),
        always: vi.fn(),
      };
    });

    // Create mock jQuery function
    mockJQuery = vi.fn((selector) => {
      if (selector === '#cluster-label') {
        return { val: vi.fn(() => 'Test Label') };
      }
      if (selector === '#cluster-description') {
        return { val: vi.fn(() => 'Test Description') };
      }
      if (selector === '#save-cluster-label') {
        return mockElement;
      }
      return mockElement;
    });
    mockJQuery.ajax = mockAjax;

    window.jQuery = mockJQuery;
    window.toastr = {
      success: vi.fn(),
      error: vi.fn(),
    };
    window.clusters = [];
  });

  describe('saveClusterLabel', () => {
    it('should return early if jQuery is not available', () => {
      window.jQuery = undefined;

      saveClusterLabel();

      // No error should be thrown
      expect(mockAjax).not.toHaveBeenCalled();
    });

    it('should return early if no cluster is selected', () => {
      setSelectedClusterId(null);

      saveClusterLabel();

      expect(mockAjax).not.toHaveBeenCalled();
    });

    it('should make AJAX request with correct parameters', () => {
      setSelectedClusterId(42);

      saveClusterLabel();

      expect(mockAjax).toHaveBeenCalledTimes(1);
      expect(mockAjax.lastOptions.url).toBe(API_ENDPOINTS.UPDATE_CLUSTER_LABEL);
      expect(mockAjax.lastOptions.type).toBe('POST');
      expect(mockAjax.lastOptions.headers['X-CSRFToken']).toBe('test-csrf-token');
      expect(mockAjax.lastOptions.data.cluster_id).toBe(42);
    });

    it('should include label and description in request', () => {
      setSelectedClusterId(1);

      saveClusterLabel();

      expect(mockAjax.lastOptions.data.label).toBe('Test Label');
      expect(mockAjax.lastOptions.data.description).toBe('Test Description');
    });

    it('should show loading state on button', () => {
      setSelectedClusterId(1);

      saveClusterLabel();

      expect(mockElement.html).toHaveBeenCalled();
      expect(mockElement.attr).toHaveBeenCalledWith('disabled', true);
    });

    it('should call success callback on successful save', () => {
      setSelectedClusterId(1);
      const onSuccess = vi.fn();

      saveClusterLabel(onSuccess);

      // Simulate successful response
      const successHandler = mockAjax.lastOptions.success;
      successHandler({ status: 'success' });

      expect(onSuccess).toHaveBeenCalledWith(1);
    });

    it('should update local cluster data on success', () => {
      setSelectedClusterId(1);
      // Use setClusters to set up the state (code now uses getClusters() internally)
      const testClusters = [
        { id: 1, label: 'Old Label', description: 'Old Desc', is_labeled: false },
      ];
      setClusters(testClusters);

      saveClusterLabel();

      const successHandler = mockAjax.lastOptions.success;
      successHandler({ status: 'success' });

      const clusters = getClusters();
      expect(clusters[0].label).toBe('Test Label');
      expect(clusters[0].description).toBe('Test Description');
      expect(clusters[0].is_labeled).toBe(true);
    });

    it('should show success toast on successful save', () => {
      setSelectedClusterId(1);

      saveClusterLabel();

      const successHandler = mockAjax.lastOptions.success;
      successHandler({ status: 'success' });

      expect(window.toastr.success).toHaveBeenCalledWith(
        'Cluster label updated successfully'
      );
    });

    it('should show error toast on API error response', () => {
      setSelectedClusterId(1);

      saveClusterLabel();

      const successHandler = mockAjax.lastOptions.success;
      successHandler({ status: 'error', message: 'Invalid cluster ID' });

      expect(window.toastr.error).toHaveBeenCalledWith(
        'Failed to update label: Invalid cluster ID'
      );
    });

    it('should show error toast on AJAX failure', () => {
      setSelectedClusterId(1);

      saveClusterLabel();

      const errorHandler = mockAjax.lastOptions.error;
      errorHandler();

      expect(window.toastr.error).toHaveBeenCalledWith(
        'Failed to update cluster label. Please try again.'
      );
    });

    it('should restore button state on complete', () => {
      setSelectedClusterId(1);
      const originalHtml = '<i class="fa fa-save"></i> Save';
      mockElement.html.mockReturnValueOnce(mockElement).mockImplementation(() => originalHtml);

      saveClusterLabel();

      const completeHandler = mockAjax.lastOptions.complete;
      completeHandler();

      expect(mockElement.attr).toHaveBeenCalledWith('disabled', false);
    });

    it('should use alert when toastr is not available', () => {
      setSelectedClusterId(1);
      window.toastr = undefined;
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

      saveClusterLabel();

      const successHandler = mockAjax.lastOptions.success;
      successHandler({ status: 'success' });

      expect(alertSpy).toHaveBeenCalledWith('Cluster label updated successfully');
    });
  });
});

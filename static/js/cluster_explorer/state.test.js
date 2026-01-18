/**
 * Tests for cluster_explorer/state.js
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  getSelectedClusterId,
  setSelectedClusterId,
  getClusters,
  setClusters,
  getIsProjectScope,
  setIsProjectScope,
  getJQuery,
  setJQuery,
  resetState,
  colorScale,
} from './state.js';

describe('cluster_explorer/state', () => {
  // Reset all state before each test
  beforeEach(() => {
    resetState();
  });

  describe('selectedClusterId', () => {
    it('should return null by default', () => {
      expect(getSelectedClusterId()).toBe(null);
    });

    it('should set and get a cluster ID', () => {
      setSelectedClusterId(42);
      expect(getSelectedClusterId()).toBe(42);
    });

    it('should allow setting cluster ID to null', () => {
      setSelectedClusterId(42);
      setSelectedClusterId(null);
      expect(getSelectedClusterId()).toBe(null);
    });

    it('should update when set multiple times', () => {
      setSelectedClusterId(1);
      expect(getSelectedClusterId()).toBe(1);

      setSelectedClusterId(2);
      expect(getSelectedClusterId()).toBe(2);

      setSelectedClusterId(3);
      expect(getSelectedClusterId()).toBe(3);
    });
  });

  describe('colorScale', () => {
    it('should return a color string for an index', () => {
      const color = colorScale(0);
      expect(typeof color).toBe('string');
      // D3 category10 colors start with #
      expect(color).toMatch(/^#[0-9a-fA-F]{6}$/);
    });

    it('should return different colors for different indices', () => {
      const color0 = colorScale(0);
      const color1 = colorScale(1);
      const color2 = colorScale(2);

      expect(color0).not.toBe(color1);
      expect(color1).not.toBe(color2);
      expect(color0).not.toBe(color2);
    });

    it('should return consistent colors for the same index', () => {
      const color1 = colorScale(5);
      const color2 = colorScale(5);
      expect(color1).toBe(color2);
    });
  });

  describe('clusters', () => {
    it('should return null by default', () => {
      expect(getClusters()).toBe(null);
    });

    it('should set and get clusters array', () => {
      const testClusters = [
        { id: 1, label: 'Cluster 1', size: 10 },
        { id: 2, label: 'Cluster 2', size: 20 },
      ];
      setClusters(testClusters);
      expect(getClusters()).toBe(testClusters);
    });

    it('should allow setting clusters to null', () => {
      setClusters([{ id: 1 }]);
      setClusters(null);
      expect(getClusters()).toBe(null);
    });

    it('should return the same array reference', () => {
      const testClusters = [{ id: 1 }];
      setClusters(testClusters);
      const retrieved = getClusters();
      expect(retrieved).toBe(testClusters);

      // Mutating the retrieved array should affect the state
      retrieved.push({ id: 2 });
      expect(getClusters().length).toBe(2);
    });
  });

  describe('isProjectScope', () => {
    it('should return false by default', () => {
      expect(getIsProjectScope()).toBe(false);
    });

    it('should set and get project scope', () => {
      setIsProjectScope(true);
      expect(getIsProjectScope()).toBe(true);
    });

    it('should coerce truthy values to boolean', () => {
      setIsProjectScope(1);
      expect(getIsProjectScope()).toBe(true);

      setIsProjectScope('yes');
      expect(getIsProjectScope()).toBe(true);
    });

    it('should coerce falsy values to boolean', () => {
      setIsProjectScope(true);
      setIsProjectScope(0);
      expect(getIsProjectScope()).toBe(false);

      setIsProjectScope(true);
      setIsProjectScope('');
      expect(getIsProjectScope()).toBe(false);

      setIsProjectScope(true);
      setIsProjectScope(null);
      expect(getIsProjectScope()).toBe(false);
    });
  });

  describe('jQuery', () => {
    it('should return null by default when window.jQuery is not available', () => {
      // In test environment, window.jQuery is undefined
      const originalJQuery = window.jQuery;
      delete window.jQuery;

      expect(getJQuery()).toBe(undefined);

      // Restore if it was set
      if (originalJQuery) {
        window.jQuery = originalJQuery;
      }
    });

    it('should return window.jQuery as fallback when not explicitly set', () => {
      const mockJQuery = () => {};
      window.jQuery = mockJQuery;

      expect(getJQuery()).toBe(mockJQuery);

      delete window.jQuery;
    });

    it('should return injected jQuery over window.jQuery', () => {
      const windowJQuery = () => 'window';
      const injectedJQuery = () => 'injected';

      window.jQuery = windowJQuery;
      setJQuery(injectedJQuery);

      expect(getJQuery()).toBe(injectedJQuery);

      delete window.jQuery;
    });

    it('should allow setting jQuery to null', () => {
      const mockJQuery = () => {};
      setJQuery(mockJQuery);
      expect(getJQuery()).toBe(mockJQuery);

      setJQuery(null);
      // Should fall back to window.jQuery (undefined in test env)
      expect(getJQuery()).toBe(undefined);
    });
  });

  describe('resetState', () => {
    it('should reset all state to defaults', () => {
      const mockJQuery = () => {};

      // Set various state values
      setSelectedClusterId(42);
      setClusters([{ id: 1 }]);
      setIsProjectScope(true);
      setJQuery(mockJQuery);

      // Verify they are set
      expect(getSelectedClusterId()).toBe(42);
      expect(getClusters()).not.toBe(null);
      expect(getIsProjectScope()).toBe(true);
      expect(getJQuery()).toBe(mockJQuery);

      // Reset
      resetState();

      // Verify all are reset (jQuery falls back to window.jQuery which is undefined)
      expect(getSelectedClusterId()).toBe(null);
      expect(getClusters()).toBe(null);
      expect(getIsProjectScope()).toBe(false);
      expect(getJQuery()).toBe(undefined);
    });
  });
});

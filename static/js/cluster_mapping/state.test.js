/**
 * Tests for cluster_mapping/state.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getSelectedClusterId, setSelectedClusterId, getApiUrls, API_URLS, resetState } from './state.js';

describe('cluster_mapping/state', () => {
  // Reset state before each test
  beforeEach(() => {
    resetState();
    // Clean up any DOM elements from previous tests
    const pageData = document.getElementById('page-data');
    if (pageData) {
      pageData.remove();
    }
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

  describe('API_URLS', () => {
    it('should use fallback URLs when page-data element is missing', () => {
      // Suppress console.warn for this test
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      expect(API_URLS.getClusterData).toBe('/clustering/get-cluster-data/');
      expect(API_URLS.createMapping).toBe('/clustering/create-mapping/');
      expect(API_URLS.updateMappingConfidence).toBe('/clustering/update-mapping-confidence/');
      expect(API_URLS.deleteMapping).toBe('/clustering/delete-mapping/');

      warnSpy.mockRestore();
    });
  });

  describe('getApiUrls (backward compatibility)', () => {
    it('should return an object with all URL properties', () => {
      // Suppress console.warn for this test
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const urls = getApiUrls();

      expect(urls).toHaveProperty('getClusterData');
      expect(urls).toHaveProperty('createMapping');
      expect(urls).toHaveProperty('updateMappingConfidence');
      expect(urls).toHaveProperty('deleteMapping');

      warnSpy.mockRestore();
    });
  });

  describe('resetState', () => {
    it('should reset selectedClusterId to null', () => {
      setSelectedClusterId(42);
      expect(getSelectedClusterId()).toBe(42);

      resetState();

      expect(getSelectedClusterId()).toBe(null);
    });
  });
});

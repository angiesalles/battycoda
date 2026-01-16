/**
 * Tests for cluster_explorer/api.js
 */

import { describe, it, expect } from 'vitest';
import { API_ENDPOINTS, buildUrl } from './api.js';

describe('cluster_explorer/api', () => {
  describe('API_ENDPOINTS', () => {
    it('should have UPDATE_CLUSTER_LABEL endpoint', () => {
      expect(API_ENDPOINTS.UPDATE_CLUSTER_LABEL).toBe('/clustering/update-cluster-label/');
    });

    it('should have GET_CLUSTER_DATA endpoint', () => {
      expect(API_ENDPOINTS.GET_CLUSTER_DATA).toBe('/clustering/get-cluster-data/');
    });

    it('should have GET_CLUSTER_MEMBERS endpoint', () => {
      expect(API_ENDPOINTS.GET_CLUSTER_MEMBERS).toBe('/clustering/get-cluster-members/');
    });

    it('should have GET_SEGMENT_DATA endpoint', () => {
      expect(API_ENDPOINTS.GET_SEGMENT_DATA).toBe('/clustering/get-segment-data/');
    });
  });

  describe('buildUrl', () => {
    it('should return endpoint unchanged when no params provided', () => {
      const result = buildUrl('/api/test/');
      expect(result).toBe('/api/test/');
    });

    it('should return endpoint unchanged when params is empty object', () => {
      const result = buildUrl('/api/test/', {});
      expect(result).toBe('/api/test/');
    });

    it('should append single query parameter', () => {
      const result = buildUrl('/api/test/', { id: 123 });
      expect(result).toBe('/api/test/?id=123');
    });

    it('should append multiple query parameters', () => {
      const result = buildUrl('/api/test/', { id: 123, limit: 50 });
      expect(result).toBe('/api/test/?id=123&limit=50');
    });

    it('should URL-encode parameter values', () => {
      const result = buildUrl('/api/test/', { name: 'hello world' });
      expect(result).toBe('/api/test/?name=hello%20world');
    });

    it('should URL-encode parameter keys', () => {
      const result = buildUrl('/api/test/', { 'my key': 'value' });
      expect(result).toBe('/api/test/?my%20key=value');
    });

    it('should filter out undefined values', () => {
      const result = buildUrl('/api/test/', { id: 123, name: undefined });
      expect(result).toBe('/api/test/?id=123');
    });

    it('should filter out null values', () => {
      const result = buildUrl('/api/test/', { id: 123, name: null });
      expect(result).toBe('/api/test/?id=123');
    });

    it('should include zero values', () => {
      const result = buildUrl('/api/test/', { offset: 0 });
      expect(result).toBe('/api/test/?offset=0');
    });

    it('should include empty string values', () => {
      const result = buildUrl('/api/test/', { filter: '' });
      expect(result).toBe('/api/test/?filter=');
    });

    it('should work with API_ENDPOINTS constants', () => {
      const result = buildUrl(API_ENDPOINTS.GET_CLUSTER_DATA, { cluster_id: 42 });
      expect(result).toBe('/clustering/get-cluster-data/?cluster_id=42');
    });
  });
});

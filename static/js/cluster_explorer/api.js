/**
 * Cluster Explorer API Configuration
 *
 * Centralizes all API endpoint URLs used by the cluster explorer.
 * URLs are read from data attributes in the template for flexibility.
 */

import {
  createApiConfig,
  buildUrl as sharedBuildUrl,
} from '../clustering/shared/api-config.js';

/**
 * API endpoints for cluster explorer operations
 * Lazily initialized on first access from DOM config element
 */
export const API_ENDPOINTS = createApiConfig(
  'cluster-explorer-config',
  {
    UPDATE_CLUSTER_LABEL: 'apiUpdateClusterLabel',
    GET_CLUSTER_DATA: 'apiGetClusterData',
    GET_CLUSTER_MEMBERS: 'apiGetClusterMembers',
    GET_SEGMENT_DATA: 'apiGetSegmentData',
  },
  {
    // Fallback URLs for tests
    UPDATE_CLUSTER_LABEL: '/clustering/update-cluster-label/',
    GET_CLUSTER_DATA: '/clustering/get-cluster-data/',
    GET_CLUSTER_MEMBERS: '/clustering/get-cluster-members/',
    GET_SEGMENT_DATA: '/clustering/get-segment-data/',
  }
);

// Re-export buildUrl for backward compatibility
export const buildUrl = sharedBuildUrl;

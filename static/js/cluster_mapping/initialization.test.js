/**
 * Tests for cluster_mapping/initialization.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  initializeExistingMappings,
  addMappingToContainer,
  updateCallBadgeCount,
} from './initialization.js';

describe('cluster_mapping/initialization', () => {
  beforeEach(() => {
    delete window.jQuery;
    document.body.innerHTML = '';
  });

  describe('initializeExistingMappings', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const addMappingFn = vi.fn();
      const updateBadgeFn = vi.fn();

      initializeExistingMappings([{ cluster_id: 1 }], addMappingFn, updateBadgeFn);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot initialize existing mappings.'
      );
      expect(addMappingFn).not.toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should call addMappingToContainer for each mapping with matching cluster box', () => {
      document.body.innerHTML = `
        <div class="cluster-box" data-cluster-id="1" data-cluster-num="1">
          <h5>Test Cluster</h5>
          <span class="color-indicator" style="background-color: rgb(255, 0, 0);"></span>
        </div>
      `;

      const addMappingFn = vi.fn();
      const updateBadgeFn = vi.fn();

      // Create a more complete jQuery mock that handles element wrapping
      const mockJQuery = (selector) => {
        // Handle element wrapping (from find returning querySelector result)
        if (selector instanceof Element || selector === null || selector === undefined) {
          const el = selector;
          return {
            length: el ? 1 : 0,
            text: () => el?.textContent?.trim() || '',
            css: (prop) => el?.style?.[prop] || '',
          };
        }
        // String selector
        if (typeof selector === 'string') {
          const elements = document.querySelectorAll(selector);
          const el = elements[0];
          return {
            length: elements.length,
            data: (key) => {
              if (!el) return undefined;
              const attrName = `data-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
              const value = el.getAttribute(attrName);
              return value ? (isNaN(value) ? value : parseInt(value)) : undefined;
            },
            find: (sel) => mockJQuery(el?.querySelector(sel)),
            text: () => el?.textContent?.trim() || '',
            css: (prop) => el?.style?.[prop] || '',
          };
        }
        return { length: 0 };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      const mappings = [
        { cluster_id: 1, call_id: 10, confidence: 0.8, id: 100 },
      ];

      initializeExistingMappings(mappings, addMappingFn, updateBadgeFn);

      expect(addMappingFn).toHaveBeenCalledWith(
        1,          // cluster_id
        1,          // cluster_num
        'Test Cluster', // label
        'rgb(255, 0, 0)',  // color from inline style
        10,         // call_id
        0.8,        // confidence
        100         // mapping_id
      );
      expect(updateBadgeFn).toHaveBeenCalledWith(10);
    });

    it('should skip mappings with no matching cluster box', () => {
      document.body.innerHTML = `
        <div class="cluster-box" data-cluster-id="1"></div>
      `;

      const addMappingFn = vi.fn();
      const updateBadgeFn = vi.fn();

      const mockJQuery = (selector) => {
        const elements = document.querySelectorAll(selector);
        return {
          length: elements.length,
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      const mappings = [
        { cluster_id: 999, call_id: 10, confidence: 0.8, id: 100 }, // No matching box
      ];

      initializeExistingMappings(mappings, addMappingFn, updateBadgeFn);

      expect(addMappingFn).not.toHaveBeenCalled();
    });
  });

  describe('addMappingToContainer', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      addMappingToContainer(1, 1, 'Label', 'red', 10, 0.8, 100);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot add mapping to container.'
      );
      consoleSpy.mockRestore();
    });

    it('should return early if container is not found', () => {
      document.body.innerHTML = '';

      const mockJQuery = (selector) => {
        return { length: 0 };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      // Should not throw
      addMappingToContainer(1, 1, 'Label', 'red', 999, 0.8, 100);
    });
  });

  describe('updateCallBadgeCount', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      updateCallBadgeCount(10);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot update call badge count.'
      );
      consoleSpy.mockRestore();
    });

    it('should return early if badge is not found', () => {
      document.body.innerHTML = '';

      const mockJQuery = (selector) => {
        return { length: 0 };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      // Should not throw
      updateCallBadgeCount(999);
    });

    it('should set specific count when provided', () => {
      document.body.innerHTML = `
        <span class="cluster-count-badge" data-call-id="10">0</span>
      `;

      let badgeText = '0';
      const mockJQuery = (selector) => {
        const elements = document.querySelectorAll(selector);
        return {
          length: elements.length,
          text: (val) => {
            if (val !== undefined) {
              badgeText = val;
              if (elements[0]) elements[0].textContent = val;
            }
            return badgeText;
          },
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      updateCallBadgeCount(10, 5);

      expect(badgeText).toBe(5);
    });

    it('should count mapping items when count not provided', () => {
      document.body.innerHTML = `
        <span class="cluster-count-badge" data-call-id="10">0</span>
        <div class="mapping-container" data-call-id="10">
          <div class="mapping-item"></div>
          <div class="mapping-item"></div>
          <div class="mapping-item"></div>
        </div>
      `;

      let badgeText = '0';
      const mockJQuery = (selector) => {
        const elements = document.querySelectorAll(selector);
        return {
          length: elements.length,
          text: (val) => {
            if (val !== undefined) {
              badgeText = String(val);
              if (elements[0]) elements[0].textContent = String(val);
            }
            return badgeText;
          },
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      updateCallBadgeCount(10);

      expect(badgeText).toBe('3');
    });
  });
});

/**
 * Tests for cluster_mapping/drag_drop.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  initializeDragAndDrop,
  createMapping,
  updateMappingConfidence,
  deleteMapping,
} from './drag_drop.js';

describe('cluster_mapping/drag_drop', () => {
  beforeEach(() => {
    delete window.jQuery;
    delete window.bootstrap;
    delete window.toastr;
    document.body.innerHTML = '';
  });

  describe('initializeDragAndDrop', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const loadDetailsFn = vi.fn();
      const createMappingFn = vi.fn();

      initializeDragAndDrop(loadDetailsFn, createMappingFn);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot initialize drag and drop.'
      );
      consoleSpy.mockRestore();
    });

    it('should set draggable attribute on cluster boxes', () => {
      document.body.innerHTML = `
        <div class="cluster-box" data-cluster-id="1"></div>
        <div class="cluster-box" data-cluster-id="2"></div>
        <div class="mapping-container" data-call-id="10"></div>
      `;

      const eventHandlers = {};
      const mockJQuery = (selector) => {
        // Handle element wrapping (from $(this))
        if (selector instanceof Element) {
          const el = selector;
          return {
            attr: (name, value) => {
              if (value !== undefined) el.setAttribute(name, value);
              return el.getAttribute(name);
            },
            on: (event, handler) => {
              eventHandlers[`element:${event}`] = handler;
            },
            data: (key) => {
              const attrName = `data-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
              return el.getAttribute(attrName);
            },
            removeClass: () => {},
            addClass: () => {},
            find: () => ({ text: () => '', css: () => '' }),
          };
        }
        // String selector
        const elements = document.querySelectorAll(selector);
        return {
          length: elements.length,
          off: () => ({ off: () => ({ off: () => {} }) }),
          each: (fn) => elements.forEach((el, i) => fn.call(el, i, el)),
          attr: (name, value) => {
            elements.forEach((el) => el.setAttribute(name, value));
          },
          on: (event, handler) => {
            eventHandlers[event] = handler;
          },
          data: (key) => elements[0]?.getAttribute(`data-${key}`),
          removeClass: () => {},
          addClass: () => {},
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      // Suppress console.log for cleaner test output
      vi.spyOn(console, 'log').mockImplementation(() => {});

      initializeDragAndDrop(vi.fn(), vi.fn());

      const boxes = document.querySelectorAll('.cluster-box');
      expect(boxes[0].getAttribute('draggable')).toBe('true');
      expect(boxes[1].getAttribute('draggable')).toBe('true');
    });
  });

  describe('createMapping', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      createMapping(1, 10);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot create mapping.'
      );
      consoleSpy.mockRestore();
    });

    it('should return early if cluster box is not found', () => {
      document.body.innerHTML = '';

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      const mockJQuery = (selector) => {
        return {
          length: 0,
          data: () => undefined,
          find: () => ({ text: () => '', css: () => '' }),
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      createMapping(999, 10);

      expect(consoleSpy).toHaveBeenCalledWith('Could not find cluster box with ID 999');
      consoleSpy.mockRestore();
      logSpy.mockRestore();
    });
  });

  describe('updateMappingConfidence', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      updateMappingConfidence(100, 0.9);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot update mapping confidence.'
      );
      consoleSpy.mockRestore();
    });

    it('should return early if mappingId is not provided', () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const mockJQuery = () => ({});
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      updateMappingConfidence(null, 0.9);

      expect(warnSpy).toHaveBeenCalledWith(
        '[ClusterMapping] No mapping ID provided. Cannot update mapping confidence.'
      );
      warnSpy.mockRestore();
    });

    it('should return early if mappingId is undefined', () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const mockJQuery = () => ({});
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      updateMappingConfidence(undefined, 0.9);

      expect(warnSpy).toHaveBeenCalledWith(
        '[ClusterMapping] No mapping ID provided. Cannot update mapping confidence.'
      );
      warnSpy.mockRestore();
    });
  });

  describe('deleteMapping', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      deleteMapping(100);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot delete mapping.'
      );
      consoleSpy.mockRestore();
    });

    it('should return early if mappingId is not provided', () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const mockJQuery = () => ({});
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      deleteMapping(null);

      expect(warnSpy).toHaveBeenCalledWith(
        '[ClusterMapping] No mapping ID provided. Cannot delete mapping.'
      );
      warnSpy.mockRestore();
    });

    it('should return early if mappingId is zero', () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const mockJQuery = () => ({});
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      deleteMapping(0);

      expect(warnSpy).toHaveBeenCalledWith(
        '[ClusterMapping] No mapping ID provided. Cannot delete mapping.'
      );
      warnSpy.mockRestore();
    });
  });
});

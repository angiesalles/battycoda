/**
 * Tests for cluster_mapping/modal_handlers.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { initializeClusterPreviewModal, loadClusterDetails } from './modal_handlers.js';

describe('cluster_mapping/modal_handlers', () => {
  beforeEach(() => {
    delete window.jQuery;
    delete window.bootstrap;
    delete window.toast;
    document.body.innerHTML = '';
  });

  describe('initializeClusterPreviewModal', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const createMappingFn = vi.fn();

      initializeClusterPreviewModal(createMappingFn);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot initialize cluster preview modal.'
      );
      consoleSpy.mockRestore();
    });

    it('should set up modal show handler', () => {
      document.body.innerHTML = `
        <div id="clusterPreviewModal"></div>
        <button id="create-mapping-btn"></button>
        <select id="mapping-call-select"></select>
      `;

      const eventHandlers = {};
      const mockJQuery = (selector) => {
        return {
          off: () => ({ off: () => {} }),
          on: (event, handler) => {
            eventHandlers[`${selector}:${event}`] = handler;
          },
          empty: () => {},
          append: () => {},
          text: () => {},
          html: () => {},
          attr: () => {},
          val: () => '',
          each: () => {},
          find: () => ({
            data: () => undefined,
            text: () => '',
          }),
          closest: () => ({
            find: () => ({ text: () => '' }),
          }),
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      const createMappingFn = vi.fn();
      initializeClusterPreviewModal(createMappingFn);

      expect(eventHandlers['#clusterPreviewModal:show.bs.modal']).toBeDefined();
      expect(eventHandlers['#create-mapping-btn:click']).toBeDefined();
    });

    it('should call toast.error when create button clicked without selection', () => {
      document.body.innerHTML = `
        <div id="clusterPreviewModal"></div>
        <button id="create-mapping-btn"></button>
        <select id="mapping-call-select"></select>
      `;

      const eventHandlers = {};
      const mockJQuery = (selector) => {
        return {
          off: () => ({ off: () => {} }),
          on: (event, handler) => {
            eventHandlers[`${selector}:${event}`] = handler;
          },
          val: () => '', // Empty selection
        };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      window.toast = { error: vi.fn() };

      const createMappingFn = vi.fn();
      initializeClusterPreviewModal(createMappingFn);

      // Simulate click
      eventHandlers['#create-mapping-btn:click']();

      expect(window.toast.error).toHaveBeenCalledWith('Please select a call type');
      expect(createMappingFn).not.toHaveBeenCalled();
    });
  });

  describe('loadClusterDetails', () => {
    it('should return early if jQuery is not available', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      loadClusterDetails(1);

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ClusterMapping] jQuery is not available. Cannot load cluster details.'
      );
      consoleSpy.mockRestore();
    });

    it('should return early if cluster box is not found', () => {
      document.body.innerHTML = '';

      const mockJQuery = (_selector) => {
        return { length: 0 };
      };
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      // Should not throw
      loadClusterDetails(999);
    });

    it('should populate preview elements from cluster box data', () => {
      document.body.innerHTML = `
        <div class="cluster-box" data-cluster-id="1" data-cluster-num="42">
          <h5>Test Cluster Label</h5>
          <small>Description text</small>
          <span class="text-muted">Size: 100</span>
          <span class="text-muted">Coherence: 0.95</span>
        </div>
        <span class="cluster-preview-id"></span>
        <span class="cluster-preview-description"></span>
        <span class="cluster-preview-size"></span>
        <span class="cluster-preview-coherence"></span>
      `;

      // Suppress console.warn from API URL fallback
      vi.spyOn(console, 'warn').mockImplementation(() => {});

      const textValues = {};
      const mockJQuery = (selector) => {
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
          find: (sel) => {
            const found = el?.querySelector(sel);
            return {
              text: () => found?.textContent?.trim() || '',
              css: () => '',
            };
          },
          text: (val) => {
            if (val !== undefined) {
              textValues[selector] = val;
              if (el) el.textContent = val;
            }
            return el?.textContent || '';
          },
        };
      };
      // Mock $.getJSON to return a thenable with .fail
      mockJQuery.getJSON = vi.fn().mockReturnValue({
        fail: vi.fn(),
      });
      mockJQuery.fn = {};
      window.jQuery = mockJQuery;

      loadClusterDetails(1);

      expect(textValues['.cluster-preview-id']).toBe('Test Cluster Label');
    });
  });
});

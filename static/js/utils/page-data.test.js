/**
 * Tests for page-data.js utility module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  getPageData,
  getPageDataValue,
  getJsonData,
  hasPageData,
  getCsrfToken,
  getCsrfHeaders,
} from './page-data.js';

describe('page-data utility', () => {
  beforeEach(() => {
    // Clean up the DOM before each test
    document.body.innerHTML = '';
  });

  describe('getPageData', () => {
    it('should return an empty object when container does not exist', () => {
      const result = getPageData();
      expect(result).toEqual({});
    });

    it('should parse data attributes from container', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-recording-id="42"
             data-name="test-recording"
             hidden>
        </div>
      `;

      const result = getPageData();

      expect(result.recordingId).toBe(42);
      expect(result.name).toBe('test-recording');
    });

    it('should convert kebab-case to camelCase', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-user-profile-id="123"
             data-api-base-url="/api/v1"
             hidden>
        </div>
      `;

      const result = getPageData();

      expect(result.userProfileId).toBe(123);
      expect(result.apiBaseUrl).toBe('/api/v1');
    });

    it('should parse boolean values correctly', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-is-active="true"
             data-is-disabled="false"
             hidden>
        </div>
      `;

      const result = getPageData();

      expect(result.isActive).toBe(true);
      expect(result.isDisabled).toBe(false);
    });

    it('should parse numeric values correctly', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-count="100"
             data-score="3.14"
             data-negative="-42"
             hidden>
        </div>
      `;

      const result = getPageData();

      expect(result.count).toBe(100);
      expect(result.score).toBe(3.14);
      expect(result.negative).toBe(-42);
    });

    it('should handle null values', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-value="null"
             hidden>
        </div>
      `;

      const result = getPageData();

      expect(result.value).toBe(null);
    });

    it('should use custom container id', () => {
      document.body.innerHTML = `
        <div id="custom-data"
             data-custom-value="42"
             hidden>
        </div>
      `;

      const result = getPageData('custom-data');

      expect(result.customValue).toBe(42);
    });
  });

  describe('getPageDataValue', () => {
    it('should return default value when container does not exist', () => {
      const result = getPageDataValue('test', 'default');
      expect(result).toBe('default');
    });

    it('should return specific data attribute value', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-recording-id="42"
             data-name="test"
             hidden>
        </div>
      `;

      expect(getPageDataValue('recording-id')).toBe(42);
      expect(getPageDataValue('name')).toBe('test');
    });

    it('should return default for non-existent attribute', () => {
      document.body.innerHTML = `
        <div id="page-data" hidden></div>
      `;

      expect(getPageDataValue('missing', 'fallback')).toBe('fallback');
    });
  });

  describe('getJsonData', () => {
    it('should return null when script does not exist', () => {
      // Suppress console.warn for this test
      vi.spyOn(console, 'warn').mockImplementation(() => {});

      const result = getJsonData('non-existent');

      expect(result).toBe(null);
      expect(console.warn).toHaveBeenCalledWith(
        'JSON data script with id "non-existent" not found'
      );
    });

    it('should parse valid JSON from script tag', () => {
      document.body.innerHTML = `
        <script id="config-data" type="application/json">
          {"key": "value", "count": 42}
        </script>
      `;

      const result = getJsonData('config-data');

      expect(result).toEqual({ key: 'value', count: 42 });
    });

    it('should return null for invalid JSON', () => {
      document.body.innerHTML = `
        <script id="bad-data" type="application/json">
          {invalid json}
        </script>
      `;

      // Suppress console.error for this test
      vi.spyOn(console, 'error').mockImplementation(() => {});

      const result = getJsonData('bad-data');

      expect(result).toBe(null);
      expect(console.error).toHaveBeenCalled();
    });

    it('should parse complex nested JSON', () => {
      const complexData = {
        users: [
          { id: 1, name: 'Alice' },
          { id: 2, name: 'Bob' },
        ],
        settings: {
          theme: 'dark',
          notifications: true,
        },
      };

      document.body.innerHTML = `
        <script id="complex-data" type="application/json">
          ${JSON.stringify(complexData)}
        </script>
      `;

      const result = getJsonData('complex-data');

      expect(result).toEqual(complexData);
    });
  });

  describe('hasPageData', () => {
    it('should return false when container does not exist', () => {
      expect(hasPageData()).toBe(false);
    });

    it('should return true when container exists', () => {
      document.body.innerHTML = '<div id="page-data" hidden></div>';
      expect(hasPageData()).toBe(true);
    });

    it('should work with custom container id', () => {
      document.body.innerHTML = '<div id="my-data" hidden></div>';

      expect(hasPageData('my-data')).toBe(true);
      expect(hasPageData('other-data')).toBe(false);
    });
  });

  describe('getCsrfToken', () => {
    it('should get token from page data container', () => {
      document.body.innerHTML = `
        <div id="page-data" data-csrf-token="token-from-container" hidden></div>
      `;

      expect(getCsrfToken()).toBe('token-from-container');
    });

    it('should get token from hidden input', () => {
      document.body.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="token-from-input">
      `;

      expect(getCsrfToken()).toBe('token-from-input');
    });

    it('should get token from meta tag', () => {
      document.body.innerHTML = `
        <meta name="csrf-token" content="token-from-meta">
      `;

      expect(getCsrfToken()).toBe('token-from-meta');
    });

    it('should prefer page data container over other sources', () => {
      document.body.innerHTML = `
        <div id="page-data" data-csrf-token="token-primary" hidden></div>
        <input type="hidden" name="csrfmiddlewaretoken" value="token-fallback">
        <meta name="csrf-token" content="token-meta">
      `;

      expect(getCsrfToken()).toBe('token-primary');
    });

    it('should return null when no token found', () => {
      document.body.innerHTML = '<div></div>';
      expect(getCsrfToken()).toBe(null);
    });
  });

  describe('getCsrfHeaders', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="page-data" data-csrf-token="test-token" hidden></div>
      `;
    });

    it('should return headers with CSRF token', () => {
      const headers = getCsrfHeaders();

      expect(headers['X-CSRFToken']).toBe('test-token');
      expect(headers['Content-Type']).toBe('application/json');
    });

    it('should merge additional headers', () => {
      const headers = getCsrfHeaders({
        Authorization: 'Bearer abc123',
        'X-Custom': 'value',
      });

      expect(headers['X-CSRFToken']).toBe('test-token');
      expect(headers['Content-Type']).toBe('application/json');
      expect(headers['Authorization']).toBe('Bearer abc123');
      expect(headers['X-Custom']).toBe('value');
    });

    it('should allow overriding Content-Type', () => {
      const headers = getCsrfHeaders({
        'Content-Type': 'text/plain',
      });

      expect(headers['Content-Type']).toBe('text/plain');
    });
  });
});

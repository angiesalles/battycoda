/**
 * Tests for taskbatch/name_validator.js
 *
 * Tests the exported functions directly for proper unit testing.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { checkNameExists, debounce, initialize } from './name_validator.js';

describe('taskbatch/name_validator', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    vi.useFakeTimers();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('checkNameExists', () => {
    it('should return false when checkUrl is not provided', async () => {
      const result = await checkNameExists('Test', null, null);
      expect(result).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should call API with URL-encoded name', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: false }),
      });

      await checkNameExists('Test Batch Name', '/api/check-name/', null);

      expect(global.fetch).toHaveBeenCalledWith('/api/check-name/?name=Test%20Batch%20Name');
    });

    it('should return true and show warning when name exists', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: true }),
      });

      document.body.innerHTML = `
        <div id="warning" style="display: none;">Name exists</div>
      `;
      const warning = document.getElementById('warning');

      const result = await checkNameExists('Test', '/api/check/', warning);

      expect(result).toBe(true);
      expect(warning.style.display).toBe('block');
    });

    it('should return false and hide warning when name does not exist', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: false }),
      });

      document.body.innerHTML = `
        <div id="warning" style="display: block;">Name exists</div>
      `;
      const warning = document.getElementById('warning');

      const result = await checkNameExists('Test', '/api/check/', warning);

      expect(result).toBe(false);
      expect(warning.style.display).toBe('none');
    });

    it('should return false and hide warning on fetch error', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      document.body.innerHTML = `
        <div id="warning" style="display: block;">Name exists</div>
      `;
      const warning = document.getElementById('warning');

      const result = await checkNameExists('Test', '/api/check/', warning);

      expect(result).toBe(false);
      expect(warning.style.display).toBe('none');
    });

    it('should work without warning element', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: true }),
      });

      const result = await checkNameExists('Test', '/api/check/', null);

      expect(result).toBe(true);
    });
  });

  describe('debounce', () => {
    it('should delay function execution', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 300);

      debouncedFn('arg1');

      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(300);

      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith('arg1');
    });

    it('should cancel previous calls on rapid invocations', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 300);

      debouncedFn('first');
      vi.advanceTimersByTime(100);

      debouncedFn('second');
      vi.advanceTimersByTime(100);

      debouncedFn('third');

      // Advance to complete the last debounce
      vi.advanceTimersByTime(300);

      // Only the last call should have executed
      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith('third');
    });

    it('should preserve this context', () => {
      const obj = {
        value: 'test',
        fn: vi.fn(function () {
          return this.value;
        }),
      };

      obj.debouncedFn = debounce(obj.fn, 100);
      obj.debouncedFn();

      vi.advanceTimersByTime(100);

      expect(obj.fn).toHaveBeenCalled();
    });
  });

  describe('initialize', () => {
    it('should do nothing when elements are missing', () => {
      document.body.innerHTML = '<div>No form elements</div>';

      // Should not throw
      expect(() => initialize()).not.toThrow();
    });

    it('should set up input listener with debounce', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: false }),
      });

      document.body.innerHTML = `
        <input type="text" id="name" data-check-url="/api/check-name/">
        <div id="name-warning" style="display: none;">Name exists</div>
      `;

      initialize();

      const nameInput = document.getElementById('name');

      // Simulate typing
      nameInput.value = 'Test';
      nameInput.dispatchEvent(new Event('input'));

      // Should not call immediately (debounced)
      expect(global.fetch).not.toHaveBeenCalled();

      // Advance past debounce delay
      vi.advanceTimersByTime(300);

      // Now it should have called
      expect(global.fetch).toHaveBeenCalledWith('/api/check-name/?name=Test');
    });

    it('should hide warning for empty input', () => {
      document.body.innerHTML = `
        <input type="text" id="name" data-check-url="/api/check-name/">
        <div id="name-warning" style="display: block;">Name exists</div>
      `;

      initialize();

      const nameInput = document.getElementById('name');
      const warning = document.getElementById('name-warning');

      // Simulate clearing input
      nameInput.value = '';
      nameInput.dispatchEvent(new Event('input'));

      expect(warning.style.display).toBe('none');
    });

    it('should check initial value if present', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: false }),
      });

      document.body.innerHTML = `
        <input type="text" id="name" value="Initial Value" data-check-url="/api/check-name/">
        <div id="name-warning" style="display: none;">Name exists</div>
      `;

      initialize();

      // Should check immediately for initial value (not debounced)
      expect(global.fetch).toHaveBeenCalledWith('/api/check-name/?name=Initial%20Value');
    });

    it('should accept custom elements via options', async () => {
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ exists: true }),
      });

      document.body.innerHTML = `
        <input type="text" id="custom-input" data-check-url="/api/custom/">
        <div id="custom-warning" style="display: none;">Warning</div>
      `;

      const input = document.getElementById('custom-input');
      const warning = document.getElementById('custom-warning');

      initialize({
        nameInput: input,
        warningElement: warning,
        debounceDelay: 100,
      });

      input.value = 'Test';
      input.dispatchEvent(new Event('input'));

      vi.advanceTimersByTime(100);

      expect(global.fetch).toHaveBeenCalledWith('/api/custom/?name=Test');
    });
  });
});

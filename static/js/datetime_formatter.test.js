/**
 * Tests for datetime_formatter.js utility module
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { formatDateTimeElements } from './datetime_formatter.js';

describe('datetime_formatter', () => {
  beforeEach(() => {
    // Clean up the DOM before each test
    document.body.innerHTML = '';
  });

  describe('formatDateTimeElements', () => {
    it('should do nothing when no elements with data-utc-date exist', () => {
      document.body.innerHTML = '<div>No date elements</div>';

      // Should not throw
      expect(() => formatDateTimeElements()).not.toThrow();
    });

    it('should format element with default (full) format', () => {
      const testDate = '2024-03-15T14:30:00Z';
      document.body.innerHTML = `
        <span data-utc-date="${testDate}">placeholder</span>
      `;

      formatDateTimeElements();

      const element = document.querySelector('[data-utc-date]');
      // Should have formatted the date (not still "placeholder")
      expect(element.textContent).not.toBe('placeholder');
      // Should contain date components
      expect(element.textContent).toBeTruthy();
    });

    it('should format element with date-only format', () => {
      const testDate = '2024-03-15T14:30:00Z';
      document.body.innerHTML = `
        <span data-utc-date="${testDate}" data-date-format="date">placeholder</span>
      `;

      formatDateTimeElements();

      const element = document.querySelector('[data-utc-date]');
      // Should have been formatted
      expect(element.textContent).not.toBe('placeholder');
      // Date-only format should not include seconds
      expect(element.textContent).not.toContain(':30:00');
    });

    it('should format element with time-only format', () => {
      const testDate = '2024-03-15T14:30:45Z';
      document.body.innerHTML = `
        <span data-utc-date="${testDate}" data-date-format="time">placeholder</span>
      `;

      formatDateTimeElements();

      const element = document.querySelector('[data-utc-date]');
      // Should have been formatted
      expect(element.textContent).not.toBe('placeholder');
      // Time format should contain time components
      expect(element.textContent).toBeTruthy();
    });

    it('should format element with datetime format', () => {
      const testDate = '2024-03-15T14:30:45Z';
      document.body.innerHTML = `
        <span data-utc-date="${testDate}" data-date-format="datetime">placeholder</span>
      `;

      formatDateTimeElements();

      const element = document.querySelector('[data-utc-date]');
      // Should have been formatted
      expect(element.textContent).not.toBe('placeholder');
    });

    it('should format multiple elements', () => {
      document.body.innerHTML = `
        <span id="date1" data-utc-date="2024-03-15T14:30:00Z">placeholder1</span>
        <span id="date2" data-utc-date="2024-03-16T10:00:00Z">placeholder2</span>
        <span id="date3" data-utc-date="2024-03-17T08:45:00Z" data-date-format="date">placeholder3</span>
      `;

      formatDateTimeElements();

      expect(document.getElementById('date1').textContent).not.toBe('placeholder1');
      expect(document.getElementById('date2').textContent).not.toBe('placeholder2');
      expect(document.getElementById('date3').textContent).not.toBe('placeholder3');
    });

    it('should work with a specific container', () => {
      document.body.innerHTML = `
        <div id="container1">
          <span id="inside" data-utc-date="2024-03-15T14:30:00Z">inside</span>
        </div>
        <div id="container2">
          <span id="outside" data-utc-date="2024-03-16T14:30:00Z">outside</span>
        </div>
      `;

      const container = document.getElementById('container1');
      formatDateTimeElements(container);

      // Element inside the container should be formatted
      expect(document.getElementById('inside').textContent).not.toBe('inside');
      // Element outside the container should NOT be formatted
      expect(document.getElementById('outside').textContent).toBe('outside');
    });

    it('should skip elements with empty data-utc-date attribute', () => {
      document.body.innerHTML = `
        <span id="empty" data-utc-date="">empty</span>
        <span id="valid" data-utc-date="2024-03-15T14:30:00Z">valid</span>
      `;

      formatDateTimeElements();

      // Empty attribute should be skipped
      expect(document.getElementById('empty').textContent).toBe('empty');
      // Valid attribute should be formatted
      expect(document.getElementById('valid').textContent).not.toBe('valid');
    });

    it('should handle invalid date strings gracefully', () => {
      document.body.innerHTML = `
        <span data-utc-date="invalid-date">placeholder</span>
      `;

      // Should not throw, but may produce "Invalid Date"
      expect(() => formatDateTimeElements()).not.toThrow();

      const element = document.querySelector('[data-utc-date]');
      // The result will be "Invalid Date" due to JavaScript Date behavior
      expect(element.textContent).toBeTruthy();
    });
  });
});

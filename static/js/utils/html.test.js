/**
 * Tests for HTML utility functions
 */

import { describe, it, expect } from 'vitest';
import { escapeHtml } from './html.js';

describe('escapeHtml', () => {
  it('should escape ampersand', () => {
    expect(escapeHtml('foo & bar')).toBe('foo &amp; bar');
  });

  it('should escape less than', () => {
    expect(escapeHtml('1 < 2')).toBe('1 &lt; 2');
  });

  it('should escape greater than', () => {
    expect(escapeHtml('2 > 1')).toBe('2 &gt; 1');
  });

  it('should escape double quotes', () => {
    expect(escapeHtml('say "hello"')).toBe('say &quot;hello&quot;');
  });

  it('should escape single quotes', () => {
    expect(escapeHtml("it's fine")).toBe('it&#39;s fine');
  });

  it('should escape multiple special characters', () => {
    expect(escapeHtml('<script>alert("XSS")</script>')).toBe(
      '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;',
    );
  });

  it('should return empty string for null', () => {
    expect(escapeHtml(null)).toBe('');
  });

  it('should return empty string for undefined', () => {
    expect(escapeHtml(undefined)).toBe('');
  });

  it('should convert numbers to strings', () => {
    expect(escapeHtml(42)).toBe('42');
  });

  it('should handle empty string', () => {
    expect(escapeHtml('')).toBe('');
  });

  it('should not modify strings without special characters', () => {
    expect(escapeHtml('normal text 123')).toBe('normal text 123');
  });

  it('should handle realistic XSS attack payloads', () => {
    // Filename-based XSS attack
    expect(escapeHtml('<img src=x onerror=alert(1)>.wav')).toBe(
      '&lt;img src=x onerror=alert(1)&gt;.wav',
    );

    // Event handler injection
    expect(escapeHtml('file" onmouseover="alert(1)')).toBe(
      'file&quot; onmouseover=&quot;alert(1)',
    );
  });
});

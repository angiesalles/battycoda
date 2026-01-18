/**
 * Tests for HTML utility functions
 */

import { describe, it, expect, vi } from 'vitest';
import { escapeHtml, validateUrl } from './html.js';

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
      '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'
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
      '&lt;img src=x onerror=alert(1)&gt;.wav'
    );

    // Event handler injection
    expect(escapeHtml('file" onmouseover="alert(1)')).toBe('file&quot; onmouseover=&quot;alert(1)');
  });
});

describe('validateUrl', () => {
  it('should return empty string for null', () => {
    expect(validateUrl(null)).toBe('');
  });

  it('should return empty string for undefined', () => {
    expect(validateUrl(undefined)).toBe('');
  });

  it('should return empty string for non-string types', () => {
    expect(validateUrl(123)).toBe('');
    expect(validateUrl({})).toBe('');
    expect(validateUrl([])).toBe('');
  });

  it('should return empty string for empty string', () => {
    expect(validateUrl('')).toBe('');
    expect(validateUrl('   ')).toBe('');
  });

  it('should allow relative URLs starting with /', () => {
    expect(validateUrl('/api/data')).toBe('/api/data');
    expect(validateUrl('/media/images/photo.jpg')).toBe('/media/images/photo.jpg');
  });

  it('should allow HTTPS URLs', () => {
    expect(validateUrl('https://example.com')).toBe('https://example.com');
    expect(validateUrl('https://example.com/path?query=1')).toBe(
      'https://example.com/path?query=1'
    );
  });

  it('should allow HTTP localhost URLs for development', () => {
    expect(validateUrl('http://localhost:8000/api')).toBe('http://localhost:8000/api');
    expect(validateUrl('http://127.0.0.1:8000/api')).toBe('http://127.0.0.1:8000/api');
  });

  it('should reject javascript: URLs', () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(validateUrl('javascript:alert(1)')).toBe('');
    expect(consoleWarn).toHaveBeenCalled();
    consoleWarn.mockRestore();
  });

  it('should reject data: URLs', () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(validateUrl('data:text/html,<script>alert(1)</script>')).toBe('');
    expect(consoleWarn).toHaveBeenCalled();
    consoleWarn.mockRestore();
  });

  it('should reject non-localhost HTTP URLs', () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(validateUrl('http://evil.com')).toBe('');
    expect(consoleWarn).toHaveBeenCalled();
    consoleWarn.mockRestore();
  });

  it('should reject vbscript: URLs', () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(validateUrl('vbscript:msgbox("XSS")')).toBe('');
    expect(consoleWarn).toHaveBeenCalled();
    consoleWarn.mockRestore();
  });

  it('should trim whitespace from URLs', () => {
    expect(validateUrl('  /api/data  ')).toBe('/api/data');
    expect(validateUrl('  https://example.com  ')).toBe('https://example.com');
  });
});

/**
 * Tests for theme-switcher.js utility module
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { applyTheme, saveThemeToLocalStorage } from './theme-switcher.js';

describe('theme-switcher', () => {
  beforeEach(() => {
    // Clean up the DOM before each test
    document.body.innerHTML = '';
    document.head.innerHTML = '';

    // Reset window.__VITE_THEME_URLS__
    delete window.__VITE_THEME_URLS__;
  });

  describe('applyTheme', () => {
    it('should do nothing when main-body element does not exist', () => {
      document.body.innerHTML = '<div>No main-body</div>';

      // Should not throw
      expect(() => applyTheme('dark')).not.toThrow();
    });

    it('should add theme class to main-body element', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('ocean');

      const mainBody = document.getElementById('main-body');
      expect(mainBody.classList.contains('theme-ocean')).toBe(true);
    });

    it('should remove existing theme classes when applying new theme', () => {
      document.body.innerHTML = '<div id="main-body" class="theme-old-theme some-other-class"></div>';

      applyTheme('new-theme');

      const mainBody = document.getElementById('main-body');
      expect(mainBody.classList.contains('theme-old-theme')).toBe(false);
      expect(mainBody.classList.contains('theme-new-theme')).toBe(true);
      expect(mainBody.classList.contains('some-other-class')).toBe(true);
    });

    it('should create CSS link element for non-default theme', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('blue-sky');

      const themeLink = document.getElementById('theme-css-blue-sky');
      expect(themeLink).not.toBeNull();
      expect(themeLink.tagName).toBe('LINK');
      expect(themeLink.rel).toBe('stylesheet');
      expect(themeLink.href).toContain('/static/css/themes/blue-sky.css');
    });

    it('should not duplicate CSS link when applying same theme twice', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('ocean');
      applyTheme('ocean');

      const themeLinks = document.querySelectorAll('#theme-css-ocean');
      expect(themeLinks.length).toBe(1);
    });

    it('should remove all theme CSS links when applying default theme', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      // Apply a non-default theme first
      applyTheme('ocean');
      expect(document.getElementById('theme-css-ocean')).not.toBeNull();

      // Apply another theme
      applyTheme('blue-sky');
      expect(document.getElementById('theme-css-blue-sky')).not.toBeNull();

      // Apply default theme
      applyTheme('default');

      // All theme CSS links should be removed
      const themeLinks = document.querySelectorAll('link[id^="theme-css-"]');
      expect(themeLinks.length).toBe(0);
    });

    it('should use Vite theme URL when available', () => {
      document.body.innerHTML = '<div id="main-body"></div>';
      window.__VITE_THEME_URLS__ = {
        ocean: '/static/dist/assets/theme-ocean-abc123.css',
      };

      applyTheme('ocean');

      const themeLink = document.getElementById('theme-css-ocean');
      expect(themeLink.href).toContain('/static/dist/assets/theme-ocean-abc123.css');
    });

    it('should fall back to static URL when Vite URL not available', () => {
      document.body.innerHTML = '<div id="main-body"></div>';
      window.__VITE_THEME_URLS__ = {
        'some-other-theme': '/static/dist/assets/theme-other.css',
      };

      applyTheme('ocean');

      const themeLink = document.getElementById('theme-css-ocean');
      expect(themeLink.href).toContain('/static/css/themes/ocean.css');
    });

    it('should handle multiple theme classes in body', () => {
      document.body.innerHTML =
        '<div id="main-body" class="theme-one theme-two theme-three other-class"></div>';

      applyTheme('new');

      const mainBody = document.getElementById('main-body');
      expect(mainBody.className).toContain('theme-new');
      expect(mainBody.className).not.toContain('theme-one');
      expect(mainBody.className).not.toContain('theme-two');
      expect(mainBody.className).not.toContain('theme-three');
      expect(mainBody.className).toContain('other-class');
    });

    it('should not create CSS link for default theme', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('default');

      const themeLink = document.getElementById('theme-css-default');
      expect(themeLink).toBeNull();
    });
  });

  describe('saveThemeToLocalStorage', () => {
    const LOCAL_STORAGE_KEY = 'battycoda_theme';

    beforeEach(() => {
      vi.clearAllMocks();
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it('should call localStorage.setItem with correct key and value', () => {
      saveThemeToLocalStorage('ocean');

      expect(localStorage.setItem).toHaveBeenCalledWith(LOCAL_STORAGE_KEY, 'ocean');
    });

    it('should call localStorage.setItem when saving different themes', () => {
      saveThemeToLocalStorage('blue-sky');

      expect(localStorage.setItem).toHaveBeenCalledWith(LOCAL_STORAGE_KEY, 'blue-sky');
    });

    it('should handle localStorage errors gracefully', () => {
      // Mock localStorage.setItem to throw (e.g., quota exceeded or private mode)
      localStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      // Should not throw even when localStorage fails
      expect(() => saveThemeToLocalStorage('ocean')).not.toThrow();
    });

    it('should handle localStorage being unavailable', () => {
      // Mock localStorage.setItem to throw SecurityError (common in some iframe scenarios)
      const securityError = new Error('Access denied');
      securityError.name = 'SecurityError';
      localStorage.setItem.mockImplementation(() => {
        throw securityError;
      });

      // Should not throw
      expect(() => saveThemeToLocalStorage('ocean')).not.toThrow();
    });
  });
});

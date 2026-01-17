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

      applyTheme('dark');

      const mainBody = document.getElementById('main-body');
      expect(mainBody.classList.contains('theme-dark')).toBe(true);
    });

    it('should remove existing theme classes when applying new theme', () => {
      document.body.innerHTML = '<div id="main-body" class="theme-light some-other-class"></div>';

      applyTheme('dark');

      const mainBody = document.getElementById('main-body');
      expect(mainBody.classList.contains('theme-light')).toBe(false);
      expect(mainBody.classList.contains('theme-dark')).toBe(true);
      expect(mainBody.classList.contains('some-other-class')).toBe(true);
    });

    it('should create CSS link element for theme', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('dark');

      const themeLink = document.getElementById('theme-css-dark');
      expect(themeLink).not.toBeNull();
      expect(themeLink.tagName).toBe('LINK');
      expect(themeLink.rel).toBe('stylesheet');
      expect(themeLink.href).toContain('/static/css/themes/dark.css');
    });

    it('should replace old theme CSS link when switching themes', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('dark');
      expect(document.getElementById('theme-css-dark')).not.toBeNull();

      applyTheme('light');

      // Old theme CSS should be removed
      expect(document.getElementById('theme-css-dark')).toBeNull();
      // New theme CSS should be present
      expect(document.getElementById('theme-css-light')).not.toBeNull();
    });

    it('should only have one theme CSS link at a time', () => {
      document.body.innerHTML = '<div id="main-body"></div>';

      applyTheme('dark');
      applyTheme('light');
      applyTheme('dark');

      const themeLinks = document.querySelectorAll('link[id^="theme-css-"]');
      expect(themeLinks.length).toBe(1);
      expect(themeLinks[0].id).toBe('theme-css-dark');
    });

    it('should use Vite theme URL when available', () => {
      document.body.innerHTML = '<div id="main-body"></div>';
      window.__VITE_THEME_URLS__ = {
        dark: '/static/dist/assets/theme-dark-abc123.css',
      };

      applyTheme('dark');

      const themeLink = document.getElementById('theme-css-dark');
      expect(themeLink.href).toContain('/static/dist/assets/theme-dark-abc123.css');
    });

    it('should fall back to static URL when Vite URL not available', () => {
      document.body.innerHTML = '<div id="main-body"></div>';
      window.__VITE_THEME_URLS__ = {
        light: '/static/dist/assets/theme-light.css',
      };

      applyTheme('dark');

      const themeLink = document.getElementById('theme-css-dark');
      expect(themeLink.href).toContain('/static/css/themes/dark.css');
    });

    it('should handle multiple theme classes in body', () => {
      document.body.innerHTML =
        '<div id="main-body" class="theme-one theme-two theme-three other-class"></div>';

      applyTheme('dark');

      const mainBody = document.getElementById('main-body');
      expect(mainBody.className).toContain('theme-dark');
      expect(mainBody.className).not.toContain('theme-one');
      expect(mainBody.className).not.toContain('theme-two');
      expect(mainBody.className).not.toContain('theme-three');
      expect(mainBody.className).toContain('other-class');
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
      saveThemeToLocalStorage('dark');

      expect(localStorage.setItem).toHaveBeenCalledWith(LOCAL_STORAGE_KEY, 'dark');
    });

    it('should call localStorage.setItem when saving different themes', () => {
      saveThemeToLocalStorage('light');

      expect(localStorage.setItem).toHaveBeenCalledWith(LOCAL_STORAGE_KEY, 'light');
    });

    it('should handle localStorage errors gracefully', () => {
      // Mock localStorage.setItem to throw (e.g., quota exceeded or private mode)
      localStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      // Should not throw even when localStorage fails
      expect(() => saveThemeToLocalStorage('dark')).not.toThrow();
    });

    it('should handle localStorage being unavailable', () => {
      // Mock localStorage.setItem to throw SecurityError (common in some iframe scenarios)
      const securityError = new Error('Access denied');
      securityError.name = 'SecurityError';
      localStorage.setItem.mockImplementation(() => {
        throw securityError;
      });

      // Should not throw
      expect(() => saveThemeToLocalStorage('dark')).not.toThrow();
    });
  });
});

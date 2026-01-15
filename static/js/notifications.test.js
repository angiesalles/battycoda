/**
 * Tests for notifications.js utility module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { formatTimeAgo, loadNavbarNotifications } from './notifications.js';

describe('notifications', () => {
  beforeEach(() => {
    // Clean up the DOM before each test
    document.body.innerHTML = '';
    vi.clearAllMocks();
  });

  describe('formatTimeAgo', () => {
    it('should return "Just now" for current time', () => {
      const now = new Date();
      expect(formatTimeAgo(now)).toBe('Just now');
    });

    it('should return "Just now" for times less than 60 seconds ago', () => {
      const thirtySecondsAgo = new Date(Date.now() - 30 * 1000);
      expect(formatTimeAgo(thirtySecondsAgo)).toBe('Just now');
    });

    it('should return minutes ago for times less than an hour', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      expect(formatTimeAgo(fiveMinutesAgo)).toBe('5 min ago');
    });

    it('should return "1 min ago" for one minute', () => {
      const oneMinuteAgo = new Date(Date.now() - 60 * 1000);
      expect(formatTimeAgo(oneMinuteAgo)).toBe('1 min ago');
    });

    it('should return singular "hour" for 1 hour ago', () => {
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
      expect(formatTimeAgo(oneHourAgo)).toBe('1 hour ago');
    });

    it('should return plural "hours" for multiple hours', () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000);
      expect(formatTimeAgo(threeHoursAgo)).toBe('3 hours ago');
    });

    it('should return singular "day" for 1 day ago', () => {
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      expect(formatTimeAgo(oneDayAgo)).toBe('1 day ago');
    });

    it('should return plural "days" for multiple days', () => {
      const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000);
      expect(formatTimeAgo(threeDaysAgo)).toBe('3 days ago');
    });

    it('should return formatted date for times more than a week ago', () => {
      const twoWeeksAgo = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000);
      const result = formatTimeAgo(twoWeeksAgo);

      // Should be a formatted date string, not a relative time
      expect(result).not.toContain('ago');
      expect(result).not.toBe('Just now');
      // Should be in locale date format (varies by locale)
      expect(result).toBeTruthy();
    });

    it('should handle edge case at exactly 60 seconds', () => {
      const sixtySecondsAgo = new Date(Date.now() - 60 * 1000);
      expect(formatTimeAgo(sixtySecondsAgo)).toBe('1 min ago');
    });

    it('should handle edge case at exactly 60 minutes', () => {
      const sixtyMinutesAgo = new Date(Date.now() - 60 * 60 * 1000);
      expect(formatTimeAgo(sixtyMinutesAgo)).toBe('1 hour ago');
    });

    it('should handle edge case at exactly 24 hours', () => {
      const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      expect(formatTimeAgo(twentyFourHoursAgo)).toBe('1 day ago');
    });

    it('should handle edge case at exactly 7 days', () => {
      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      const result = formatTimeAgo(sevenDaysAgo);

      // At exactly 7 days, it should return a formatted date
      expect(result).not.toContain('days ago');
    });
  });

  describe('loadNavbarNotifications', () => {
    it('should return early if navbarNotificationsUrl is not available', () => {
      // Set up page-data without the URL
      document.body.innerHTML = '<div id="page-data" hidden></div>';

      // Should not throw and should not make any AJAX calls
      expect(() => loadNavbarNotifications()).not.toThrow();
    });

    it('should make AJAX call when URL is available', () => {
      document.body.innerHTML = `
        <div id="page-data"
             data-navbar-notifications-url="/api/notifications/"
             data-mark-notification-read-url="/api/notifications/0/read/"
             hidden>
        </div>
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      // Mock jQuery ajax
      const mockAjax = vi.fn();
      global.$.ajax = mockAjax;

      loadNavbarNotifications();

      expect(mockAjax).toHaveBeenCalledWith(
        expect.objectContaining({
          url: '/api/notifications/',
          type: 'GET',
          dataType: 'json',
        })
      );
    });
  });
});

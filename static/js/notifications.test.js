/**
 * Tests for notifications.js utility module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { formatTimeAgo, loadNavbarNotifications, initialize } from './notifications.js';

// Mock the page-data module
vi.mock('./utils/page-data.js', () => ({
  getPageData: vi.fn(() => ({})),
  fetchWithCsrf: vi.fn(),
}));

import { getPageData, fetchWithCsrf } from './utils/page-data.js';

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
    it('should return early if navbarNotificationsUrl is not available', async () => {
      getPageData.mockReturnValue({});

      await loadNavbarNotifications();

      expect(fetchWithCsrf).not.toHaveBeenCalled();
    });

    it('should make fetch call when URL is available', async () => {
      // Set up page data
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      // Set up DOM
      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      // Mock successful fetch response
      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 0,
            notifications: [],
          }),
      });

      await loadNavbarNotifications();

      expect(fetchWithCsrf).toHaveBeenCalledWith('/api/notifications/');
    });

    it('should update indicator when there are unread notifications', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 5,
            notifications: [],
          }),
      });

      await loadNavbarNotifications();

      const indicator = document.getElementById('notificationIndicator');
      expect(indicator.classList.contains('indicator-new')).toBe(true);
      expect(indicator.textContent).toBe('5');
    });

    it('should hide indicator when there are no unread notifications', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator" class="indicator-new"></span>
        <ul id="notificationsList"></ul>
      `;

      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 0,
            notifications: [],
          }),
      });

      await loadNavbarNotifications();

      const indicator = document.getElementById('notificationIndicator');
      expect(indicator.classList.contains('indicator-new')).toBe(false);
      expect(indicator.style.display).toBe('none');
    });

    it('should render notifications list', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      const testDate = new Date().toISOString();
      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 2,
            notifications: [
              {
                id: 1,
                title: 'Test notification',
                icon: 's7-bell',
                link: '/some/link/',
                created_at: testDate,
              },
              {
                id: 2,
                title: 'Another notification',
                icon: 's7-info',
                link: null,
                created_at: testDate,
              },
            ],
          }),
      });

      await loadNavbarNotifications();

      const notificationsList = document.getElementById('notificationsList');
      expect(notificationsList.children.length).toBe(2);
      expect(notificationsList.querySelector('#notification-1')).toBeTruthy();
      expect(notificationsList.querySelector('#notification-2')).toBeTruthy();
    });

    it('should show empty state when no notifications', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 0,
            notifications: [],
          }),
      });

      await loadNavbarNotifications();

      const notificationsList = document.getElementById('notificationsList');
      expect(notificationsList.textContent).toContain('No notifications');
    });

    it('should show error state on fetch failure', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      fetchWithCsrf.mockRejectedValue(new Error('Network error'));

      await loadNavbarNotifications();

      const notificationsList = document.getElementById('notificationsList');
      expect(notificationsList.textContent).toContain('Failed to load notifications');
    });

    it('should handle notification with link', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 1,
            notifications: [
              {
                id: 42,
                title: 'Click me',
                icon: 's7-bell',
                link: '/task/123/',
                created_at: new Date().toISOString(),
              },
            ],
          }),
      });

      await loadNavbarNotifications();

      const link = document.querySelector('#notification-42 a');
      expect(link.href).toContain('/api/notifications/42/read/');
    });

    it('should handle notification without link', async () => {
      getPageData.mockReturnValue({
        navbarNotificationsUrl: '/api/notifications/',
        markNotificationReadUrl: '/api/notifications/0/read/',
      });

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      fetchWithCsrf.mockResolvedValue({
        json: () =>
          Promise.resolve({
            success: true,
            unread_count: 1,
            notifications: [
              {
                id: 42,
                title: 'No link',
                icon: 's7-bell',
                link: null,
                created_at: new Date().toISOString(),
              },
            ],
          }),
      });

      await loadNavbarNotifications();

      const link = document.querySelector('#notification-42 a');
      expect(link.getAttribute('href')).toBe('#');
    });
  });

  describe('initialize', () => {
    it('should set up click handler on dropdown', () => {
      getPageData.mockReturnValue({});

      document.body.innerHTML = `
        <div id="notificationsDropdown"></div>
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      const dropdown = document.getElementById('notificationsDropdown');
      const addEventListenerSpy = vi.spyOn(dropdown, 'addEventListener');

      initialize();

      expect(addEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function));
    });

    it('should handle missing dropdown gracefully', () => {
      getPageData.mockReturnValue({});

      document.body.innerHTML = `
        <span id="notificationIndicator"></span>
        <ul id="notificationsList"></ul>
      `;

      // Should not throw
      expect(() => initialize()).not.toThrow();
    });
  });
});

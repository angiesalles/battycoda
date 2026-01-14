/**
 * API mock helpers for testing
 */

import { vi } from 'vitest';

/**
 * Mock a successful API response
 */
export function mockApiSuccess(data) {
  global.fetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  });
}

/**
 * Mock an API error response
 */
export function mockApiError(status = 500, message = 'Server error') {
  global.fetch.mockResolvedValueOnce({
    ok: false,
    status,
    statusText: message,
    json: () => Promise.resolve({ error: message }),
    text: () => Promise.resolve(JSON.stringify({ error: message })),
  });
}

/**
 * Mock a network failure
 */
export function mockNetworkError(message = 'Network error') {
  global.fetch.mockRejectedValueOnce(new Error(message));
}

/**
 * Get all fetch call arguments
 */
export function getFetchCalls() {
  return global.fetch.mock.calls;
}

/**
 * Assert fetch was called with specific URL
 */
export function expectFetchCalledWith(url, options = {}) {
  expect(global.fetch).toHaveBeenCalledWith(
    expect.stringContaining(url),
    expect.objectContaining(options)
  );
}

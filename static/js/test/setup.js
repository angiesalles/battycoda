/**
 * Vitest global test setup
 *
 * This file runs before all tests and sets up:
 * - Browser API mocks
 * - jQuery mock (for legacy code)
 * - Common test utilities
 */

import { vi, beforeEach, afterEach } from 'vitest';

// ============================================================================
// Browser API Mocks
// ============================================================================

// Mock fetch for API tests
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  })
);

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock;

// ============================================================================
// jQuery Mock (for legacy code compatibility)
// ============================================================================

const jQueryMock = vi.fn((selector) => ({
  // Basic selection/traversal
  find: vi.fn(() => jQueryMock(selector)),
  closest: vi.fn(() => jQueryMock(selector)),
  parent: vi.fn(() => jQueryMock(selector)),
  children: vi.fn(() => jQueryMock(selector)),
  siblings: vi.fn(() => jQueryMock(selector)),
  first: vi.fn(() => jQueryMock(selector)),
  last: vi.fn(() => jQueryMock(selector)),
  eq: vi.fn(() => jQueryMock(selector)),

  // DOM manipulation
  html: vi.fn(),
  text: vi.fn(),
  val: vi.fn(),
  attr: vi.fn(),
  data: vi.fn(),
  prop: vi.fn(),
  addClass: vi.fn(() => jQueryMock(selector)),
  removeClass: vi.fn(() => jQueryMock(selector)),
  toggleClass: vi.fn(() => jQueryMock(selector)),
  hasClass: vi.fn(() => false),
  css: vi.fn(() => jQueryMock(selector)),
  show: vi.fn(() => jQueryMock(selector)),
  hide: vi.fn(() => jQueryMock(selector)),
  toggle: vi.fn(() => jQueryMock(selector)),
  append: vi.fn(() => jQueryMock(selector)),
  prepend: vi.fn(() => jQueryMock(selector)),
  remove: vi.fn(() => jQueryMock(selector)),
  empty: vi.fn(() => jQueryMock(selector)),

  // Events
  on: vi.fn(() => jQueryMock(selector)),
  off: vi.fn(() => jQueryMock(selector)),
  trigger: vi.fn(() => jQueryMock(selector)),
  click: vi.fn(() => jQueryMock(selector)),
  submit: vi.fn(() => jQueryMock(selector)),
  ready: vi.fn((cb) => {
    if (cb) cb();
    return jQueryMock(selector);
  }),

  // AJAX
  ajax: vi.fn(() => Promise.resolve({})),

  // Utilities
  each: vi.fn((cb) => {
    if (cb) cb.call({}, 0, {});
    return jQueryMock(selector);
  }),
  length: 0,
  get: vi.fn(() => []),
  toArray: vi.fn(() => []),
}));

// Static jQuery methods
jQueryMock.ajax = vi.fn(() => Promise.resolve({}));
jQueryMock.get = vi.fn(() => Promise.resolve({}));
jQueryMock.post = vi.fn(() => Promise.resolve({}));
jQueryMock.getJSON = vi.fn(() => Promise.resolve({}));
jQueryMock.extend = vi.fn((target, ...sources) => Object.assign(target || {}, ...sources));
jQueryMock.each = vi.fn();
jQueryMock.fn = {};

global.$ = jQueryMock;
global.jQuery = jQueryMock;

// ============================================================================
// Test Lifecycle Hooks
// ============================================================================

beforeEach(() => {
  // Reset all mocks before each test
  vi.clearAllMocks();

  // Reset fetch mock to default behavior
  global.fetch.mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  });
});

afterEach(() => {
  // Clean up after each test
  vi.restoreAllMocks();
});

// ============================================================================
// Test Utilities
// ============================================================================

/**
 * Helper to create a mock Response object for fetch
 */
export function mockFetchResponse(data, options = {}) {
  const { ok = true, status = 200, statusText = 'OK' } = options;

  return Promise.resolve({
    ok,
    status,
    statusText,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
  });
}

/**
 * Helper to create a mock DOM element
 */
export function createMockElement(tag = 'div', attributes = {}) {
  const element = document.createElement(tag);
  Object.entries(attributes).forEach(([key, value]) => {
    if (key === 'dataset') {
      Object.entries(value).forEach(([dataKey, dataValue]) => {
        element.dataset[dataKey] = dataValue;
      });
    } else if (key === 'style' && typeof value === 'object') {
      Object.assign(element.style, value);
    } else {
      element.setAttribute(key, value);
    }
  });
  return element;
}

/**
 * Helper to wait for async operations
 */
export function flushPromises() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

/**
 * Tests for file upload handler
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { createUploadHandler, hasRequiredFiles } from './upload-handler.js';

describe('hasRequiredFiles', () => {
  /**
   * Helper to create a mock file input with files
   */
  function createMockFileInput(fileCount) {
    return { files: { length: fileCount } };
  }

  describe('single file upload', () => {
    it('should return true when WAV file is selected', () => {
      const inputs = {
        wavFileInput: createMockFileInput(1),
        pickleFileInput: createMockFileInput(0),
      };

      expect(hasRequiredFiles(inputs, false)).toBe(true);
    });

    it('should return true when both WAV and pickle files selected', () => {
      const inputs = {
        wavFileInput: createMockFileInput(1),
        pickleFileInput: createMockFileInput(1),
      };

      expect(hasRequiredFiles(inputs, false)).toBe(true);
    });

    it('should return false when no WAV file selected', () => {
      const inputs = {
        wavFileInput: createMockFileInput(0),
        pickleFileInput: createMockFileInput(1),
      };

      expect(hasRequiredFiles(inputs, false)).toBe(false);
    });

    it('should return false when WAV input is null', () => {
      const inputs = {
        wavFileInput: null,
        pickleFileInput: createMockFileInput(1),
      };

      expect(hasRequiredFiles(inputs, false)).toBe(false);
    });
  });

  describe('batch upload', () => {
    it('should return true when WAV files are selected', () => {
      const inputs = {
        wavFilesInput: createMockFileInput(3),
        pickleFilesInput: createMockFileInput(0),
      };

      expect(hasRequiredFiles(inputs, true)).toBe(true);
    });

    it('should return false when no WAV files selected in batch', () => {
      const inputs = {
        wavFilesInput: createMockFileInput(0),
        pickleFilesInput: createMockFileInput(2),
      };

      expect(hasRequiredFiles(inputs, true)).toBe(false);
    });

    it('should return false when WAV files input is null', () => {
      const inputs = {
        wavFilesInput: null,
        pickleFilesInput: createMockFileInput(1),
      };

      // Function uses Boolean() wrapper to ensure false is returned (not null)
      expect(hasRequiredFiles(inputs, true)).toBe(false);
    });
  });

  describe('pickle-only form', () => {
    it('should return true when pickle file is selected', () => {
      const inputs = {
        formType: 'pickle_only',
        pickleFileInput: createMockFileInput(1),
      };

      expect(hasRequiredFiles(inputs, false)).toBe(true);
    });

    it('should return false when no pickle file selected', () => {
      const inputs = {
        formType: 'pickle_only',
        pickleFileInput: createMockFileInput(0),
      };

      expect(hasRequiredFiles(inputs, false)).toBe(false);
    });

    it('should return false when pickle input is null', () => {
      const inputs = {
        formType: 'pickle_only',
        pickleFileInput: null,
      };

      // Function uses Boolean() wrapper to ensure false is returned (not null)
      expect(hasRequiredFiles(inputs, false)).toBe(false);
    });
  });
});

describe('createUploadHandler', () => {
  let mockXhr;
  let form;
  let progressBar;
  let statusText;
  let originalXHR;

  beforeEach(() => {
    // Save original XMLHttpRequest
    originalXHR = global.XMLHttpRequest;

    // Create mock XHR
    mockXhr = {
      open: vi.fn(),
      send: vi.fn(),
      abort: vi.fn(),
      readyState: 0,
      status: 200,
      statusText: 'OK',
      responseText: '',
      responseURL: '',
      upload: {
        addEventListener: vi.fn(),
      },
      addEventListener: vi.fn(),
    };

    // Mock XMLHttpRequest constructor using a function that returns mockXhr
    function MockXMLHttpRequest() {
      return mockXhr;
    }
    global.XMLHttpRequest = MockXMLHttpRequest;

    // Create DOM elements
    form = document.createElement('form');
    form.action = '/api/upload/';

    progressBar = document.createElement('div');
    progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');

    statusText = document.createElement('div');

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { href: '/upload/', assign: vi.fn() },
      writable: true,
    });
  });

  afterEach(() => {
    // Restore original XMLHttpRequest
    global.XMLHttpRequest = originalXHR;
    vi.restoreAllMocks();
  });

  it('should create handler with start and abort methods', () => {
    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    expect(handler).toHaveProperty('start');
    expect(handler).toHaveProperty('abort');
    expect(typeof handler.start).toBe('function');
    expect(typeof handler.abort).toBe('function');
  });

  it('should open POST request to form action on start', () => {
    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    // In jsdom, form.action gets resolved to full URL (e.g., http://localhost:3000/api/upload/)
    expect(mockXhr.open).toHaveBeenCalledWith(
      'POST',
      expect.stringContaining('/api/upload/'),
      true
    );
    expect(mockXhr.send).toHaveBeenCalled();
  });

  it('should use window.location.href when form has no action', () => {
    form.action = '';

    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    // When form.action is empty, it should use the current location
    expect(mockXhr.open).toHaveBeenCalledWith('POST', expect.any(String), true);
  });

  it('should reset progress on start', () => {
    progressBar.style.width = '50%';
    progressBar.textContent = '50%';
    progressBar.classList.add('bg-success');

    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    expect(progressBar.style.width).toBe('0%');
    expect(progressBar.textContent).toBe('0%');
    expect(progressBar.classList.contains('bg-success')).toBe(false);
  });

  it('should register progress event listener', () => {
    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    expect(mockXhr.upload.addEventListener).toHaveBeenCalledWith('progress', expect.any(Function));
  });

  it('should register load event listener', () => {
    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    expect(mockXhr.addEventListener).toHaveBeenCalledWith('load', expect.any(Function));
  });

  it('should register error event listener', () => {
    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    expect(mockXhr.addEventListener).toHaveBeenCalledWith('error', expect.any(Function));
  });

  it('should register abort event listener', () => {
    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();

    expect(mockXhr.addEventListener).toHaveBeenCalledWith('abort', expect.any(Function));
  });

  it('should abort XHR when abort is called', () => {
    mockXhr.readyState = 2; // Headers received

    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();
    handler.abort();

    expect(mockXhr.abort).toHaveBeenCalled();
  });

  it('should not abort if XHR is already complete', () => {
    mockXhr.readyState = 4; // Done

    const handler = createUploadHandler({
      form,
      progressBar,
      statusText,
    });

    handler.start();
    handler.abort();

    expect(mockXhr.abort).not.toHaveBeenCalled();
  });

  describe('response handling', () => {
    it('should call onSuccess callback on successful response', () => {
      const onSuccess = vi.fn();
      const onError = vi.fn();

      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
        onSuccess,
        onError,
      });

      handler.start();

      // Simulate successful response
      mockXhr.status = 200;
      mockXhr.responseText = JSON.stringify({
        success: true,
        recordings_created: 5,
        redirect_url: '/batch/123/',
      });

      // Get the load callback and call it
      const loadCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'load'
      )[1];
      loadCallback();

      expect(onSuccess).toHaveBeenCalledWith(
        expect.objectContaining({
          success: true,
          recordings_created: 5,
        })
      );
      expect(onError).not.toHaveBeenCalled();
    });

    it('should call onError callback on failed response', () => {
      const onSuccess = vi.fn();
      const onError = vi.fn();

      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
        onSuccess,
        onError,
      });

      handler.start();

      // Simulate error response
      mockXhr.status = 200;
      mockXhr.responseText = JSON.stringify({
        success: false,
        error: 'Invalid file format',
      });

      const loadCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'load'
      )[1];
      loadCallback();

      expect(onError).toHaveBeenCalledWith('Invalid file format');
      expect(onSuccess).not.toHaveBeenCalled();
    });

    it('should show error on HTTP error status', () => {
      const onError = vi.fn();

      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
        onError,
      });

      handler.start();

      // Simulate HTTP error
      mockXhr.status = 500;
      mockXhr.statusText = 'Internal Server Error';

      const loadCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'load'
      )[1];
      loadCallback();

      expect(onError).toHaveBeenCalledWith('Upload failed (500: Internal Server Error)');
    });

    it('should handle network errors', () => {
      const onError = vi.fn();

      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
        onError,
      });

      handler.start();

      // Simulate network error
      const errorCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'error'
      )[1];
      errorCallback();

      expect(onError).toHaveBeenCalledWith('Network error occurred');
    });

    it('should show cancelled state on abort', () => {
      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
      });

      handler.start();

      // Simulate abort
      const abortCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'abort'
      )[1];
      abortCallback();

      expect(statusText.textContent).toBe('Upload cancelled');
      expect(progressBar.classList.contains('bg-warning')).toBe(true);
    });

    it('should use server message if provided', () => {
      const onSuccess = vi.fn();

      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
        onSuccess,
      });

      handler.start();

      mockXhr.status = 200;
      mockXhr.responseText = JSON.stringify({
        success: true,
        message: 'Custom success message from server',
      });

      const loadCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'load'
      )[1];
      loadCallback();

      expect(statusText.innerHTML).toContain('Custom success message from server');
    });

    it('should redirect to responseURL for non-JSON responses', () => {
      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
      });

      handler.start();

      mockXhr.status = 200;
      mockXhr.responseText = '<html>Redirected page</html>';
      mockXhr.responseURL = '/success-page/';

      const loadCallback = mockXhr.addEventListener.mock.calls.find(
        (call) => call[0] === 'load'
      )[1];
      loadCallback();

      expect(window.location.assign).toHaveBeenCalledWith('/success-page/');
    });
  });

  describe('progress tracking', () => {
    it('should update progress bar during upload', () => {
      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
      });

      handler.start();

      // Get the progress callback
      const progressCallback = mockXhr.upload.addEventListener.mock.calls.find(
        (call) => call[0] === 'progress'
      )[1];

      // Simulate progress event
      progressCallback({
        lengthComputable: true,
        loaded: 50000000,
        total: 100000000,
      });

      expect(progressBar.style.width).toBe('50%');
      expect(progressBar.textContent).toBe('50%');
    });

    it('should ignore non-computable progress events', () => {
      const handler = createUploadHandler({
        form,
        progressBar,
        statusText,
      });

      handler.start();

      // Reset progress bar after resetProgress was called
      progressBar.style.width = '0%';

      const progressCallback = mockXhr.upload.addEventListener.mock.calls.find(
        (call) => call[0] === 'progress'
      )[1];

      // Simulate non-computable progress event
      progressCallback({
        lengthComputable: false,
        loaded: 0,
        total: 0,
      });

      // Progress bar should not have changed from its initial state
      expect(progressBar.style.width).toBe('0%');
    });
  });
});

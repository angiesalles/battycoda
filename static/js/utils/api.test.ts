/**
 * Tests for api.ts utility module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  ApiError,
  apiRequest,
  fetchJson,
  postJson,
  putJson,
  patchJson,
  deleteRequest,
  isApiError,
  getErrorMessage,
  isSuccessResponse,
  isErrorResponse,
} from './api';

// Mock getCsrfToken from page-data
vi.mock('./page-data.js', () => ({
  getCsrfToken: vi.fn(() => 'mock-csrf-token'),
}));

/**
 * Helper to create a mock Response object
 */
function createMockResponse(
  data: unknown,
  options: { ok?: boolean; status?: number; statusText?: string; contentType?: string } = {}
): Response {
  const { ok = true, status = 200, statusText = 'OK', contentType = 'application/json' } = options;

  return {
    ok,
    status,
    statusText,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers({ 'content-type': contentType }),
  } as Response;
}

describe('api utility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  describe('ApiError', () => {
    it('should create an error with message and status', () => {
      const error = new ApiError('Not found', 404);

      expect(error.message).toBe('Not found');
      expect(error.status).toBe(404);
      expect(error.name).toBe('ApiError');
      expect(error.response).toBeUndefined();
    });

    it('should include response data when provided', () => {
      const responseData = { status: 'error' as const, message: 'Validation failed' };
      const error = new ApiError('Validation failed', 400, responseData);

      expect(error.status).toBe(400);
      expect(error.response).toEqual(responseData);
    });

    it('should be instanceof Error', () => {
      const error = new ApiError('Test error', 500);

      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(ApiError);
    });
  });

  describe('apiRequest', () => {
    it('should make a successful GET request', async () => {
      const mockData = { id: 1, name: 'Test' };
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(mockData));

      const result = await apiRequest<typeof mockData>('/api/test/');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-CSRFToken': 'mock-csrf-token',
          }),
          credentials: 'same-origin',
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should make a POST request with body', async () => {
      const requestBody = { name: 'New Item' };
      const responseData = { id: 1, name: 'New Item' };
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(responseData));

      const result = await apiRequest<typeof responseData>('/api/create/', {
        method: 'POST',
        body: requestBody,
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/create/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody),
        })
      );
      expect(result).toEqual(responseData);
    });

    it('should throw ApiError on HTTP error response', async () => {
      const errorResponse = { status: 'error' as const, message: 'Not found' };
      vi.mocked(global.fetch).mockResolvedValueOnce(
        createMockResponse(errorResponse, { ok: false, status: 404, statusText: 'Not Found' })
      );

      try {
        await apiRequest('/api/missing/');
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        expect(isApiError(error)).toBe(true);
        if (isApiError(error)) {
          expect(error.status).toBe(404);
          expect(error.message).toBe('Not found');
          expect(error.response).toEqual(errorResponse);
        }
      }
    });

    it('should handle non-JSON responses', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: () => Promise.reject(new Error('Not JSON')),
        headers: new Headers({ 'content-type': 'text/html' }),
      } as Response);

      const result = await apiRequest('/api/html/');

      expect(result).toEqual({});
    });

    it('should throw ApiError for non-JSON error responses', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.reject(new Error('Not JSON')),
        headers: new Headers({ 'content-type': 'text/html' }),
      } as Response);

      await expect(apiRequest('/api/error/')).rejects.toThrow(ApiError);

      try {
        await apiRequest('/api/error/');
      } catch (error) {
        if (isApiError(error)) {
          expect(error.status).toBe(500);
          expect(error.message).toBe('Request failed: Internal Server Error');
        }
      }
    });

    it('should include additional headers', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse({}));

      await apiRequest('/api/test/', {
        headers: { Authorization: 'Bearer token123' },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test/',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer token123',
            'X-CSRFToken': 'mock-csrf-token',
          }),
        })
      );
    });

    it('should use default error message when response has no message', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        createMockResponse({ status: 'error' }, { ok: false, status: 400 })
      );

      try {
        await apiRequest('/api/test/');
      } catch (error) {
        if (isApiError(error)) {
          expect(error.message).toBe('Request failed with status 400');
        }
      }
    });
  });

  describe('fetchJson', () => {
    it('should make a GET request', async () => {
      const mockData = [{ id: 1 }, { id: 2 }];
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(mockData));

      const result = await fetchJson<typeof mockData>('/api/items/');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/items/',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('postJson', () => {
    it('should make a POST request with body', async () => {
      const body = { name: 'Test' };
      const response = { id: 1, name: 'Test' };
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(response));

      const result = await postJson<typeof response>('/api/create/', body);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/create/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(body),
        })
      );
      expect(result).toEqual(response);
    });
  });

  describe('putJson', () => {
    it('should make a PUT request with body', async () => {
      const body = { id: 1, name: 'Updated' };
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(body));

      const result = await putJson<typeof body>('/api/items/1/', body);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/items/1/',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(body),
        })
      );
      expect(result).toEqual(body);
    });
  });

  describe('patchJson', () => {
    it('should make a PATCH request with body', async () => {
      const body = { name: 'Patched' };
      const response = { id: 1, name: 'Patched' };
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(response));

      const result = await patchJson<typeof response>('/api/items/1/', body);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/items/1/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(body),
        })
      );
      expect(result).toEqual(response);
    });
  });

  describe('deleteRequest', () => {
    it('should make a DELETE request', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse({}));

      await deleteRequest('/api/items/1/');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/items/1/',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('should return response data if provided', async () => {
      const response = { status: 'success', message: 'Deleted' };
      vi.mocked(global.fetch).mockResolvedValueOnce(createMockResponse(response));

      const result = await deleteRequest<typeof response>('/api/items/1/');

      expect(result).toEqual(response);
    });
  });

  describe('isApiError', () => {
    it('should return true for ApiError instances', () => {
      const error = new ApiError('Test', 500);
      expect(isApiError(error)).toBe(true);
    });

    it('should return false for regular Error instances', () => {
      const error = new Error('Test');
      expect(isApiError(error)).toBe(false);
    });

    it('should return false for non-error values', () => {
      expect(isApiError('error')).toBe(false);
      expect(isApiError(null)).toBe(false);
      expect(isApiError(undefined)).toBe(false);
      expect(isApiError({ message: 'error' })).toBe(false);
    });
  });

  describe('getErrorMessage', () => {
    it('should extract message from ApiError with response', () => {
      const error = new ApiError('Generic', 400, {
        status: 'error',
        message: 'Validation failed: name is required',
      });

      expect(getErrorMessage(error)).toBe('Validation failed: name is required');
    });

    it('should use ApiError message when response has no message', () => {
      const error = new ApiError('Connection failed', 500);

      expect(getErrorMessage(error)).toBe('Connection failed');
    });

    it('should extract message from regular Error', () => {
      const error = new Error('Something went wrong');

      expect(getErrorMessage(error)).toBe('Something went wrong');
    });

    it('should return fallback for non-error values', () => {
      expect(getErrorMessage('error')).toBe('An unexpected error occurred');
      expect(getErrorMessage(null)).toBe('An unexpected error occurred');
      expect(getErrorMessage(undefined)).toBe('An unexpected error occurred');
    });

    it('should use custom fallback when provided', () => {
      expect(getErrorMessage(null, 'Custom fallback')).toBe('Custom fallback');
    });
  });

  describe('isSuccessResponse', () => {
    it('should return true for success responses', () => {
      const response = { status: 'success' as const, data: { id: 1 } };
      expect(isSuccessResponse(response)).toBe(true);
    });

    it('should return false for error responses', () => {
      const response = { status: 'error' as const, message: 'Failed' };
      expect(isSuccessResponse(response)).toBe(false);
    });
  });

  describe('isErrorResponse', () => {
    it('should return true for error responses', () => {
      const response = { status: 'error' as const, message: 'Failed' };
      expect(isErrorResponse(response)).toBe(true);
    });

    it('should return false for success responses', () => {
      const response = { status: 'success' as const, data: { id: 1 } };
      expect(isErrorResponse(response)).toBe(false);
    });
  });
});

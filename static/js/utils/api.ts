/**
 * Type-safe API Utilities
 *
 * Provides typed wrapper functions for making API requests to the Django backend.
 * This module demonstrates TypeScript usage in BattyCoda and provides type safety
 * for common API operations.
 *
 * Usage:
 * ```typescript
 * import { fetchJson, postJson, apiRequest } from '@/utils/api';
 * import type { Recording, ApiResponse } from '@/types';
 *
 * // GET request with typed response
 * const recording = await fetchJson<Recording>('/api/recordings/123/');
 *
 * // POST request with typed body and response
 * const result = await postJson<{ status: string }>('/api/update/', { name: 'test' });
 * ```
 */

import type { ApiResponse, ApiErrorResponse } from '../types/api';
import { getCsrfToken } from './page-data.js';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: ApiErrorResponse
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Default request options
 */
interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeout?: number;
}

/**
 * Build headers for API requests
 * @param additionalHeaders - Extra headers to include
 * @returns Headers object with CSRF token and Content-Type
 */
function buildHeaders(additionalHeaders: Record<string, string> = {}): Record<string, string> {
  const csrfToken = getCsrfToken();
  return {
    'Content-Type': 'application/json',
    ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    ...additionalHeaders,
  };
}

/**
 * Make an API request with timeout support
 * @param url - The URL to request
 * @param options - Request options
 * @returns The response
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit & { timeout?: number }
): Promise<Response> {
  const { timeout = 30000, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Make a type-safe API request
 *
 * @template T - The expected response type
 * @param url - The URL to request
 * @param options - Request options (method, body, headers, etc.)
 * @returns Promise resolving to the typed response data
 * @throws {ApiError} If the request fails or returns an error status
 *
 * @example
 * const data = await apiRequest<Recording>('/api/recordings/123/');
 *
 * @example
 * const result = await apiRequest<{ id: number }>('/api/create/', {
 *   method: 'POST',
 *   body: { name: 'New Recording' }
 * });
 */
export async function apiRequest<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const { body, timeout, headers: additionalHeaders, ...fetchOptions } = options;

  const response = await fetchWithTimeout(url, {
    ...fetchOptions,
    headers: buildHeaders(additionalHeaders as Record<string, string>),
    credentials: 'same-origin',
    body: body ? JSON.stringify(body) : undefined,
    timeout,
  });

  // Handle non-JSON responses
  const contentType = response.headers.get('content-type');
  if (!contentType?.includes('application/json')) {
    if (!response.ok) {
      throw new ApiError(`Request failed: ${response.statusText}`, response.status);
    }
    return {} as T;
  }

  const data = await response.json();

  if (!response.ok) {
    const errorResponse = data as ApiErrorResponse;
    throw new ApiError(
      errorResponse.message || `Request failed with status ${response.status}`,
      response.status,
      errorResponse
    );
  }

  return data as T;
}

/**
 * Make a GET request and parse JSON response
 *
 * @template T - The expected response type
 * @param url - The URL to fetch
 * @param options - Additional request options
 * @returns Promise resolving to the typed response data
 *
 * @example
 * const recordings = await fetchJson<Recording[]>('/api/recordings/');
 */
export async function fetchJson<T>(
  url: string,
  options: Omit<RequestOptions, 'method' | 'body'> = {}
): Promise<T> {
  return apiRequest<T>(url, { ...options, method: 'GET' });
}

/**
 * Make a POST request with JSON body
 *
 * @template T - The expected response type
 * @param url - The URL to post to
 * @param body - The data to send (will be JSON stringified)
 * @param options - Additional request options
 * @returns Promise resolving to the typed response data
 *
 * @example
 * const result = await postJson<ApiResponse>('/api/clusters/update-label/', {
 *   cluster_id: 1,
 *   label: 'My Cluster'
 * });
 */
export async function postJson<T>(
  url: string,
  body: unknown,
  options: Omit<RequestOptions, 'method' | 'body'> = {}
): Promise<T> {
  return apiRequest<T>(url, { ...options, method: 'POST', body });
}

/**
 * Make a PUT request with JSON body
 *
 * @template T - The expected response type
 * @param url - The URL to put to
 * @param body - The data to send
 * @param options - Additional request options
 * @returns Promise resolving to the typed response data
 */
export async function putJson<T>(
  url: string,
  body: unknown,
  options: Omit<RequestOptions, 'method' | 'body'> = {}
): Promise<T> {
  return apiRequest<T>(url, { ...options, method: 'PUT', body });
}

/**
 * Make a PATCH request with JSON body
 *
 * @template T - The expected response type
 * @param url - The URL to patch
 * @param body - The data to send
 * @param options - Additional request options
 * @returns Promise resolving to the typed response data
 */
export async function patchJson<T>(
  url: string,
  body: unknown,
  options: Omit<RequestOptions, 'method' | 'body'> = {}
): Promise<T> {
  return apiRequest<T>(url, { ...options, method: 'PATCH', body });
}

/**
 * Make a DELETE request
 *
 * @template T - The expected response type (usually void or success message)
 * @param url - The URL to delete
 * @param options - Additional request options
 * @returns Promise resolving to the typed response data
 */
export async function deleteRequest<T = void>(
  url: string,
  options: Omit<RequestOptions, 'method' | 'body'> = {}
): Promise<T> {
  return apiRequest<T>(url, { ...options, method: 'DELETE' });
}

/**
 * Check if an error is an ApiError
 * @param error - The error to check
 * @returns True if the error is an ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/**
 * Extract a user-friendly error message from an error
 * @param error - The error to extract message from
 * @param fallback - Fallback message if extraction fails
 * @returns A user-friendly error message
 */
export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  if (isApiError(error)) {
    return error.response?.message || error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

/**
 * Type guard to check if an API response indicates success
 */
export function isSuccessResponse<T>(
  response: ApiResponse<T>
): response is { status: 'success'; data?: T; message?: string } {
  return response.status === 'success';
}

/**
 * Type guard to check if an API response indicates an error
 */
export function isErrorResponse(response: ApiResponse): response is ApiErrorResponse {
  return response.status === 'error';
}

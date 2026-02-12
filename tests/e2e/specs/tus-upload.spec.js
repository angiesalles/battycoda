import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';
import users from '../fixtures/users.json' with { type: 'json' };
import fs from 'fs';
import path from 'path';

/**
 * End-to-end tests for TUS resumable upload protocol.
 *
 * Tests the server-side TUS endpoint via authenticated HTTP requests,
 * exercising the full create → patch → finalize → recording created flow.
 */

// Create a minimal valid WAV file (44-byte header + 2000 bytes of silence)
function createTestWavBuffer(dataBytes = 2000) {
  const header = Buffer.alloc(44);
  const data = Buffer.alloc(dataBytes, 0); // silence
  const fileSize = 44 + dataBytes;

  // RIFF header
  header.write('RIFF', 0);
  header.writeUInt32LE(fileSize - 8, 4);
  header.write('WAVE', 8);

  // fmt chunk
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16); // chunk size
  header.writeUInt16LE(1, 20); // PCM format
  header.writeUInt16LE(1, 22); // mono
  header.writeUInt32LE(44100, 24); // sample rate
  header.writeUInt32LE(88200, 28); // byte rate (44100 * 1 * 2)
  header.writeUInt16LE(2, 32); // block align
  header.writeUInt16LE(16, 34); // bits per sample

  // data chunk
  header.write('data', 36);
  header.writeUInt32LE(dataBytes, 40);

  return Buffer.concat([header, data]);
}

function encodeMetadataValue(value) {
  return Buffer.from(value).toString('base64');
}

function buildMetadataHeader(metadata) {
  return Object.entries(metadata)
    .map(([key, value]) => `${key} ${encodeMetadataValue(value)}`)
    .join(', ');
}

test.describe('TUS Upload - Unauthenticated', () => {
  test('TUS endpoint redirects to login when not authenticated', async ({
    request,
  }) => {
    const response = await request.post('/tus/', {
      headers: {
        'Upload-Length': '1024',
        'Tus-Resumable': '1.0.0',
      },
      maxRedirects: 0,
    });

    // Should redirect to login (302)
    expect(response.status()).toBe(302);
  });
});

test.describe('TUS Upload - Authenticated', () => {
  // Log in via the browser to get session cookies, then use them for API calls
  test.beforeEach(async ({ page }) => {
    await login(page, users.testUser.username, users.testUser.password);
  });

  test('OPTIONS returns TUS capabilities', async ({ page }) => {
    const response = await page.request.fetch('/tus/', { method: 'OPTIONS' });

    expect(response.status()).toBe(204);
    expect(response.headers()['tus-resumable']).toBe('1.0.0');
    expect(response.headers()['tus-extension']).toContain('creation');
    expect(response.headers()['tus-max-size']).toBeTruthy();
  });

  test('POST creates an upload and returns Location', async ({ page }) => {
    // Look up the species and project IDs from the create recording form
    await page.goto('/recordings/create/');
    const speciesId = await page.locator('#id_species option:not([value=""])').first().getAttribute('value');
    const projectId = await page.locator('#id_project option:not([value=""])').first().getAttribute('value');

    const metadata = buildMetadataHeader({
      filename: 'e2e-test.wav',
      name: 'E2E TUS Test Recording',
      species_id: speciesId,
      project_id: projectId,
    });

    const response = await page.request.fetch('/tus/', {
      method: 'POST',
      headers: {
        'Upload-Length': '1024',
        'Upload-Metadata': metadata,
        'Tus-Resumable': '1.0.0',
        'Content-Type': 'application/octet-stream',
      },
    });

    expect(response.status()).toBe(201);
    expect(response.headers()['location']).toMatch(/\/tus\/[0-9a-f-]+/);
    expect(response.headers()['upload-offset']).toBe('0');
  });

  test('full upload lifecycle: create → HEAD → PATCH → recording created', async ({
    page,
  }) => {
    // Get species/project IDs from the form
    await page.goto('/recordings/create/');
    const speciesId = await page.locator('#id_species option:not([value=""])').first().getAttribute('value');
    const projectId = await page.locator('#id_project option:not([value=""])').first().getAttribute('value');

    const wavBuffer = createTestWavBuffer(2000);
    const totalSize = wavBuffer.length;

    // 1. POST — create the upload
    const metadata = buildMetadataHeader({
      filename: 'e2e-lifecycle.wav',
      name: 'E2E Lifecycle Recording',
      species_id: speciesId,
      project_id: projectId,
      split_long_files: 'false',
    });

    const createResponse = await page.request.fetch('/tus/', {
      method: 'POST',
      headers: {
        'Upload-Length': String(totalSize),
        'Upload-Metadata': metadata,
        'Tus-Resumable': '1.0.0',
        'Content-Type': 'application/octet-stream',
      },
    });

    expect(createResponse.status()).toBe(201);
    const location = createResponse.headers()['location'];
    expect(location).toBeTruthy();

    // Extract the path from the absolute URL
    const uploadPath = new URL(location).pathname;

    // 2. HEAD — verify offset is 0
    const headResponse = await page.request.fetch(uploadPath, {
      method: 'HEAD',
    });

    expect(headResponse.status()).toBe(200);
    expect(headResponse.headers()['upload-offset']).toBe('0');
    expect(headResponse.headers()['upload-length']).toBe(String(totalSize));

    // 3. PATCH — send the file in two chunks
    const midpoint = Math.floor(totalSize / 2);
    const chunk1 = wavBuffer.subarray(0, midpoint);
    const chunk2 = wavBuffer.subarray(midpoint);

    // First chunk
    const patch1Response = await page.request.fetch(uploadPath, {
      method: 'PATCH',
      headers: {
        'Upload-Offset': '0',
        'Content-Type': 'application/offset+octet-stream',
        'Tus-Resumable': '1.0.0',
      },
      data: chunk1,
    });

    expect(patch1Response.status()).toBe(204);
    expect(patch1Response.headers()['upload-offset']).toBe(String(midpoint));

    // 4. HEAD again — verify offset advanced
    const headResponse2 = await page.request.fetch(uploadPath, {
      method: 'HEAD',
    });
    expect(headResponse2.headers()['upload-offset']).toBe(String(midpoint));

    // 5. PATCH — send final chunk (triggers finalization)
    const patch2Response = await page.request.fetch(uploadPath, {
      method: 'PATCH',
      headers: {
        'Upload-Offset': String(midpoint),
        'Content-Type': 'application/offset+octet-stream',
        'Tus-Resumable': '1.0.0',
      },
      data: chunk2,
    });

    expect(patch2Response.status()).toBe(204);
    expect(patch2Response.headers()['upload-offset']).toBe(String(totalSize));

    // Should have finalization headers
    const redirectUrl = patch2Response.headers()['x-redirect-url'];
    expect(redirectUrl).toBeTruthy();
    expect(redirectUrl).toMatch(/\/recordings\/\d+/);

    // 6. Verify the recording was actually created
    const recordingPage = await page.goto(redirectUrl);
    expect(recordingPage.status()).toBe(200);
    await expect(page.locator('body')).toContainText('E2E Lifecycle Recording');
  });

  test('PATCH with wrong offset returns 409 conflict', async ({ page }) => {
    await page.goto('/recordings/create/');
    const speciesId = await page.locator('#id_species option:not([value=""])').first().getAttribute('value');
    const projectId = await page.locator('#id_project option:not([value=""])').first().getAttribute('value');

    const metadata = buildMetadataHeader({
      filename: 'e2e-conflict.wav',
      name: 'E2E Conflict Test',
      species_id: speciesId,
      project_id: projectId,
    });

    // Create upload
    const createResponse = await page.request.fetch('/tus/', {
      method: 'POST',
      headers: {
        'Upload-Length': '1024',
        'Upload-Metadata': metadata,
        'Tus-Resumable': '1.0.0',
        'Content-Type': 'application/octet-stream',
      },
    });

    const uploadPath = new URL(createResponse.headers()['location']).pathname;

    // Try to PATCH with offset 500 (server is at 0)
    const patchResponse = await page.request.fetch(uploadPath, {
      method: 'PATCH',
      headers: {
        'Upload-Offset': '500',
        'Content-Type': 'application/offset+octet-stream',
        'Tus-Resumable': '1.0.0',
      },
      data: Buffer.alloc(100),
    });

    expect(patchResponse.status()).toBe(409);
  });

  test('DELETE cancels upload and cleans up', async ({ page }) => {
    await page.goto('/recordings/create/');
    const speciesId = await page.locator('#id_species option:not([value=""])').first().getAttribute('value');
    const projectId = await page.locator('#id_project option:not([value=""])').first().getAttribute('value');

    const metadata = buildMetadataHeader({
      filename: 'e2e-delete.wav',
      name: 'E2E Delete Test',
      species_id: speciesId,
      project_id: projectId,
    });

    // Create upload
    const createResponse = await page.request.fetch('/tus/', {
      method: 'POST',
      headers: {
        'Upload-Length': '1024',
        'Upload-Metadata': metadata,
        'Tus-Resumable': '1.0.0',
        'Content-Type': 'application/octet-stream',
      },
    });

    const uploadPath = new URL(createResponse.headers()['location']).pathname;

    // Delete it
    const deleteResponse = await page.request.fetch(uploadPath, {
      method: 'DELETE',
      headers: { 'Tus-Resumable': '1.0.0' },
    });

    expect(deleteResponse.status()).toBe(204);

    // HEAD should now return 404
    const headResponse = await page.request.fetch(uploadPath, {
      method: 'HEAD',
    });

    expect(headResponse.status()).toBe(404);
  });
});

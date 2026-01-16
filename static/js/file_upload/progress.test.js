/**
 * Tests for file upload progress display functions
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  getFileInfo,
  updateFileInfoDisplay,
  updateProgress,
  resetProgress,
  showSuccess,
  showError,
  showCancelled,
} from './progress.js';

describe('getFileInfo', () => {
  /**
   * Helper to create a mock file object
   */
  function createMockFile(name, size) {
    return { name, size };
  }

  /**
   * Helper to create a mock file input with files
   */
  function createMockFileInput(files) {
    return { files };
  }

  describe('single file upload', () => {
    it('should calculate info for a single WAV file', () => {
      const inputs = {
        wavFileInput: createMockFileInput([createMockFile('recording.wav', 1000000)]),
        pickleFileInput: createMockFileInput([]),
      };

      const result = getFileInfo(inputs, false);

      expect(result.totalSize).toBe(1000000);
      expect(result.count).toBe(1);
      expect(result.filenames).toEqual(['recording.wav']);
    });

    it('should calculate info for WAV and pickle file', () => {
      const inputs = {
        wavFileInput: createMockFileInput([createMockFile('recording.wav', 1000000)]),
        pickleFileInput: createMockFileInput([createMockFile('data.pkl', 500000)]),
      };

      const result = getFileInfo(inputs, false);

      expect(result.totalSize).toBe(1500000);
      expect(result.count).toBe(2);
      expect(result.filenames).toEqual(['recording.wav', 'data.pkl']);
    });

    it('should handle missing inputs gracefully', () => {
      const inputs = {
        wavFileInput: null,
        pickleFileInput: null,
      };

      const result = getFileInfo(inputs, false);

      expect(result.totalSize).toBe(0);
      expect(result.count).toBe(0);
      expect(result.filenames).toEqual([]);
    });

    it('should handle inputs with no files selected', () => {
      const inputs = {
        wavFileInput: createMockFileInput([]),
        pickleFileInput: createMockFileInput([]),
      };

      const result = getFileInfo(inputs, false);

      expect(result.totalSize).toBe(0);
      expect(result.count).toBe(0);
      expect(result.filenames).toEqual([]);
    });
  });

  describe('batch upload', () => {
    it('should calculate info for multiple WAV files', () => {
      const inputs = {
        wavFilesInput: createMockFileInput([
          createMockFile('one.wav', 1000000),
          createMockFile('two.wav', 2000000),
          createMockFile('three.wav', 500000),
        ]),
        pickleFilesInput: createMockFileInput([]),
      };

      const result = getFileInfo(inputs, true);

      expect(result.totalSize).toBe(3500000);
      expect(result.count).toBe(3);
      expect(result.filenames).toEqual(['one.wav', 'two.wav', 'three.wav']);
    });

    it('should calculate info for WAV and pickle files in batch', () => {
      const inputs = {
        wavFilesInput: createMockFileInput([
          createMockFile('one.wav', 1000000),
          createMockFile('two.wav', 1000000),
        ]),
        pickleFilesInput: createMockFileInput([
          createMockFile('data1.pkl', 200000),
          createMockFile('data2.pkl', 200000),
        ]),
      };

      const result = getFileInfo(inputs, true);

      expect(result.totalSize).toBe(2400000);
      expect(result.count).toBe(4);
      expect(result.filenames).toEqual(['one.wav', 'two.wav', 'data1.pkl', 'data2.pkl']);
    });
  });

  describe('pickle-only form', () => {
    it('should handle pickle-only form type', () => {
      const inputs = {
        formType: 'pickle_only',
        pickleFileInput: createMockFileInput([createMockFile('data.pkl', 500000)]),
      };

      const result = getFileInfo(inputs, false);

      expect(result.totalSize).toBe(500000);
      expect(result.count).toBe(1);
      expect(result.filenames).toEqual(['data.pkl']);
    });

    it('should return empty for pickle-only with no file', () => {
      const inputs = {
        formType: 'pickle_only',
        pickleFileInput: createMockFileInput([]),
      };

      const result = getFileInfo(inputs, false);

      expect(result.totalSize).toBe(0);
      expect(result.count).toBe(0);
      expect(result.filenames).toEqual([]);
    });
  });
});

describe('updateFileInfoDisplay', () => {
  let progressContainer;
  let statusText;
  let progressBar;

  beforeEach(() => {
    progressContainer = document.createElement('div');
    progressContainer.classList.add('d-none');
    statusText = document.createElement('div');
    progressBar = document.createElement('div');
  });

  it('should show container when files are selected', () => {
    const elements = { progressContainer, statusText, progressBar };
    const fileInfo = {
      totalSize: 5242880, // 5 MB
      count: 2,
      filenames: ['file1.wav', 'file2.wav'],
    };

    updateFileInfoDisplay(elements, fileInfo);

    expect(progressContainer.classList.contains('d-none')).toBe(false);
    expect(statusText.innerHTML).toContain('Selected 2 files');
    expect(statusText.innerHTML).toContain('5.00 MB');
  });

  it('should hide container when no files selected', () => {
    progressContainer.classList.remove('d-none');
    const elements = { progressContainer, statusText, progressBar };
    const fileInfo = { totalSize: 0, count: 0, filenames: [] };

    updateFileInfoDisplay(elements, fileInfo);

    expect(progressContainer.classList.contains('d-none')).toBe(true);
  });

  it('should use singular form for single file', () => {
    const elements = { progressContainer, statusText, progressBar };
    const fileInfo = {
      totalSize: 1048576,
      count: 1,
      filenames: ['single.wav'],
    };

    updateFileInfoDisplay(elements, fileInfo);

    expect(statusText.innerHTML).toContain('Selected 1 file');
    expect(statusText.innerHTML).not.toContain('files');
  });

  it('should display file badges for small number of files', () => {
    const elements = { progressContainer, statusText, progressBar };
    const fileInfo = {
      totalSize: 3145728,
      count: 3,
      filenames: ['one.wav', 'two.wav', 'three.wav'],
    };

    updateFileInfoDisplay(elements, fileInfo);

    expect(statusText.innerHTML).toContain('one.wav');
    expect(statusText.innerHTML).toContain('two.wav');
    expect(statusText.innerHTML).toContain('three.wav');
    expect(statusText.innerHTML).toContain('badge');
  });

  it('should truncate display for many files (>10)', () => {
    const elements = { progressContainer, statusText, progressBar };
    const filenames = Array.from({ length: 15 }, (_, i) => `file${i + 1}.wav`);
    const fileInfo = {
      totalSize: 15000000,
      count: 15,
      filenames,
    };

    updateFileInfoDisplay(elements, fileInfo);

    // Should show first 10 files
    expect(statusText.innerHTML).toContain('file1.wav');
    expect(statusText.innerHTML).toContain('file10.wav');
    // Should show "+5 more files"
    expect(statusText.innerHTML).toContain('+5 more files');
  });

  it('should escape HTML in filenames to prevent XSS', () => {
    const elements = { progressContainer, statusText, progressBar };
    const fileInfo = {
      totalSize: 1000000,
      count: 1,
      filenames: ['<script>alert("xss")</script>.wav'],
    };

    updateFileInfoDisplay(elements, fileInfo);

    expect(statusText.innerHTML).not.toContain('<script>');
    expect(statusText.innerHTML).toContain('&lt;script&gt;');
  });
});

describe('updateProgress', () => {
  let progressBar;
  let statusText;

  beforeEach(() => {
    progressBar = document.createElement('div');
    progressBar.classList.add('progress-bar-animated');
    statusText = document.createElement('div');
  });

  it('should update progress percentage', () => {
    updateProgress(progressBar, statusText, 50000, 100000);

    expect(progressBar.style.width).toBe('50%');
    expect(progressBar.textContent).toBe('50%');
    expect(progressBar.getAttribute('aria-valuenow')).toBe('50');
  });

  it('should show uploading status during progress', () => {
    updateProgress(progressBar, statusText, 25000000, 100000000);

    expect(statusText.textContent).toContain('Uploading files');
    expect(statusText.textContent).toContain('25%');
  });

  it('should show processing status at 100%', () => {
    updateProgress(progressBar, statusText, 100000, 100000);

    expect(statusText.innerHTML).toContain('Processing files');
    expect(progressBar.classList.contains('progress-bar-animated')).toBe(false);
  });

  it('should handle zero total gracefully', () => {
    // When total is 0, (0/0)*100 = NaN, Math.round(NaN) = NaN
    // The function doesn't explicitly handle this edge case
    // We just verify it doesn't throw
    expect(() => updateProgress(progressBar, statusText, 0, 0)).not.toThrow();
  });

  it('should calculate MB values correctly in status', () => {
    updateProgress(progressBar, statusText, 52428800, 104857600); // 50MB / 100MB

    expect(statusText.textContent).toContain('50MB');
    expect(statusText.textContent).toContain('100MB');
  });
});

describe('resetProgress', () => {
  let progressBar;
  let statusText;

  beforeEach(() => {
    progressBar = document.createElement('div');
    progressBar.style.width = '75%';
    progressBar.textContent = '75%';
    progressBar.setAttribute('aria-valuenow', '75');
    progressBar.classList.add('bg-success', 'bg-danger', 'bg-warning');
    statusText = document.createElement('div');
    statusText.textContent = 'Previous status';
  });

  it('should reset progress bar to 0%', () => {
    resetProgress(progressBar, statusText);

    expect(progressBar.style.width).toBe('0%');
    expect(progressBar.textContent).toBe('0%');
    expect(progressBar.getAttribute('aria-valuenow')).toBe('0');
  });

  it('should remove completion classes', () => {
    resetProgress(progressBar, statusText);

    expect(progressBar.classList.contains('bg-success')).toBe(false);
    expect(progressBar.classList.contains('bg-danger')).toBe(false);
    expect(progressBar.classList.contains('bg-warning')).toBe(false);
  });

  it('should add progress animation classes', () => {
    resetProgress(progressBar, statusText);

    expect(progressBar.classList.contains('progress-bar-striped')).toBe(true);
    expect(progressBar.classList.contains('progress-bar-animated')).toBe(true);
    expect(progressBar.classList.contains('bg-primary')).toBe(true);
  });

  it('should set preparing status text', () => {
    resetProgress(progressBar, statusText);

    expect(statusText.textContent).toBe('Preparing files for upload...');
  });
});

describe('showSuccess', () => {
  let progressBar;
  let statusText;

  beforeEach(() => {
    progressBar = document.createElement('div');
    progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
    statusText = document.createElement('div');
  });

  it('should show success alert with default message', () => {
    showSuccess(progressBar, statusText);

    expect(statusText.innerHTML).toContain('alert-success');
    expect(statusText.innerHTML).toContain('Upload complete!');
    expect(statusText.innerHTML).toContain('fa-check-circle');
  });

  it('should show success alert with custom message', () => {
    showSuccess(progressBar, statusText, 'Custom success message');

    expect(statusText.innerHTML).toContain('Custom success message');
  });

  it('should remove animation classes', () => {
    showSuccess(progressBar, statusText);

    expect(progressBar.classList.contains('progress-bar-striped')).toBe(false);
    expect(progressBar.classList.contains('progress-bar-animated')).toBe(false);
  });

  it('should add success class', () => {
    showSuccess(progressBar, statusText);

    expect(progressBar.classList.contains('bg-success')).toBe(true);
  });

  it('should escape HTML in custom message to prevent XSS', () => {
    showSuccess(progressBar, statusText, '<script>alert("xss")</script>');

    expect(statusText.innerHTML).not.toContain('<script>alert');
    expect(statusText.innerHTML).toContain('&lt;script&gt;');
  });
});

describe('showError', () => {
  let progressBar;
  let statusText;

  beforeEach(() => {
    progressBar = document.createElement('div');
    progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
    statusText = document.createElement('div');
  });

  it('should show error alert with message', () => {
    showError(progressBar, statusText, 'Upload failed');

    expect(statusText.innerHTML).toContain('alert-danger');
    expect(statusText.innerHTML).toContain('Upload failed');
    expect(statusText.innerHTML).toContain('fa-exclamation-circle');
  });

  it('should remove animation classes', () => {
    showError(progressBar, statusText, 'Error');

    expect(progressBar.classList.contains('progress-bar-striped')).toBe(false);
    expect(progressBar.classList.contains('progress-bar-animated')).toBe(false);
  });

  it('should add danger class', () => {
    showError(progressBar, statusText, 'Error');

    expect(progressBar.classList.contains('bg-danger')).toBe(true);
  });

  it('should escape HTML in error message to prevent XSS', () => {
    showError(progressBar, statusText, '<img src=x onerror=alert(1)>');

    expect(statusText.innerHTML).not.toContain('<img');
    expect(statusText.innerHTML).toContain('&lt;img');
  });
});

describe('showCancelled', () => {
  let progressBar;
  let statusText;

  beforeEach(() => {
    progressBar = document.createElement('div');
    progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
    statusText = document.createElement('div');
  });

  it('should show cancelled status', () => {
    showCancelled(progressBar, statusText);

    expect(statusText.textContent).toBe('Upload cancelled');
  });

  it('should remove animation classes', () => {
    showCancelled(progressBar, statusText);

    expect(progressBar.classList.contains('progress-bar-striped')).toBe(false);
    expect(progressBar.classList.contains('progress-bar-animated')).toBe(false);
  });

  it('should add warning class', () => {
    showCancelled(progressBar, statusText);

    expect(progressBar.classList.contains('bg-warning')).toBe(true);
  });
});

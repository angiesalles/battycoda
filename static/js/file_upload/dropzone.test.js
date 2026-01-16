/**
 * Tests for file upload dropzone functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setupDropzone } from './dropzone.js';

/**
 * Helper to create a mock file
 */
function createMockFile(name, size = 1048576) {
  return {
    name,
    size,
    type: 'audio/wav',
  };
}

/**
 * Helper to mock the files property on an input element
 * jsdom doesn't allow setting files directly, so we use Object.defineProperty
 */
function mockInputFiles(input, files) {
  // Create a FileList-like object
  const fileList = Object.assign([...files], {
    length: files.length,
    item: (i) => files[i] || null,
  });

  Object.defineProperty(input, 'files', {
    value: fileList,
    writable: true,
    configurable: true,
  });
}

describe('setupDropzone', () => {
  let fileInput;
  let container;

  beforeEach(() => {
    // Create container and file input
    container = document.createElement('div');
    fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.name = 'wav_file';
    container.appendChild(fileInput);
    document.body.innerHTML = '';
    document.body.appendChild(container);
  });

  it('should return early if fileInput is null', () => {
    // Should not throw
    expect(() => setupDropzone(null)).not.toThrow();
  });

  it('should create dropzone wrapper element', () => {
    setupDropzone(fileInput);

    const dropzone = container.querySelector('.file-dropzone');
    expect(dropzone).not.toBeNull();
    expect(dropzone.classList.contains('p-4')).toBe(true);
    expect(dropzone.classList.contains('border')).toBe(true);
    expect(dropzone.classList.contains('border-secondary')).toBe(true);
    expect(dropzone.classList.contains('rounded')).toBe(true);
  });

  it('should hide the original file input', () => {
    setupDropzone(fileInput);

    expect(fileInput.style.display).toBe('none');
  });

  it('should insert dropzone before file input', () => {
    setupDropzone(fileInput);

    const dropzone = container.querySelector('.file-dropzone');
    expect(dropzone.nextSibling).toBe(fileInput);
  });

  it('should show singular text for single file input', () => {
    fileInput.multiple = false;
    setupDropzone(fileInput);

    const dropzone = container.querySelector('.file-dropzone');
    expect(dropzone.textContent).toContain('Drag & drop your file here');
    expect(dropzone.textContent).toContain('Selected file:');
  });

  it('should show plural text for multiple file input', () => {
    fileInput.multiple = true;
    setupDropzone(fileInput);

    const dropzone = container.querySelector('.file-dropzone');
    expect(dropzone.textContent).toContain('Drag & drop your files here');
    expect(dropzone.textContent).toContain('Selected files:');
  });

  it('should contain file upload icon', () => {
    setupDropzone(fileInput);

    const dropzone = container.querySelector('.file-dropzone');
    const icon = dropzone.querySelector('.fa-file-upload');
    expect(icon).not.toBeNull();
  });

  it('should show "None" as initial selected filename', () => {
    setupDropzone(fileInput);

    const dropzone = container.querySelector('.file-dropzone');
    const filenameSpan = dropzone.querySelector('.selected-filename');
    expect(filenameSpan.textContent).toBe('None');
  });

  describe('click handling', () => {
    it('should trigger file input click when dropzone is clicked', () => {
      setupDropzone(fileInput);

      const dropzone = container.querySelector('.file-dropzone');
      const clickSpy = vi.spyOn(fileInput, 'click');

      dropzone.click();

      expect(clickSpy).toHaveBeenCalled();
    });
  });

  describe('file selection display', () => {
    it('should update display when single file is selected', () => {
      setupDropzone(fileInput);

      // Mock the files property
      const mockFile = createMockFile('recording.wav', 1048576);
      mockInputFiles(fileInput, [mockFile]);

      // Trigger change event
      fileInput.dispatchEvent(new Event('change'));

      const dropzone = container.querySelector('.file-dropzone');
      const filenameSpan = dropzone.querySelector('.selected-filename');

      expect(filenameSpan.textContent).toContain('recording.wav');
      expect(filenameSpan.textContent).toContain('1.00 MB');
    });

    it('should add success border when file is selected', () => {
      setupDropzone(fileInput);

      const mockFile = createMockFile('recording.wav');
      mockInputFiles(fileInput, [mockFile]);

      fileInput.dispatchEvent(new Event('change'));

      const dropzone = container.querySelector('.file-dropzone');
      expect(dropzone.classList.contains('border-success')).toBe(true);
      expect(dropzone.classList.contains('border-secondary')).toBe(false);
    });

    it('should show multiple files summary for batch upload', () => {
      fileInput.multiple = true;
      setupDropzone(fileInput);

      const file1 = createMockFile('one.wav', 1048576);
      const file2 = createMockFile('two.wav', 2097152);
      mockInputFiles(fileInput, [file1, file2]);

      fileInput.dispatchEvent(new Event('change'));

      const dropzone = container.querySelector('.file-dropzone');
      const filenameSpan = dropzone.querySelector('.selected-filename');

      expect(filenameSpan.textContent).toContain('2 files selected');
      expect(filenameSpan.textContent).toContain('3.00 MB');
    });

    it('should reset display when files are cleared', () => {
      setupDropzone(fileInput);

      // First add a file
      mockInputFiles(fileInput, [createMockFile('recording.wav')]);
      fileInput.dispatchEvent(new Event('change'));

      // Then clear files
      mockInputFiles(fileInput, []);
      fileInput.dispatchEvent(new Event('change'));

      const dropzone = container.querySelector('.file-dropzone');
      const filenameSpan = dropzone.querySelector('.selected-filename');

      expect(filenameSpan.textContent).toBe('None');
      expect(dropzone.classList.contains('border-secondary')).toBe(true);
      expect(dropzone.classList.contains('border-success')).toBe(false);
    });
  });

  describe('drag and drop handling', () => {
    /**
     * Helper to create a drag event
     * For drop events, includes a mock dataTransfer with empty files
     */
    function createDragEvent(type) {
      const event = new Event(type, { bubbles: true, cancelable: true });

      // For drop events, we need to mock dataTransfer
      if (type === 'drop') {
        Object.defineProperty(event, 'dataTransfer', {
          value: {
            files: [],
          },
          writable: false,
        });
      }

      return event;
    }

    it('should prevent default on drag events', () => {
      setupDropzone(fileInput);
      const dropzone = container.querySelector('.file-dropzone');

      // Test non-drop events
      const nonDropEvents = ['dragenter', 'dragover', 'dragleave'];
      nonDropEvents.forEach((eventType) => {
        const event = createDragEvent(eventType);
        const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
        const stopPropagationSpy = vi.spyOn(event, 'stopPropagation');

        dropzone.dispatchEvent(event);

        expect(preventDefaultSpy).toHaveBeenCalled();
        expect(stopPropagationSpy).toHaveBeenCalled();
      });

      // Test drop event separately with mocked dataTransfer
      const dropEvent = createDragEvent('drop');
      const dropPreventDefaultSpy = vi.spyOn(dropEvent, 'preventDefault');
      const dropStopPropagationSpy = vi.spyOn(dropEvent, 'stopPropagation');

      dropzone.dispatchEvent(dropEvent);

      expect(dropPreventDefaultSpy).toHaveBeenCalled();
      expect(dropStopPropagationSpy).toHaveBeenCalled();
    });

    it('should add visual feedback classes on dragenter', () => {
      setupDropzone(fileInput);
      const dropzone = container.querySelector('.file-dropzone');

      dropzone.dispatchEvent(createDragEvent('dragenter'));

      expect(dropzone.classList.contains('border-primary')).toBe(true);
      expect(dropzone.classList.contains('bg-dark')).toBe(true);
    });

    it('should add visual feedback classes on dragover', () => {
      setupDropzone(fileInput);
      const dropzone = container.querySelector('.file-dropzone');

      dropzone.dispatchEvent(createDragEvent('dragover'));

      expect(dropzone.classList.contains('border-primary')).toBe(true);
      expect(dropzone.classList.contains('bg-dark')).toBe(true);
    });

    it('should remove visual feedback classes on dragleave', () => {
      setupDropzone(fileInput);
      const dropzone = container.querySelector('.file-dropzone');

      // First trigger dragenter to add classes
      dropzone.dispatchEvent(createDragEvent('dragenter'));
      expect(dropzone.classList.contains('border-primary')).toBe(true);

      // Then trigger dragleave to remove them
      dropzone.dispatchEvent(createDragEvent('dragleave'));

      expect(dropzone.classList.contains('border-primary')).toBe(false);
      expect(dropzone.classList.contains('bg-dark')).toBe(false);
    });

    it('should remove visual feedback classes on drop', () => {
      setupDropzone(fileInput);
      const dropzone = container.querySelector('.file-dropzone');

      // First trigger dragenter to add classes
      dropzone.dispatchEvent(createDragEvent('dragenter'));

      // Trigger drop - files will be empty since we can't mock dataTransfer properly
      dropzone.dispatchEvent(createDragEvent('drop'));

      expect(dropzone.classList.contains('border-primary')).toBe(false);
      expect(dropzone.classList.contains('bg-dark')).toBe(false);
    });

    // Note: Testing actual file drop functionality is challenging in jsdom
    // because DataTransfer and FileList mocking is complex.
    // The core drop event handling (preventing defaults, visual feedback) is tested above.
    // File drop functionality should be tested in E2E tests with a real browser.
  });
});

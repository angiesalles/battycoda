/**
 * Tests for file upload validation utilities
 */

import { describe, it, expect } from 'vitest';
import { isValidWavFile, isValidPickleFile, validateFiles, formatFileSize } from './validation.js';

describe('isValidWavFile', () => {
  it('should accept .wav extension', () => {
    const file = { name: 'recording.wav' };
    expect(isValidWavFile(file)).toBe(true);
  });

  it('should accept .wave extension', () => {
    const file = { name: 'recording.wave' };
    expect(isValidWavFile(file)).toBe(true);
  });

  it('should accept uppercase extensions', () => {
    const file = { name: 'recording.WAV' };
    expect(isValidWavFile(file)).toBe(true);
  });

  it('should accept mixed case extensions', () => {
    const file = { name: 'recording.WaV' };
    expect(isValidWavFile(file)).toBe(true);
  });

  it('should reject non-wav files', () => {
    const file = { name: 'recording.mp3' };
    expect(isValidWavFile(file)).toBe(false);
  });

  it('should reject files with wav in the name but different extension', () => {
    const file = { name: 'wav_recording.mp3' };
    expect(isValidWavFile(file)).toBe(false);
  });

  it('should reject pickle files', () => {
    const file = { name: 'data.pickle' };
    expect(isValidWavFile(file)).toBe(false);
  });

  it('should handle files with multiple dots', () => {
    const file = { name: 'my.recording.wav' };
    expect(isValidWavFile(file)).toBe(true);
  });

  it('should reject files with no extension', () => {
    const file = { name: 'recording' };
    expect(isValidWavFile(file)).toBe(false);
  });
});

describe('isValidPickleFile', () => {
  it('should accept .pickle extension', () => {
    const file = { name: 'data.pickle' };
    expect(isValidPickleFile(file)).toBe(true);
  });

  it('should accept .pkl extension', () => {
    const file = { name: 'data.pkl' };
    expect(isValidPickleFile(file)).toBe(true);
  });

  it('should accept uppercase extensions', () => {
    const file = { name: 'data.PICKLE' };
    expect(isValidPickleFile(file)).toBe(true);
  });

  it('should accept mixed case extensions', () => {
    const file = { name: 'data.PiCkLe' };
    expect(isValidPickleFile(file)).toBe(true);
  });

  it('should reject non-pickle files', () => {
    const file = { name: 'data.json' };
    expect(isValidPickleFile(file)).toBe(false);
  });

  it('should reject wav files', () => {
    const file = { name: 'recording.wav' };
    expect(isValidPickleFile(file)).toBe(false);
  });

  it('should handle files with multiple dots', () => {
    const file = { name: 'my.data.pkl' };
    expect(isValidPickleFile(file)).toBe(true);
  });
});

describe('validateFiles', () => {
  it('should separate valid and invalid files', () => {
    const files = [{ name: 'valid.wav' }, { name: 'invalid.mp3' }, { name: 'another.wav' }];

    const result = validateFiles(files, isValidWavFile);

    expect(result.valid).toHaveLength(2);
    expect(result.invalid).toHaveLength(1);
    expect(result.valid[0].name).toBe('valid.wav');
    expect(result.valid[1].name).toBe('another.wav');
    expect(result.invalid[0].name).toBe('invalid.mp3');
  });

  it('should return all files as valid when all pass validation', () => {
    const files = [{ name: 'one.wav' }, { name: 'two.wav' }, { name: 'three.wave' }];

    const result = validateFiles(files, isValidWavFile);

    expect(result.valid).toHaveLength(3);
    expect(result.invalid).toHaveLength(0);
  });

  it('should return all files as invalid when none pass validation', () => {
    const files = [{ name: 'one.mp3' }, { name: 'two.ogg' }, { name: 'three.flac' }];

    const result = validateFiles(files, isValidWavFile);

    expect(result.valid).toHaveLength(0);
    expect(result.invalid).toHaveLength(3);
  });

  it('should handle empty file list', () => {
    const files = [];

    const result = validateFiles(files, isValidWavFile);

    expect(result.valid).toHaveLength(0);
    expect(result.invalid).toHaveLength(0);
  });

  it('should work with custom validators', () => {
    const files = [
      { name: 'big.wav', size: 1000000 },
      { name: 'small.wav', size: 100 },
    ];

    const sizeValidator = (file) => file.size > 1000;
    const result = validateFiles(files, sizeValidator);

    expect(result.valid).toHaveLength(1);
    expect(result.valid[0].name).toBe('big.wav');
    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].name).toBe('small.wav');
  });

  it('should preserve file objects in results', () => {
    const files = [
      { name: 'file.wav', size: 1000, lastModified: 12345 },
      { name: 'file.mp3', size: 2000, lastModified: 67890 },
    ];

    const result = validateFiles(files, isValidWavFile);

    expect(result.valid[0].size).toBe(1000);
    expect(result.valid[0].lastModified).toBe(12345);
    expect(result.invalid[0].size).toBe(2000);
    expect(result.invalid[0].lastModified).toBe(67890);
  });
});

describe('formatFileSize', () => {
  it('should format 0 bytes', () => {
    expect(formatFileSize(0)).toBe('0 Bytes');
  });

  it('should format bytes', () => {
    expect(formatFileSize(500)).toBe('500 Bytes');
  });

  it('should format kilobytes', () => {
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
  });

  it('should format megabytes', () => {
    expect(formatFileSize(1048576)).toBe('1 MB');
    expect(formatFileSize(5242880)).toBe('5 MB');
    expect(formatFileSize(1572864)).toBe('1.5 MB');
  });

  it('should format gigabytes', () => {
    expect(formatFileSize(1073741824)).toBe('1 GB');
    expect(formatFileSize(2147483648)).toBe('2 GB');
  });

  it('should format with two decimal places', () => {
    expect(formatFileSize(1234567)).toBe('1.18 MB');
    expect(formatFileSize(9876543)).toBe('9.42 MB');
  });

  it('should handle large numbers', () => {
    expect(formatFileSize(10737418240)).toBe('10 GB');
  });

  it('should handle small byte values', () => {
    expect(formatFileSize(1)).toBe('1 Bytes');
    expect(formatFileSize(512)).toBe('512 Bytes');
    expect(formatFileSize(1023)).toBe('1023 Bytes');
  });
});

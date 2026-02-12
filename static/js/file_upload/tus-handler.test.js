/**
 * Tests for TUS upload handler utilities.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { extractFormMetadata, isTusSupported } from './tus-handler.js';

describe('isTusSupported', () => {
  it('returns a boolean', () => {
    expect(typeof isTusSupported()).toBe('boolean');
  });
});

describe('extractFormMetadata', () => {
  let form;

  beforeEach(() => {
    form = document.createElement('form');
  });

  function addInput(name, value) {
    const input = document.createElement('input');
    input.name = name;
    input.value = value;
    form.appendChild(input);
  }

  function addCheckbox(name, checked) {
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.name = name;
    input.value = 'on';
    input.checked = checked;
    form.appendChild(input);
  }

  it('extracts basic form fields', () => {
    addInput('name', 'My Recording');
    addInput('species', '42');
    addInput('project', '7');
    addInput('description', 'A test recording');

    const meta = extractFormMetadata(form);

    expect(meta.name).toBe('My Recording');
    expect(meta.species_id).toBe('42');
    expect(meta.project_id).toBe('7');
    expect(meta.description).toBe('A test recording');
  });

  it('extracts optional metadata fields', () => {
    addInput('name', 'Rec');
    addInput('species', '1');
    addInput('project', '1');
    addInput('location', 'Forest A');
    addInput('equipment', 'Recorder X');
    addInput('recorded_date', '2025-01-15');
    addInput('environmental_conditions', 'Windy');

    const meta = extractFormMetadata(form);

    expect(meta.location).toBe('Forest A');
    expect(meta.equipment).toBe('Recorder X');
    expect(meta.recorded_date).toBe('2025-01-15');
    expect(meta.environmental_conditions).toBe('Windy');
  });

  it('handles split_long_files checkbox when checked', () => {
    addInput('name', 'Rec');
    addInput('species', '1');
    addInput('project', '1');
    addCheckbox('split_long_files', true);

    const meta = extractFormMetadata(form);
    expect(meta.split_long_files).toBe('true');
  });

  it('handles split_long_files checkbox when unchecked', () => {
    addInput('name', 'Rec');
    addInput('species', '1');
    addInput('project', '1');
    // Unchecked checkboxes are not included in FormData
    // so split_long_files won't be "on"
    addCheckbox('split_long_files', false);

    const meta = extractFormMetadata(form);
    expect(meta.split_long_files).toBe('false');
  });

  it('omits empty fields', () => {
    addInput('name', 'Rec');
    addInput('species', '1');
    addInput('project', '1');
    addInput('location', '');

    const meta = extractFormMetadata(form);
    expect(meta).not.toHaveProperty('location');
  });
});

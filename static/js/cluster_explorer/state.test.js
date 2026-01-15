/**
 * Tests for cluster_explorer/state.js
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { getSelectedClusterId, setSelectedClusterId, colorScale } from './state.js';

describe('cluster_explorer/state', () => {
  describe('selectedClusterId', () => {
    beforeEach(() => {
      // Reset state before each test
      setSelectedClusterId(null);
    });

    it('should return null by default', () => {
      expect(getSelectedClusterId()).toBe(null);
    });

    it('should set and get a cluster ID', () => {
      setSelectedClusterId(42);
      expect(getSelectedClusterId()).toBe(42);
    });

    it('should allow setting cluster ID to null', () => {
      setSelectedClusterId(42);
      setSelectedClusterId(null);
      expect(getSelectedClusterId()).toBe(null);
    });

    it('should update when set multiple times', () => {
      setSelectedClusterId(1);
      expect(getSelectedClusterId()).toBe(1);

      setSelectedClusterId(2);
      expect(getSelectedClusterId()).toBe(2);

      setSelectedClusterId(3);
      expect(getSelectedClusterId()).toBe(3);
    });
  });

  describe('colorScale', () => {
    it('should return a color string for an index', () => {
      const color = colorScale(0);
      expect(typeof color).toBe('string');
      // D3 category10 colors start with #
      expect(color).toMatch(/^#[0-9a-fA-F]{6}$/);
    });

    it('should return different colors for different indices', () => {
      const color0 = colorScale(0);
      const color1 = colorScale(1);
      const color2 = colorScale(2);

      expect(color0).not.toBe(color1);
      expect(color1).not.toBe(color2);
      expect(color0).not.toBe(color2);
    });

    it('should return consistent colors for the same index', () => {
      const color1 = colorScale(5);
      const color2 = colorScale(5);
      expect(color1).toBe(color2);
    });
  });
});

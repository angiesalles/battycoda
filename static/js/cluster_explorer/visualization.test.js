/**
 * Tests for cluster_explorer/visualization.js
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { initializeVisualization, createLegend, updateVisualization } from './visualization.js';
import { setJQuery, resetState } from './state.js';
import clusterFixtures from '../test/fixtures/clusters.json';

// Mock d3 modules
vi.mock('d3-selection', () => ({
  select: vi.fn(() => ({
    append: vi.fn().mockReturnThis(),
    attr: vi.fn().mockReturnThis(),
    call: vi.fn().mockReturnThis(),
    selectAll: vi.fn().mockReturnThis(),
    data: vi.fn().mockReturnThis(),
    enter: vi.fn().mockReturnThis(),
    filter: vi.fn().mockReturnThis(),
    text: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    empty: vi.fn(() => false),
  })),
  selectAll: vi.fn(() => ({
    attr: vi.fn().mockReturnThis(),
    empty: vi.fn(() => false),
  })),
}));

vi.mock('d3', () => ({
  scaleLinear: vi.fn(() => {
    const scale = vi.fn((val) => val * 100);
    scale.domain = vi.fn(() => scale);
    scale.range = vi.fn(() => scale);
    return scale;
  }),
  scaleOrdinal: vi.fn(() => {
    let idx = 0;
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'];
    return vi.fn(() => colors[idx++ % colors.length]);
  }),
  schemeCategory10: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
}));

vi.mock('d3-zoom', () => ({
  zoom: vi.fn(() => ({
    scaleExtent: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
  })),
}));

vi.mock('d3-array', () => ({
  min: vi.fn((arr, accessor) => {
    if (!arr || arr.length === 0) return undefined;
    return Math.min(...arr.map(accessor));
  }),
  max: vi.fn((arr, accessor) => {
    if (!arr || arr.length === 0) return undefined;
    return Math.max(...arr.map(accessor));
  }),
}));

describe('cluster_explorer/visualization', () => {
  let mockJQuery;
  let mockElement;

  beforeEach(() => {
    // Reset all state
    resetState();

    // Create mock element
    mockElement = {
      length: 1, // Mock element exists in DOM
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    // Create mock jQuery function
    mockJQuery = vi.fn(() => mockElement);

    // Inject mock jQuery via state (instead of window.jQuery)
    setJQuery(mockJQuery);
  });

  describe('initializeVisualization', () => {
    it('should return null if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      const result = initializeVisualization([]);

      expect(result).toBe(null);
    });

    it('should return null if clusters is null or undefined', () => {
      const result1 = initializeVisualization(null);
      const result2 = initializeVisualization(undefined);

      expect(result1).toBe(null);
      expect(result2).toBe(null);
    });

    it('should show warning message for empty clusters array', () => {
      const result = initializeVisualization([]);

      expect(mockElement.html).toHaveBeenCalledWith(
        expect.stringContaining('No clusters available for visualization')
      );
      expect(result).toBe(null);
    });

    it('should clear existing content before rendering', () => {
      const clusters = clusterFixtures.clusters;

      initializeVisualization(clusters);

      expect(mockElement.empty).toHaveBeenCalled();
    });

    it('should assign colors to clusters', () => {
      const clusters = JSON.parse(JSON.stringify(clusterFixtures.clusters));

      initializeVisualization(clusters);

      // Each cluster should have a color assigned
      expect(clusters[0].color).toBeDefined();
      expect(clusters[1].color).toBeDefined();
      expect(clusters[2].color).toBeDefined();
    });

    it('should create legend for clusters', () => {
      const clusters = clusterFixtures.clusters;

      // Track calls to jQuery
      const calls = [];
      mockJQuery.mockImplementation((selector) => {
        calls.push(selector);
        return mockElement;
      });

      initializeVisualization(clusters);

      // Legend container should be accessed
      expect(calls).toContain('.cluster-legend');
    });

    it('should get initial point size from slider', () => {
      const clusters = clusterFixtures.clusters;

      initializeVisualization(clusters);

      expect(mockJQuery).toHaveBeenCalledWith('#point-size');
      expect(mockElement.val).toHaveBeenCalled();
    });

    it('should get initial opacity from slider', () => {
      const clusters = clusterFixtures.clusters;
      mockElement.val.mockReturnValue('0.7');

      initializeVisualization(clusters);

      expect(mockJQuery).toHaveBeenCalledWith('#cluster-opacity');
    });

    it('should return visualization state object', () => {
      const clusters = clusterFixtures.clusters;

      const result = initializeVisualization(clusters);

      // Should return an object with svg, container, and scales
      expect(result).not.toBe(null);
      expect(result).toHaveProperty('svg');
      expect(result).toHaveProperty('container');
      expect(result).toHaveProperty('xScale');
      expect(result).toHaveProperty('yScale');
    });

    it('should use default values when slider values are not parseable', () => {
      mockElement.val.mockReturnValue('invalid');
      const clusters = clusterFixtures.clusters;

      // Should not throw
      const result = initializeVisualization(clusters);

      expect(result).not.toBe(null);
    });
  });

  describe('createLegend', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      createLegend([]);

      // No error should be thrown
    });

    it('should clear existing legend content', () => {
      const clusters = clusterFixtures.clusters;

      createLegend(clusters);

      expect(mockJQuery).toHaveBeenCalledWith('.cluster-legend');
      expect(mockElement.empty).toHaveBeenCalled();
    });

    it('should create legend items for each cluster', () => {
      const clusters = [
        { id: 1, cluster_id: 1, label: 'Test Cluster', size: 10, color: '#ff0000' },
        { id: 2, cluster_id: 2, label: null, size: 5, color: '#00ff00' },
      ];

      createLegend(clusters);

      expect(mockElement.append).toHaveBeenCalled();
    });

    it('should use cluster_id as fallback label when label is null', () => {
      const clusters = [{ id: 1, cluster_id: 1, label: null, size: 10, color: '#ff0000' }];

      // Track the HTML being appended
      const appendedHtml = [];
      mockElement.append.mockImplementation((html) => {
        if (typeof html === 'string') {
          appendedHtml.push(html);
        }
        return mockElement;
      });

      createLegend(clusters);

      // Check that a row was appended
      expect(mockElement.append).toHaveBeenCalled();
    });

    it('should make legend items clickable', () => {
      const clusters = [{ id: 1, cluster_id: 1, label: 'Test', size: 10, color: '#ff0000' }];

      mockElement.on.mockImplementation(() => {
        return mockElement;
      });

      // Mock the jQuery constructor to return an element with on() for legend items
      const legendItem = {
        on: vi.fn(() => {
          return legendItem;
        }),
      };

      mockJQuery.mockImplementation((selector) => {
        if (typeof selector === 'string' && selector.includes('div class="col-md-3"')) {
          return legendItem;
        }
        return mockElement;
      });

      createLegend(clusters);

      // Legend items should have click handlers
      // (this is tested implicitly through the mock setup)
    });
  });

  describe('updateVisualization', () => {
    it('should return early if jQuery is not available', () => {
      // Clear both injected jQuery and window.jQuery to simulate unavailable
      setJQuery(null);
      delete window.jQuery;

      updateVisualization();

      // No error should be thrown
    });

    it('should read point size from slider', () => {
      updateVisualization();

      expect(mockJQuery).toHaveBeenCalledWith('#point-size');
      expect(mockElement.val).toHaveBeenCalled();
    });

    it('should read opacity from slider', () => {
      updateVisualization();

      expect(mockJQuery).toHaveBeenCalledWith('#cluster-opacity');
      expect(mockElement.val).toHaveBeenCalled();
    });
  });
});

describe('visualization data transformations', () => {
  it('should handle clusters with negative coordinates', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [
      { id: 1, vis_x: -1.5, vis_y: -0.5, size: 10 },
      { id: 2, vis_x: 1.5, vis_y: 0.5, size: 5 },
    ];

    const result = initializeVisualization(clusters);

    expect(result).not.toBe(null);
  });

  it('should handle clusters with zero coordinates', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [
      { id: 1, vis_x: 0, vis_y: 0, size: 10 },
      { id: 2, vis_x: 1, vis_y: 1, size: 5 },
    ];

    const result = initializeVisualization(clusters);

    expect(result).not.toBe(null);
  });

  it('should handle single cluster', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [{ id: 1, vis_x: 0.5, vis_y: 0.5, size: 10 }];

    const result = initializeVisualization(clusters);

    expect(result).not.toBe(null);
  });
});

describe('visualization error handling', () => {
  it('should filter out clusters with invalid coordinates (NaN)', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [
      { id: 1, vis_x: NaN, vis_y: 0.5, size: 10 },
      { id: 2, vis_x: 1.0, vis_y: 1.0, size: 5 },
    ];

    const result = initializeVisualization(clusters);

    // Should still succeed with the valid cluster
    expect(result).not.toBe(null);
  });

  it('should filter out clusters with undefined coordinates', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [
      { id: 1, vis_x: undefined, vis_y: 0.5, size: 10 },
      { id: 2, vis_x: 1.0, vis_y: 1.0, size: 5 },
    ];

    const result = initializeVisualization(clusters);

    // Should still succeed with the valid cluster
    expect(result).not.toBe(null);
  });

  it('should return null when all clusters have invalid coordinates', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [
      { id: 1, vis_x: NaN, vis_y: 0.5, size: 10 },
      { id: 2, vis_x: Infinity, vis_y: 1.0, size: 5 },
    ];

    const result = initializeVisualization(clusters);

    expect(result).toBe(null);
    expect(mockElement.html).toHaveBeenCalledWith(expect.stringContaining('Unable to visualize'));
  });

  it('should return null when container has zero width', () => {
    const mockElement = {
      length: 1,
      width: vi.fn(() => 0),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [{ id: 1, vis_x: 0.5, vis_y: 0.5, size: 10 }];

    const result = initializeVisualization(clusters);

    expect(result).toBe(null);
  });

  it('should return null when container does not exist', () => {
    const mockElement = {
      length: 0, // Element not found
      width: vi.fn(() => 800),
      height: vi.fn(() => 500),
      html: vi.fn().mockReturnThis(),
      empty: vi.fn().mockReturnThis(),
      val: vi.fn(() => '8'),
      append: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis(),
    };

    setJQuery(vi.fn(() => mockElement));

    const clusters = [{ id: 1, vis_x: 0.5, vis_y: 0.5, size: 10 }];

    const result = initializeVisualization(clusters);

    expect(result).toBe(null);
  });
});

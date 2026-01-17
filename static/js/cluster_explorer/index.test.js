/**
 * Tests for cluster_explorer/index.js
 *
 * Tests the main entry point and initialization of the cluster explorer module.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { resetState, setJQuery, getClusters, getIsProjectScope } from './state.js';

// Mock the imported modules
vi.mock('./visualization.js', () => ({
  initializeVisualization: vi.fn(),
  createLegend: vi.fn(),
  updateVisualization: vi.fn(),
}));

vi.mock('./interactions.js', () => ({
  selectCluster: vi.fn(),
  loadClusterDetails: vi.fn(),
  loadClusterMembers: vi.fn(),
}));

vi.mock('./controls.js', () => ({
  loadSegmentDetails: vi.fn(),
  initializeControls: vi.fn(),
}));

vi.mock('./data_loader.js', () => ({
  saveClusterLabel: vi.fn(),
}));

// Import after mocking
import { initClusterExplorer } from './index.js';
import { initializeVisualization } from './visualization.js';
import { selectCluster } from './interactions.js';
import { initializeControls, loadSegmentDetails } from './controls.js';
import { saveClusterLabel } from './data_loader.js';

describe('cluster_explorer/index', () => {
  let mockJQuery;
  let mockElement;
  let eventHandlers;
  let documentEventHandlers;
  let consoleErrorSpy;
  let consoleWarnSpy;

  beforeEach(() => {
    // Reset all state
    resetState();
    eventHandlers = {};
    documentEventHandlers = {};

    // Clear mocks
    vi.clearAllMocks();

    // Create mock element for jQuery selectors
    mockElement = {
      off: vi.fn().mockReturnThis(),
      on: vi.fn((event, selectorOrHandler, handler) => {
        if (typeof selectorOrHandler === 'string') {
          // Delegated event: $(document).on('click', '.selector', handler)
          documentEventHandlers[`${event}:${selectorOrHandler}`] = handler;
        } else {
          // Direct event: $(element).on('click', handler)
          eventHandlers[event] = selectorOrHandler;
        }
        return mockElement;
      }),
      data: vi.fn((key) => (key === 'segment-id' ? 123 : null)),
    };

    // Create mock jQuery function
    mockJQuery = vi.fn((selector) => {
      if (selector === document) {
        return {
          off: vi.fn().mockReturnThis(),
          on: vi.fn((event, selectorStr, handler) => {
            documentEventHandlers[`${event}:${selectorStr}`] = handler;
            return mockElement;
          }),
        };
      }
      return mockElement;
    });

    // Spy on console methods
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    // Clean up window globals
    delete window.jQuery;

    // Clean up any DOM config elements from previous tests
    const existingConfig = document.getElementById('cluster-explorer-config');
    if (existingConfig) {
      existingConfig.remove();
    }
    const existingData = document.getElementById('cluster-data');
    if (existingData) {
      existingData.remove();
    }
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });

  describe('initClusterExplorer', () => {
    it('should return early and log error when jQuery is not available', () => {
      // Ensure jQuery is not available
      setJQuery(null);
      delete window.jQuery;

      const clusters = [{ id: 1, label: 'Cluster 1' }];
      initClusterExplorer(clusters);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClusterExplorer] jQuery is not available. Cannot initialize cluster explorer.'
      );
      expect(initializeVisualization).not.toHaveBeenCalled();
    });

    it('should return early and log error when clusters is not provided', () => {
      setJQuery(mockJQuery);

      initClusterExplorer(null);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClusterExplorer] No clusters data provided. Cannot initialize cluster explorer.'
      );
      expect(initializeVisualization).not.toHaveBeenCalled();
    });

    it('should return early when clusters is undefined', () => {
      setJQuery(mockJQuery);

      initClusterExplorer(undefined);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ClusterExplorer] No clusters data provided. Cannot initialize cluster explorer.'
      );
      expect(initializeVisualization).not.toHaveBeenCalled();
    });

    it('should initialize with valid clusters and jQuery', () => {
      setJQuery(mockJQuery);
      const clusters = [
        { id: 1, label: 'Cluster 1', vis_x: 0, vis_y: 0 },
        { id: 2, label: 'Cluster 2', vis_x: 1, vis_y: 1 },
      ];

      initClusterExplorer(clusters);

      expect(initializeVisualization).toHaveBeenCalledWith(clusters);
      expect(initializeControls).toHaveBeenCalled();
    });

    it('should store clusters in state module', () => {
      setJQuery(mockJQuery);
      const clusters = [{ id: 1, label: 'Cluster 1' }];

      initClusterExplorer(clusters);

      expect(getClusters()).toBe(clusters);
    });

    it('should use options.jQuery when provided (dependency injection)', () => {
      // Do not set jQuery in state
      setJQuery(null);
      delete window.jQuery;

      const injectedJQuery = vi.fn(() => mockElement);
      const clusters = [{ id: 1, label: 'Cluster 1' }];

      initClusterExplorer(clusters, { jQuery: injectedJQuery });

      // Should not error because jQuery was injected
      expect(consoleErrorSpy).not.toHaveBeenCalledWith(
        '[ClusterExplorer] jQuery is not available. Cannot initialize cluster explorer.'
      );
      expect(initializeVisualization).toHaveBeenCalledWith(clusters);
    });

    it('should use options.isProjectScope when provided', () => {
      setJQuery(mockJQuery);
      const clusters = [{ id: 1, label: 'Cluster 1' }];

      initClusterExplorer(clusters, { isProjectScope: true });

      expect(getIsProjectScope()).toBe(true);
    });

    it('should set isProjectScope to false when option is explicitly false', () => {
      setJQuery(mockJQuery);
      // Create DOM config element with true value
      const configEl = document.createElement('div');
      configEl.id = 'cluster-explorer-config';
      configEl.dataset.isProjectScope = 'true';
      document.body.appendChild(configEl);

      const clusters = [{ id: 1, label: 'Cluster 1' }];

      // Options should override DOM config
      initClusterExplorer(clusters, { isProjectScope: false });

      expect(getIsProjectScope()).toBe(false);

      // Cleanup
      document.body.removeChild(configEl);
    });

    it('should fall back to DOM config element when options.isProjectScope is undefined', () => {
      setJQuery(mockJQuery);
      // Create DOM config element
      const configEl = document.createElement('div');
      configEl.id = 'cluster-explorer-config';
      configEl.dataset.isProjectScope = 'true';
      document.body.appendChild(configEl);

      const clusters = [{ id: 1, label: 'Cluster 1' }];

      initClusterExplorer(clusters, {});

      expect(getIsProjectScope()).toBe(true);

      // Cleanup
      document.body.removeChild(configEl);
    });

    it('should default isProjectScope to false when not provided anywhere', () => {
      setJQuery(mockJQuery);
      // No DOM config element, no options
      const clusters = [{ id: 1, label: 'Cluster 1' }];

      initClusterExplorer(clusters);

      expect(getIsProjectScope()).toBe(false);
    });

    it('should remove existing event handlers before adding new ones', () => {
      setJQuery(mockJQuery);
      const clusters = [{ id: 1 }];

      initClusterExplorer(clusters);

      // Check that off() was called for both selectors
      expect(mockElement.off).toHaveBeenCalledWith('click');
    });

    it('should set up save button click handler', () => {
      setJQuery(mockJQuery);
      const clusters = [{ id: 1 }];

      initClusterExplorer(clusters);

      // Verify save button handler was set up
      expect(mockJQuery).toHaveBeenCalledWith('#save-cluster-label');
      expect(mockElement.on).toHaveBeenCalledWith('click', expect.any(Function));
    });

    it('should call saveClusterLabel when save button is clicked', () => {
      setJQuery(mockJQuery);
      const clusters = [{ id: 1 }];

      initClusterExplorer(clusters);

      // Trigger the click handler
      const clickHandler = eventHandlers['click'];
      expect(clickHandler).toBeDefined();
      clickHandler();

      expect(saveClusterLabel).toHaveBeenCalledWith(expect.any(Function));
    });

    it('should set up delegated click handler for view segment buttons', () => {
      const docElement = {
        off: vi.fn().mockReturnThis(),
        on: vi.fn((event, selector, handler) => {
          documentEventHandlers[`${event}:${selector}`] = handler;
          return docElement;
        }),
      };

      mockJQuery = vi.fn((selector) => {
        if (selector === document) {
          return docElement;
        }
        return mockElement;
      });
      setJQuery(mockJQuery);

      const clusters = [{ id: 1 }];
      initClusterExplorer(clusters);

      expect(mockJQuery).toHaveBeenCalledWith(document);
      expect(docElement.on).toHaveBeenCalledWith('click', '.view-segment-btn', expect.any(Function));
    });

    it('should load segment details when view segment button is clicked', () => {
      const mockButtonElement = {
        data: vi.fn((key) => (key === 'segment-id' ? 456 : null)),
      };

      const docElement = {
        off: vi.fn().mockReturnThis(),
        on: vi.fn((event, selector, handler) => {
          documentEventHandlers[`${event}:${selector}`] = handler;
          return docElement;
        }),
      };

      mockJQuery = vi.fn((selector) => {
        if (selector === document) {
          return docElement;
        }
        return mockElement;
      });
      setJQuery(mockJQuery);

      const clusters = [{ id: 1 }];
      initClusterExplorer(clusters);

      // Simulate clicking a view segment button
      const clickHandler = documentEventHandlers['click:.view-segment-btn'];
      expect(clickHandler).toBeDefined();

      // Call the handler with mocked `this` context
      mockJQuery.mockReturnValueOnce(mockButtonElement);
      clickHandler.call(mockButtonElement);

      expect(loadSegmentDetails).toHaveBeenCalledWith(456);
    });

    it('should work with empty clusters array', () => {
      setJQuery(mockJQuery);
      const clusters = [];

      initClusterExplorer(clusters);

      expect(initializeVisualization).toHaveBeenCalledWith(clusters);
      expect(getClusters()).toEqual([]);
    });
  });

  describe('saveClusterLabel callback', () => {
    it('should re-initialize visualization and re-select cluster on successful save', () => {
      setJQuery(mockJQuery);
      const clusters = [{ id: 42, label: 'Test Cluster' }];

      initClusterExplorer(clusters);

      // Trigger the click handler that was set up for the save button
      const clickHandler = eventHandlers['click'];
      expect(clickHandler).toBeDefined();
      clickHandler();

      // Now saveClusterLabel should have been called with a callback function
      expect(saveClusterLabel).toHaveBeenCalledWith(expect.any(Function));
      const saveCallback = saveClusterLabel.mock.calls[0][0];
      expect(saveCallback).toBeDefined();

      // Clear only visualization and selectCluster mocks to verify they're called again
      initializeVisualization.mockClear();
      selectCluster.mockClear();

      // Call the callback with a cluster ID (simulating successful save)
      saveCallback(42);

      expect(initializeVisualization).toHaveBeenCalledWith(clusters);
      expect(selectCluster).toHaveBeenCalledWith(42);
    });
  });

  describe('module exports', () => {
    it('should export state functions', async () => {
      const module = await import('./index.js');
      expect(module.getSelectedClusterId).toBeDefined();
      expect(module.setSelectedClusterId).toBeDefined();
      expect(module.getClusters).toBeDefined();
      expect(module.setClusters).toBeDefined();
      expect(module.getIsProjectScope).toBeDefined();
      expect(module.setIsProjectScope).toBeDefined();
      expect(module.getJQuery).toBeDefined();
      expect(module.setJQuery).toBeDefined();
    });

    it('should export visualization functions', async () => {
      const module = await import('./index.js');
      expect(module.initializeVisualization).toBeDefined();
      expect(module.createLegend).toBeDefined();
      expect(module.updateVisualization).toBeDefined();
    });

    it('should export interaction functions', async () => {
      const module = await import('./index.js');
      expect(module.selectCluster).toBeDefined();
      expect(module.loadClusterDetails).toBeDefined();
      expect(module.loadClusterMembers).toBeDefined();
    });

    it('should export control functions', async () => {
      const module = await import('./index.js');
      expect(module.loadSegmentDetails).toBeDefined();
    });

    it('should export data loader functions', async () => {
      const module = await import('./index.js');
      expect(module.saveClusterLabel).toBeDefined();
    });

    it('should export initClusterExplorer', async () => {
      const module = await import('./index.js');
      expect(module.initClusterExplorer).toBeDefined();
    });
  });
});

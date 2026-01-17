/**
 * Cluster Explorer Visualization Module
 *
 * Implements interactive visualization of audio clusters using D3.js.
 * D3 is now bundled via npm for tree-shaking benefits.
 */

import { select, selectAll } from 'd3-selection';
import { scaleLinear, scaleOrdinal, schemeCategory10 } from 'd3';
import { zoom } from 'd3-zoom';
import { min, max } from 'd3-array';

import { colorScale } from './state.js';
import { selectCluster } from './interactions.js';
import { escapeHtml } from '../utils/html.js';

/**
 * Initialize the cluster visualization
 * @param {Array} clusters - Array of cluster data from the server
 * @returns {Object|null} Visualization state or null if no clusters
 */
export function initializeVisualization(clusters) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot initialize visualization.');
    return null;
  }
  if (!clusters) {
    console.error('[ClusterExplorer] No clusters data provided. Cannot initialize visualization.');
    return null;
  }

  // If there are no clusters, show a message
  if (clusters.length === 0) {
    $('#cluster-visualization').html(
      '<div class="alert alert-warning">No clusters available for visualization</div>'
    );
    return null;
  }

  // Validate cluster data has required visualization coordinates
  const validClusters = clusters.filter((cluster) => {
    const hasValidCoords =
      typeof cluster.vis_x === 'number' &&
      typeof cluster.vis_y === 'number' &&
      !isNaN(cluster.vis_x) &&
      !isNaN(cluster.vis_y) &&
      isFinite(cluster.vis_x) &&
      isFinite(cluster.vis_y);
    if (!hasValidCoords) {
      console.warn(
        `[ClusterExplorer] Cluster ${cluster.id || cluster.cluster_id} has invalid coordinates (vis_x: ${cluster.vis_x}, vis_y: ${cluster.vis_y}). Skipping.`
      );
    }
    return hasValidCoords;
  });

  if (validClusters.length === 0) {
    console.error('[ClusterExplorer] No clusters with valid visualization coordinates found.');
    $('#cluster-visualization').html(
      '<div class="alert alert-danger">Unable to visualize clusters: No valid coordinate data available.</div>'
    );
    return null;
  }

  if (validClusters.length < clusters.length) {
    console.warn(
      `[ClusterExplorer] ${clusters.length - validClusters.length} clusters with invalid coordinates were excluded from visualization.`
    );
  }

  // Check if visualization container exists
  const vizContainer = $('#cluster-visualization');
  if (vizContainer.length === 0) {
    console.error('[ClusterExplorer] Visualization container #cluster-visualization not found in DOM.');
    return null;
  }

  // Configure the visualization
  const width = vizContainer.width();
  if (!width || width <= 0) {
    console.error('[ClusterExplorer] Visualization container has zero or invalid width.');
    return null;
  }
  const height = 500;
  const margin = { top: 20, right: 20, bottom: 20, left: 20 };

  // Clear any existing content
  vizContainer.empty();

  // Create the SVG container with error handling
  let svg;
  try {
    const selection = select('#cluster-visualization');
    if (selection.empty()) {
      console.error('[ClusterExplorer] D3 selection for #cluster-visualization is empty.');
      return null;
    }
    svg = selection.append('svg').attr('width', width).attr('height', height);
  } catch (error) {
    console.error('[ClusterExplorer] Failed to create SVG container:', error);
    vizContainer.html('<div class="alert alert-danger">Failed to initialize visualization.</div>');
    return null;
  }

  // Create a container group for zooming
  const container = svg.append('g').attr('class', 'container');

  // Add zoom behavior with error handling
  try {
    const zoomBehavior = zoom()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoomBehavior);
  } catch (error) {
    console.error('[ClusterExplorer] Failed to set up zoom behavior:', error);
    // Continue without zoom - visualization is still usable
  }

  // Get initial control values
  const pointSize = parseInt($('#point-size').val()) || 8;
  const opacity = parseFloat($('#cluster-opacity').val()) || 0.7;

  // Assign colors to clusters (use validClusters from now on)
  const scale = colorScale || scaleOrdinal(schemeCategory10);
  validClusters.forEach((cluster, i) => {
    cluster.color = scale(i);
  });

  // Find the data range for x and y coordinates
  let xMin = min(validClusters, (d) => d.vis_x);
  let xMax = max(validClusters, (d) => d.vis_x);
  let yMin = min(validClusters, (d) => d.vis_y);
  let yMax = max(validClusters, (d) => d.vis_y);

  // Validate that we have valid min/max values
  if (xMin === undefined || xMax === undefined || yMin === undefined || yMax === undefined) {
    console.error('[ClusterExplorer] Failed to calculate data range from cluster coordinates.');
    vizContainer.html(
      '<div class="alert alert-danger">Failed to calculate visualization bounds.</div>'
    );
    return null;
  }

  // Handle edge case where all points have the same coordinates
  if (xMin === xMax) {
    xMin -= 1;
    xMax += 1;
  }
  if (yMin === yMax) {
    yMin -= 1;
    yMax += 1;
  }

  // Add some padding
  const padding = 0.1;
  const xRange = xMax - xMin;
  const yRange = yMax - yMin;
  xMin -= xRange * padding;
  xMax += xRange * padding;
  yMin -= yRange * padding;
  yMax += yRange * padding;

  // Create scales
  const xScale = scaleLinear()
    .domain([xMin, xMax])
    .range([margin.left, width - margin.right]);

  const yScale = scaleLinear()
    .domain([yMin, yMax])
    .range([height - margin.bottom, margin.top]);

  // Draw the cluster points with error handling
  try {
    container
      .selectAll('.cluster-point')
      .data(validClusters)
      .enter()
      .append('circle')
      .attr('class', 'cluster-point')
      .attr('cx', (d) => xScale(d.vis_x))
      .attr('cy', (d) => yScale(d.vis_y))
      .attr('r', pointSize)
      .attr('fill', (d) => d.color)
      .attr('opacity', opacity)
      .attr('stroke', '#000')
      .attr('stroke-width', 1)
      .attr('cursor', 'pointer')
      .on('mouseover', function (event, d) {
        select(this).attr('stroke-width', 2).attr('stroke', '#000');

        container
          .append('text')
          .attr('class', 'tooltip')
          .attr('x', xScale(d.vis_x) + 10)
          .attr('y', yScale(d.vis_y) - 10)
          .text(d.label || `Cluster ${d.cluster_id}`)
          .attr('fill', '#000')
          .attr('font-weight', 'bold');
      })
      .on('mouseout', function () {
        select(this).attr('stroke-width', 1);
        container.selectAll('.tooltip').remove();
      })
      .on('click', function (event, d) {
        selectCluster(d.id);
      });

    // Add cluster labels for labeled clusters
    container
      .selectAll('.cluster-label')
      .data(validClusters.filter((c) => c.is_labeled))
      .enter()
      .append('text')
      .attr('class', 'cluster-label')
      .attr('x', (d) => xScale(d.vis_x) + 10)
      .attr('y', (d) => yScale(d.vis_y) + 3)
      .text((d) => d.label)
      .attr('fill', '#000')
      .attr('font-size', '10px');
  } catch (error) {
    console.error('[ClusterExplorer] Failed to draw cluster points:', error);
    vizContainer.html('<div class="alert alert-danger">Failed to render cluster visualization.</div>');
    return null;
  }

  // Create the legend
  createLegend(validClusters);

  return { svg, container, xScale, yScale };
}

/**
 * Create a legend for the cluster visualization
 * @param {Array} clusters - Array of cluster data
 */
export function createLegend(clusters) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot create legend.');
    return;
  }

  const legendDiv = $('.cluster-legend');
  legendDiv.empty();

  const legendHtml = $('<div class="row"></div>');

  clusters.forEach((cluster) => {
    const clusterLabel = cluster.label || `Cluster ${cluster.cluster_id}`;
    const legendItem = $(`
            <div class="col-md-3 mb-2">
                <div class="d-flex align-items-center" style="cursor: pointer;">
                    <div style="width: 15px; height: 15px; background-color: ${escapeHtml(cluster.color)}; margin-right: 5px;"></div>
                    <small>${escapeHtml(clusterLabel)} (${cluster.size})</small>
                </div>
            </div>
        `);

    legendItem.on('click', () => {
      selectCluster(cluster.id);
    });

    legendHtml.append(legendItem);
  });

  legendDiv.append(legendHtml);
}

/**
 * Update the visualization based on control settings
 */
export function updateVisualization() {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot update visualization.');
    return;
  }

  const pointSize = parseInt($('#point-size').val()) || 8;
  const opacity = parseFloat($('#cluster-opacity').val()) || 0.7;

  const points = selectAll('.cluster-point');
  if (points.empty()) {
    console.warn('[ClusterExplorer] No cluster points found to update.');
    return;
  }

  try {
    points.attr('r', pointSize).attr('opacity', opacity);
  } catch (error) {
    console.error('[ClusterExplorer] Failed to update cluster point attributes:', error);
  }
}

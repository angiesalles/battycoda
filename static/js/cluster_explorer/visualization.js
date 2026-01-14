/**
 * Cluster Explorer Visualization Module
 *
 * Implements interactive visualization of audio clusters using D3.js.
 */

import { colorScale } from './state.js';
import { selectCluster } from './interactions.js';

/**
 * Initialize the cluster visualization
 * @param {Array} clusters - Array of cluster data from the server
 * @returns {Object|null} Visualization state or null if no clusters
 */
export function initializeVisualization(clusters) {
    const $ = window.jQuery;
    const d3 = window.d3;
    if (!$ || !d3 || !clusters) return null;

    // If there are no clusters, show a message
    if (clusters.length === 0) {
        $('#cluster-visualization').html(
            '<div class="alert alert-warning">No clusters available for visualization</div>'
        );
        return null;
    }

    // Configure the visualization
    const width = $('#cluster-visualization').width();
    const height = 500;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    // Clear any existing content
    $('#cluster-visualization').empty();

    // Create the SVG container
    const svg = d3
        .select('#cluster-visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create a container group for zooming
    const container = svg.append('g').attr('class', 'container');

    // Add zoom behavior
    const zoom = d3
        .zoom()
        .scaleExtent([0.5, 5])
        .on('zoom', (event) => {
            container.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Get initial control values
    const pointSize = parseInt($('#point-size').val()) || 8;
    const opacity = parseFloat($('#cluster-opacity').val()) || 0.7;

    // Assign colors to clusters
    const scale = colorScale || d3.scaleOrdinal(d3.schemeCategory10);
    clusters.forEach((cluster, i) => {
        cluster.color = scale(i);
    });

    // Find the data range for x and y coordinates
    let xMin = d3.min(clusters, (d) => d.vis_x);
    let xMax = d3.max(clusters, (d) => d.vis_x);
    let yMin = d3.min(clusters, (d) => d.vis_y);
    let yMax = d3.max(clusters, (d) => d.vis_y);

    // Add some padding
    const padding = 0.1;
    const xRange = xMax - xMin;
    const yRange = yMax - yMin;
    xMin -= xRange * padding;
    xMax += xRange * padding;
    yMin -= yRange * padding;
    yMax += yRange * padding;

    // Create scales
    const xScale = d3
        .scaleLinear()
        .domain([xMin, xMax])
        .range([margin.left, width - margin.right]);

    const yScale = d3
        .scaleLinear()
        .domain([yMin, yMax])
        .range([height - margin.bottom, margin.top]);

    // Draw the cluster points
    container
        .selectAll('.cluster-point')
        .data(clusters)
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
            d3.select(this).attr('stroke-width', 2).attr('stroke', '#000');

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
            d3.select(this).attr('stroke-width', 1);
            container.selectAll('.tooltip').remove();
        })
        .on('click', function (event, d) {
            selectCluster(d.id);
        });

    // Add cluster labels for labeled clusters
    container
        .selectAll('.cluster-label')
        .data(clusters.filter((c) => c.is_labeled))
        .enter()
        .append('text')
        .attr('class', 'cluster-label')
        .attr('x', (d) => xScale(d.vis_x) + 10)
        .attr('y', (d) => yScale(d.vis_y) + 3)
        .text((d) => d.label)
        .attr('fill', '#000')
        .attr('font-size', '10px');

    // Create the legend
    createLegend(clusters);

    return { svg, container, xScale, yScale };
}

/**
 * Create a legend for the cluster visualization
 * @param {Array} clusters - Array of cluster data
 */
export function createLegend(clusters) {
    const $ = window.jQuery;
    if (!$) return;

    const legendDiv = $('.cluster-legend');
    legendDiv.empty();

    const legendHtml = $('<div class="row"></div>');

    clusters.forEach((cluster) => {
        const clusterLabel = cluster.label || `Cluster ${cluster.cluster_id}`;
        const legendItem = $(`
            <div class="col-md-3 mb-2">
                <div class="d-flex align-items-center" style="cursor: pointer;">
                    <div style="width: 15px; height: 15px; background-color: ${cluster.color}; margin-right: 5px;"></div>
                    <small>${clusterLabel} (${cluster.size})</small>
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
    const d3 = window.d3;
    if (!$ || !d3) return;

    const pointSize = parseInt($('#point-size').val());
    const opacity = parseFloat($('#cluster-opacity').val());

    d3.selectAll('.cluster-point').attr('r', pointSize).attr('opacity', opacity);
}

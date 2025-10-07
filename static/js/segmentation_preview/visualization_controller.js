// Visualization controller - orchestration
// References: rendering.js, state.js, events.js
/**
 * Visualization Controller
 * Manages the main drawing logic and delegates to specific visualization types
 */

import { drawSpectrogram } from './spectrogram_drawing.js';
import { drawWaveform } from './waveform_drawing.js';
import { drawSegmentMarkers, drawTimeLabels } from './drawing_utilities.js';
import { setupViewToggle } from './spectrogram_display.js';

export function drawPreviewVisualization(canvas, data) {
    const visualizationType = window.currentVisualizationType || 'spectrogram';
    console.log('Drawing preview visualization:', visualizationType);
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    console.log('Canvas context and dimensions:', ctx, width, height);
    
    // Clear the canvas
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, width, height);
    console.log('Canvas cleared');
    
    // Use proper spectrogram with frequency axes if available
    if (visualizationType === 'spectrogram' && data.spectrogram_url) {
        console.log('Using spectrogram with frequency axes from:', data.spectrogram_url);
        drawSpectrogramWithAxes(canvas, data);
    } else if (visualizationType === 'spectrogram') {
        console.log('Spectrogram is being generated, showing status...');
        drawGeneratingStatus(canvas, data);
    } else {
        console.log('Using simulated waveform visualization');
        drawSimulatedVisualization(canvas, data, visualizationType);
    }
    
    console.log('Visualization drawing completed');
}

// Real audio processing is no longer needed - spectrograms are generated server-side

function drawSimulatedVisualization(canvas, data, visualizationType) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    console.log('Drawing simulated', visualizationType, 'with dimensions:', width, 'x', height);
    
    if (visualizationType === 'spectrogram') {
        drawSpectrogram(ctx, null, null, width, height, true); // true = simulated
        drawSegmentMarkers(ctx, data, width, height, 0);
    } else {
        drawWaveform(ctx, data, width, height, true); // true = simulated
        const centerY = height / 2;
        drawSegmentMarkers(ctx, data, width, height, centerY);
    }
    
    drawTimeLabels(ctx, data, width, height);
}

function drawSpectrogramWithAxes(canvas, data) {
    // Replace canvas with proper spectrogram display with frequency axes
    const container = canvas.parentNode;
    
    // Clear the container and replace with spectrogram grid
    container.innerHTML = '';
    
    // Create the spectrogram with axes using the dedicated module
    createSpectrogramGrid(container, data);
}

function createSpectrogramGrid(container, data) {
    // Import the functionality from spectrogram_display.js
    // This creates the full grid with frequency and time axes
    
    // Create grid container for spectrogram with axes
    const gridContainer = document.createElement('div');
    gridContainer.className = 'spectrogram-preview-grid';
    gridContainer.style.cssText = `
        display: grid;
        grid-template-columns: 60px 1fr;
        grid-template-rows: 1fr 40px;
        grid-template-areas: 
            "freq-axis spectrogram"
            "corner time-axis";
        height: 300px;
        width: 100%;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        background-color: #f8f9fa;
    `;
    
    // Create frequency axis with ticks
    const freqAxis = createFrequencyAxis();
    const spectrogramContainer = createSpectrogramContainer(data);
    const timeAxis = createTimeAxis(data);
    const corner = createCorner();
    
    // Assemble the grid
    gridContainer.appendChild(freqAxis);
    gridContainer.appendChild(spectrogramContainer);
    gridContainer.appendChild(timeAxis);
    gridContainer.appendChild(corner);
    
    container.appendChild(gridContainer);
    
    // Add frequency axis label
    addFrequencyLabel(container);
}

function createFrequencyAxis() {
    const freqAxis = document.createElement('div');
    freqAxis.style.cssText = `
        grid-area: freq-axis;
        position: relative;
        border-right: 2px solid #333;
        background-color: #f8f9fa;
        padding: 5px 0;
    `;
    
    // Calculate mel scale positions for frequency ticks
    const maxFreq = 100000; // 100 kHz max frequency
    const freqTicksHz = [100000, 80000, 60000, 40000, 20000, 10000, 5000, 0]; // Hz
    
    // Convert frequencies to mel scale and calculate positions
    function hzToMel(freq) {
        return 2595 * Math.log10(1 + freq / 700);
    }
    
    const maxMel = hzToMel(maxFreq);
    
    freqTicksHz.forEach((freq) => {
        const freqMel = hzToMel(freq);
        // Position from top (100% = top of axis, 0% = bottom)
        const positionPercent = 100 - (freqMel / maxMel * 100);
        
        const tick = document.createElement('div');
        tick.style.cssText = `
            position: absolute;
            top: ${positionPercent}%;
            width: 100%;
            font-size: 10px;
            color: #666;
            text-align: right;
            padding-right: 8px;
            line-height: 1;
            transform: translateY(-50%);
        `;
        tick.textContent = `${freq / 1000} kHz`;

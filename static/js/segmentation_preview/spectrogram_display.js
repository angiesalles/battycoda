/**
 * Spectrogram display functionality for segmentation preview
 */

export function setupViewToggle(data) {
    const spectrogramToggle = document.getElementById('spectrogramToggle');
    const waveformToggle = document.getElementById('waveformToggle');
    const visualizationTitle = document.getElementById('visualizationTitle');
    
    if (spectrogramToggle && waveformToggle) {
        spectrogramToggle.addEventListener('click', function() {
            // Update button states
            spectrogramToggle.classList.add('active');
            waveformToggle.classList.remove('active');
            visualizationTitle.textContent = 'Spectrogram';
            
            // Show spectrogram view
            displaySpectrogram(data);
        });
        
        waveformToggle.addEventListener('click', function() {
            // Update button states
            waveformToggle.classList.add('active');
            spectrogramToggle.classList.remove('active');
            visualizationTitle.textContent = 'Waveform';
            
            // Show timeline view
            displayTimeline(data);
        });
        
        // Default to spectrogram view
        displaySpectrogram(data);
    }
}

function displaySpectrogram(data) {
    const container = document.getElementById('previewWaveformContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Check if we have a spectrogram URL from the server
    if (data.spectrogram_url) {
        // Display actual spectrogram image with frequency axis
        createSpectrogramWithAxes(container, data);
    } else {
        // Fallback: show message that spectrogram is being generated
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-cog fa-spin"></i>
                <p class="mt-2">Spectrogram is being generated... Please try refreshing in a moment.</p>
                <p class="small">Showing timeline view instead:</p>
            </div>
        `;
        // Fall back to timeline
        setTimeout(() => displayTimeline(data), 2000);
    }
}

function createSpectrogramWithAxes(container, data) {
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
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    `;
    
    // Add frequency tick marks - mel scale typical bat frequencies
    const freqTicks = [100, 80, 60, 40, 20, 10, 5, 0]; // kHz
    freqTicks.forEach((freq) => {
        const tick = document.createElement('div');
        tick.style.cssText = `
            position: relative;
            font-size: 10px;
            color: #666;
            text-align: right;
            padding-right: 8px;
            line-height: 1;
        `;
        tick.textContent = `${freq} kHz`;
        
        // Add tick mark line
        const tickMark = document.createElement('span');
        tickMark.style.cssText = `
            position: absolute; 
            right: -2px; 
            top: 50%; 
            transform: translateY(-50%); 
            width: 5px; 
            height: 1px; 
            background: #333;
        `;
        tick.appendChild(tickMark);
        
        freqAxis.appendChild(tick);
    });
    
    return freqAxis;
}

function createSpectrogramContainer(data) {
    const spectrogramContainer = document.createElement('div');
    spectrogramContainer.style.cssText = `
        grid-area: spectrogram;
        position: relative;
        overflow: hidden;
    `;
    
    // Add spectrogram image
    const spectrogramImg = document.createElement('img');
    spectrogramImg.src = data.spectrogram_url;
    spectrogramImg.style.cssText = `
        width: 100%;
        height: 100%;
        object-fit: fill;
    `;
    spectrogramImg.onload = () => {
        console.log('Spectrogram image loaded successfully');
        addSegmentOverlays(spectrogramContainer, data);
    };
    spectrogramImg.onerror = () => {
        console.error('Failed to load spectrogram image');
        spectrogramContainer.innerHTML = `
            <div class="text-center text-muted mt-5">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Spectrogram could not be loaded</p>
            </div>
        `;
    };
    
    spectrogramContainer.appendChild(spectrogramImg);
    return spectrogramContainer;
}

function createTimeAxis(data) {
    const timeAxis = document.createElement('div');
    timeAxis.style.cssText = `
        grid-area: time-axis;
        position: relative;
        border-top: 2px solid #333;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding-top: 5px;
    `;
    
    // Add time tick marks
    const timeRange = data.preview_end - data.preview_start;
    const numTimeTicks = Math.min(6, Math.ceil(timeRange));
    for (let i = 0; i <= numTimeTicks; i++) {
        const time = data.preview_start + (i / numTimeTicks) * timeRange;
        const tick = document.createElement('div');
        tick.style.cssText = `
            font-size: 10px;
            color: #666;
            text-align: center;
            position: relative;
        `;
        tick.textContent = `${time.toFixed(1)}s`;
        
        // Add tick mark line
        const tickMark = document.createElement('span');
        tickMark.style.cssText = `
            position: absolute; 
            top: -7px; 
            left: 50%; 
            transform: translateX(-50%); 
            width: 1px; 
            height: 5px; 
            background: #333;
        `;
        tick.appendChild(tickMark);
        
        timeAxis.appendChild(tick);
    }
    
    return timeAxis;
}

function createCorner() {
    const corner = document.createElement('div');
    corner.style.cssText = `
        grid-area: corner;
        border-right: 2px solid #333;
        border-top: 2px solid #333;
    `;
    return corner;
}

function addFrequencyLabel(container) {
    const freqLabel = document.createElement('div');
    freqLabel.textContent = 'Frequency';
    freqLabel.style.cssText = `
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%) rotate(-90deg);
        font-size: 12px;
        color: #666;
        font-weight: bold;
    `;
    container.style.position = 'relative';
    container.appendChild(freqLabel);
}

function addSegmentOverlays(spectrogramContainer, data) {
    if (!data.segments || data.segments.length === 0) return;
    
    const timeRange = data.preview_end - data.preview_start;
    
    data.segments.forEach((segment, index) => {
        // Calculate position as percentage of the container width
        const startPercent = ((segment.onset - data.preview_start) / timeRange) * 100;
        const widthPercent = (segment.duration / timeRange) * 100;
        
        if (startPercent >= 0 && startPercent <= 100) {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: absolute;
                left: ${startPercent}%;
                top: 0;
                width: ${widthPercent}%;
                height: 100%;
                border: 2px solid #ff6b35;
                border-radius: 3px;
                background: rgba(255, 107, 53, 0.2);
                pointer-events: none;
                box-sizing: border-box;
            `;
            
            // Add segment label
            const label = document.createElement('div');
            label.textContent = `S${index + 1}`;
            label.style.cssText = `
                position: absolute;
                top: 2px;
                left: 2px;
                background: rgba(255, 107, 53, 0.8);
                color: white;
                font-size: 10px;
                padding: 1px 3px;
                border-radius: 2px;
                line-height: 1;
            `;
            
            overlay.appendChild(label);
            spectrogramContainer.appendChild(overlay);
        }
    });
}

function displayTimeline(data) {
    const container = document.getElementById('previewWaveformContainer');
    if (!container) return;
    
    // Import the timeline drawing function from the main module
    if (window.drawPreviewWaveform) {
        container.innerHTML = '';
        
        const canvas = document.createElement('canvas');
        canvas.id = 'previewWaveformCanvas';
        canvas.style.width = '100%';
        canvas.style.height = '200px';
        canvas.style.border = '1px solid #dee2e6';
        canvas.style.backgroundColor = '#f8f9fa';
        
        const rect = container.getBoundingClientRect();
        canvas.width = rect.width || 800;
        canvas.height = 200;
        
        container.appendChild(canvas);
        window.drawPreviewWaveform(canvas, data);
    }
}
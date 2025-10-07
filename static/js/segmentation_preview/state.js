// State management
    
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
        background-color: #f8f9fa;
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
        background-color: #f8f9fa;
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

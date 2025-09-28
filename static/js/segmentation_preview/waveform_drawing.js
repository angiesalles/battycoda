/**
 * Waveform Drawing
 * Handles drawing both real and simulated waveforms
 */

export function drawWaveform(ctx, audioDataOrPreviewData, width, height, isSimulated = false) {
    if (isSimulated) {
        drawSimulatedWaveform(ctx, audioDataOrPreviewData, width, height);
    } else {
        drawRealWaveform(ctx, audioDataOrPreviewData, width, height);
    }
    
    // Draw center line for waveforms
    drawCenterLine(ctx, width, height / 2);
}

function drawRealWaveform(ctx, audioData, width, height) {
    const centerY = height / 2;
    const samplesPerPixel = Math.ceil(audioData.length / width);
    
    // Draw the waveform
    ctx.strokeStyle = '#6c757d';
    ctx.lineWidth = 1;
    ctx.beginPath();
    
    for (let x = 0; x < width; x++) {
        const startSample = x * samplesPerPixel;
        const endSample = Math.min(startSample + samplesPerPixel, audioData.length);
        
        // Find min and max values in this pixel's worth of samples
        let min = 0;
        let max = 0;
        
        for (let i = startSample; i < endSample; i++) {
            const sample = audioData[i];
            if (sample < min) min = sample;
            if (sample > max) max = sample;
        }
        
        // Convert to pixel coordinates
        const yMin = centerY + (min * centerY * 0.8);
        const yMax = centerY + (max * centerY * 0.8);
        
        // Draw vertical line for this pixel
        if (x === 0) {
            ctx.moveTo(x, yMin);
        } else {
            ctx.lineTo(x, yMin);
        }
        ctx.lineTo(x, yMax);
    }
    ctx.stroke();
}

function drawSimulatedWaveform(ctx, data, width, height) {
    const centerY = height / 2;
    
    // Draw a more realistic looking random waveform
    ctx.strokeStyle = '#6c757d';
    ctx.lineWidth = 1;
    ctx.beginPath();
    
    const timeRange = data.preview_end - data.preview_start;
    
    for (let x = 0; x < width; x++) {
        // Create more realistic audio-like patterns
        const t = (x / width) * timeRange;
        
        // Combine multiple frequencies for more realistic audio appearance
        let amplitude = 0;
        amplitude += Math.sin(t * 50) * 0.3; // Low frequency component
        amplitude += Math.sin(t * 200) * 0.2 * Math.random(); // Mid frequency with noise
        amplitude += Math.sin(t * 1000) * 0.1 * Math.random(); // High frequency with noise
        amplitude += (Math.random() - 0.5) * 0.15; // Random noise
        
        // Add some envelope variation
        const envelope = 0.5 + 0.5 * Math.sin(t * 5 + Math.random());
        amplitude *= envelope;
        
        const y = centerY + amplitude * centerY * 0.6;
        
        if (x === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    ctx.stroke();
}

function drawCenterLine(ctx, width, centerY) {
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();
}
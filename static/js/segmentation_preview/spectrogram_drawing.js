/**
 * Spectrogram Drawing
 * Handles drawing both real and simulated spectrograms
 */

export async function drawSpectrogram(ctx, audioData, sampleRate, width, height, isSimulated = false) {
    if (isSimulated) {
        drawSimulatedSpectrogram(ctx, width, height);
    } else {
        await drawRealSpectrogram(ctx, audioData, sampleRate, width, height);
    }
}

async function drawRealSpectrogram(ctx, audioData, sampleRate, width, height) {
    console.log('Generating spectrogram from audio data...');
    
    // Spectrogram parameters
    const fftSize = 512;
    const hopSize = fftSize / 4;
    const windowSize = fftSize;
    
    // Calculate number of time frames
    const numFrames = Math.floor((audioData.length - fftSize) / hopSize) + 1;
    
    // Create frequency bins (we'll only show up to Nyquist/2 for better visualization)
    const numFreqBins = fftSize / 4; // Show up to 1/4 of sample rate
    const maxFreq = sampleRate / 4;
    
    // Prepare spectrogram data
    const spectrogramData = [];
    
    // Simple FFT-like analysis (approximation for visualization)
    for (let frame = 0; frame < numFrames; frame++) {
        const frameStart = frame * hopSize;
        const frameData = audioData.slice(frameStart, frameStart + windowSize);
        
        // Apply Hanning window
        const windowedData = frameData.map((sample, i) => {
            const windowValue = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (windowSize - 1));
            return sample * windowValue;
        });
        
        // Compute power spectrum (simplified)
        const powerSpectrum = new Array(numFreqBins).fill(0);
        
        for (let bin = 0; bin < numFreqBins; bin++) {
            const freq = (bin / numFreqBins) * maxFreq;
            let power = 0;
            
            // Simple frequency analysis
            for (let i = 0; i < windowedData.length; i++) {
                const phase = 2 * Math.PI * freq * i / sampleRate;
                power += windowedData[i] * Math.cos(phase);
            }
            powerSpectrum[bin] = Math.abs(power);
        }
        
        spectrogramData.push(powerSpectrum);
    }
    
    // Draw spectrogram
    const timeStep = width / numFrames;
    const freqStep = height / numFreqBins;
    
    // Find max power for normalization
    let maxPower = 0;
    spectrogramData.forEach(frame => {
        frame.forEach(power => {
            if (power > maxPower) maxPower = power;
        });
    });
    
    // Draw the spectrogram pixels
    for (let frameIdx = 0; frameIdx < numFrames; frameIdx++) {
        const x = frameIdx * timeStep;
        const frame = spectrogramData[frameIdx];
        
        for (let binIdx = 0; binIdx < numFreqBins; binIdx++) {
            const y = height - (binIdx + 1) * freqStep; // Flip Y axis (high freq at top)
            const power = frame[binIdx];
            const normalizedPower = power / maxPower;
            
            // Color mapping: dark blue to bright yellow
            const color = getSpectrogramColor(normalizedPower);
            ctx.fillStyle = color;
            ctx.fillRect(x, y, Math.ceil(timeStep), Math.ceil(freqStep));
        }
    }
    
    console.log('Spectrogram generation completed');
}

function drawSimulatedSpectrogram(ctx, width, height) {
    // Create a gradient background to simulate spectrogram
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#000033');    // Dark blue at top (high freq)
    gradient.addColorStop(0.3, '#000066'); 
    gradient.addColorStop(0.7, '#000099');
    gradient.addColorStop(1, '#0000cc');    // Lighter blue at bottom (low freq)
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Simulate some bat call patterns
    for (let x = 0; x < width; x++) {
        // Add some bright spots to simulate calls
        if (Math.random() < 0.15) { // 15% chance of call activity
            // Simulate a call with frequency sweep
            const callIntensity = Math.random() * 0.8 + 0.2;
            const freqStart = Math.random() * 0.7 + 0.1; // Start frequency (0.1-0.8 of height)
            const freqEnd = Math.random() * 0.7 + 0.1;   // End frequency
            
            // Draw a short frequency line
            const callWidth = Math.random() * 5 + 2; // 2-7 pixels wide
            for (let dx = 0; dx < callWidth && x + dx < width; dx++) {
                const freqPos = freqStart + (freqEnd - freqStart) * (dx / callWidth);
                const y = height * freqPos;
                
                // Create bright yellow/orange spots for calls
                const intensity = callIntensity * (1 - dx / callWidth); // Fade out
                const alpha = intensity * 0.8;
                
                ctx.fillStyle = `rgba(255, 200, 0, ${alpha})`;
                ctx.fillRect(x + dx, y - 2, 2, 4);
            }
        }
        
        // Add some background noise
        for (let y = 0; y < height; y += 4) {
            if (Math.random() < 0.05) { // Low density noise
                const intensity = Math.random() * 0.3;
                ctx.fillStyle = `rgba(100, 150, 255, ${intensity})`;
                ctx.fillRect(x, y, 1, 2);
            }
        }
    }
}

function getSpectrogramColor(normalizedPower) {
    // Color mapping: dark blue to bright yellow
    let r, g, b;
    if (normalizedPower < 0.2) {
        // Dark blue background
        r = 0; g = 0; b = Math.floor(100 + normalizedPower * 300);
    } else if (normalizedPower < 0.5) {
        // Blue to cyan
        const t = (normalizedPower - 0.2) / 0.3;
        r = 0; 
        g = Math.floor(t * 200);
        b = Math.floor(200 + t * 55);
    } else if (normalizedPower < 0.8) {
        // Cyan to yellow
        const t = (normalizedPower - 0.5) / 0.3;
        r = Math.floor(t * 255);
        g = 255;
        b = Math.floor(255 * (1 - t));
    } else {
        // Yellow to white
        const t = (normalizedPower - 0.8) / 0.2;
        r = 255;
        g = 255;
        b = Math.floor(t * 255);
    }
    
    return `rgb(${r}, ${g}, ${b})`;
}
// Event handlers
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

function drawServerSpectrogram(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    console.log('Loading server-generated spectrogram image...');
    
    const img = new Image();
    img.crossOrigin = 'anonymous'; // Handle CORS if needed
    
    img.onload = function() {
        console.log('Spectrogram image loaded successfully');
        
        // Draw the spectrogram image to fit the canvas
        ctx.drawImage(img, 0, 0, width, height);
        
        // Draw segment markers on top
        drawSegmentMarkers(ctx, data, width, height, 0);
        
        // Draw time labels
        drawTimeLabels(ctx, data, width, height);
        
        console.log('Server spectrogram drawn with segment markers');
    };
    
    img.onerror = function() {
        console.error('Failed to load spectrogram image, falling back to simulated');
        drawSimulatedVisualization(canvas, data, 'spectrogram');
    };
    
    img.src = data.spectrogram_url;
}

function drawGeneratingStatus(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    console.log('Drawing generating status message');
    
    // Clear background
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, width, height);
    
    // Draw border
    ctx.strokeStyle = '#dee2e6';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, width, height);
    
    // Draw centered message
    ctx.fillStyle = '#6c757d';
    ctx.font = '18px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const centerX = width / 2;
    const centerY = height / 2;
    
    // Spinner animation (simple rotating dots)
    const time = Date.now() / 200;
    const dots = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    const spinner = dots[Math.floor(time) % dots.length];
    
    ctx.fillText(`${spinner} Generating spectrogram...`, centerX, centerY - 10);
    
    // Draw smaller instruction text
    ctx.font = '14px Arial';
    ctx.fillStyle = '#868e96';
    ctx.fillText('This will take a few seconds. The preview will refresh automatically.', centerX, centerY + 20);
    
    // Still draw segment markers on top if available
    if (data.segments && data.segments.length > 0) {
        drawSegmentMarkers(ctx, data, width, height, 0);
    }
    
    // Draw time labels
    drawTimeLabels(ctx, data, width, height);
    
    // Set up auto-refresh after 3 seconds
    setTimeout(() => {
        console.log('Auto-refreshing preview to check for generated spectrogram...');
        // Trigger a new preview request
        if (window.refreshPreviewCallback) {
            window.refreshPreviewCallback();
        }
    }, 3000);
}
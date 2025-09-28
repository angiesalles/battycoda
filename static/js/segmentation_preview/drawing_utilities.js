/**
 * Drawing Utilities
 * Common drawing functions for segment markers, time labels, etc.
 */

export function drawSegmentMarkers(ctx, data, width, height, centerY) {
    // Draw segment markers
    if (data.segments && data.segments.length > 0) {
        const timeRange = data.preview_end - data.preview_start;
        
        data.segments.forEach((segment, index) => {
            // Calculate positions relative to preview window
            const startX = ((segment.onset - data.preview_start) / timeRange) * width;
            const endX = ((segment.offset - data.preview_start) / timeRange) * width;
            
            // Only draw if segment is within the visible range
            if (startX >= 0 && startX <= width) {
                // Draw segment boundary lines
                ctx.strokeStyle = '#007bff';
                ctx.lineWidth = 2;
                
                // Start line
                ctx.beginPath();
                ctx.moveTo(startX, 10);
                ctx.lineTo(startX, height - 10);
                ctx.stroke();
                
                // End line (if within bounds)
                if (endX <= width) {
                    ctx.beginPath();
                    ctx.moveTo(endX, 10);
                    ctx.lineTo(endX, height - 10);
                    ctx.stroke();
                    
                    // Draw segment highlight
                    ctx.fillStyle = 'rgba(0, 123, 255, 0.2)';
                    ctx.fillRect(startX, 10, endX - startX, height - 20);
                }
                
                // Draw segment label
                ctx.fillStyle = '#007bff';
                ctx.font = '12px Arial';
                ctx.fillText(`S${index + 1}`, startX + 2, 25);
            }
        });
    }
}

export function drawTimeLabels(ctx, data, width, height) {
    // Draw time labels
    ctx.fillStyle = '#000';
    ctx.font = '10px Arial';
    ctx.fillText(`${data.preview_start.toFixed(1)}s`, 5, height - 5);
    ctx.fillText(`${data.preview_end.toFixed(1)}s`, width - 35, height - 5);
}
/**
 * Spectrogram Data Renderer - Client-side rendering of HDF5 spectrogram data
 *
 * Efficiently renders spectrogram data as image data directly to canvas.
 */

import { CanvasInteractions } from './canvas_interactions.js';

export class SpectrogramDataRenderer {
    constructor(containerId, recordingId, player) {
        this.containerId = containerId;
        this.recordingId = recordingId;
        this.player = player;
        this.spectrogramData = null;
        this.metadata = null;
        this.canvas = null;
        this.ctx = null;
        this.spectrogramImage = null; // Pre-rendered image data
        this.canvasInteractions = new CanvasInteractions(player);

        this.setupCanvas();
    }
    
    setupCanvas() {
        // Find or create canvas for spectrogram rendering
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('Spectrogram container not found:', this.containerId);
            return;
        }

        this.canvas = document.createElement('canvas');
        this.canvas.className = 'spectrogram-canvas';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.zIndex = '1'; // Below waveform but above background

        container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        // Setup canvas interactions (symmetric with waveform)
        this.canvasInteractions.setupCanvasHandlers(this.canvas, this.canvas.width, 0, 1);

        // Create loading indicator
        this.loadingDiv = document.createElement('div');
        this.loadingDiv.className = 'spectrogram-loading';
        this.loadingDiv.style.position = 'absolute';
        this.loadingDiv.style.top = '50%';
        this.loadingDiv.style.left = '50%';
        this.loadingDiv.style.transform = 'translate(-50%, -50%)';
        this.loadingDiv.style.textAlign = 'center';
        this.loadingDiv.style.zIndex = '2';
        this.loadingDiv.style.color = '#666';
        this.loadingDiv.innerHTML = `
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div style="margin-top: 8px; font-size: 12px;">Loading spectrogram data...</div>
            <div style="margin-top: 4px; font-size: 11px;" id="spectrogram-progress-${this.containerId}">0%</div>
        `;
        container.appendChild(this.loadingDiv);

        console.log('Spectrogram canvas created for container:', this.containerId);
    }
    
    async loadSpectrogramData() {
        try {
            console.log('Loading spectrogram data for recording:', this.recordingId);

            const response = await fetch(`/recordings/${this.recordingId}/spectrogram-data/`);

            if (!response.ok) {
                console.error('Failed to load spectrogram data:', response.status);
                if (this.loadingDiv) this.loadingDiv.remove();
                return false;
            }

            // Get total size for progress tracking
            const contentLength = response.headers.get('content-length');
            const total = parseInt(contentLength, 10);

            // Read response with progress tracking
            const reader = response.body.getReader();
            const chunks = [];
            let receivedLength = 0;

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                chunks.push(value);
                receivedLength += value.length;

                // Update progress
                if (total) {
                    const progress = Math.round((receivedLength / total) * 100);
                    const progressEl = document.getElementById(`spectrogram-progress-${this.containerId}`);
                    if (progressEl) {
                        progressEl.textContent = `${progress}% (${(receivedLength / 1024 / 1024).toFixed(1)} MB)`;
                    }
                }
            }

            // Combine chunks into single ArrayBuffer
            const chunksAll = new Uint8Array(receivedLength);
            let position = 0;
            for (let chunk of chunks) {
                chunksAll.set(chunk, position);
                position += chunk.length;
            }

            const arrayBuffer = chunksAll.buffer;
            const dataView = new DataView(arrayBuffer);

            // Read metadata length (4 bytes, little-endian uint32)
            const metadataLength = dataView.getUint32(0, true);

            // Read metadata JSON
            const metadataBytes = new Uint8Array(arrayBuffer, 4, metadataLength);
            const metadataString = new TextDecoder().decode(metadataBytes);
            this.metadata = JSON.parse(metadataString);

            // Read spectrogram data (float16 array)
            const dataOffset = 4 + metadataLength;
            const numValues = this.metadata.n_freq_bins * this.metadata.n_frames;

            // Check if offset is aligned for Uint16Array (must be multiple of 2)
            if (dataOffset % 2 !== 0) {
                // Copy data to ensure proper alignment
                const byteLength = numValues * 2;
                const alignedBuffer = new ArrayBuffer(byteLength);
                const source = new Uint8Array(arrayBuffer, dataOffset, byteLength);
                const dest = new Uint8Array(alignedBuffer);
                dest.set(source);
                this.spectrogramDataRaw = new Uint16Array(alignedBuffer);
            } else {
                // Offset is aligned, can use directly
                this.spectrogramDataRaw = new Uint16Array(arrayBuffer, dataOffset, numValues);
            }

            // Keep a reference for 2D indexing: data[freq * n_frames + frame]
            this.spectrogramData = this.spectrogramDataRaw;
            
            // Update progress to "Processing..."
            const progressEl = document.getElementById(`spectrogram-progress-${this.containerId}`);
            if (progressEl) {
                progressEl.textContent = 'Processing data...';
            }

            // Pre-compute normalization values
            await this.createSpectrogramImage();

            // Remove loading indicator
            if (this.loadingDiv) {
                this.loadingDiv.remove();
                this.loadingDiv = null;
            }

            console.log('Spectrogram data loaded and ready:', {
                frames: this.metadata.n_frames,
                freqBins: this.metadata.n_freq_bins,
                duration: this.metadata.duration,
                sampleRate: this.metadata.sample_rate
            });

            return true;

        } catch (error) {
            console.error('Error loading spectrogram data:', error);
            if (this.loadingDiv) {
                this.loadingDiv.innerHTML = '<div style="color: red;">Error loading spectrogram</div>';
            }
            return false;
        }
    }
    
    async createSpectrogramImage() {
        // Don't pre-render - we'll render on-demand to match canvas size
        // Calculate 1st and 99th percentiles for normalization (1% saturation on each end)
        const freqBins = this.metadata.n_freq_bins;
        const frames = this.metadata.n_frames;

        // Store helper function for decoding float16
        this.decodeFloat16 = (bits) => {
            const sign = (bits & 0x8000) >> 15;
            const exponent = (bits & 0x7C00) >> 10;
            const fraction = bits & 0x03FF;
            if (exponent === 0) return (sign ? -1 : 1) * Math.pow(2, -14) * (fraction / 1024);
            if (exponent === 0x1F) return fraction ? NaN : (sign ? -Infinity : Infinity);
            return (sign ? -1 : 1) * Math.pow(2, exponent - 15) * (1 + fraction / 1024);
        };

        // Decode all values for percentile calculation
        console.log('Decoding all spectrogram values for percentile calculation...');
        const values = new Float32Array(this.spectrogramData.length);
        for (let i = 0; i < this.spectrogramData.length; i++) {
            values[i] = this.decodeFloat16(this.spectrogramData[i]);
        }

        // Sort values to find 1st percentile and max
        console.log('Sorting values for percentile calculation...');
        const sortedValues = Float32Array.from(values).sort((a, b) => a - b);

        // Use 1st percentile for lower bound, max for upper bound
        const p1Index = Math.floor(sortedValues.length * 0.01);

        this.minVal = sortedValues[p1Index];
        this.maxVal = sortedValues[sortedValues.length - 1];
        this.valueRange = this.maxVal - this.minVal;

        console.log('Spectrogram normalization range (1st percentile to max):', {
            p1: this.minVal,
            max: this.maxVal,
            valueRange: this.valueRange,
            totalValues: sortedValues.length
        });

        return true;
    }
    
    render(viewStartTime = 0, viewEndTime = null, canvasWidth = null, canvasHeight = null) {
        if (!this.spectrogramData || !this.metadata) {
            console.warn('No spectrogram data available for rendering');
            return;
        }

        // Set canvas dimensions
        if (canvasWidth && canvasHeight) {
            this.canvas.width = canvasWidth;
            this.canvas.height = canvasHeight;
        } else {
            const rect = this.canvas.getBoundingClientRect();
            this.canvas.width = rect.width;
            this.canvas.height = rect.height;
        }

        if (this.canvas.width === 0 || this.canvas.height === 0) {
            console.warn('Canvas has zero dimensions, skipping render');
            return;
        }

        // Calculate time range
        const totalDuration = this.metadata.duration;
        const endTime = viewEndTime || totalDuration;
        const totalFrames = this.metadata.n_frames;
        const freqBins = this.metadata.n_freq_bins;

        // Map time to frame indices
        const startFrame = Math.floor((viewStartTime / totalDuration) * totalFrames);
        const endFrame = Math.ceil((endTime / totalDuration) * totalFrames);
        const frameCount = endFrame - startFrame;

        // Create ImageData matching canvas size
        const imageData = this.ctx.createImageData(this.canvas.width, this.canvas.height);
        const data = imageData.data;

        // Render by sampling the spectrogram data to match canvas dimensions
        for (let canvasY = 0; canvasY < this.canvas.height; canvasY++) {
            // Map canvas Y to frequency bin (flip Y axis)
            const freq = Math.floor(((this.canvas.height - 1 - canvasY) / this.canvas.height) * freqBins);

            for (let canvasX = 0; canvasX < this.canvas.width; canvasX++) {
                // Map canvas X to frame
                const frame = startFrame + Math.floor((canvasX / this.canvas.width) * frameCount);

                // Get data value
                const dataIndex = freq * totalFrames + frame;
                const rawValue = this.decodeFloat16(this.spectrogramData[dataIndex]);
                const normalizedValue = (rawValue - this.minVal) / this.valueRange;

                // Apply roseus colormap
                const color = this.applyRoseusColormap(normalizedValue);

                const pixelIndex = (canvasY * this.canvas.width + canvasX) * 4;
                data[pixelIndex] = color.r;
                data[pixelIndex + 1] = color.g;
                data[pixelIndex + 2] = color.b;
                data[pixelIndex + 3] = 255;
            }
        }

        // Put the image data on the canvas
        this.ctx.putImageData(imageData, 0, 0);

        // Update interaction parameters for current view (symmetric with waveform)
        const visibleDuration = endTime - viewStartTime;
        this.canvasInteractions.updateViewParameters(this.canvas.width, viewStartTime, visibleDuration);

        console.log('Spectrogram rendered:', {
            viewRange: `${viewStartTime.toFixed(2)}s - ${endTime.toFixed(2)}s`,
            frameRange: `${startFrame} - ${endFrame}`,
            canvasSize: `${this.canvas.width}x${this.canvas.height}`
        });
    }
    
    applyRoseusColormap(value) {
        // Roseus colormap - 256 RGB values
        const roseusColormap = [[1,1,1],[1,2,2],[2,2,2],[2,3,3],[2,3,4],[2,4,5],[2,5,6],[3,6,7],[3,7,8],[3,8,10],[3,9,12],[3,10,14],[3,12,16],[3,13,17],[3,14,19],[2,15,21],[2,16,23],[2,17,25],[2,18,27],[2,19,30],[1,20,32],[1,21,34],[1,22,36],[1,23,38],[1,24,40],[0,25,43],[0,26,45],[0,27,47],[0,27,50],[0,28,52],[0,29,54],[0,30,57],[0,30,59],[1,31,62],[1,32,64],[1,32,67],[2,33,69],[3,33,72],[4,34,74],[5,35,77],[6,35,79],[8,35,82],[9,36,84],[11,36,86],[13,37,89],[15,37,91],[17,37,94],[19,37,96],[21,38,99],[23,38,101],[25,38,104],[27,38,106],[29,38,108],[31,38,111],[33,38,113],[35,38,115],[38,38,118],[40,38,120],[42,38,122],[44,38,124],[46,38,126],[49,38,128],[51,38,130],[53,37,132],[55,37,134],[58,37,136],[60,36,138],[62,36,139],[65,36,141],[67,35,143],[69,35,144],[72,35,146],[74,34,147],[76,34,149],[79,33,150],[81,33,151],[84,32,152],[86,32,153],[88,31,154],[91,31,155],[93,30,156],[95,29,157],[98,29,158],[100,28,159],[103,28,159],[105,27,160],[107,27,160],[110,26,161],[112,26,161],[114,25,161],[117,25,162],[119,24,162],[121,24,162],[124,23,162],[126,23,162],[128,23,162],[131,22,161],[133,22,161],[135,22,161],[137,22,161],[140,22,160],[142,22,160],[144,22,159],[146,22,159],[148,22,158],[150,22,157],[153,22,157],[155,23,156],[157,23,155],[159,23,154],[161,24,153],[163,24,152],[165,25,151],[167,26,150],[169,26,149],[171,27,148],[173,28,147],[175,29,146],[177,29,145],[179,30,144],[181,31,142],[183,32,141],[184,33,140],[186,34,139],[188,35,137],[190,36,136],[192,37,135],[193,39,133],[195,40,132],[197,41,130],[198,42,129],[200,43,128],[202,45,126],[203,46,125],[205,47,123],[206,48,122],[208,50,120],[209,51,119],[211,52,117],[212,54,116],[214,55,114],[215,57,113],[217,58,111],[218,60,110],[219,61,109],[221,63,107],[222,64,106],[223,66,104],[225,67,103],[226,69,101],[227,70,100],[228,72,99],[229,73,97],[230,75,96],[231,77,94],[233,78,93],[234,80,92],[235,82,91],[236,83,89],[237,85,88],[237,87,87],[238,89,86],[239,90,84],[240,92,83],[241,94,82],[242,96,81],[242,97,80],[243,99,79],[244,101,78],[245,103,77],[245,105,76],[246,107,75],[246,108,74],[247,110,74],[248,112,73],[248,114,72],[248,116,72],[249,118,71],[249,120,71],[250,122,70],[250,124,70],[250,126,70],[251,128,70],[251,130,69],[251,132,70],[251,134,70],[251,136,70],[252,138,70],[252,140,70],[252,142,71],[252,144,72],[252,146,72],[252,148,73],[252,150,74],[251,152,75],[251,154,76],[251,156,77],[251,158,78],[251,160,80],[251,162,81],[250,164,83],[250,166,85],[250,168,87],[249,170,88],[249,172,90],[248,174,93],[248,176,95],[248,178,97],[247,180,99],[247,182,102],[246,184,104],[246,186,107],[245,188,110],[244,190,112],[244,192,115],[243,194,118],[243,195,121],[242,197,124],[242,199,127],[241,201,131],[240,203,134],[240,205,137],[239,207,140],[239,208,144],[238,210,147],[238,212,151],[237,213,154],[237,215,158],[236,217,161],[236,218,165],[236,220,169],[236,222,172],[235,223,176],[235,225,180],[235,226,183],[235,228,187],[235,229,191],[235,230,194],[236,232,198],[236,233,201],[236,234,205],[237,236,208],[237,237,212],[238,238,215],[239,239,219],[240,240,222],[241,242,225],[242,243,228],[243,244,231],[244,245,234],[246,246,237],[247,247,240],[249,248,242],[251,249,245],[253,250,247],[254,251,249]];

        value = Math.max(0, Math.min(1, value));
        const index = Math.floor(value * 255);
        const color = roseusColormap[index];

        return {
            r: color[0],
            g: color[1],
            b: color[2]
        };
    }
    
    // Method to handle viewport changes (called by waveform player)
    updateView(viewStartTime, viewEndTime, canvasWidth, canvasHeight) {
        this.render(viewStartTime, viewEndTime, canvasWidth, canvasHeight);
    }
    
    // Initialize and load data
    async initialize() {
        const success = await this.loadSpectrogramData();
        if (success) {
            // Initial render of full spectrogram
            this.render();
        }
        return success;
    }
    
    // Show/hide methods for view switching
    show() {
        if (this.canvas) {
            this.canvas.style.display = 'block';
        }
    }
    
    hide() {
        if (this.canvas) {
            this.canvas.style.display = 'none';
        }
    }
    
    destroy() {
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}
/**
 * Spectrogram Data Renderer - Client-side rendering of HDF5 spectrogram data
 *
 * Efficiently renders spectrogram data as image data directly to canvas.
 */

import { CanvasInteractions } from './canvas_interactions.js';
import { ROSEUS_COLORMAP } from '../utils/colormaps.js';

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
      for (const chunk of chunks) {
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
        sampleRate: this.metadata.sample_rate,
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
    // Calculate 1st percentile and max for normalization

    // Store helper function for decoding float16
    this.decodeFloat16 = (bits) => {
      const sign = (bits & 0x8000) >> 15;
      const exponent = (bits & 0x7c00) >> 10;
      const fraction = bits & 0x03ff;
      if (exponent === 0) return (sign ? -1 : 1) * Math.pow(2, -14) * (fraction / 1024);
      if (exponent === 0x1f) return fraction ? NaN : sign ? -Infinity : Infinity;
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
      totalValues: sortedValues.length,
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
      canvasSize: `${this.canvas.width}x${this.canvas.height}`,
    });
  }

  applyRoseusColormap(value) {
    value = Math.max(0, Math.min(1, value));
    const index = Math.floor(value * 255);
    const color = ROSEUS_COLORMAP[index];

    return {
      r: color[0],
      g: color[1],
      b: color[2],
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

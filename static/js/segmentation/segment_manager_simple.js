/**
 * BattyCoda Segment Manager - Simple & Clean
 * 
 * Main controller for segment management functionality
 */

import { SegmentLoader } from './segment_loader.js';
import { SegmentCRUD } from './segment_crud.js';
import { SegmentDisplay } from './segment_display.js';
import { ViewportManager } from './viewport_manager.js';

export class SegmentManager {
    constructor(options) {
        // Configuration
        this.recordingId = options.recordingId;
        this.waveformId = options.waveformId || 'segment-waveform';
        this.csrfToken = options.csrfToken;
        
        // Initialize modules
        this.loader = new SegmentLoader(this.recordingId);
        this.crud = new SegmentCRUD(this.recordingId, this.csrfToken);
        this.display = new SegmentDisplay(this.waveformId);
        this.viewport = new ViewportManager(this.loader);
        
        // State
        this.segments = options.segments || [];
        this.currentSelection = null;
        
        // Debug logging
        console.log('SegmentManager initialized with', this.segments.length, 'segments');
        console.log('Initial segments:', this.segments);
        
        // Initialize
        this.initializeEventHandlers();
        
        // Wait for waveform player to be ready before updating display
        this.waitForWaveformPlayer().then(() => {
            this.updateDisplay();
        });
    }
    
    // Wait for waveform player to be ready
    async waitForWaveformPlayer() {
        return new Promise((resolve) => {
            const checkPlayer = () => {
                if (window.waveformPlayers && 
                    window.waveformPlayers[this.waveformId] && 
                    window.waveformPlayers[this.waveformId].player &&
                    window.waveformPlayers[this.waveformId].player.duration > 0) {
                    console.log('Waveform player is ready');
                    resolve();
                } else {
                    console.log('Waiting for waveform player...');
                    setTimeout(checkPlayer, 100);
                }
            };
            checkPlayer();
        });
    }
    
    // Initialize event handlers
    initializeEventHandlers() {
        // Form submission
        const segmentForm = document.getElementById('segment-form');
        if (segmentForm) {
            segmentForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        // Cancel button
        const cancelBtn = document.getElementById('cancel-segment-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideSegmentForm());
        }
        
        // Selection monitoring for waveform
        this.startSelectionMonitoring();
    }
    
    // Monitor waveform selection
    startSelectionMonitoring() {
        if (window.waveformPlayers && window.waveformPlayers[this.waveformId]) {
            const player = window.waveformPlayers[this.waveformId];
            
            if (player.player && player.player.on) {
                player.player.on('region-update-end', () => {
                    this.handleSelectionChange();
                });
            }
        }
    }
    
    // Handle selection change in waveform
    handleSelectionChange() {
        const player = window.waveformPlayers[this.waveformId];
        if (player?.player?.regions?.list) {
            const regions = Object.values(player.player.regions.list);
            if (regions.length > 0) {
                const region = regions[0];
                this.currentSelection = { start: region.start, end: region.end };
                this.showSegmentForm();
            }
        }
    }
    
    // Show/hide segment form
    showSegmentForm() {
        const formContainer = document.getElementById('segment-form-container');
        const onsetField = document.getElementById('id_onset');
        const offsetField = document.getElementById('id_offset');
        
        if (formContainer && this.currentSelection) {
            formContainer.style.display = 'block';
            if (onsetField) onsetField.value = this.currentSelection.start.toFixed(3);
            if (offsetField) offsetField.value = this.currentSelection.end.toFixed(3);
        }
    }
    
    hideSegmentForm() {
        const formContainer = document.getElementById('segment-form-container');
        if (formContainer) formContainer.style.display = 'none';
        
        const player = window.waveformPlayers[this.waveformId];
        if (player?.player?.clearRegions) {
            player.player.clearRegions();
        }
    }
    
    // Handle form submission
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const segmentData = {
            onset: parseFloat(formData.get('onset')),
            offset: parseFloat(formData.get('offset')),
            name: formData.get('name') || '',
            notes: formData.get('notes') || ''
        };
        
        try {
            const newSegment = await this.crud.createSegment(segmentData);
            this.segments.push(newSegment);
            
            this.updateDisplay();
            this.hideSegmentForm();
            this.showMessage('success', 'Segment added successfully');
        } catch (error) {
            this.showMessage('danger', `Error: ${error.message}`);
        }
    }
    
    // Delete segment
    async deleteSegment(segmentId) {
        if (!confirm('Are you sure you want to delete this segment?')) return;
        
        try {
            await this.crud.deleteSegment(segmentId);
            this.segments = this.segments.filter(segment => segment.id != segmentId);
            this.updateDisplay();
            this.showMessage('success', 'Segment deleted successfully');
        } catch (error) {
            this.showMessage('danger', `Error: ${error.message}`);
        }
    }
    
    // Play a specific segment
    playSegment(onset, offset) {
        const player = window.waveformPlayers[this.waveformId];
        if (player?.player?.playRegion) {
            player.player.playRegion(onset, offset);
        }
    }
    
    // Update all displays
    updateDisplay() {
        this.updateWaveformDisplay();
        this.updateSegmentsList();
    }
    
    // Update waveform display
    updateWaveformDisplay() {
        const playerWrapper = window.waveformPlayers[this.waveformId];
        if (!playerWrapper) return;
        
        // Update waveform with current segments
        const playerSegments = this.segments.map(segment => ({
            id: segment.id,
            onset: segment.onset,
            offset: segment.offset
        }));
        
        if (playerWrapper.setSegments) {
            playerWrapper.setSegments(playerSegments);
        }
        
        // Load segments for current viewport if zoomed in
        this.viewport.loadSegmentsForCurrentView(playerWrapper, (newSegments) => {
            // Merge with existing segments
            const filteredSegments = newSegments.filter(newSeg => 
                !this.segments.some(existingSeg => existingSeg.id === newSeg.id)
            );
            
            this.segments = [...this.segments, ...filteredSegments];
            this.segments.sort((a, b) => a.onset - b.onset);
            
            this.updateDisplay();
        });
    }
    
    // Update segments list display
    updateSegmentsList() {
        const visibleSegments = this.display.getVisibleSegments(this.segments);
        this.display.renderSegmentsList(visibleSegments);
        this.display.updateSegmentsCount(visibleSegments.length);
    }
    
    // Show message
    showMessage(type, message) {
        console.log(`${type.toUpperCase()}: ${message}`);
        
        const messagesContainer = document.querySelector('.messages');
        if (messagesContainer) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            messagesContainer.appendChild(alertDiv);
            
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 5000);
        }
    }
}
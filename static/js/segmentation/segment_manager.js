/**
 * BattyCoda Segment Manager
 * 
 * This file contains code for managing segments in a recording:
 * - Creating segments from selections in the waveform
 * - Listing segments
 * - Editing segments
 * - Deleting segments
 * - Synchronizing with the waveform display
 */

class SegmentManager {
    constructor(options) {
        // Configuration
        this.recordingId = options.recordingId;
        this.waveformId = options.waveformId || 'segment-waveform';
        this.csrfToken = options.csrfToken;
        
        // State
        this.segments = options.segments || [];
        this.currentSelection = null;
        this.lastSelection = null;
        this.isEditing = false;
        this.endButtonClicked = false;
        
        // Initialize
        this.initializeEventHandlers();
        this.startSelectionMonitoring();
        this.updateSegmentsDisplay();
    }
    
    // Initialize all event handlers
    initializeEventHandlers() {
        console.log('Initializing segment manager event handlers');
        
        // Cancel button
        const cancelBtn = document.getElementById('cancel-segment-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideSegmentForm());
        }
        
        // Form submission
        const segmentForm = document.getElementById('segment-form');
        if (segmentForm) {
            segmentForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        // Set End button
        const setEndBtn = document.getElementById(`${this.waveformId}-set-end-btn`);
        if (setEndBtn) {
            setEndBtn.addEventListener('click', () => {
                this.endButtonClicked = true;
            });
        }
        
        // Add listeners to existing segment rows
        this.addEventListenersToSegmentRows();
    }
    
    // Start monitoring for waveform selections
    startSelectionMonitoring() {
        setInterval(() => {
            if (window.waveformPlayers && window.waveformPlayers[this.waveformId]) {
                const selection = window.waveformPlayers[this.waveformId].getSelection();
                this.processSelection(selection);
            }
        }, 500);
    }
    
    // Process a selection from the waveform
    processSelection(selection) {
        if (selection.start !== null && selection.end !== null) {
            const selectionString = `${selection.start}-${selection.end}`;
            if (this.lastSelection !== selectionString || this.endButtonClicked) {
                this.currentSelection = selection;
                this.lastSelection = selectionString;
                this.endButtonClicked = false;
                
                // Create segment automatically
                this.createSegmentFromSelection(selection.start, selection.end);
            }
        }
    }
    
    // Create a segment from the current selection
    async createSegmentFromSelection(start, end) {
        console.log(`Creating segment from selection: ${start} - ${end}`);
        
        // Create default name with timestamp
        const segmentName = `Segment ${new Date().toISOString().slice(11, 19)}`;
        
        // Prepare form data
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.csrfToken);
        formData.append('name', segmentName);
        formData.append('onset', start.toFixed(6));
        formData.append('offset', end.toFixed(6));
        formData.append('notes', '');
        
        try {
            // Send request to server
            const response = await fetch(`/segments/${this.recordingId}/add/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Add to segments array
                this.segments.push(data.segment);
                
                // Update UI
                this.updateSegmentsDisplay();
                this.updateWaveformDisplay();
                
                // Show success message
                this.showMessage('success', 'Segment added successfully');
            } else {
                this.showMessage('danger', data.error || 'Failed to add segment');
            }
        } catch (error) {
            console.error('Error creating segment:', error);
            this.showMessage('danger', `Error: ${error.message}`);
        }
    }
    
    // Handle segment form submission
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const segmentId = formData.get('id');
        
        try {
            let url;
            if (segmentId) {
                // Edit existing segment
                url = `/segments/${segmentId}/edit/`;
            } else {
                // Add new segment
                url = `/segments/${this.recordingId}/add/`;
            }
            
            // Add CSRF token if not present
            if (!formData.has('csrfmiddlewaretoken')) {
                formData.append('csrfmiddlewaretoken', this.csrfToken);
            }
            
            // Send request
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                if (segmentId) {
                    // Update existing segment
                    const index = this.segments.findIndex(s => s.id == segmentId);
                    if (index !== -1) {
                        this.segments[index] = data.segment;
                    }
                } else {
                    // Add new segment
                    this.segments.push(data.segment);
                }
                
                // Update UI
                this.updateSegmentsDisplay();
                this.updateWaveformDisplay();
                this.hideSegmentForm();
                
                // Show success message
                this.showMessage('success', segmentId ? 'Segment updated successfully' : 'Segment added successfully');
            } else {
                this.showMessage('danger', data.error || 'Failed to save segment');
            }
        } catch (error) {
            console.error('Error saving segment:', error);
            this.showMessage('danger', `Error: ${error.message}`);
        }
    }
    
    // Delete a segment
    async deleteSegment(segmentId) {
        if (!confirm('Are you sure you want to delete this segment?')) {
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.csrfToken);
            
            // Send request
            const response = await fetch(`/segments/${segmentId}/delete/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Remove from segments array
                this.segments = this.segments.filter(segment => segment.id != segmentId);
                
                // Update UI
                this.updateSegmentsDisplay();
                this.updateWaveformDisplay();
                
                // Show success message
                this.showMessage('success', 'Segment deleted successfully');
            } else {
                this.showMessage('danger', data.error || 'Failed to delete segment');
            }
        } catch (error) {
            console.error('Error deleting segment:', error);
            this.showMessage('danger', `Error: ${error.message}`);
        }
    }
    
    // Show segment edit form
    showSegmentForm(mode, data) {
        const segmentFormCard = document.getElementById('segment-form-card');
        const segmentFormTitle = document.getElementById('segment-form-title');
        const segmentId = document.getElementById('segment-id');
        const segmentName = document.getElementById('segment-name');
        const segmentOnset = document.getElementById('segment-onset');
        const segmentOffset = document.getElementById('segment-offset');
        const segmentNotes = document.getElementById('segment-notes');
        
        if (!segmentFormCard) return;
        
        // Set form title
        segmentFormTitle.textContent = mode === 'add' ? 'Add Segment' : 'Edit Segment';
        
        // Set form values
        segmentId.value = data.id || '';
        segmentName.value = data.name || '';
        segmentOnset.value = data.onset.toFixed(6);
        segmentOffset.value = data.offset.toFixed(6);
        segmentNotes.value = data.notes || '';
        
        // Show form
        segmentFormCard.style.display = 'block';
        segmentFormCard.scrollIntoView({ behavior: 'smooth' });
        
        this.isEditing = true;
    }
    
    // Hide segment edit form
    hideSegmentForm() {
        const segmentFormCard = document.getElementById('segment-form-card');
        const segmentForm = document.getElementById('segment-form');
        
        if (!segmentFormCard || !segmentForm) return;
        
        segmentFormCard.style.display = 'none';
        segmentForm.reset();
        this.isEditing = false;
    }
    
    // Update segments list in UI
    updateSegmentsDisplay() {
        const segmentsList = document.getElementById('segments-list');
        const segmentsCount = document.getElementById('segments-count');
        const noSegmentsMessage = document.getElementById('no-segments-message');
        const createTasksBtn = document.getElementById('create-tasks-btn');
        const tableContainer = document.querySelector('#segments-container .table-responsive');
        
        if (!segmentsList) return;
        
        // Clear existing list
        segmentsList.innerHTML = '';
        
        // Add rows for each segment
        this.segments.forEach(segment => {
            const row = document.createElement('tr');
            row.id = `segment-row-${segment.id}`;
            row.dataset.segmentId = segment.id;
            
            row.innerHTML = `
                <td>${segment.id}</td>
                <td>${segment.onset.toFixed(2)}s - ${segment.offset.toFixed(2)}s</td>
                <td>${(segment.offset - segment.onset).toFixed(2)}s</td>
                <td>
                    <div class="segment-actions" data-segment-id="${segment.id}" 
                         data-onset="${segment.onset}" data-offset="${segment.offset}"
                         data-name="${segment.name || ''}" data-notes="${segment.notes || ''}"></div>
                </td>
            `;
            
            segmentsList.appendChild(row);
        });
        
        // Add event listeners to buttons
        this.addEventListenersToSegmentRows();
        
        // Update segment count
        if (segmentsCount) {
            segmentsCount.textContent = this.segments.length;
        }
        
        // Show/hide table and message
        if (tableContainer && noSegmentsMessage) {
            if (this.segments.length > 0) {
                tableContainer.style.display = 'block';
                noSegmentsMessage.style.display = 'none';
                
                // Enable create tasks button
                if (createTasksBtn) {
                    createTasksBtn.classList.remove('disabled');
                    createTasksBtn.removeAttribute('disabled');
                }
            } else {
                tableContainer.style.display = 'none';
                noSegmentsMessage.style.display = 'block';
                
                // Disable create tasks button
                if (createTasksBtn) {
                    createTasksBtn.classList.add('disabled');
                    createTasksBtn.setAttribute('disabled', 'disabled');
                }
            }
        }
    }
    
    // Update waveform display with segments
    updateWaveformDisplay() {
        if (window.waveformPlayers && window.waveformPlayers[this.waveformId]) {
            const player = window.waveformPlayers[this.waveformId];
            
            // Format segments for the waveform player
            const playerSegments = this.segments.map(segment => ({
                id: segment.id,
                onset: segment.onset,
                offset: segment.offset
            }));
            
            // Update the waveform player
            player.setSegments(playerSegments);
        }
    }
    
    // Render action buttons for a segment
    renderSegmentActionButtons(segmentActionsContainer) {
        if (!segmentActionsContainer) return;
        
        // Get segment data from the container
        const segmentId = segmentActionsContainer.dataset.segmentId;
        const onset = parseFloat(segmentActionsContainer.dataset.onset);
        const offset = parseFloat(segmentActionsContainer.dataset.offset);
        const name = segmentActionsContainer.dataset.name || '';
        const notes = segmentActionsContainer.dataset.notes || '';
        
        // Create button group wrapper
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'btn-group btn-group-sm';
        
        // Create play button
        const playButton = document.createElement('button');
        playButton.className = 'btn btn-success play-segment-btn mr-1';
        playButton.innerHTML = '<i class="fas fa-play"></i>';
        playButton.dataset.onset = onset;
        playButton.dataset.offset = offset;
        
        // Add click event for play button
        playButton.addEventListener('click', () => {
            // Play segment using waveform player
            if (window.waveformPlayers && window.waveformPlayers[this.waveformId]) {
                const player = window.waveformPlayers[this.waveformId].player;
                if (player && player.playRegion) {
                    player.playRegion(onset, offset);
                }
            }
        });
        
        // Create edit button
        const editButton = document.createElement('button');
        editButton.className = 'btn btn-warning edit-segment-btn mr-1';
        editButton.innerHTML = '<i class="fas fa-edit"></i>';
        editButton.dataset.segmentId = segmentId;
        editButton.dataset.segmentName = name;
        editButton.dataset.segmentOnset = onset;
        editButton.dataset.segmentOffset = offset;
        editButton.dataset.segmentNotes = notes;
        
        // Add click event for edit button
        editButton.addEventListener('click', () => {
            this.showSegmentForm('edit', {
                id: segmentId,
                name: name,
                onset: onset,
                offset: offset,
                notes: notes
            });
        });
        
        // Create delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-danger delete-segment-btn';
        deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
        deleteButton.dataset.segmentId = segmentId;
        
        // Add click event for delete button
        deleteButton.addEventListener('click', () => {
            this.deleteSegment(segmentId);
        });
        
        // Append all buttons to the group
        buttonGroup.appendChild(playButton);
        buttonGroup.appendChild(editButton);
        buttonGroup.appendChild(deleteButton);
        
        // Clear and append the button group to the container
        segmentActionsContainer.innerHTML = '';
        segmentActionsContainer.appendChild(buttonGroup);
    }
    
    // Add event listeners to segment rows and render action buttons
    addEventListenersToSegmentRows() {
        // Find all segment action containers
        const actionContainers = document.querySelectorAll('.segment-actions');
        
        // Render buttons for each container
        actionContainers.forEach(container => {
            this.renderSegmentActionButtons(container);
        });
    }
    
    // Show a toast message
    showMessage(type, message) {
        const messagesContainer = document.querySelector('.messages');
        if (!messagesContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = 'alert';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        messagesContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Check if running in browser
if (typeof window !== 'undefined') {
    // Make the class available globally
    window.SegmentManager = SegmentManager;
}

// Export for ES modules
export { SegmentManager };
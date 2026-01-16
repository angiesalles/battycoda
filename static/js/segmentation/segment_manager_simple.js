/**
 * BattyCoda Segment Manager - Simple & Clean
 *
 * Main controller for segment management functionality
 */

import { SegmentCRUD } from './segment_crud.js';
import { SegmentDisplay } from './segment_display.js';
import { SegmentSearchPagination } from './segment_search_pagination.js';
import { escapeHtml } from '../utils/html.js';

export class SegmentManager {
  constructor(options) {
    // Configuration
    this.recordingId = options.recordingId;
    this.segmentationId = options.segmentationId;
    this.playerId = options.waveformId || 'segment-waveform';
    this.csrfToken = options.csrfToken;
    this.readOnly = options.readOnly || false;

    // Initialize modules
    this.crud = new SegmentCRUD(this.segmentationId, this.csrfToken);
    this.display = new SegmentDisplay(this.playerId, this.readOnly);
    this.searchPagination = new SegmentSearchPagination();

    // State
    this.segments = options.segments || [];
    this.currentSelection = null;

    // Debug logging
    console.log('SegmentManager initialized with', this.segments.length, 'segments');
    console.log('Initial segments:', this.segments);
    console.log('Read-only mode:', this.readOnly);

    // Initialize
    this.initializeEventHandlers();
    this.initializeSearchAndPagination();

    // Wait for waveform player to be ready before updating display
    this.waitForWaveformPlayer().then(() => {
      this.updateDisplay();
    });
  }

  // Wait for player to be ready
  async waitForWaveformPlayer() {
    return new Promise((resolve) => {
      const checkPlayer = () => {
        if (
          window.players &&
          window.players[this.playerId] &&
          window.players[this.playerId].player &&
          window.players[this.playerId].player.duration > 0
        ) {
          console.log('Player is ready');
          resolve();
        } else {
          console.log('Waiting for player...');
          setTimeout(checkPlayer, 100);
        }
      };
      checkPlayer();
    });
  }

  // Initialize event handlers
  initializeEventHandlers() {
    // Selection monitoring for waveform (only in edit mode)
    if (!this.readOnly) {
      this.startSelectionMonitoring();
    }
  }

  // Initialize search and pagination
  initializeSearchAndPagination() {
    // Set up page change handler
    this.display.setPageChangeHandler((page) => {
      this.searchPagination.setPage(page);
      this.updateSegmentsList();
    });

    // Set up search input handlers
    const searchId = document.getElementById('segment-search-id');
    const minDuration = document.getElementById('segment-search-min-duration');
    const maxDuration = document.getElementById('segment-search-max-duration');
    const clearBtn = document.getElementById('segment-search-clear');

    const applyFilters = () => {
      this.searchPagination.updateFilters({
        id: searchId?.value || '',
        minDuration: minDuration?.value ? parseFloat(minDuration.value) : null,
        maxDuration: maxDuration?.value ? parseFloat(maxDuration.value) : null,
      });
      this.updateSegmentsList();
    };

    // Debounce search inputs
    let searchTimeout;
    const debouncedSearch = () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(applyFilters, 300);
    };

    if (searchId) searchId.addEventListener('input', debouncedSearch);
    if (minDuration) minDuration.addEventListener('input', debouncedSearch);
    if (maxDuration) maxDuration.addEventListener('input', debouncedSearch);

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (searchId) searchId.value = '';
        if (minDuration) minDuration.value = '';
        if (maxDuration) maxDuration.value = '';
        this.searchPagination.clearFilters();
        this.updateSegmentsList();
      });
    }
  }

  // Monitor player selection
  startSelectionMonitoring() {
    setInterval(() => {
      this.checkPlayerSelection();
    }, 200);
  }

  // Check if player has complete selection
  checkPlayerSelection() {
    const playerWrapper = window.players?.[this.playerId];
    if (!playerWrapper?.player) return;

    const player = playerWrapper.player;

    // Check if both selection points are set
    if (player.selectionStart !== null && player.selectionEnd !== null) {
      // Only create segment if selection has changed
      if (
        !this.currentSelection ||
        this.currentSelection.start !== player.selectionStart ||
        this.currentSelection.end !== player.selectionEnd
      ) {
        this.currentSelection = {
          start: player.selectionStart,
          end: player.selectionEnd,
        };
        this.createSegmentFromSelection();
      }
    }
  }

  // Automatically create segment from current selection
  async createSegmentFromSelection() {
    if (!this.currentSelection) return;

    const segmentData = {
      onset: this.currentSelection.start,
      offset: this.currentSelection.end,
      name: '',
      notes: '',
    };

    try {
      const newSegment = await this.crud.createSegment(segmentData);
      this.segments.push(newSegment);
      this.segments.sort((a, b) => a.onset - b.onset);

      // Clear selection
      const playerWrapper = window.players[this.playerId];
      if (playerWrapper?.player) {
        playerWrapper.player.selectionStart = null;
        playerWrapper.player.selectionEnd = null;
        playerWrapper.player.updateSelectionDisplay();
        playerWrapper.player.redrawCurrentView();
      }
      this.currentSelection = null;

      this.updateDisplay();
      this.showMessage('success', 'Segment created successfully');
    } catch (error) {
      this.showMessage('danger', `Error creating segment: ${error.message}`);
    }
  }

  // Delete segment
  async deleteSegment(segmentId) {
    if (!confirm('Are you sure you want to delete this segment?')) return;

    try {
      await this.crud.deleteSegment(segmentId);
      this.segments = this.segments.filter((segment) => segment.id !== segmentId);
      this.updateDisplay();
      this.showMessage('success', 'Segment deleted successfully');
    } catch (error) {
      this.showMessage('danger', `Error: ${error.message}`);
    }
  }

  // Play a specific segment
  playSegment(onset, offset) {
    const player = window.players[this.playerId];
    if (player?.player?.playRegion) {
      player.player.playRegion(onset, offset);
    }
  }

  // Update all displays
  updateDisplay() {
    this.updatePlayerDisplay();
    this.updateSegmentsList();
  }

  // Update player display
  updatePlayerDisplay() {
    const playerWrapper = window.players[this.playerId];
    if (!playerWrapper) return;

    // Update waveform with current segments
    const playerSegments = this.segments.map((segment) => ({
      id: segment.id,
      onset: segment.onset,
      offset: segment.offset,
    }));

    if (playerWrapper.setSegments) {
      playerWrapper.setSegments(playerSegments);
    }
  }

  // Update segments list display
  updateSegmentsList() {
    // Apply search/filter
    const filteredSegments = this.searchPagination.filterSegments(this.segments);

    // Get current page of segments
    const pageSegments = this.searchPagination.getCurrentPage();

    // Get pagination info
    const paginationInfo = this.searchPagination.getPaginationInfo();

    // Render the list with pagination
    this.display.renderSegmentsList(pageSegments, paginationInfo);
    this.display.updateSegmentsCount(filteredSegments.length);
  }

  // Refresh segments list (public method for external calls)
  refreshSegmentsList() {
    this.updateSegmentsList();
  }

  // Show message
  showMessage(type, message) {
    console.log(`${type.toUpperCase()}: ${message}`);

    const messagesContainer = document.querySelector('.messages');
    if (messagesContainer) {
      const alertDiv = document.createElement('div');
      alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
      alertDiv.innerHTML = `
                ${escapeHtml(message)}
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

/**
 * BattyCoda Main Entry Point
 *
 * This file is the main entry point for Vite bundling.
 * It imports and initializes core utilities that should be available on all pages.
 *
 * Feature-specific modules (player, segmentation, clustering, etc.) are loaded
 * separately on the pages that need them for better code splitting.
 */

// Core utilities that run on every page
// These are imported for their side effects (they self-initialize on DOMContentLoaded)

// Date/time formatting - converts UTC timestamps to local time
import './datetime_formatter.js';

// Theme switcher - allows users to switch between Maisonnette themes
import './theme-switcher.js';

// Notifications - handles navbar notification loading and updates
import './notifications.js';

/**
 * Feature modules (dynamically imported where needed):
 *
 * - player/          : Waveform audio player with spectrogram support
 * - segmentation/    : Segment management and editing
 * - cluster_explorer/: Interactive cluster visualization with D3
 * - cluster_mapping/ : Cluster-to-call-type mapping interface
 * - file_upload/     : Advanced file upload with progress tracking
 *
 * These modules are loaded via separate entry points to enable code splitting.
 * Pages that need them will import them directly.
 */

console.log('BattyCoda initialized');

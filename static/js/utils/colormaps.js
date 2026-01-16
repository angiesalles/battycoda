/**
 * Colormap definitions for BattyCoda spectrograms.
 *
 * Single source of truth is static/data/colormaps.json which is consumed
 * by both Python (battycoda_app/audio/colormaps.py) and JavaScript (here).
 */

import colormaps from '../../data/colormaps.json';

export const ROSEUS_COLORMAP = colormaps.roseus;

"""
Colormap definitions for BattyCoda spectrograms.

Single source of truth is static/data/colormaps.json which is consumed
by both Python (here) and JavaScript (static/js/utils/colormaps.js).
"""

import json
from pathlib import Path

# Load colormap from JSON - single source of truth
_COLORMAP_JSON_PATH = Path(__file__).parent.parent.parent / "static" / "data" / "colormaps.json"

with open(_COLORMAP_JSON_PATH) as f:
    _COLORMAPS = json.load(f)

ROSEUS_COLORMAP = _COLORMAPS["roseus"]

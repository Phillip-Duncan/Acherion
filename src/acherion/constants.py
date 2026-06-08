"""Layout constants for Acherion."""

from __future__ import annotations

# Canvas layout dimensions (used for node seeding positions).
_CANVAS_MIN_HEIGHT = 980
_CANVAS_MIN_WIDTH = 1600

# World half-extent around the hidden origin.
# The rendered stage is twice this size so nodes can move into negative space
# without exposing a visible board edge during normal use.
_CANVAS_WORLD_WIDTH = 8000
_CANVAS_WORLD_HEIGHT = 6000

# Node layout.
_NODE_WIDTH = 360
_NODE_TOP = 20
_NODE_STEP = 320

# Column positions for each dock group.
_SOURCE_X = 40
_MANUAL_X = 460
_MANUAL_Y = 120
_SINK_RIGHT = 40
_SINK_X = _CANVAS_MIN_WIDTH - _NODE_WIDTH - _SINK_RIGHT

# Node group colour palette (assigned in round-robin order, skip used ones).
_GROUP_COLOURS: tuple[str, ...] = (
    '#1d9bf0',  # blue
    '#00ba7c',  # green
    '#ffd400',  # yellow
    '#f4212e',  # red
    '#a855f7',  # purple
    '#f97316',  # orange
    '#06b6d4',  # cyan
    '#ec4899',  # pink
)

# Default drag offset used when the server triggers drag start.
_DROP_X_OFFSET = 120
_DROP_Y_OFFSET = 20

# Shared visual and snap spacing for the free-move canvas grid.
_GRID_SNAP_SIZE = 20

# Pin geometry (used for static fallback SVG paths).
_HEADER_HEIGHT = 60
_BODY_TOP_PADDING = 0
_PIN_ROW_HEIGHT = 40
_PIN_CENTER_OFFSET = 20
_PIN_EDGE_OFFSET = 20

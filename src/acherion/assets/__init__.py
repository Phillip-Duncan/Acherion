"""Bundled CSS and client JavaScript for Acherion surfaces."""

from __future__ import annotations

from acherion.constants import _CANVAS_WORLD_WIDTH, _GRID_SNAP_SIZE
from acherion.assets.css import CHROME_CSS, NODE_CSS, SEARCH_CSS, WORKBENCH_CSS
from acherion.assets.js import CLIENT_JS


def _build_css_bundle() -> str:
    """Return the compiled CSS bundle for the designer workbench."""
    return '\n'.join((SEARCH_CSS, WORKBENCH_CSS, NODE_CSS, CHROME_CSS)).replace(
        '__CANVAS_STAGE_WIDTH__',
        str(_CANVAS_WORLD_WIDTH * 2),
    ).replace('__ACH_GRID_SNAP_SIZE__', str(_GRID_SNAP_SIZE))


_ACH_CSS = _build_css_bundle()
_ACH_CLIENT_JS = CLIENT_JS.replace(
    '__ACH_GRID_SNAP_SIZE__',
    str(_GRID_SNAP_SIZE),
)

__all__ = ['_ACH_CLIENT_JS', '_ACH_CSS']
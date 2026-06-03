"""Shared constants and helpers for visual-logic render mixins."""

from __future__ import annotations

from typing import Any

from nicegui import ui

_DEFAULT_NODE_HEIGHT = 108
_NODE_BODY_GAP = 8
_FUNCTION_BOX_TOP_PAD = 126
_FUNCTION_BOX_SIDE_PAD = 176
_FUNCTION_BOX_SIDE_PAD_COMPACT = 40
_FUNCTION_BOX_BOTTOM_PAD = 40
_FUNCTION_BOX_MIN_WIDTH = 720
_FUNCTION_BOX_MIN_WIDTH_COMPACT = 440
_FUNCTION_BOX_MIN_HEIGHT = 260
_FUNCTION_BOX_PORT_TOP = 122
_FUNCTION_BOX_PORT_CARD_HEIGHT = 40
_FUNCTION_BOX_PORT_GAP = 8
_FUNCTION_BOX_PORT_BOTTOM_PAD = 24
_GROUP_FRAME_SIDE_PAD = 28
_GROUP_FRAME_TOP_PAD = 46
_GROUP_FRAME_BOTTOM_PAD = 28

FUNCTION_PORT_TYPE_OPTIONS: dict[str, str] = {
    'any': 'any',
    'float': 'float',
    'bool': 'bool',
    'str': 'str',
    'list': 'list',
    'np.ndarray': 'np.ndarray',
    'object': 'object',
    'Figure': 'Figure',
}


def render_acherion_icon(
    icon: str,
    *,
    classes: str,
    style: str = '',
) -> Any:
    """Render either a Material icon name or inline SVG markup."""
    icon_text = str(icon or '').strip()
    if icon_text.startswith('<svg'):
        element = ui.html(icon_text, sanitize=False).classes(classes)
    else:
        element = ui.icon(icon_text).classes(classes)
    if style:
        element.style(style)
    return element

"""Standalone theme helpers for the extracted Acherion workbench."""

from __future__ import annotations

from collections.abc import Mapping

from nicegui import ui

from acherion.theme import (
    acherion_ui_colors,
    build_acherion_theme_override_css,
    build_scoped_acherion_theme_css,
)

_STANDALONE_LAYOUT_CSS = """
.nicegui-content {
    padding: 0 !important;
    gap: 0 !important;
    align-items: stretch !important;
}
.ach-standalone-page {
    min-height: 100vh;
    width: 100%;
    padding: 16px;
    box-sizing: border-box;
    background: var(--oe-bg);
}
.ach-standalone-page .ach-workbench {
    min-height: calc(100vh - 32px);
    height: calc(100vh - 32px);
    max-height: none;
}
"""


def apply_standalone_theme(
    theme_overrides: Mapping[str, str] | None = None,
) -> None:
    """Inject standalone CSS for the Acherion workbench."""
    ui.colors(**acherion_ui_colors(theme_overrides))
    ui.add_css(build_scoped_acherion_theme_css(':root'))
    ui.add_css(
        build_acherion_theme_override_css(
            scope_selector=':root',
            theme_overrides=theme_overrides,
        )
    )
    ui.add_css(_STANDALONE_LAYOUT_CSS)

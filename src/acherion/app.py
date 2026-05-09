"""Standalone NiceGUI launcher for the extracted Acherion workbench."""

from __future__ import annotations

from functools import cache

import acherion.api.completions  # noqa: F401 - registers editor endpoints
import acherion.embed as acherion_embed
from nicegui import ui

from acherion.standalone_host import (
    StandaloneAcherionHost,
    load_acherion_graph_namespace,
    run_standalone_acherion_preview,
    standalone_editor_visible_code,
)
from acherion.standalone_theme import apply_standalone_theme


@cache
def _register_pages() -> None:
    """Register the standalone fullscreen workbench page once."""
    @ui.page('/')
    def index_page() -> None:
        """Render the standalone Acherion workbench page."""
        workbench: acherion_embed.AcherionWorkbench | None = None

        def _run_preview() -> bool:
            if workbench is None:
                return False
            designer = workbench.designer
            try:
                preview_result = run_standalone_acherion_preview(
                    designer.graph_state(),
                    bindings=designer.preview_bindings(),
                )
            except Exception as exc:
                designer.set_status_message(
                    f'Preview run failed: {exc}',
                    negative=True,
                )
                return False
            designer.apply_preview_result(preview_result)
            status_text = str(
                preview_result.state_values.get('hint') or 'Preview updated.'
            ).strip()
            designer.set_status_message(status_text or 'Preview updated.')
            return True

        def _handle_change() -> None:
            _run_preview()

        workbench = acherion_embed.AcherionWorkbench(
            host=StandaloneAcherionHost(),
            on_change=_handle_change,
            on_run_preview=_run_preview,
            before_build=apply_standalone_theme,
            container_classes='ach-standalone-page',
            code_editor_theme='vscodeDark',
            code_editor_classes=(
                'w-full h-full oe-code-editor ach-standalone-code-view'
            ),
            code_editor_style='height:100%; min-height:0',
            code_transform=standalone_editor_visible_code,
            refresh_code_on_change=True,
            refresh_code_after_build=True,
            validate_generated_code=load_acherion_graph_namespace,
            apply_to_code_status_message='Generated code refreshed.',
            session_storage_key='acherion.preferences',
        )
        workbench.build()
        _run_preview()


def main(
    host: str = '127.0.0.1',
    port: int = 8081,
    reload: bool = False,
) -> None:
    """Run the standalone NiceGUI workbench."""
    _register_pages()
    ui.run(host=host, port=port, reload=reload, title='Acherion')

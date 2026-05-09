"""AcherionDesigner - NiceGUI component for the Acherion graph."""

# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

import uuid
from typing import Any, Callable

from nicegui.client import Client

from acherion.constants import (
    _DROP_X_OFFSET,
    _DROP_Y_OFFSET,
)
from acherion.host import AcherionHost
from acherion.embed.designer.interactions import (
    _DesignerInteractionsMixin,
)
from acherion.embed.designer.shell import (
    _DesignerShellMixin,
)
from acherion.graphops.catalog import (
    _GraphOpsCatalogMixin,
)
from acherion.graphops.connections import (
    _GraphOpsConnectionsMixin,
)
from acherion.graphops.function_boxes import (
    _GraphOpsFunctionBoxesMixin,
)
from acherion.graphops.pins import _GraphOpsPinsMixin
from acherion.graphops.ops import _GraphOpsMixin
from acherion.model import (
    AcherionGraph,
)
from acherion.embed.render.editor import (
    _RenderEditorMixin,
)
from acherion.embed.render.layout import (
    _RenderLayoutMixin,
)
from acherion.embed.render.nodes import (
    _RenderNodesMixin,
)
from acherion.embed.render.pins import _RenderPinsMixin


class AcherionDesigner(  # pyright: ignore
    _DesignerShellMixin,
    _DesignerInteractionsMixin,
    _GraphOpsCatalogMixin,
    _GraphOpsFunctionBoxesMixin,
    _GraphOpsPinsMixin,
    _GraphOpsConnectionsMixin,
    _GraphOpsMixin,
    _RenderLayoutMixin,
    _RenderPinsMixin,
    _RenderEditorMixin,
    _RenderNodesMixin,
):
    """NiceGUI editor for the visual-logic graph."""

    def __init__(
        self,
        *,
        host: AcherionHost | None = None,
        on_change: Callable[[], None] | None = None,
        on_apply_to_code: Callable[[], None] | None = None,
        on_run_preview: Callable[[], bool] | None = None,
        on_validate: Callable[[], bool] | None = None,
        build_code_view: Callable[[], None] | None = None,
        on_mode_change: Callable[[str], None] | None = None,
        initial_mode: str = 'graph',
    ) -> None:
        self._graph = AcherionGraph()
        self._host = host
        self._on_change = on_change
        self._on_apply_to_code = on_apply_to_code
        self._on_run_preview = on_run_preview
        self._on_validate = on_validate
        self._build_code_view = build_code_view
        self._on_mode_change = on_mode_change
        self._editor_mode: str = initial_mode
        self._preview_bindings: dict[str, dict[str, Any]] = {}
        self._preview_reference_values: dict[str, Any] = {}
        self._preview_state_values: dict[str, Any] = {}
        self._canvas_el: Any = None
        self._graph_host_el: Any = None
        self._code_host_el: Any = None
        self._mode_toggle_btn: Any = None
        self._hint_label: Any = None
        self._status_override_text: str | None = None  # type: ignore[assignment]
        self._status_override_negative: bool = False
        self._drag_node_id: str | None = None  # type: ignore[assignment]
        self._drag_offset_x: int = _DROP_X_OFFSET
        self._drag_offset_y: int = _DROP_Y_OFFSET
        self._pending_source_node_id: str | None = None  # type: ignore[assignment]
        self._selected_connection_id: str | None = None
        self._selected_node_ids: set[str] = set()
        # Context menu state.
        self._ctx_menu_node_id = None
        self._ctx_menu_cx: int = 0
        self._ctx_menu_cy: int = 0
        self._ctx_container_el: Any = None
        self._overlay_host_el: Any = None
        self._ctx_menu_query: str = ''
        self._ctx_align_query: str = ''
        self._palette_query: str = ''
        self._css_injected: bool = False
        self._client_js_injected: bool = False
        self._client: Client | None = None  # type: ignore[assignment]
        self._redraw_revision: int = 0
        dom_token = uuid.uuid4().hex[:8]
        self._frame_dom_id = f'ach-workbench-{dom_token}'
        self._viewport_dom_id = f'ach-shell-{dom_token}'
        self._canvas_dom_id = f'ach-canvas-{dom_token}'
        self._palette_dom_id = f'ach-palette-{dom_token}'

    @property
    def frame_dom_id(self) -> str:
        """Return the stable DOM id for the root workbench element."""
        return self._frame_dom_id

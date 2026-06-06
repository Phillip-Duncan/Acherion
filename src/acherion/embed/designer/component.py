"""AcherionDesigner - NiceGUI component for the Acherion graph."""

# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

import json
import uuid
from typing import Any, Callable

from nicegui.client import Client

import acherion.preferences as acherion_preferences
from acherion.constants import (
    _DROP_X_OFFSET,
    _DROP_Y_OFFSET,
)
from acherion.host import AcherionHost
from acherion.embed.designer.interactions import (
    _DesignerInteractionsMixin,
)
from acherion.embed.designer.preferences_dialog import (
    _DesignerPreferencesDialogMixin,
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
    _graph_to_dict,
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
    _DesignerPreferencesDialogMixin,
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
        on_local_change: Callable[[], None] | None = None,
        on_apply_to_code: Callable[[], None] | None = None,
        on_run_preview: Callable[[], bool] | None = None,
        on_validate: Callable[[], bool] | None = None,
        build_code_view: Callable[[], None] | None = None,
        on_mode_change: Callable[[str], None] | None = None,
        preferences_state: (
            acherion_preferences.AcherionPreferencesState | None
        ) = None,
        on_preferences_change: Callable[
            [dict[str, dict[str, str]]],
            None,
        ] | None = None,
        on_preferences_preview: Callable[
            [dict[str, dict[str, str]]],
            None,
        ] | None = None,
        initial_mode: str = 'graph',
    ) -> None:
        self._graph = AcherionGraph()
        self._host = host
        self._on_change = on_change
        self._on_local_change = on_local_change
        self._on_apply_to_code = on_apply_to_code
        self._on_run_preview = on_run_preview
        self._on_validate = on_validate
        self._build_code_view = build_code_view
        self._on_mode_change = on_mode_change
        self._preferences_state = (
            preferences_state
            or acherion_preferences.AcherionPreferencesState()
        )
        self._on_preferences_change = on_preferences_change
        self._on_preferences_preview = on_preferences_preview
        self._editor_mode: str = initial_mode
        self._preview_bindings: dict[str, dict[str, Any]] = {}
        self._preview_reference_values: dict[str, Any] = {}
        self._preview_state_values: dict[str, Any] = {}
        self._pending_inline_local_change: bool = False
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
        self._palette_collapsed_categories: set[str] = set()
        self._preferences_dialog: Any = None
        self._preferences_search_query: str = ''
        self._preferences_active_category: str = 'Appearance'
        self._preferences_draft = self._preferences_state.to_dict()
        self._preferences_saved_snapshot = self._preferences_state.to_dict()
        self._preferences_commit_on_close: bool = False
        self._preferences_capture_shortcut_id: str | None = None
        self._preferences_nav_container: Any = None
        self._preferences_content_container: Any = None
        self._help_topics_container: Any = None
        self._help_content_container: Any = None
        self._help_search_query: str = ''
        self._help_active_topic: str = 'getting_started'
        self._clipboard_snapshot: dict[str, Any] | None = None
        self._clipboard_paste_count: int = 0
        initial_graph_data = _graph_to_dict(self._graph)
        self._history_undo: list[dict[str, Any]] = [
            {
                'graph': initial_graph_data,
                'selected_node_ids': [],
                'selected_connection_id': None,
            }
        ]
        self._history_redo: list[dict[str, Any]] = []
        self._history_last_graph_token: str = json.dumps(
            initial_graph_data,
            sort_keys=True,
            separators=(',', ':'),
        )
        self._history_suspended: bool = False
        self._css_injected: bool = False
        self._client_js_injected: bool = False
        self._client: Client | None = None  # type: ignore[assignment]
        self._redraw_revision: int = 0
        self._graph_cache_revision: int = 0
        self._connection_specs_cache_revision: int = -1
        self._connection_specs_cache: list[dict[str, Any]] | None = None
        self._outgoing_source_refs_cache: set[tuple[str, int]] = set()
        self._input_pin_specs_cache: dict[
            str,
            tuple[int, list[dict[str, str]]],
        ] = {}
        self._output_pin_specs_cache: dict[
            str,
            tuple[int, list[dict[str, str]]],
        ] = {}
        self._node_bounds_cache_revision: int = -1
        self._node_bounds_cache: dict[str, tuple[int, int, int, int]] = {}
        self._function_box_bounds_cache: dict[
            str,
            tuple[int, int, int, int],
        ] = {}
        self._node_lookup_cache_revision: int = -1
        self._node_lookup_cache: dict[str, AcherionNode] = {}
        dom_token = uuid.uuid4().hex[:8]
        self._frame_dom_id = f'ach-workbench-{dom_token}'
        self._viewport_dom_id = f'ach-shell-{dom_token}'
        self._canvas_dom_id = f'ach-canvas-{dom_token}'
        self._palette_dom_id = f'ach-palette-{dom_token}'

    @property
    def frame_dom_id(self) -> str:
        """Return the stable DOM id for the root workbench element."""
        return self._frame_dom_id

    def run_client_javascript(
        self,
        code: str,
        *,
        timeout: float = 1.0,
    ) -> None:
        """Run one client-side JavaScript snippet through the designer."""
        self._run_client_javascript(code, timeout=timeout)

    def set_session_storage_item(self, key: str, value: str) -> None:
        """Store one string value in session storage for this client."""
        payload = json.dumps({'key': key, 'value': value})
        self.run_client_javascript(
            '(() => {'
            f'const payload = {payload};'
            'try {'
            '  sessionStorage.setItem(payload.key, payload.value);'
            '} catch (_error) {'
            '}'
            '})();'
        )

    async def get_session_storage_item(self, key: str) -> str:
        """Read one string value from session storage for this client."""
        client = self._client
        if client is None:
            return ''
        result = await client.run_javascript(
            '(() => {'
            'try {'
            f'  return sessionStorage.getItem({key!r}) || "";'
            '} catch (_error) {'
            '  return "";'
            '}'
            '})();',
            timeout=3.0,
        )
        if result is None:
            return ''
        return str(result)

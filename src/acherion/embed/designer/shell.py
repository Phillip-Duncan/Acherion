"""Shell and lifecycle mixin for AcherionDesigner."""

# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Literal, cast

from nicegui import background_tasks, ui

from acherion.assets import (
    _ACH_CLIENT_JS,
    _ACH_CSS,
)
from acherion.events import (
    collect_acherion_external_events,
    serializable_acherion_external_events,
)
from acherion.model import (
    AcherionGraph,
    AcherionNode,
    _graph_from_dict,
    _graph_to_dict,
)
from acherion.preview import (
    AcherionPreviewRunResult,
)

if TYPE_CHECKING:
    from nicegui.client import Client


class _DesignerShellMixin:
    """Public API, build, refresh, and notification helpers."""

    _graph: AcherionGraph
    _drag_node_id: str | None = None
    _pending_source_node_id: str | None = None
    _status_override_text: str | None = None
    _status_override_negative: bool = False
    _selected_connection_id: Any = None

    @property
    def mode(self: Any) -> str:
        """Return current Logic Studio view mode."""
        return str(self._editor_mode)

    @property
    def nodes(self) -> list[AcherionNode]:
        """Return the current graph nodes."""
        return self._graph.nodes

    def has_nodes(self: Any) -> bool:
        """Return whether the graph contains any nodes."""
        return bool(self._graph.nodes)

    def has_user_logic(self: Any) -> bool:
        """Return whether graph contains user-authored logic."""
        if any(not self._is_system_node(n) for n in self._graph.nodes):
            return True
        return any(
            self._is_system_sink_node(n)
            and str(n.params.get('source') or '').strip()
            for n in self._graph.nodes
        )

    def _normalize_graph(self: Any) -> None:
        self._sync_manual_schema_keys()
        self._prune_obsolete_function_io_nodes()
        self._sync_system_nodes()
        self._ensure_function_box_entries()
        self._sync_custom_function_nodes()
        self._prune_invalid_exec_connections()

    def set_graph_from_dict(self: Any, data: dict[str, Any] | None) -> None:
        """Replace graph state from persisted builder_state data."""
        self._graph = _graph_from_dict(data)
        self._normalize_graph()
        self.clear_preview_results()
        self.force_redraw()

    def to_dict(self: Any) -> dict[str, Any]:
        """Return the current graph as a serialisable dict."""
        self._normalize_graph()
        return _graph_to_dict(self._graph)

    def graph_state(self: Any) -> AcherionGraph:
        """Return a detached normalized graph snapshot."""
        return _graph_from_dict(self.to_dict())

    def preview_bindings(self: Any) -> dict[str, dict[str, Any]]:
        """Return current transient preview values grouped by scope."""
        return {
            scope: dict(values)
            for scope, values in self._preview_bindings.items()
        }

    def preview_binding_values(self: Any, scope: str) -> dict[str, Any]:
        """Return current transient preview values for one scope."""
        clean_scope = str(scope or '').strip()
        if not clean_scope:
            return {}
        return dict(self._preview_bindings.get(clean_scope, {}))

    def preview_reference_values(self: Any) -> dict[str, Any]:
        """Return latest preview values keyed by opaque runtime reference."""
        return dict(self._preview_reference_values)

    def preview_state_values(self: Any) -> dict[str, Any]:
        """Return latest preview state keyed by host-defined names."""
        return dict(self._preview_state_values)

    def set_preview_binding_value(
        self: Any,
        scope: str,
        key: str,
        value: Any,
    ) -> None:
        """Store one transient preview value by scope and schema key."""
        clean_scope = str(scope or '').strip()
        clean_key = str(key or '').strip()
        if not clean_scope or not clean_key:
            return
        scope_values = self._preview_bindings.setdefault(clean_scope, {})
        scope_values[clean_key] = value
        self._clear_preview_runtime_state()
        self.refresh()
        if self._on_run_preview is not None:
            self._on_run_preview()

    def clear_preview_binding_value(self: Any, scope: str, key: str) -> None:
        """Remove one transient preview value by scope and key."""
        clean_scope = str(scope or '').strip()
        clean_key = str(key or '').strip()
        if not clean_scope or not clean_key:
            return
        scope_values = self._preview_bindings.get(clean_scope)
        if scope_values is not None:
            scope_values.pop(clean_key, None)
            if not scope_values:
                self._preview_bindings.pop(clean_scope, None)
        self._clear_preview_runtime_state()
        self.refresh()
        if self._on_run_preview is not None:
            self._on_run_preview()

    def apply_preview_result(
        self: Any,
        result: AcherionPreviewRunResult,
    ) -> None:
        """Replace the latest runtime preview result for the current graph."""
        self._preview_reference_values = dict(result.reference_values)
        self._preview_state_values = dict(result.state_values)
        self.refresh()
        hint = str(self._preview_state_values.get('hint') or '').strip()
        self._update_hint(hint or 'Preview updated.')

    def clear_preview_results(self: Any) -> None:
        """Clear all transient preview bindings and runtime preview state."""
        self._preview_bindings = {}
        self._clear_preview_runtime_state()

    def _clear_preview_runtime_state(self: Any) -> None:
        """Clear preview values captured from the last preview execution."""
        self._preview_reference_values = {}
        self._preview_state_values = {}

    def generated_user_code(self: Any) -> str:
        """Return the current graph compiled as editor-ready user code."""
        self._normalize_graph()
        if self._host is not None:
            return str(self._host.generated_user_code(self))
        raise RuntimeError(
            'AcherionDesigner requires a host to generate user code.'
        )

    def generated_runtime_bindings(
        self: Any,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Return hidden UI-role bindings for generated graph code."""
        self._normalize_graph()
        if self._host is not None:
            return cast(
                dict[str, dict[str, dict[str, Any]]],
                self._host.generated_runtime_bindings(self),
            )
        return {}

    def generated_external_events(
        self: Any,
    ) -> dict[str, dict[str, str]]:
        """Return hidden external-event metadata for generated graph code."""
        self._normalize_graph()
        return serializable_acherion_external_events(
            collect_acherion_external_events(self._graph.nodes)
        )

    def build(self: Any) -> None:
        """Render the visual-logic designer into current NiceGUI context."""
        self._client = ui.context.client
        self._ensure_css()
        self._ensure_client_js()
        self._normalize_graph()
        with ui.element('div').classes(
            'ach-workbench oe-surface rounded-lg w-full min-w-0'
        ).props(f'id={self._frame_dom_id}'):
            self._render_workbench_menu_bar()
            with ui.element('div').classes('ach-workbench-body'):
                with ui.element('div').classes('ach-workbench-main') as graph_host:
                    self._graph_host_el = graph_host
                    self._render_palette(self._palette_dom_id)
                    with ui.element('div').classes(
                        'ach-sidebar-resizer'
                    ).props(
                        'role=separator aria-orientation=vertical '
                        'title="Drag to resize node sidebar. '
                        'Double-click to reset width."'
                    ) as resize_handle:
                        resize_handle.on(
                            'pointerdown',
                            lambda _e: None,
                            js_handler=(
                                '(e) => {'
                                'window.__oeAcherion?.beginSidebarResize('
                                'e.currentTarget, e.clientX);'
                                'e.preventDefault();'
                                'e.stopPropagation();'
                                '}'
                            ),
                        )
                        resize_handle.on(
                            'dblclick',
                            lambda _e: None,
                            js_handler=(
                                '(e) => {'
                                'window.__oeAcherion?.resetSidebarWidth('
                                'e.currentTarget.closest(".ach-workbench")'
                                ');'
                                'e.preventDefault();'
                                'e.stopPropagation();'
                                '}'
                            ),
                        )
                        ui.element('div').classes('ach-sidebar-resizer-grip')
                    with ui.element('div').classes('ach-shell').props(
                        f'tabindex=0 id={self._viewport_dom_id}'
                    ) as viewport:
                        self._attach_viewport_events(viewport)
                        self._canvas_el = ui.element('div').classes(
                            'ach-canvas'
                        ).props(f'tabindex=0 id={self._canvas_dom_id}')
                        self._attach_canvas_events(self._canvas_el)
                        self._ctx_container_el = ui.element('div')
                        self._overlay_host_el = ui.element('div')
                with ui.element('div').classes('ach-code-pane') as code_host:
                    self._code_host_el = code_host
                    if self._build_code_view is not None:
                        self._build_code_view()

        self.force_redraw()
        self._apply_mode_visibility()
        self.apply_preferences_state()

    def force_redraw(self: Any) -> None:
        """Refresh graph UI again after layout settles."""
        self._redraw_revision += 1
        redraw_revision = self._redraw_revision

        def _redraw_once() -> None:
            if redraw_revision != self._redraw_revision:
                return
            if self._canvas_el is None:
                return
            self.refresh()
            self._apply_mode_visibility()
            self._sync_client_viewport()

        _redraw_once()
        self._schedule_client_callback(
            0.0,
            _redraw_once,
            name='acherion redraw next tick',
        )
        self._schedule_client_callback(
            0.18,
            _redraw_once,
            name='acherion redraw settle 180ms',
        )
        self._schedule_client_callback(
            0.45,
            _redraw_once,
            name='acherion redraw settle 450ms',
        )
        self._schedule_client_callback(
            0.9,
            _redraw_once,
            name='acherion redraw settle 900ms',
        )

    def set_mode(self: Any, mode: str) -> None:
        """Switch between graph and code workbench modes."""
        if mode not in {'graph', 'code'}:
            return
        if self._editor_mode == mode:
            self._apply_mode_visibility()
            return
        self._editor_mode = mode
        self._apply_mode_visibility()
        if mode == 'graph':
            self._sync_client_viewport()
        if self._on_mode_change is not None:
            self._on_mode_change(mode)

    def refresh(self: Any) -> None:
        """Re-render node cards and connection SVG."""
        self._normalize_graph()
        valid_ids = {n.node_id for n in self._graph.nodes}
        self._selected_node_ids &= valid_ids
        pure_pending = (
            self._pending_source_node_id.split('@', 1)[0]
            if self._pending_source_node_id
            else None
        )
        if pure_pending not in valid_ids:
            self._pending_source_node_id = None
        valid_conn_ids = {
            str(spec['connection_id']) for spec in self._connection_specs()
        }
        if self._selected_connection_id not in valid_conn_ids:
            self._selected_connection_id = None
        if self._canvas_el is None:
            return
        self._canvas_el.clear()
        self._canvas_el.style(
            f'height:{self._canvas_height()}px;'
            f'width:max(100%,{self._canvas_width()}px);'
            f'--ach-origin-x:{self._canvas_origin_x()}px;'
            f'--ach-origin-y:{self._canvas_origin_y()}px;'
        )
        with self._canvas_el:
            self._render_links()
            if not self._graph.nodes:
                ui.label(
                    'No nodes yet. Add components from the left sidebar.'
                ).classes('ach-empty text-sm').style(
                    f'position:absolute; left:{self._world_to_canvas_x(32)}px;'
                    f' top:{self._world_to_canvas_y(32)}px; width:360px;'
                )
                self._sync_client_viewport()
                return
            index_map = {
                node.node_id: index
                for index, node in enumerate(self._graph.nodes)
            }
            self._render_group_frames()
            for node in self._graph.nodes:
                self._render_node(node, index_map[node.node_id])
            self._sync_client_viewport()
        if self._ctx_container_el is not None:
            self._ctx_container_el.clear()
            with self._ctx_container_el:
                self._render_context_menu()

    def _apply_mode_visibility(self: Any) -> None:
        graph_active = self._editor_mode == 'graph'
        if self._graph_host_el is not None:
            if graph_active:
                self._graph_host_el.classes(remove='ach-mode-hidden')
            else:
                self._graph_host_el.classes(add='ach-mode-hidden')
        if self._code_host_el is not None:
            if graph_active:
                self._code_host_el.classes(add='ach-mode-hidden')
            else:
                self._code_host_el.classes(remove='ach-mode-hidden')
        if self._mode_toggle_btn is not None:
            self._mode_toggle_btn.set_text('Code' if graph_active else 'Graph')
            self._mode_toggle_btn.props(
                'icon=code' if graph_active else 'icon=account_tree'
            )

    def _ensure_css(self: Any) -> None:
        if self._css_injected:
            return
        self._css_injected = True
        ui.add_css(_ACH_CSS)

    def _run_client_javascript(
        self: Any,
        code: str,
        *,
        timeout: float = 1.0,
    ) -> None:
        client = cast('Client | None', getattr(self, '_client', None))
        if client is None:
            try:
                client = ui.context.client
            except RuntimeError:
                return
            self._client = client
        client.run_javascript(code, timeout=timeout)

    def _schedule_client_callback(
        self: Any,
        delay: float,
        callback: Callable[[], None],
        *,
        name: str,
    ) -> None:
        client = cast('Client | None', getattr(self, '_client', None))
        if client is None:
            try:
                client = ui.context.client
            except RuntimeError:
                return
            self._client = client

        async def _run_later() -> None:
            if delay > 0:
                await asyncio.sleep(delay)
            if getattr(client, '_deleted', False):
                return
            client.safe_invoke(callback)

        background_tasks.create(_run_later(), name=name)

    def _ensure_client_js(self: Any) -> None:
        if self._client_js_injected:
            return
        self._client_js_injected = True
        self._run_client_javascript(_ACH_CLIENT_JS)

    def _sync_client_viewport(self: Any) -> None:
        vp = self._viewport_dom_id
        self._run_client_javascript(
            f'(function(){{'
            f'const sync=()=>{{'
            f'const vp=document.getElementById({vp!r});'
            f'if(!vp)return;'
            f'window.__oeAcherion?.observeViewport(vp);'
            f'window.__oeAcherion?.syncViewport(vp);'
            f'}};'
            f'sync();'
            f'setTimeout(sync,0);'
            f'setTimeout(sync,80);'
            f'setTimeout(sync,250);'
            f'setTimeout(sync,700);'
            f'}})()'
        )

    def _notify_change(self: Any) -> None:
        self._clear_preview_runtime_state()
        self.refresh()
        self._update_hint()
        if self._on_change is not None:
            self._on_change()

    def _render_toolbar_menu(
        self: Any,
        label: str,
        items: list[tuple[str, Callable[[], Any]]],
    ) -> None:
        label_token = label.lower().replace(' ', '-')
        button_dom_id = f'{self._frame_dom_id}-{label_token}-button'
        menu_dom_id = f'{self._frame_dom_id}-{label_token}-menu'
        with ui.button(label).props(
            f'flat dense no-caps color=white id={button_dom_id}'
        ).classes(
            'ach-menu-button'
        ):
            with ui.menu().props(
                'auto-close anchor=bottom left self=top left '
                f'offset=[0,4] id={menu_dom_id}'
            ).classes('ach-menubar-menu') as menu:
                menu.on(
                    'show',
                    lambda _e, bid=button_dom_id, mid=menu_dom_id: (
                        self._show_toolbar_menu(bid, mid)
                    ),
                )
                menu.on(
                    'hide',
                    lambda _e, mid=menu_dom_id: self._hide_toolbar_menu(mid),
                )
                for item_label, handler in items:
                    ui.menu_item(item_label, on_click=handler)

    def _show_toolbar_menu(
        self: Any,
        button_dom_id: str,
        menu_dom_id: str,
    ) -> None:
        self._set_menu_open(True)
        self._run_client_javascript(
            f'(function(){{'
            f'const align=()=>{{'
            f'const button=document.getElementById({button_dom_id!r});'
            f'const menu=document.getElementById({menu_dom_id!r});'
            f'if(!button||!menu)return;'
            f'menu.removeAttribute("data-ach-aligned");'
            f'const buttonRect=button.getBoundingClientRect();'
            f'const menuRect=menu.getBoundingClientRect();'
            f'const maxLeft=Math.max('
            f'8, window.innerWidth - menuRect.width - 8'
            f');'
            f'const left=Math.min(Math.max(buttonRect.left, 8), maxLeft);'
            f'menu.style.left=`${{Math.round(left)}}px`;'
            f'menu.style.top=`${{Math.round(buttonRect.bottom + 4)}}px`;'
            f'menu.style.right="auto";'
            f'menu.style.transformOrigin="top left";'
            f'menu.setAttribute("data-ach-aligned", "true");'
            f'}};'
            f'requestAnimationFrame(align);'
            f'setTimeout(align,0);'
            f'setTimeout(align,80);'
            f'}})()'
        )

    def _hide_toolbar_menu(self: Any, menu_dom_id: str) -> None:
        self._set_menu_open(False)
        self._run_client_javascript(
            f'(function(){{'
            f'const menu=document.getElementById({menu_dom_id!r});'
            f'if(!menu)return;'
            f'menu.removeAttribute("data-ach-aligned");'
            f'}})()'
        )

    def _set_menu_open(self: Any, is_open: bool) -> None:
        frame_id = self._frame_dom_id
        class_name = 'ach-workbench-menu-open'
        action = 'add' if is_open else 'remove'
        self._run_client_javascript(
            f'(function(){{'
            f'const frame=document.getElementById({frame_id!r});'
            f'if(!frame)return;'
            f'frame.classList[{action!r}]({class_name!r});'
            f'}})()'
        )

    def _render_workbench_menu_bar(self: Any) -> None:
        with ui.element('div').classes('ach-menubar'):
            with ui.element('div').classes('ach-menubar-left'):
                with ui.row().classes('ach-menubar-menus'):
                    self._render_toolbar_menu(
                        'File',
                        [
                            ('Preferences', self._open_preferences_dialog),
                            ('Compile to Code', self._apply_to_code),
                            ('Refresh Canvas', self.refresh),
                        ],
                    )
                    self._render_toolbar_menu(
                        'Edit',
                        [
                            ('Copy Selection', self._copy_current_selection),
                            ('Paste', self._paste_current_selection),
                            ('Clear Selection', self._clear_selection),
                            ('Delete Selection', self._delete_current_selection),
                        ],
                    )
                    self._render_toolbar_menu(
                        'View',
                        [
                            ('Zoom In', lambda: self._zoom_view(1.12)),
                            ('Zoom Out', lambda: self._zoom_view(0.89)),
                            ('Reset View', self._reset_view),
                        ],
                    )
                    self._render_toolbar_menu(
                        'Window',
                        [('Toggle Full Screen', self._toggle_full_screen)],
                    )
                    self._render_toolbar_menu(
                        'Tools',
                        [
                            ('Center on Graph', self._center_on_graph),
                            ('Sync Viewport', self._sync_client_viewport),
                        ],
                    )
                    self._render_toolbar_menu(
                        'Help',
                        [
                            ('Show Shortcuts', self._show_shortcuts_help),
                            ('Show Wiring Tips', self._show_wiring_help),
                        ],
                    )
                    ui.element('div').classes('ach-menubar-separator')
                    self._mode_toggle_btn = ui.button(
                        'Code',
                        icon='code',
                        on_click=lambda: self.set_mode(
                            'code' if self._editor_mode == 'graph' else 'graph'
                        ),
                    ).props('flat dense no-caps color=white').classes(
                        'ach-mode-button'
                    )
                    ui.button(
                        'Compile',
                        icon='play_arrow',
                        on_click=self._apply_to_code,
                    ).props('unelevated dense no-caps').classes(
                        'ach-compile-button'
                    )
                    ui.button(
                        'Validate',
                        icon='check_circle',
                        on_click=self._validate_current,
                    ).props('flat dense no-caps color=white').classes(
                        'ach-validate-button'
                    )
            with ui.element('div').classes('ach-menubar-right'):
                with ui.element('div').classes('ach-statusbar'):
                    ui.label('Status').classes('ach-statusbar-label')
                    self._hint_label = ui.label('').classes(
                        'ach-statusbar-text'
                    )
                    self._update_hint()

    def _run_viewport_command(self: Any, command: str) -> None:
        viewport_id = self._viewport_dom_id
        self._run_client_javascript(
            f'(function(){{'
            f'const vp=document.getElementById({viewport_id!r});'
            f'const h=window.__oeAcherion;'
            f'if(!vp||!h)return;'
            f'{command}'
            f'}})()'
        )

    def _focus_canvas_shortcuts(self: Any) -> None:
        """Return keyboard shortcut focus to the graph canvas."""
        canvas_id = self._canvas_dom_id
        self._run_client_javascript(
            f'(function(){{'
            f'const canvas=document.getElementById({canvas_id!r});'
            f'if(!canvas)return;'
            f'requestAnimationFrame(() => canvas.focus());'
            f'setTimeout(() => canvas.focus(), 50);'
            f'}})()'
        )

    def _clear_selection(self: Any) -> None:
        if not self._selected_node_ids and self._selected_connection_id is None:
            return
        self._selected_node_ids.clear()
        self._selected_connection_id = None
        self.refresh()
        self._update_hint()

    def _copy_current_selection(self: Any) -> None:
        ok, message = self._copy_selection_to_clipboard()
        self._notify_ui(
            message,
            type='positive' if ok else 'warning',
        )

    async def _current_viewport_paste_anchor(
        self: Any,
    ) -> tuple[int | None, int | None]:
        """Return current snapped viewport cursor anchor for paste."""
        client = cast('Client | None', getattr(self, '_client', None))
        if client is None:
            try:
                client = ui.context.client
            except RuntimeError:
                return (None, None)
            self._client = client
        result = await client.run_javascript(
            '(() => {'
            f'const vp = document.getElementById({self._viewport_dom_id!r});'
            'const h = window.__oeAcherion;'
            'if (!vp || !h) return {anchor_x: null, anchor_y: null};'
            'h.ensureViewportState(vp);'
            'const rawClientX = parseFloat(vp.dataset.cursorClientX || "");'
            'const rawClientY = parseFloat(vp.dataset.cursorClientY || "");'
            'if (!Number.isFinite(rawClientX) || !Number.isFinite(rawClientY)) {'
            '  return {anchor_x: null, anchor_y: null};'
            '}'
            'const pt = h.worldPoint(vp, rawClientX, rawClientY);'
            'const snapped = h.snapPoint(vp, pt.x, pt.y);'
            'return {'
            '  anchor_x: Math.round(snapped.x),'
            '  anchor_y: Math.round(snapped.y),'
            '};'
            '})()',
            timeout=3.0,
        )
        if not isinstance(result, dict):
            return (None, None)
        raw_anchor_x = result.get('anchor_x')
        raw_anchor_y = result.get('anchor_y')
        try:
            anchor_x = None if raw_anchor_x in (None, '') else int(raw_anchor_x)
        except (TypeError, ValueError):
            anchor_x = None
        try:
            anchor_y = None if raw_anchor_y in (None, '') else int(raw_anchor_y)
        except (TypeError, ValueError):
            anchor_y = None
        return (anchor_x, anchor_y)

    async def _paste_current_selection(self: Any) -> None:
        anchor_x, anchor_y = await self._current_viewport_paste_anchor()
        ok, message = self._paste_copied_nodes(
            anchor_x=anchor_x,
            anchor_y=anchor_y,
        )
        self._notify_ui(
            message,
            type='positive' if ok else 'warning',
        )

    def _delete_current_selection(self: Any) -> None:
        if self._selected_node_ids:
            to_delete = set(self._selected_node_ids)
            self._selected_node_ids.clear()
            self._delete_nodes_batch(to_delete)
            return
        if self._selected_connection_id is not None:
            self._delete_selected_connection()
            return
        self._notify_ui(
            'Select nodes or a connection first.',
            type='warning',
        )

    def _zoom_view(self: Any, factor: float) -> None:
        self._run_viewport_command(f'h.zoomViewport(vp,{factor});')

    def _reset_view(self: Any) -> None:
        self._run_viewport_command('h.resetViewport(vp);')

    def _center_on_graph(self: Any) -> None:
        self._run_viewport_command('h.centerGraph(vp);')

    def _toggle_full_screen(self: Any) -> None:
        frame_id = self._frame_dom_id
        self._run_client_javascript(
            f'(function(){{'
            f'const frame=document.getElementById({frame_id!r});'
            f'const h=window.__oeAcherion;'
            f'if(!frame||!h)return;'
            f'h.toggleFullscreen(frame);'
            f'}})()'
        )

    def _show_shortcuts_help(self: Any) -> None:
        self._notify_ui(
            'Shortcuts: '
            f'{self._shortcut_display_binding("toggle_selection")} toggles '
            'node selection. '
            f'{self._shortcut_display_binding("box_select")} starts box '
            'selection. '
            f'{self._shortcut_display_binding("copy_selection")} copies '
            'selected nodes. '
            f'{self._shortcut_display_binding("paste_selection")} pastes '
            'them. '
            f'{self._shortcut_display_binding("delete_selection_primary")} '
            'deletes selected nodes or connections. '
            f'{self._shortcut_display_binding("clear_selection")} clears '
            'selection.',
            type='info',
        )

    def _show_wiring_help(self: Any) -> None:
        self._notify_ui(
            'Click an output pin, then an input pin to connect. White exec '
            'wires control order. Coloured pins carry data values.',
            type='info',
        )

    def _notify_ui(
        self: Any,
        message: str,
        *,
        type: Literal[
            'positive',
            'negative',
            'warning',
            'info',
            'ongoing',
        ] = 'info',
    ) -> None:
        """Show a notification using stable host context when possible."""
        host = self._overlay_host_el or self._canvas_el or self._ctx_container_el
        if host is not None:
            with host:
                ui.notify(message, type=type)
            return
        ui.notify(message, type=type)

    def _persist_only(self: Any) -> None:
        """Persist data without re-rendering node cards."""
        if self._on_change is not None:
            self._on_change()

    def _validate_current(self: Any) -> None:
        if self._on_validate is None:
            self._notify_ui(
                'Validation is not available for this Logic Studio instance.',
                type='warning',
            )
            return
        self._on_validate()

    def set_status_message(
        self: Any,
        message: str,
        *,
        negative: bool = False,
    ) -> None:
        """Persist and display a workbench status message."""
        self._status_override_text = message
        self._status_override_negative = negative
        self._update_hint()

    def clear_status_message(self: Any) -> None:
        """Return the workbench status bar to contextual hints."""
        self._status_override_text = None
        self._status_override_negative = False
        self._update_hint()

    def _apply_to_code(self: Any) -> None:
        if self._on_apply_to_code is not None:
            self._on_apply_to_code()

    def _update_hint(self: Any, message: str | None = None) -> None:
        if self._hint_label is None:
            return
        negative = False
        if message is None:
            if self._status_override_text is not None:
                message = self._status_override_text
                negative = self._status_override_negative
            elif self._drag_node_id is not None:
                message = 'Dragging node. Release to place it.'
            elif self._selected_node_ids:
                count = len(self._selected_node_ids)
                message = (
                    f'{count} node{"s" if count > 1 else ""} selected. '
                    f'{self._shortcut_display_binding("toggle_selection")} '
                    'toggles selection. Drag any selected node to move '
                    f'group. {self._shortcut_display_binding("copy_selection")} '
                    'copies it. '
                    f'{self._shortcut_display_binding("paste_selection")} '
                    'pastes it. Right-click for group options. '
                    f'{self._shortcut_display_binding("delete_selection_primary")} '
                    'removes selection. '
                    f'{self._shortcut_display_binding("clear_selection")} '
                    'clears it.'
                )
            elif self._selected_connection_id is not None:
                message = (
                    'Connection selected. Press '
                    f'{self._shortcut_display_binding("delete_selection_primary")} '
                    'to remove it, or right-click the wire.'
                )
            elif self._pending_source_node_id is not None:
                message = (
                    f'Connecting from '
                    f'{self._source_label(self._pending_source_node_id)}. '
                    'Click an input pin.'
                )
            else:
                message = (
                    'Drag node headers to place boxes. Click an output pin, '
                    'then an input pin to connect components.'
                )
        self._hint_label.text = message
        self._hint_label.classes(remove='text-positive text-negative')
        if negative:
            self._hint_label.classes(add='text-negative')
        elif self._status_override_text is not None:
            self._hint_label.classes(add='text-positive')
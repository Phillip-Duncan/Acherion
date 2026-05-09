"""Node shell, context menu, and palette rendering mixin."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from typing import Any, Protocol, cast

from nicegui import ui

from acherion.registry import (
    _palette_sections,
    _template_category_label,
    _template_flavor,
    is_acherion_producer_kind,
)
from acherion.model import (
    AcherionNode,
    _node_var_name,
    _template_icon,
    _template_title,
)
from acherion.node import (
    acherion_node_identifier,
)
from acherion.render.shared import (
    _GROUP_FRAME_BOTTOM_PAD,
    _GROUP_FRAME_SIDE_PAD,
    _GROUP_FRAME_TOP_PAD,
)


def _event_int_arg(args: Any, key: str) -> int | None:
    """Return integer event arg when present and parseable."""
    if not isinstance(args, dict):
        return None
    value = cast(dict[str, object], args).get(key)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str) or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class _RenderNodesMixin:
    """Higher-level node, group, context-menu, and palette rendering."""

    @staticmethod
    def _node_header_slug(
        node: AcherionNode,
        graph_index: int,
    ) -> str:
        """Return stable schema slug to show under a node title."""
        identifier = acherion_node_identifier(node.kind, node)
        if identifier is not None:
            return identifier
        if is_acherion_producer_kind(node.kind):
            return _node_var_name(graph_index, node)
        return ''

    @staticmethod
    def _palette_badge_text(template: Any) -> str:
        """Return the short palette badge text for one node template."""
        if str(getattr(template, 'category', '') or '').strip() == 'ui':
            return 'UI'
        return str(getattr(template, 'flavor', '') or '').upper()

    def _render_manual_node(
        self: Any,
        node: AcherionNode,
        graph_index: int,  # noqa: ARG002
    ) -> None:
        if node.kind == 'function_box':
            self._render_function_box_node(node, graph_index)
            return
        self._render_body_pin_rows(node)

    def _render_node(
        self: Any,
        node: AcherionNode,
        graph_index: int,
    ) -> None:
        if self._is_function_entry(node):
            return
        title = node.title or _template_title(node.kind)
        header_slug = self._node_header_slug(node, graph_index)
        group_name = str(node.params.get('group') or '').strip()
        group_token = group_name.encode('utf-8').hex() if group_name else ''
        function_box_id = (
            node.node_id if self._is_function_box(node)
            else self._function_parent_id(node)
        )
        parent_function_id = self._function_parent_id(node)
        is_function_box = '1' if self._is_function_box(node) else '0'
        with ui.element('div').classes(
            f'ach-node {self._node_tone_class(node)}'
            + (' ach-function-box' if self._is_function_box(node) else '')
            + (' ach-node-selected' if node.node_id in self._selected_node_ids else '')
        ).style(self._node_style(node)).props(
            f'data-node-id={node.node_id} '
            f'data-group-token={group_token} '
            f'data-function-box-id={function_box_id} '
            f'data-parent-function-id={parent_function_id} '
            f'data-is-function-box={is_function_box}'
        ) as node_el:
            node_el.on(
                'mousedown',
                lambda _e: None,
                js_handler=(
                    '(e) => {'
                    'if (e.button !== 0) return;'
                    'if (e.ctrlKey || e.metaKey) return;'
                    'if (e.target.closest('
                    '".q-btn,.q-field,.q-checkbox,.q-toggle,'
                    '.ach-pin-btn,input,textarea,select")) return;'
                    'const node = e.currentTarget;'
                    'const viewport = node.closest(".ach-shell");'
                    'const helper = window.__oeAcherion;'
                    'if (!viewport || !helper) return;'
                    'const point = helper.worldPoint(viewport, e.clientX, e.clientY);'
                    'const stage = helper.stage(viewport);'
                    'const origin = helper.origin(stage);'
                    'const left = (parseFloat(node.style.left || "0") - origin.x);'
                    'const top = (parseFloat(node.style.top || "0") - origin.y);'
                    'viewport.dataset.dragCandidateNodeId = node.dataset.nodeId || "";'
                    'viewport.dataset.dragGroupToken = '
                    'node.dataset.groupToken || "";'
                    'viewport.dataset.dragStartClientX = String(e.clientX);'
                    'viewport.dataset.dragStartClientY = String(e.clientY);'
                    'viewport.dataset.dragOffsetX = String(point.x - left);'
                    'viewport.dataset.dragOffsetY = String(point.y - top);'
                    'e.preventDefault();'
                    'e.stopPropagation();'
                    '}'
                ),
            )
            node_el.on(
                'click',
                lambda e: self._toggle_node_selection(e),
                js_handler=(
                    '(e) => {'
                    'if (e.target.closest('
                    '".q-btn,.q-field,.q-checkbox,.q-toggle,'
                    '.ach-pin-btn,input,textarea,select")) return;'
                    'const vp = e.currentTarget.closest(".ach-shell");'
                    'const toggle = !!(e.ctrlKey || e.metaKey);'
                    'if (toggle) {'
                    'if (vp) vp.dataset.suppressNextCanvasClick = "1";'
                    'e.preventDefault(); e.stopPropagation();'
                    '}'
                    'emit({node_id: e.currentTarget.dataset.nodeId || "", toggle});'
                    '}'
                ),
            )
            node_el.on(
                'contextmenu',
                lambda e: self._handle_node_contextmenu(e),
                js_handler=(
                    '(e) => {'
                    'e.preventDefault(); e.stopPropagation();'
                    'emit({'
                    'node_id: e.currentTarget.dataset.nodeId || "",'
                    ' cx: e.clientX, cy: e.clientY'
                    '});'
                    '}'
                ),
            )
            if self._is_function_box(node):
                self._render_function_box_node(node, graph_index)
                return
            with ui.element('div').classes('ach-node-head'):
                ui.icon('drag_indicator').classes('ach-node-drag')
                ui.icon(_template_icon(node.kind)).classes(
                    'ach-node-kind-icon '
                    f'ach-node-kind-icon-{_template_flavor(node.kind)}'
                ).style('font-size:18px;')
                with ui.column().classes('gap-0 min-w-0'):
                    ui.label(title).classes('text-sm font-semibold')
                    if header_slug:
                        ui.label(header_slug).classes(
                            'text-xs oe-muted'
                        )
                ui.space()
                if self._is_system_node(node) or node.kind == 'function_entry':
                    ui.label('AUTO').classes('ach-badge')
                else:
                    ui.button(
                        icon='edit',
                        on_click=lambda _e, nid=node.node_id: (
                            self._open_node_config_dialog(nid)
                        ),
                    ).props('flat dense round')
                    ui.button(
                        icon='delete',
                        color='negative',
                        on_click=lambda _e, nid=node.node_id: self._delete_node(nid),
                    ).props('flat dense round')

            with ui.element('div').classes('ach-node-body'):
                self._render_top_exec_row(node)
                if self._is_system_source_node(node):
                    self._render_system_source_node(node)
                elif self._is_system_sink_node(node):
                    self._render_system_sink_node(node, graph_index)
                else:
                    self._render_manual_node(node, graph_index)
                self._render_node_preview_card(node)

    def _render_group_frames(self: Any) -> None:
        """Render translucent colour-coded frame divs behind member nodes."""
        groups = getattr(self._graph, 'groups', {}) or {}
        if not groups:
            return
        group_members: dict[str, list] = {}
        for node in self._graph.nodes:
            group_name = str(node.params.get('group') or '').strip()
            if group_name and group_name in groups:
                group_members.setdefault(group_name, []).append(node)
        for name, members in group_members.items():
            if any(
                node.node_id == name and self._is_function_box(node)
                for node in self._graph.nodes
            ):
                continue
            colour = groups[name]
            member_bounds = [self._node_bounds(node) for node in members]
            red = int(colour[1:3], 16)
            green = int(colour[3:5], 16)
            blue = int(colour[5:7], 16)
            x1 = max(
                16,
                min(left for left, _top, _width, _height in member_bounds)
                - _GROUP_FRAME_SIDE_PAD,
            )
            y1 = max(
                16,
                min(top for _left, top, _width, _height in member_bounds)
                - _GROUP_FRAME_TOP_PAD,
            )
            x2 = max(
                left + width
                for left, _top, width, _height in member_bounds
            ) + _GROUP_FRAME_SIDE_PAD
            y2 = max(
                top + height
                for _left, top, _width, height in member_bounds
            ) + _GROUP_FRAME_BOTTOM_PAD
            width = x2 - x1
            height = y2 - y1
            bg = f'rgba({red},{green},{blue},0.05)'
            border = f'rgba({red},{green},{blue},0.42)'
            with ui.element('div').classes('ach-group-frame').style(
                f'left:{x1}px; top:{y1}px;'
                f' width:{width}px; height:{height}px;'
                f' background:{bg}; border:1.5px dashed {border};'
            ):
                ui.label(f'{name} - {len(members)}').classes('ach-group-label').style(
                    f'color:{colour};'
                )

    def _render_context_menu(self: Any) -> None:
        """Render floating right-click context menu."""
        if getattr(self, '_ctx_menu_node_id', None) is None:
            return
        selected: set[str] = set(self._selected_node_ids)
        cx: int = getattr(self, '_ctx_menu_cx', 0)
        cy: int = getattr(self, '_ctx_menu_cy', 0)
        n_sel = len(selected)
        groups: dict[str, str] = dict(getattr(self._graph, 'groups', {}) or {})
        selected_groups = sorted({
            str(node.params.get('group') or '').strip()
            for node in self._graph.nodes
            if node.node_id in selected and str(node.params.get('group') or '').strip()
        })
        has_grouped = any(
            str(node.params.get('group') or '').strip()
            for node in self._graph.nodes
            if node.node_id in selected
        )
        owner = cast(Any, self)
        menu_dom_id = f'{owner._frame_dom_id}-ctx-menu'

        def _sync_context_menu_layout() -> None:
            owner._run_client_javascript(
                f'(function(){{'
                f'const menu=document.getElementById({menu_dom_id!r});'
                f'const h=window.__oeAcherion;'
                f'if(!menu||!h)return;'
                f'setTimeout(() => h.positionContextMenu(menu,{cx},{cy}),0);'
                f'setTimeout(() => h.positionContextMenu(menu,{cx},{cy}),80);'
                f'}})()'
            )

        alignment_sections: list[tuple[str, list[dict[str, str]]]] = [
            (
                'Align',
                [
                    {
                        'command': 'align_top',
                        'icon': 'vertical_align_top',
                        'label': 'Align Top',
                    },
                    {
                        'command': 'align_middle',
                        'icon': 'vertical_align_center',
                        'label': 'Align Middle',
                    },
                    {
                        'command': 'align_bottom',
                        'icon': 'vertical_align_bottom',
                        'label': 'Align Bottom',
                    },
                    {
                        'command': 'align_left',
                        'icon': 'format_align_left',
                        'label': 'Align Left',
                    },
                    {
                        'command': 'align_center',
                        'icon': 'format_align_center',
                        'label': 'Align Center',
                    },
                    {
                        'command': 'align_right',
                        'icon': 'format_align_right',
                        'label': 'Align Right',
                    },
                    {
                        'command': 'straighten_connections',
                        'icon': 'straighten',
                        'label': 'Straighten Connection(s)',
                    },
                ],
            ),
            (
                'Distribute',
                [
                    {
                        'command': 'distribute_horizontally',
                        'icon': 'swap_horiz',
                        'label': 'Distribute Horizontally',
                    },
                    {
                        'command': 'distribute_vertically',
                        'icon': 'swap_vert',
                        'label': 'Distribute Vertically',
                    },
                ],
            ),
            (
                'Stack',
                [
                    {
                        'command': 'stack_horizontally',
                        'icon': 'view_week',
                        'label': 'Stack Horizontally',
                    },
                    {
                        'command': 'stack_vertically',
                        'icon': 'view_agenda',
                        'label': 'Stack Vertically',
                    },
                ],
            ),
        ]
        alignment_keywords = ' '.join(
            item['label']
            for _section_title, items in alignment_sections
            for item in items
        )
        menu_sections: list[tuple[str, list[dict[str, Any]]]] = [
            (
                'Node Actions',
                [
                    {
                        'icon': 'delete_outline',
                        'label': 'Delete Selection',
                        'action': self._ctx_delete_selection,
                        'danger': True,
                    },
                ],
            ),
            (
                'Organization',
                [
                    {
                        'icon': 'format_align_left',
                        'label': 'Alignment',
                        'keywords': alignment_keywords,
                        'submenu': 'alignment',
                    },
                    {
                        'icon': 'add_circle_outline',
                        'label': 'New Group From Selection',
                        'action': self._open_new_group_dialog,
                    },
                    *[
                        {
                            'icon': 'folder_open',
                            'label': f'Add to "{group_name}"',
                            'action': (
                                lambda name=group_name: self._ctx_add_to_group(name)
                            ),
                            'keywords': f'group {group_name}',
                        }
                        for group_name in groups
                    ],
                    *([
                        {
                            'icon': 'edit',
                            'label': 'Rename Group',
                            'action': self._open_rename_group_dialog,
                        },
                    ] if len(selected_groups) == 1 else []),
                    *([
                        {
                            'icon': 'folder_off',
                            'label': 'Remove From Group',
                            'action': self._ctx_remove_from_group,
                        },
                    ] if has_grouped else []),
                ],
            ),
            (
                'Function',
                [
                    {
                        'icon': 'functions',
                        'label': 'Create Function From Selection',
                        'action': self._open_extract_function_dialog,
                    },
                ],
            ),
        ]

        def _matches(query: str, *parts: str) -> bool:
            query = query.strip().lower()
            if not query:
                return True
            haystack = ' '.join(part for part in parts if part).lower()
            return query in haystack

        def _render_item(
            label: str,
            *,
            icon: str,
            on_click: Any = None,
            danger: bool = False,
            disabled: bool = False,
            submenu_renderer: Any = None,
        ) -> None:
            classes = ['ach-ctx-item']
            if danger:
                classes.append('ach-ctx-danger')
            if disabled:
                classes.append('ach-ctx-item-disabled')
            if submenu_renderer is not None:
                classes.append('ach-ctx-item-has-submenu')
            item = ui.element('div').classes(' '.join(classes))
            if on_click is not None and not disabled:
                item.on('click', lambda _: on_click())
            with item:
                ui.icon(icon).style('font-size:18px;')
                ui.label(label).classes('ach-ctx-item-label')
                if submenu_renderer is not None:
                    ui.icon('chevron_right').classes('ach-ctx-item-arrow')
                    with ui.element('div').classes('ach-ctx-submenu'):
                        submenu_renderer()

        menu_items_renderer: Any = None
        align_items_renderer: Any = None

        def _set_menu_query(value: str) -> None:
            self._ctx_menu_query = str(value or '')
            if menu_items_renderer is not None:
                menu_items_renderer.refresh()
            _sync_context_menu_layout()

        def _set_align_query(value: str) -> None:
            self._ctx_align_query = str(value or '')
            if align_items_renderer is not None:
                align_items_renderer.refresh()
            _sync_context_menu_layout()

        def _render_alignment_submenu() -> None:
            nonlocal align_items_renderer
            with ui.element('div').classes('ach-ctx-submenu-panel'):
                with ui.element('div').classes('ach-ctx-search-row'):
                    ui.input(
                        value=str(getattr(self, '_ctx_align_query', '') or ''),
                        placeholder='Start typing to search',
                        on_change=lambda e: _set_align_query(
                            str(getattr(e, 'value', '') or '')
                        ),
                    ).props('outlined dense clearable').classes(
                        'w-full ach-ctx-search-field'
                    )
                ui.label('Alignment').classes('ach-ctx-selection')

                @ui.refreshable
                def _render_alignment_items() -> None:
                    rendered_any = False
                    query = str(getattr(self, '_ctx_align_query', '') or '')
                    for section_title, items in alignment_sections:
                        visible = [
                            item
                            for item in items
                            if _matches(query, section_title, item['label'])
                        ]
                        if not visible:
                            continue
                        rendered_any = True
                        ui.label(section_title).classes('ach-ctx-section')
                        for item in visible:
                            _render_item(
                                item['label'],
                                icon=item['icon'],
                                on_click=lambda command=item['command']: (
                                    self._ctx_apply_layout_command(command)
                                ),
                            )
                    if not rendered_any:
                        ui.label(
                            'No alignment actions match this search.'
                        ).classes('ach-ctx-empty')

                align_items_renderer = _render_alignment_items
                _render_alignment_items()

        ui.element('div').classes('ach-ctx-backdrop').on(
            'click', lambda _: self._ctx_dismiss()
        )
        with ui.element('div').classes('ach-ctx-menu').props(
            f'id={menu_dom_id}'
        ).style(
            f'left:{cx}px; top:{cy}px;'
        ):
            with ui.element('div').classes('ach-ctx-search-row'):
                ui.input(
                    value=str(getattr(self, '_ctx_menu_query', '') or ''),
                    placeholder='Start typing to search',
                    on_change=lambda e: _set_menu_query(
                        str(getattr(e, 'value', '') or '')
                    ),
                ).props('outlined dense clearable').classes(
                    'w-full ach-ctx-search-field'
                )
            ui.label(
                f'{n_sel} node{"s" if n_sel != 1 else ""} selected'
            ).classes('ach-ctx-selection')

            @ui.refreshable
            def _render_menu_items() -> None:
                rendered_any = False
                query = str(getattr(self, '_ctx_menu_query', '') or '')
                for section_title, items in menu_sections:
                    visible = [
                        item
                        for item in items
                        if _matches(
                            query,
                            section_title,
                            str(item.get('label') or ''),
                            str(item.get('keywords') or ''),
                        )
                    ]
                    if not visible:
                        continue
                    rendered_any = True
                    ui.label(section_title).classes('ach-ctx-section')
                    for item in visible:
                        submenu_renderer = (
                            _render_alignment_submenu
                            if item.get('submenu') == 'alignment'
                            else None
                        )
                        _render_item(
                            str(item.get('label') or ''),
                            icon=str(item.get('icon') or 'chevron_right'),
                            on_click=item.get('action'),
                            danger=bool(item.get('danger')),
                            disabled=bool(item.get('disabled')),
                            submenu_renderer=submenu_renderer,
                        )
                if not rendered_any:
                    ui.label('No actions match this search.').classes(
                        'ach-ctx-empty'
                    )

            menu_items_renderer = _render_menu_items
            _render_menu_items()
        _sync_context_menu_layout()

    def _render_palette(self: Any, palette_dom_id: str) -> None:
        """Render the node-type palette sidebar."""
        owner = cast(_PaletteOwner, self)
        sections = _palette_sections()
        default_sidebar_key = 'nodes'

        def _palette_matches(template: Any) -> bool:
            query = str(getattr(self, '_palette_query', '') or '').strip().lower()
            if not query:
                return True
            haystack = ' '.join(
                (
                    str(template.kind),
                    str(template.label),
                    str(template.tooltip),
                    str(template.category),
                    str(template.flavor),
                    _template_category_label(str(template.kind)),
                )
            ).lower()
            return query in haystack

        with ui.element('div').classes('ach-palette-shell').props(
            f'id={palette_dom_id} role=navigation aria-label="Node palette" '
            f'data-active-sidebar={default_sidebar_key} data-pane-open=1'
        ):
            with ui.element('div').classes('ach-activitybar').props(
                'aria-label="Sidebar activity bar"'
            ):
                button = ui.button(icon='widgets').props(
                    'flat dense round '
                    'aria-label="Nodes" title="Nodes" '
                    f'data-sidebar-key={default_sidebar_key}'
                ).classes('ach-activity-button ach-activity-button-active')
                button.on(
                    'click',
                    lambda _e: None,
                    js_handler=(
                        '(e) => {'
                        'window.__oeAcherion?.toggleSidebarSection('
                        'e.currentTarget);'
                        'e.preventDefault();'
                        'e.stopPropagation();'
                        '}'
                    ),
                )

            with ui.element('div').classes('ach-sidebar-pane-frame'):
                with ui.element('div').classes('ach-palette-header'):
                    ui.label('Nodes').classes('ach-palette-title')

                    def _set_palette_query(raw_value: Any) -> None:
                        owner = cast(Any, self)
                        self._palette_query = str(raw_value or '').strip().lower()
                        _render_palette_items.refresh()
                        owner._run_client_javascript(
                            f'(function(){{'
                            f'const frame=document.getElementById('
                            f'{owner._frame_dom_id!r});'
                            f'if(!frame)return;'
                            f'setTimeout(() => '
                            f'window.__oeAcherion?.syncSidebarState(frame),0);'
                            f'setTimeout(() => '
                            f'window.__oeAcherion?.syncSidebarState(frame),80);'
                            f'}})()'
                        )

                    with ui.row().classes('w-full ach-palette-search'):
                        ui.input(
                            placeholder='Search nodes...',
                            on_change=lambda e: _set_palette_query(
                                getattr(e, 'value', ''),
                            ),
                        ).props('outlined dense clearable').classes('w-full')

                @ui.refreshable
                def _render_palette_items() -> None:
                    with ui.element('div').classes('ach-sidebar-pane-stack'):
                        with ui.element('div').classes(
                            'ach-sidebar-pane ach-sidebar-pane-active'
                        ).props(f'data-sidebar-key={default_sidebar_key}'):
                            with ui.element('div').classes('ach-palette-list'):
                                rendered_any = False
                                for category, items in sections:
                                    visible = [
                                        template
                                        for template in items
                                        if _palette_matches(template)
                                    ]
                                    if not visible:
                                        continue
                                    rendered_any = True
                                    with ui.element('div').classes(
                                        'ach-palette-section'
                                    ):
                                        ui.label(
                                            _template_category_label(items[0].kind)
                                        ).classes('ach-palette-section-title')
                                        with ui.element('div').classes(
                                            'ach-palette-section-body'
                                        ):
                                            for template in visible:
                                                with ui.element('div').classes(
                                                    'ach-palette-item'
                                                ).props(
                                                    'draggable=true '
                                                    f'data-kind="{template.kind}"'
                                                ) as item_el:
                                                    item_el.on(
                                                        'click',
                                                        lambda e, k=template.kind: (
                                                            owner._add_node(
                                                                k,
                                                                center_x=_event_int_arg(
                                                                    e.args,
                                                                    'x',
                                                                ),
                                                                center_y=_event_int_arg(
                                                                    e.args,
                                                                    'y',
                                                                ),
                                                            )
                                                        ),
                                                        js_handler=(
                                                            '(e) => {'
                                                            'const shell = '
                                                            'e.currentTarget.closest('
                                                            '".ach-workbench-main")'
                                                            '?.querySelector('
                                                            '".ach-shell"'
                                                            ');'
                                                            'const helper = '
                                                            'window.__oeAcherion;'
                                                            'if (!shell || !helper) {'
                                                            'emit({});'
                                                            'return;'
                                                            '}'
                                                            'const rect = '
                                                            'shell.getBoundingClientRect();'
                                                            'const point = '
                                                            'helper.worldPoint('
                                                            'shell,'
                                                            'rect.left + (rect.width / 2),'
                                                            'rect.top + (rect.height / 2)'
                                                            ');'
                                                            'emit({'
                                                            'x: Math.round(point.x),'
                                                            'y: Math.round(point.y)'
                                                            '});'
                                                            '}'
                                                        ),
                                                    )
                                                    item_el.on(
                                                        'dragstart',
                                                        lambda _e: None,
                                                        js_handler=(
                                                            '(e) => {'
                                                            "e.dataTransfer.setData('text/ach-kind',"
                                                            'e.currentTarget.dataset.kind);'
                                                            "e.dataTransfer.effectAllowed='copy';"
                                                            '}'
                                                        ),
                                                    )
                                                    ui.icon(template.icon).classes(
                                                        'ach-palette-item-icon '
                                                        f'ach-node-kind-icon-'
                                                        f'{template.flavor}'
                                                    )
                                                    with ui.element('div').classes(
                                                        'min-w-0'
                                                    ):
                                                        with ui.row().classes(
                                                            'items-center gap-2'
                                                        ):
                                                            ui.label(
                                                                template.label
                                                            ).classes(
                                                                'ach-palette-item-name'
                                                            )
                                                            ui.label(
                                                                self._palette_badge_text(
                                                                    template
                                                                )
                                                            ).classes(
                                                                'ach-palette-item-pill '
                                                                'ach-palette-item-pill-'
                                                                f'{template.flavor}'
                                                            )
                                                        if template.tooltip:
                                                            ui.label(
                                                                template.tooltip
                                                            ).classes(
                                                                'ach-palette-item-desc'
                                                            )
                                if not rendered_any:
                                    ui.label(
                                        'No nodes match this filter.'
                                    ).classes('ach-empty ach-sidebar-empty')

                _render_palette_items()


class _PaletteOwner(Protocol):
    def _add_node(
        self,
        kind: str,
        center_x: int | None = None,
        center_y: int | None = None,
    ) -> None:
        ...
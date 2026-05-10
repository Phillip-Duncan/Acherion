"""Interaction and event mixin for AcherionDesigner."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import json
from typing import Any

from nicegui import ui

from acherion.constants import (
    _DROP_X_OFFSET,
    _DROP_Y_OFFSET,
    _MANUAL_X,
    _MANUAL_Y,
)
from acherion.registry import (
    is_acherion_manual_add_kind,
)
from acherion.model import (
    AcherionNode,
    _template_title,
)


class _DesignerInteractionsMixin:
    """Selection, drag, grouping, and JS event wiring helpers."""

    _drag_node_id: str | None = None
    _ctx_menu_node_id: str | None = None
    _selected_connection_id: str | None = None

    def _node_by_id(
        self: Any,
        node_id: str | None,
    ) -> AcherionNode | None:
        if not node_id:
            return None
        pure_id = node_id.split('@')[0] if '@' in node_id else node_id
        return next(
            (node for node in self._graph.nodes if node.node_id == pure_id),
            None,
        )

    def _source_label(self: Any, source_id: str | None) -> str:
        if not source_id:
            return 'Unconnected'
        node = self._node_by_id(source_id)
        if node is None:
            return 'Unconnected'
        base = node.title or _template_title(node.kind)
        if source_id and '@' in source_id:
            pin_idx = int(source_id.split('@', 1)[1])
            specs = self._output_pin_specs(node)
            if pin_idx < len(specs):
                return f'{base} ({specs[pin_idx]["label"]})'
        return base

    @staticmethod
    def _connection_id(
        target_node_id: str,
        pin_id: str,
        *,
        source_id: str = '',
    ) -> str:
        if pin_id == 'exec_source' and source_id:
            return f'{target_node_id}@@{pin_id}@@{source_id}'
        return f'{target_node_id}@@{pin_id}'

    @staticmethod
    def _split_connection_id(
        connection_id: str,
    ) -> tuple[str, str, str] | None:
        if '@@' not in connection_id:
            return None
        parts = connection_id.split('@@')
        if len(parts) == 2:
            target_id, pin_id = parts
            return (target_id, pin_id, '')
        if len(parts) == 3:
            target_id, pin_id, source_id = parts
            return (target_id, pin_id, source_id)
        return None

    def _start_drag_node(self: Any, node_id: str, event: Any = None) -> None:
        self._drag_node_id = node_id
        args = dict((event.args if event is not None else None) or {})
        self._drag_offset_x = int(args.get('offset_x') or _DROP_X_OFFSET)
        self._drag_offset_y = int(args.get('offset_y') or _DROP_Y_OFFSET)
        if self._canvas_el is not None:
            self._canvas_el.classes(add='ach-canvas-dragging')
        self._update_hint()

    def _finish_drag_node(self: Any, event: Any) -> None:
        """Persist final drag positions from JS mouseup handler."""
        args = dict(event.args or {})

        if 'rubber_node_ids' in args:
            valid = {node.node_id for node in self._graph.nodes}
            new_sel = {
                node_id
                for node_id in (args['rubber_node_ids'] or [])
                if node_id in valid
            }
            if args.get('add'):
                self._selected_node_ids.update(new_sel)
            else:
                self._selected_node_ids = new_sel
            self._notify_change()
            return

        node_id = str(args.get('node_id') or self._drag_node_id or '')
        self._drag_node_id = None
        if self._canvas_el is not None:
            self._canvas_el.classes(remove='ach-canvas-dragging')
        if not node_id:
            return
        dragged = self._node_by_id(node_id)
        if dragged is None:
            return
        raw_left = args.get('left')
        raw_top = args.get('top')
        if raw_left is None or raw_top is None:
            self._update_hint()
            return
        left, top = self._snap_grid_point(raw_left, raw_top)
        dragged.params['x'] = left
        dragged.params['y'] = top
        dragged.params['dock'] = 'free'
        dragged.params['manual_position'] = True
        moved_nodes: list[tuple[AcherionNode, int, int]] = [
            (dragged, left, top)
        ]
        for move in list(args.get('group_moves') or []):
            group_id = str(move.get('node_id') or '')
            group_left = move.get('left')
            group_top = move.get('top')
            if not group_id or group_left is None or group_top is None:
                continue
            group_node = self._node_by_id(group_id)
            if group_node is None:
                continue
            group_node.params['x'] = int(group_left)
            group_node.params['y'] = int(group_top)
            group_node.params['dock'] = 'free'
            group_node.params['manual_position'] = True
            moved_nodes.append(
                (group_node, int(group_left), int(group_top))
            )
        for moved_node, moved_left, moved_top in moved_nodes:
            self._assign_node_to_containing_function_box(
                moved_node,
                moved_left,
                moved_top,
            )
        self._notify_change()

    def _toggle_node_selection(self: Any, event: Any) -> None:
        """Toggle one node or select whole group on normal click."""
        args = dict(event.args or {})
        node_id = str(args.get('node_id') or '')
        toggle = bool(args.get('toggle'))
        valid = {node.node_id for node in self._graph.nodes}
        if node_id not in valid:
            return

        if toggle:
            if node_id in self._selected_node_ids:
                self._selected_node_ids.discard(node_id)
            else:
                self._selected_node_ids.add(node_id)
            self._notify_change()
            return

        node = self._node_by_id(node_id)
        if node is None:
            return
        group_ids = self._selection_ids_for_node(node)
        if (
            group_ids == self._selected_node_ids
            and self._selected_connection_id is None
        ):
            return
        self._selected_connection_id = None
        self._selected_node_ids = group_ids
        self._notify_change()

    def _selection_ids_for_node(self: Any, node: AcherionNode) -> set[str]:
        group_name = str(node.params.get('group') or '').strip()
        if not group_name:
            return {node.node_id}
        return {
            current.node_id
            for current in self._graph.nodes
            if str(current.params.get('group') or '').strip() == group_name
        }

    def _handle_node_contextmenu(self: Any, event: Any) -> None:
        """Show context menu for right-clicked node."""
        args = dict(event.args or {})
        node_id = str(args.get('node_id') or '')
        valid = {node.node_id for node in self._graph.nodes}
        if node_id not in valid:
            return
        if node_id not in self._selected_node_ids:
            node = self._node_by_id(node_id)
            if node is None:
                return
            self._selected_node_ids = self._selection_ids_for_node(node)
        self._ctx_menu_node_id = node_id
        self._ctx_menu_cx = int(args.get('cx') or 0)
        self._ctx_menu_cy = int(args.get('cy') or 0)
        self._reset_context_menu_queries()
        self.refresh()
        self._update_hint()

    def _reset_context_menu_queries(self: Any) -> None:
        self._ctx_menu_query = ''
        self._ctx_align_query = ''

    def _ctx_dismiss(self: Any) -> None:
        """Dismiss context menu without changing selection."""
        self._ctx_menu_node_id = None
        self._reset_context_menu_queries()
        if self._ctx_container_el is not None:
            self._ctx_container_el.clear()
        frame_dom_id = getattr(self, '_frame_dom_id', '')
        if frame_dom_id:
            self._run_client_javascript(
                f'(function(){{'
                f'const frame=document.getElementById({frame_dom_id!r});'
                f'if(!frame)return;'
                f'frame.querySelectorAll(".ach-ctx-menu,.ach-ctx-backdrop")'
                f'.forEach((el) => el.remove());'
                f'}})()'
            )
        self._update_hint()

    def _next_default_group_name(self: Any) -> str:
        """Return next available default group label."""
        index = 1
        while True:
            name = f'Group {index}'
            if name not in self._graph.groups:
                return name
            index += 1

    def _next_default_function_name(self: Any) -> str:
        """Return next available default function-box title."""
        used = {
            str(node.params.get('function_name') or '')
            for node in self._manual_nodes()
            if self._is_function_box(node)
        }
        index = 1
        while True:
            title = f'Function {index}'
            if self._sanitize_identifier(title, 'function_box') not in used:
                return title
            index += 1

    def _selected_group_name(self: Any) -> str:
        """Return shared selected group name when selection has exactly one."""
        groups = {
            str(node.params.get('group') or '').strip()
            for node in self._graph.nodes
            if node.node_id in self._selected_node_ids
            and str(node.params.get('group') or '').strip()
        }
        return next(iter(groups)) if len(groups) == 1 else ''

    def _rename_group(
        self: Any,
        old_name: str,
        new_name: str,
    ) -> tuple[bool, str]:
        """Rename a group while preserving colour and membership."""
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not old_name or old_name not in self._graph.groups:
            return (False, 'Group no longer exists.')
        if not new_name:
            return (False, 'Enter a group name.')
        if new_name != old_name and new_name in self._graph.groups:
            return (False, f'Group {new_name} already exists.')
        if new_name == old_name:
            return (True, f'Group name remains {new_name}.')
        colour = self._graph.groups.pop(old_name)
        self._graph.groups[new_name] = colour
        for node in self._graph.nodes:
            if str(node.params.get('group') or '').strip() == old_name:
                node.params['group'] = new_name
        self._notify_change()
        return (True, f'Renamed group to {new_name}.')

    def _open_new_group_dialog(self: Any) -> None:
        """Create a group from selection using next default name."""
        node_ids = set(self._selected_node_ids)
        self._ctx_dismiss()
        if not node_ids:
            self._notify_ui('Select nodes first.', type='warning')
            return
        name = self._next_default_group_name()
        self._create_group(name, node_ids)
        self._notify_ui(f'Created group {name}.', type='positive')

    def _open_rename_group_dialog(self: Any) -> None:
        """Open rename dialog for currently selected group."""
        group_name = self._selected_group_name()
        self._ctx_dismiss()
        if not group_name:
            self._notify_ui(
                'Select nodes from one group first.',
                type='warning',
            )
            return
        if self._overlay_host_el is None:
            return
        with self._overlay_host_el:
            dlg = ui.dialog()
            with dlg, ui.card().style(
                'background:#000000; border:1px solid #2f3336;'
                ' border-radius:12px; padding:20px; min-width:320px;'
            ):
                ui.label('Rename group').classes('text-base font-bold oe-text')
                name_input = ui.input('Group name', value=group_name).classes(
                    'w-full'
                )
                with ui.row().classes('justify-end gap-2 w-full pt-2'):
                    ui.button('Close', on_click=dlg.close).props('flat')

                    def _save() -> None:
                        ok, message = self._rename_group(
                            group_name,
                            str(name_input.value or ''),
                        )
                        self._notify_ui(
                            message,
                            type='positive' if ok else 'warning',
                        )
                        if ok:
                            dlg.close()

                    ui.button('Save', on_click=_save).classes(
                        'oe-btn-primary'
                    )
        dlg.open()

    def _open_extract_function_dialog(self: Any) -> None:
        """Extract selection into function box with default name."""
        anchor_node_id = self._ctx_menu_node_id
        self._ctx_dismiss()
        ok, message = self._extract_function_from_selection(
            self._next_default_function_name(),
            return_node_id=anchor_node_id,
        )
        self._notify_ui(
            message,
            type='positive' if ok else 'warning',
        )

    def _ctx_add_to_group(self: Any, name: str) -> None:
        """Add selected nodes to existing group."""
        node_ids = set(self._selected_node_ids)
        self._ctx_dismiss()
        self._add_nodes_to_group(name, node_ids)

    def _ctx_remove_from_group(self: Any) -> None:
        """Remove selected nodes from their group."""
        node_ids = set(self._selected_node_ids)
        self._ctx_dismiss()
        self._remove_nodes_from_group(node_ids)

    def _ctx_apply_layout_command(self: Any, command: str) -> None:
        """Apply one alignment/distribution command from the context menu."""
        self._ctx_dismiss()
        ok, message = self._layout_selected_nodes(command)
        self._notify_ui(
            message,
            type='positive' if ok else 'warning',
        )

    def _ctx_delete_selection(self: Any) -> None:
        """Delete selected nodes via context menu."""
        to_delete = set(self._selected_node_ids)
        self._ctx_dismiss()
        self._selected_node_ids.clear()
        self._delete_nodes_batch(to_delete)

    def _handle_viewport_mousemove(self: Any, event: Any) -> None:
        args = dict(event.args or {})
        if str(args.get('action') or '') != 'start':
            return
        node_id = str(args.get('node_id') or '')
        if not node_id:
            return
        self._start_drag_node(node_id, event)

    def _handle_canvas_click(self: Any, event: Any) -> None:
        args = dict(event.args or {})
        action = str(args.get('action') or '')
        if action == 'select':
            self._select_connection(str(args.get('connection_id') or ''))
            return
        if action == 'clear':
            ctx_was_open = self._ctx_menu_node_id is not None
            self._ctx_menu_node_id = None
            changed = (
                ctx_was_open
                or self._selected_connection_id is not None
                or bool(self._selected_node_ids)
            )
            self._selected_connection_id = None
            self._selected_node_ids.clear()
            if changed:
                self.refresh()
            self._update_hint()

    def _handle_canvas_context(self: Any, event: Any) -> None:
        connection_id = str((event.args or {}).get('connection_id') or '')
        if connection_id:
            self._delete_connection(connection_id)

    def _handle_canvas_drop(self: Any, event: Any) -> None:
        args = dict(event.args or {})
        spec_data = str(args.get('spec') or '').strip()
        raw_x = args.get('x')
        raw_y = args.get('y')
        x = _MANUAL_X if raw_x in (None, '') else int(str(raw_x))
        y = _MANUAL_Y if raw_y in (None, '') else int(str(raw_y))
        x, y = self._snap_grid_point(x, y)
        if spec_data:
            try:
                spec = json.loads(spec_data)
            except json.JSONDecodeError:
                spec = None
            if isinstance(spec, dict):
                self._add_variable_node_at_position(spec, x, y)
                return
        kind = str(args.get('kind') or '')
        if not is_acherion_manual_add_kind(kind):
            return
        self._add_node_at_position(kind, x, y)

    def _handle_canvas_key(self: Any, event: Any) -> None:
        args = dict(event.args or {})
        shortcut_id = str(args.get('shortcut_id') or '')
        key = str(args.get('key') or '')
        if shortcut_id == 'delete_selection_primary':
            if self._selected_node_ids:
                to_delete = set(self._selected_node_ids)
                self._selected_node_ids.clear()
                self._delete_nodes_batch(to_delete)
            else:
                self._delete_selected_connection()
            return
        if shortcut_id == 'clear_selection' or key == 'Escape':
            if self._selected_node_ids:
                self._selected_node_ids.clear()
                self.refresh()
                self._update_hint()
            elif self._selected_connection_id is not None:
                self._selected_connection_id = None
                self.refresh()
                self._update_hint()

    def _attach_viewport_events(self: Any, viewport: Any) -> None:
        viewport.on(
            'mousedown',
            lambda _e: None,
            js_handler=(
                '(e) => {'
                'if (e.button !== 0) return;'
                'if (e.target.closest(".ach-node")) return;'
                'if (e.target.closest(".ach-link-hitbox")) return;'
                'if (e.target.closest(".ach-palette-shell")) return;'
                'const vp = e.currentTarget;'
                'const h = window.__oeAcherion;'
                'if (h && h.matchesShortcut(e, "box_select_add", "drag")) {'
                'h.ensureViewportState(vp);'
                'const pt = h.worldPoint(vp, e.clientX, e.clientY);'
                'vp.dataset.rubberActive = "1";'
                'vp.dataset.rubberStartX = String(pt.x);'
                'vp.dataset.rubberStartY = String(pt.y);'
                'vp.dataset.rubberShift = "1";'
                'vp.classList.add("ach-shell-selecting");'
                'return;'
                '}'
                'if (h && h.matchesShortcut(e, "box_select", "drag")) {'
                'h.ensureViewportState(vp);'
                'const pt = h.worldPoint(vp, e.clientX, e.clientY);'
                'vp.dataset.rubberActive = "1";'
                'vp.dataset.rubberStartX = String(pt.x);'
                'vp.dataset.rubberStartY = String(pt.y);'
                'vp.dataset.rubberShift = "0";'
                'vp.classList.add("ach-shell-selecting");'
                'return;'
                '}'
                'vp.dataset.panActive = "1";'
                'vp.dataset.panLastX = String(e.clientX);'
                'vp.dataset.panLastY = String(e.clientY);'
                'vp.classList.add("ach-shell-panning");'
                '}'
            ),
        )
        viewport.on(
            'mousemove',
            self._handle_viewport_mousemove,
            js_handler=(
                '(e) => {'
                'const vp = e.currentTarget;'
                'const h = window.__oeAcherion;'
                'if (h) h.ensureViewportState(vp);'
                'const cid = vp.dataset.dragCandidateNodeId || "";'
                'if (cid && h) {'
                'const sx = parseFloat(vp.dataset.dragStartClientX || "0");'
                'const sy = parseFloat(vp.dataset.dragStartClientY || "0");'
                'const moved = Math.hypot(e.clientX - sx, e.clientY - sy);'
                'let aid = vp.dataset.dragNodeId || "";'
                'if (!aid && moved >= 4) {'
                'aid = cid;'
                'vp.dataset.dragNodeId = aid;'
                'vp.classList.add("ach-shell-dragging-node");'
                'const stage = h.stage(vp);'
                'const nd = stage ? h.findNode(stage, aid) : null;'
                'if (nd) nd.classList.add("ach-node-dragging");'
                'if (stage && nd) {'
                'const selNds = Array.from(stage.querySelectorAll(".ach-node-selected")).map(n=>n.dataset.nodeId);'
                'if (selNds.includes(aid) && selNds.length > 1) {'
                'const dl=parseFloat(nd.style.left||"0"),dt=parseFloat(nd.style.top||"0");'
                'const grp=selNds.filter(id=>id!==aid).map(id=>{'
                'const gn=h.findNode(stage,id);'
                'return gn?{id,rx:parseFloat(gn.style.left||"0")-dl,ry:parseFloat(gn.style.top||"0")-dt}:null;'
                '}).filter(Boolean);'
                'vp.dataset.dragGroupData=JSON.stringify(grp);'
                '} else if ((nd.dataset.isFunctionBox || "") === "1") {'
                'const fid = nd.dataset.nodeId || aid;'
                'const dl=parseFloat(nd.style.left||"0"),dt=parseFloat(nd.style.top||"0");'
                'const inBox=(n,targetId)=>{'
                'let pid=n.dataset.parentFunctionId||"";'
                'let guard=0;'
                'while(pid && guard<32){'
                'if(pid===targetId)return true;'
                'const parent=h.findNode(stage,pid);'
                'pid=parent?(parent.dataset.parentFunctionId||""):"";'
                'guard+=1;'
                '}'
                'return false;'
                '};'
                'const grp=Array.from(stage.querySelectorAll(".ach-node")).filter(n=>'
                '(n.dataset.nodeId||"")!==aid && inBox(n,fid)).map(n=>({'
                'id:n.dataset.nodeId||"",'
                'rx:parseFloat(n.style.left||"0")-dl,'
                'ry:parseFloat(n.style.top||"0")-dt'
                '})).filter(item=>item.id);'
                'vp.dataset.dragGroupData=JSON.stringify(grp);'
                '} else if ((nd.dataset.groupToken || "")) {'
                'const gt = nd.dataset.groupToken || "";'
                'const dl=parseFloat(nd.style.left||"0"),dt=parseFloat(nd.style.top||"0");'
                'const grp=Array.from(stage.querySelectorAll(".ach-node")).filter(n=>'
                '(n.dataset.groupToken||"")===gt && (n.dataset.nodeId||"")!==aid).map(n=>({'
                'id:n.dataset.nodeId||"",'
                'rx:parseFloat(n.style.left||"0")-dl,'
                'ry:parseFloat(n.style.top||"0")-dt'
                '})).filter(item=>item.id);'
                'vp.dataset.dragGroupData=JSON.stringify(grp);'
                '} else { vp.dataset.dragGroupData="[]"; }'
                '} else { vp.dataset.dragGroupData="[]"; }'
                'emit({action:"start",node_id:aid,'
                'offset_x:Math.round(parseFloat(vp.dataset.dragOffsetX||"0")),'
                'offset_y:Math.round(parseFloat(vp.dataset.dragOffsetY||"0"))});'
                '}'
                'if (aid) {'
                'const pt = h.worldPoint(vp, e.clientX, e.clientY);'
                'const snapped = h.snapPoint('
                'vp,'
                'pt.x - parseFloat(vp.dataset.dragOffsetX||"0"),'
                'pt.y - parseFloat(vp.dataset.dragOffsetY||"0")'
                ');'
                'const l = snapped.x;'
                'const t = snapped.y;'
                'const stage = h.stage(vp);'
                'if (stage) {'
                'h.moveNode(stage, aid, l, t);'
                'const grp=JSON.parse(vp.dataset.dragGroupData||"[]");'
                'grp.forEach(item=>h.moveNode(stage,item.id,l+item.rx,t+item.ry));'
                '}'
                'return;'
                '}'
                '}'
                'if (vp.dataset.rubberActive==="1" && h) {'
                'const pt=h.worldPoint(vp,e.clientX,e.clientY);'
                'h.updateRubberBand(vp,parseFloat(vp.dataset.rubberStartX||"0"),parseFloat(vp.dataset.rubberStartY||"0"),pt.x,pt.y);'
                'return;'
                '}'
                'if (vp.dataset.panActive !== "1") return;'
                'const stage = vp.querySelector(".ach-canvas");'
                'if (!stage) return;'
                'const lx = parseFloat(vp.dataset.panLastX || "0");'
                'const ly = parseFloat(vp.dataset.panLastY || "0");'
                'const dx = e.clientX - lx, dy = e.clientY - ly;'
                'const px = parseFloat(vp.dataset.panX || "0") + dx;'
                'const py = parseFloat(vp.dataset.panY || "0") + dy;'
                'vp.dataset.panX = String(px);'
                'vp.dataset.panY = String(py);'
                'vp.dataset.panLastX = String(e.clientX);'
                'vp.dataset.panLastY = String(e.clientY);'
                'h.applyViewportTransform(vp);'
                '}'
            ),
        )
        finish_js = (
            '(e) => {'
            'const vp = e.currentTarget;'
            'const h = window.__oeAcherion;'
            'const aid = vp.dataset.dragNodeId || "";'
            'const clear = () => {'
            'vp.dataset.dragCandidateNodeId = "";'
            'vp.dataset.dragGroupToken = "";'
            'vp.dataset.dragStartClientX = "";'
            'vp.dataset.dragStartClientY = "";'
            'vp.dataset.dragOffsetX = "";'
            'vp.dataset.dragOffsetY = "";'
            '};'
            'if (vp.dataset.rubberActive === "1" && h) {'
            'const stage = h.stage(vp);'
            'const pt = h.worldPoint(vp, e.clientX, e.clientY);'
            'const x1=parseFloat(vp.dataset.rubberStartX||"0");'
            'const y1=parseFloat(vp.dataset.rubberStartY||"0");'
            'const nodeIds=stage?h.nodesInRect(stage,x1,y1,pt.x,pt.y):[];'
            'h.clearRubberBand(vp);'
            'vp.dataset.rubberActive="";'
            'vp.dataset.suppressNextCanvasClick="1";'
            'vp.classList.remove("ach-shell-selecting");'
            'clear();'
            'emit({rubber_node_ids:nodeIds,add:vp.dataset.rubberShift==="1"});'
            'return;'
            '}'
            'if (aid && h) {'
            'const pt = h.worldPoint(vp, e.clientX, e.clientY);'
            'const snapped = h.snapPoint('
            'vp,'
            'pt.x - parseFloat(vp.dataset.dragOffsetX||"0"),'
            'pt.y - parseFloat(vp.dataset.dragOffsetY||"0")'
            ');'
            'const l = snapped.x;'
            'const t = snapped.y;'
            'const stage = h.stage(vp);'
            'const grpData = JSON.parse(vp.dataset.dragGroupData||"[]");'
            'if (stage) {'
            'h.moveNode(stage, aid, l, t);'
            'const nd = h.findNode(stage, aid);'
            'if (nd) nd.classList.remove("ach-node-dragging");'
            'grpData.forEach(item => {'
            'h.moveNode(stage,item.id,l+item.rx,t+item.ry);'
            'const gnd=h.findNode(stage,item.id);if(gnd)gnd.classList.remove("ach-node-dragging");'
            '});'
            '}'
            'vp.dataset.dragNodeId = "";'
            'vp.classList.remove("ach-shell-dragging-node");'
            'vp.dataset.dragGroupData = "[]";'
            'clear();'
            'const gm = grpData.map(item => ({'
            'node_id:item.id,'
            'left:Math.round(l + item.rx),'
            'top:Math.round(t + item.ry)'
            '}));'
            'emit({node_id:aid,left:Math.round(l),top:Math.round(t),group_moves:gm});'
            'return;'
            '}'
            'clear();'
            'vp.dataset.panActive = "0";'
            'vp.classList.remove("ach-shell-panning");'
            '}'
        )
        viewport.on('mouseup', self._finish_drag_node, js_handler=finish_js)
        viewport.on('mouseleave', self._finish_drag_node, js_handler=finish_js)
        viewport.on(
            'wheel',
            lambda _e: None,
            js_handler=(
                '(e) => {'
                'const vp = e.currentTarget;'
                'const h = window.__oeAcherion;'
                'if (e.target.closest(".ach-palette-shell")) return;'
                'if (vp.dataset.dragNodeId || vp.dataset.dragCandidateNodeId) return;'
                'if (!h || !h.matchesShortcut(e, "zoom_canvas", "wheel")) return;'
                'e.preventDefault();'
                'h.ensureViewportState(vp);'
                'const stage = vp.querySelector(".ach-canvas");'
                'if (!stage) return;'
                'const rect = vp.getBoundingClientRect();'
                'const os = parseFloat(vp.dataset.scale || "1");'
                'const zoom = e.deltaY < 0 ? 1.12 : 0.89;'
                'const ns = Math.max(0.08, Math.min(4.0, os * zoom));'
                'const px = parseFloat(vp.dataset.panX || "0");'
                'const py = parseFloat(vp.dataset.panY || "0");'
                'const wx = (e.clientX - rect.left - px) / os;'
                'const wy = (e.clientY - rect.top - py) / os;'
                'vp.dataset.scale = String(ns);'
                'vp.dataset.panX = String((e.clientX - rect.left) - wx * ns);'
                'vp.dataset.panY = String((e.clientY - rect.top) - wy * ns);'
                'h.applyViewportTransform(vp);'
                '}'
            ),
        )
        viewport.on(
            'dragover',
            lambda _e: None,
            js_handler=(
                '(e) => {'
                "if (!e.dataTransfer.types.includes('text/ach-kind') && !e.dataTransfer.types.includes('text/ach-node-spec')) return;"
                'e.preventDefault();'
                "e.dataTransfer.dropEffect = 'copy';"
                '}'
            ),
        )
        viewport.on(
            'drop',
            self._handle_canvas_drop,
            js_handler=(
                '(e) => {'
                "const spec = e.dataTransfer.getData('text/ach-node-spec');"
                "const kind = e.dataTransfer.getData('text/ach-kind');"
                'if (!spec && !kind) return;'
                'e.preventDefault();'
                'const vp = e.currentTarget;'
                'const h = window.__oeAcherion;'
                'if (!h) return;'
                'const pt = h.worldPoint(vp, e.clientX, e.clientY);'
                'const snapped = h.snapPoint(vp, pt.x, pt.y);'
                'emit({kind: kind, spec: spec, x: Math.round(snapped.x), y: Math.round(snapped.y)});'
                '}'
            ),
        )

    def _attach_canvas_events(self: Any, canvas: Any) -> None:
        canvas.on(
            'click',
            self._handle_canvas_click,
            js_handler=(
                '(e) => {'
                'const vp = e.currentTarget.closest(".ach-shell");'
                'if (vp && vp.dataset.suppressNextCanvasClick === "1") {'
                'vp.dataset.suppressNextCanvasClick = "";'
                'return;'
                '}'
                'if (e.ctrlKey || e.metaKey) return;'
                'const hit = e.target.closest(".ach-link-hitbox");'
                'if (hit) {'
                'e.preventDefault(); e.stopPropagation();'
                'e.currentTarget.focus();'
                'emit({action:"select",'
                'connection_id:hit.dataset.connectionId||""});'
                'return;'
                '}'
                'if (e.target.closest(".ach-node")) return;'
                'emit({action:"clear"});'
                '}'
            ),
        )
        canvas.on(
            'contextmenu.prevent',
            self._handle_canvas_context,
            js_handler=(
                '(e) => {'
                'const hit = e.target.closest(".ach-link-hitbox");'
                'if (!hit) return;'
                'e.preventDefault(); e.stopPropagation();'
                'e.currentTarget.focus();'
                'emit({connection_id:hit.dataset.connectionId||""});'
                '}'
            ),
        )
        canvas.on(
            'keydown',
            self._handle_canvas_key,
            js_handler=(
                '(e) => {'
                'const h = window.__oeAcherion;'
                'if (!h) return;'
                'const tag = (e.target.tagName || "").toUpperCase();'
                'if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT"'
                ' || e.target.isContentEditable) return;'
                'let shortcutId = "";'
                'if (h.matchesShortcut(e, "delete_selection_primary", "keyboard")) {'
                'shortcutId = "delete_selection_primary";'
                '} else if (h.matchesShortcut(e, "clear_selection", "keyboard")) {'
                'shortcutId = "clear_selection";'
                '}'
                'if (!shortcutId) return;'
                'e.preventDefault(); e.stopPropagation();'
                'emit({shortcut_id: shortcutId, key:e.key});'
                '}'
            ),
        )
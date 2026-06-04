"""Connection and source-reference helpers for visual-logic graph ops."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from typing import Any

from acherion.catalog import types as _catalog_types
from acherion.model import AcherionNode


class _GraphOpsConnectionsMixin:
    """Connection bookkeeping, source references, and wire actions."""

    @staticmethod
    def _normalize_exec_sources(value: object) -> list[str]:
        """Return a cleaned list of exec source ids."""
        if isinstance(value, str):
            cleaned = str(value or '').strip()
            return [cleaned] if cleaned else []
        if not isinstance(value, list):
            return []
        out: list[str] = []
        seen: set[str] = set()
        for raw_source in value:
            cleaned = str(raw_source or '').strip()
            if not cleaned or cleaned in seen:
                continue
            out.append(cleaned)
            seen.add(cleaned)
        return out

    def _exec_source_ids(self: Any, node: AcherionNode) -> list[str]:
        """Return all exec sources for one node."""
        sources = [
            self._canonical_exec_source_id(source_id)
            for source_id in self._normalize_exec_sources(
                node.params.get('exec_sources')
            )
        ]
        sources = self._normalize_exec_sources(sources)
        node.params['exec_sources'] = list(sources)
        node.params.pop('exec_source', None)
        return list(sources)

    def _canonical_exec_source_id(
        self: Any,
        source_id: str,
    ) -> str:
        """Return canonical exec source id for one stored connection."""
        cleaned = str(source_id or '').strip()
        if not cleaned or '@' in cleaned:
            return cleaned
        source_node = self._node_by_id(self._pure_node_id(cleaned))
        if source_node is None:
            return cleaned
        exec_indexes = [
            index
            for index, pin in enumerate(self._output_pin_specs(source_node))
            if str(pin.get('type') or '') == 'exec'
        ]
        if len(exec_indexes) != 1:
            return cleaned
        return f'{source_node.node_id}@{exec_indexes[0]}'

    def _set_exec_sources(
        self: Any,
        node: AcherionNode,
        source_ids: list[str],
    ) -> None:
        """Persist exec-source fan-in list."""
        normalized = [
            self._canonical_exec_source_id(source_id)
            for source_id in self._normalize_exec_sources(source_ids)
        ]
        normalized = self._normalize_exec_sources(normalized)
        node.params['exec_sources'] = list(normalized)
        node.params.pop('exec_source', None)

    def _prune_invalid_exec_connections(self: Any) -> None:
        """Drop exec links that no longer point at an exec-capable output."""
        for node in self._graph.nodes:
            source_ids = self._exec_source_ids(node)
            if not source_ids:
                continue
            has_exec_input = any(
                pin.get('pin_id') == 'exec_source'
                for pin in self._input_pin_specs(node)
            )
            if not has_exec_input:
                node.params.pop('exec_sources', None)
                continue
            valid_sources: list[str] = []
            for source_id in source_ids:
                source_node = self._node_by_id(self._pure_node_id(source_id))
                if source_node is None:
                    continue
                output_specs = self._output_pin_specs(source_node)
                output_index = self._source_pin_index(source_id)
                if output_index >= len(output_specs):
                    continue
                if str(output_specs[output_index].get('type') or '') != 'exec':
                    continue
                valid_sources.append(source_id)
            self._set_exec_sources(node, valid_sources)

    def _clear_outgoing_connections(self: Any, source_id: str) -> None:
        """Clear all outgoing wires that currently use one exact source id."""
        if not source_id:
            return
        for node in self._graph.nodes:
            for pin in self._input_pin_specs(node):
                if pin['pin_id'] == 'exec_source':
                    remaining_sources = [
                        stored_source
                        for stored_source in self._exec_source_ids(node)
                        if stored_source != source_id
                    ]
                    if len(remaining_sources) != len(
                        self._exec_source_ids(node)
                    ):
                        self._set_exec_sources(node, remaining_sources)
                    continue
                if self._input_source_id(node, pin['pin_id']) != source_id:
                    continue
                self._set_input_source(node, pin['pin_id'], '')

    def _clear_removed_source_refs(
        self: Any,
        *,
        removed_node_ids: set[str],
        removed_source_ids: set[str],
    ) -> None:
        if not removed_node_ids and not removed_source_ids:
            return
        for node in self._graph.nodes:
            for pin in self._input_pin_specs(node):
                if pin['pin_id'] == 'exec_source':
                    remaining_sources = [
                        source_id
                        for source_id in self._exec_source_ids(node)
                        if (
                            self._pure_node_id(source_id)
                            not in removed_node_ids
                            and source_id not in removed_source_ids
                        )
                    ]
                    if len(remaining_sources) != len(
                        self._exec_source_ids(node)
                    ):
                        self._set_exec_sources(node, remaining_sources)
                    continue
                source_id = self._input_source_id(node, pin['pin_id'])
                if not source_id:
                    continue
                if (
                    self._pure_node_id(source_id) in removed_node_ids
                    or source_id in removed_source_ids
                ):
                    self._set_input_source(node, pin['pin_id'], '')
        pending_source_id = str(self._pending_source_node_id or '')
        if (
            self._pure_node_id(pending_source_id) in removed_node_ids
            or pending_source_id in removed_source_ids
        ):
            self._pending_source_node_id = None

    def _clear_input_sources_for_node(
        self: Any,
        node: AcherionNode,
    ) -> bool:
        """Clear all incoming source refs and literal pin fallbacks on a node."""
        changed = False
        for pin in self._input_pin_specs(node):
            pin_id = str(pin.get('pin_id') or '').strip()
            if not pin_id:
                continue
            if pin_id == 'exec_source':
                current_sources = self._exec_source_ids(node)
                if current_sources:
                    self._set_exec_sources(node, [])
                    changed = True
                continue
            if self._input_source_id(node, pin_id):
                self._set_input_source(node, pin_id, '')
                changed = True

        raw_literals = node.params.get('pin_literals')
        if isinstance(raw_literals, dict) and raw_literals:
            node.params.pop('pin_literals', None)
            changed = True
        elif 'pin_literals' in node.params and not isinstance(raw_literals, dict):
            node.params.pop('pin_literals', None)
            changed = True

        return changed

    def _clear_stored_source_refs_for_node(
        self: Any,
        node: AcherionNode,
    ) -> bool:
        """Clear stale source-reference stores not represented by visible pins."""
        changed = False
        exec_sources = self._normalize_exec_sources(
            node.params.get('exec_sources')
        )
        if exec_sources:
            node.params['exec_sources'] = []
            changed = True
        if node.params.pop('exec_source', None):
            changed = True

        arg_sources = list(node.params.get('arg_sources') or [])
        if any(str(source_id or '').strip() for source_id in arg_sources):
            node.params['arg_sources'] = ['' for _source_id in arg_sources]
            changed = True

        named_sources = dict(node.params.get('named_sources') or {})
        if any(str(source_id or '').strip() for source_id in named_sources.values()):
            node.params['named_sources'] = {
                name: '' for name in named_sources
            }
            changed = True

        box_input_sources = dict(node.params.get('box_input_sources') or {})
        if any(
            str(source_id or '').strip()
            for source_id in box_input_sources.values()
        ):
            node.params['box_input_sources'] = {
                input_id: '' for input_id in box_input_sources
            }
            changed = True

        return changed

    def _clear_outgoing_refs_to_node_ids(
        self: Any,
        node_ids: set[str],
    ) -> bool:
        """Clear all graph refs whose source node is in node_ids."""
        target_ids = {
            str(node_id or '').strip()
            for node_id in node_ids
            if str(node_id or '').strip()
        }
        if not target_ids:
            return False
        changed = False
        for node in self._graph.nodes:
            for pin in self._input_pin_specs(node):
                pin_id = str(pin.get('pin_id') or '').strip()
                if not pin_id:
                    continue
                if pin_id == 'exec_source':
                    current_sources = self._exec_source_ids(node)
                    remaining_sources = [
                        source_id
                        for source_id in current_sources
                        if self._pure_node_id(source_id) not in target_ids
                    ]
                    if len(remaining_sources) != len(current_sources):
                        self._set_exec_sources(node, remaining_sources)
                        changed = True
                    continue

                source_id = self._input_source_id(node, pin_id)
                if (
                    source_id
                    and self._pure_node_id(source_id) in target_ids
                ):
                    self._set_input_source(node, pin_id, '')
                    changed = True

        pending_source_id = str(self._pending_source_node_id or '')
        if pending_source_id and self._pure_node_id(pending_source_id) in target_ids:
            self._pending_source_node_id = None
            changed = True
        return changed

    def _clear_node_pins(
        self: Any,
        node_ids: set[str],
    ) -> bool:
        """Clear all incoming and outgoing pin refs for selected nodes."""
        valid_ids = {
            node.node_id
            for node in self._graph.nodes
            if node.node_id in node_ids
        }
        if not valid_ids:
            return False

        changed = self._clear_outgoing_refs_to_node_ids(valid_ids)
        for node in self._graph.nodes:
            if node.node_id not in valid_ids:
                continue
            if self._clear_input_sources_for_node(node):
                changed = True
            if self._clear_stored_source_refs_for_node(node):
                changed = True
        if changed:
            self._selected_connection_id = None
        return changed

    def _input_source_id(
        self: Any,
        node: AcherionNode,
        pin_id: str,
    ) -> str:
        if pin_id == 'exec_source':
            return next(iter(self._exec_source_ids(node)), '')
        if pin_id.startswith('fin:'):
            input_node_id = pin_id.split(':', 1)[1]
            sources = dict(node.params.get('box_input_sources') or {})
            return str(sources.get(input_node_id) or '')
        if pin_id.startswith('arg:'):
            arg_index = int(pin_id.split(':', 1)[1])
            arg_sources = list(node.params.get('arg_sources') or [])
            if arg_index >= len(arg_sources):
                return ''
            return str(arg_sources[arg_index] or '')
        if pin_id.startswith('named:'):
            param_name = pin_id.split(':', 1)[1]
            named = dict(node.params.get('named_sources') or {})
            return str(named.get(param_name) or '')
        return str(node.params.get(pin_id) or '')

    def _set_input_source(
        self: Any,
        node: AcherionNode,
        pin_id: str,
        source_id: str,
    ) -> None:
        if pin_id == 'exec_source':
            self._set_exec_sources(node, [source_id] if source_id else [])
            return
        if pin_id.startswith('fin:'):
            input_node_id = pin_id.split(':', 1)[1]
            sources = dict(node.params.get('box_input_sources') or {})
            sources[input_node_id] = source_id
            node.params['box_input_sources'] = sources
            return
        if pin_id.startswith('arg:'):
            arg_index = int(pin_id.split(':', 1)[1])
            arg_sources = list(node.params.get('arg_sources') or [])
            while len(arg_sources) <= arg_index:
                arg_sources.append('')
            arg_sources[arg_index] = source_id
            node.params['arg_sources'] = arg_sources
            return
        if pin_id.startswith('named:'):
            param_name = pin_id.split(':', 1)[1]
            named = dict(node.params.get('named_sources') or {})
            named[param_name] = source_id
            node.params['named_sources'] = named
            return
        node.params[pin_id] = source_id

    def _connection_specs(self: Any) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for node in self._graph.nodes:
            for input_index, pin in enumerate(self._input_pin_specs(node)):
                source_ids = (
                    self._exec_source_ids(node)
                    if pin['pin_id'] == 'exec_source'
                    else [self._input_source_id(node, pin['pin_id'])]
                )
                for source_id in source_ids:
                    if not source_id:
                        continue
                    source_node_id = self._pure_node_id(source_id)
                    source_node = self._node_by_id(source_node_id)
                    if source_node is None:
                        continue
                    if not self._output_pin_specs(source_node):
                        continue
                    specs.append({
                        'connection_id': self._connection_id(
                            node.node_id,
                            pin['pin_id'],
                            source_id=source_id,
                        ),
                        'source_node': source_node,
                        'full_source_id': source_id,
                        'out_pin_index': self._source_pin_index(source_id),
                        'target_node': node,
                        'pin_id': pin['pin_id'],
                        'input_index': input_index,
                    })
        return specs

    def _has_outgoing_connection(self: Any, full_source_id: str) -> bool:
        target_nid = self._pure_node_id(full_source_id)
        target_pin = self._source_pin_index(full_source_id)
        for spec in self._connection_specs():
            stored = spec['full_source_id']
            if (
                self._pure_node_id(stored) == target_nid
                and self._source_pin_index(stored) == target_pin
            ):
                return True
        return False

    def _select_connection(self: Any, connection_id: str | None) -> None:
        self._selected_connection_id = (
            str(connection_id or '').strip() or None
        )
        self.refresh()
        self._update_hint()

    def _delete_connection(self: Any, connection_id: str | None) -> None:
        data = self._split_connection_id(str(connection_id or ''))
        if data is None:
            return
        target_node_id, pin_id, source_id = data
        target_node = self._node_by_id(target_node_id)
        if target_node is None:
            return
        self._selected_connection_id = None
        if pin_id == 'exec_source':
            remaining = [
                stored_source
                for stored_source in self._exec_source_ids(target_node)
                if stored_source != source_id
            ]
            self._set_exec_sources(target_node, remaining)
        else:
            self._set_input_source(target_node, pin_id, '')
        self._notify_change()

    def _delete_selected_connection(self: Any) -> None:
        self._delete_connection(self._selected_connection_id)

    def _start_connection(self: Any, source_node_id: str) -> None:
        self._selected_connection_id = None
        if self._pending_source_node_id == source_node_id:
            self._pending_source_node_id = None
        else:
            self._pending_source_node_id = source_node_id
        self.refresh()
        self._update_hint()

    def _connect_input_pin(
        self: Any,
        node: AcherionNode,
        pin_id: str,
    ) -> None:
        if self._pending_source_node_id is None:
            self._update_hint(
                'Select an output pin first, then click an input pin.'
            )
            return
        pending_type = self._pending_output_type()
        target_type = 'any'
        for pin in self._input_pin_specs(node):
            if pin['pin_id'] == pin_id:
                target_type = str(pin.get('type') or 'any')
                break
        if pending_type != 'any' and target_type != 'any':
            if not _catalog_types.types_compatible(pending_type, target_type):
                self._update_hint(
                    f'Incompatible types: output "{pending_type}" cannot '
                    f'connect to input "{target_type}". '
                    f'Choose a compatible output pin.'
                )
                return
        if pending_type == 'exec':
            self._clear_outgoing_connections(self._pending_source_node_id)
            current_sources = self._exec_source_ids(node)
            if self._pending_source_node_id not in current_sources:
                current_sources.append(self._pending_source_node_id)
            self._set_exec_sources(node, current_sources)
        else:
            self._set_input_source(node, pin_id, self._pending_source_node_id)
        self._pending_source_node_id = None
        self._notify_change()

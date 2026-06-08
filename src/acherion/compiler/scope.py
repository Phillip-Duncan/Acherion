"""Exec-flow scope helpers for visual-logic compilation."""

from __future__ import annotations

from typing import Protocol

import acherion.graph_helpers as _graph_helpers
import acherion.node_behaviors as acherion_node_behaviors
from acherion.catalog import runtime as _catalog_runtime
from acherion.catalog import types as _catalog_types

from acherion.compiler.graph import (
    _FunctionBoxGraphView,
    _iter_param_sources,
)
from acherion.compiler.utils import _input_param_expr
from acherion.compiler.state import EmitState
from acherion.registry import (
    _template_has_exec_input,
    _template_has_exec_output,
)
from acherion.model import (
    AcherionNode,
    _node_var_name,
)


_CONSTANT_OUTPUT_TYPE_BY_VALUE_TYPE = {
    'number': 'float',
    'int': 'int',
    'text': 'str',
    'bool': 'bool',
    'dict': 'dict',
}
_ELSE_IF_BRANCH_MIN_CONDITIONS = 1


class _EmitNodeCallback(Protocol):
    """Protocol for node emitters used by exec-flow scope traversal."""

    def __call__(
        self,
        *,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> None:
        ...


class _EmitScope:
    """Emit one scope by following explicit execution pins."""

    def __init__(
        self,
        scope_nodes: list[AcherionNode],
        *,
        state: EmitState,
        function_graph: _FunctionBoxGraphView,
        original_index: dict[str, int],
        entry_node_id: str = '',
        allow_implicit_roots: bool = False,
        owner_name: str | None = 'self',
    ) -> None:
        self._scope_nodes = list(scope_nodes)
        self._state = state
        self._original_index = dict(original_index)
        self._function_graph = function_graph
        self._entry_node_id = str(entry_node_id or '')
        self._allow_implicit_roots = bool(allow_implicit_roots)
        self._owner_name = owner_name
        self._node_index = {
            node.node_id: node for node in self._scope_nodes
        }
        self._emitting_nodes: set[str] = set()
        self._emitted_levels: dict[str, int] = {}
        self._emitting_exec_nodes: set[str] = set()
        self._seeding_getter_nodes: set[str] = set()
        self._dependency_stack: list[str] = []
        self._collects_seeded = False
        self._exec_targets = self._build_exec_targets()

    def seed_collects(self) -> None:
        """Initialize collect accumulators before control flow begins."""
        if self._collects_seeded:
            return
        for node in self._ordered_nodes():
            if node.kind != 'collect':
                continue
            var_name = self._var_name(node)
            self._state.lines.append(f'    {var_name} = []')
            self._state.store(node.node_id, var_name)
        self._collects_seeded = True

    def emit(self, emit_node: _EmitNodeCallback) -> None:
        """Emit this scope by following explicit exec edges."""
        self.seed_collects()
        if self._entry_node_id:
            entry_node = self._node_index.get(self._entry_node_id)
            if entry_node is not None:
                self._emit_exec_node(
                    entry_node,
                    indent_level=1,
                    emit_node=emit_node,
                )
            else:
                self._emit_entry_successors(
                    self._entry_node_id,
                    indent_level=1,
                    emit_node=emit_node,
                )
            return
        if not self._allow_implicit_roots:
            return
        for node in self._ordered_nodes():
            if not self._is_exec_root(node):
                continue
            self._emit_exec_node(node, indent_level=1, emit_node=emit_node)

    def _emit_entry_successors(
        self,
        entry_source_id: str,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        for next_node in self._exec_targets.get(entry_source_id, []):
            self._emit_exec_node(
                next_node,
                indent_level=indent_level,
                emit_node=emit_node,
            )

    def ensure_source(
        self,
        source_id: str,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        """Ensure code exists for one value source within this scope."""
        if not source_id or self._source_is_known(source_id):
            return
        node = self._node_index.get(self._pure_source_id(source_id))
        if node is None:
            return
        if acherion_node_behaviors.compiler_is_exec_gated_producer(node):
            self._seed_unexecuted_producer_none(node, source_id)
            return
        if not self._can_emit_as_dependency(node):
            self._seed_backward_getter_alias(
                node,
                indent_level=indent_level,
                emit_node=emit_node,
            )
            return
        self._ensure_value_emitted(
            node,
            indent_level=indent_level,
            emit_node=emit_node,
        )

    def _ordered_nodes(self) -> list[AcherionNode]:
        return sorted(
            self._scope_nodes,
            key=lambda node: self._original_index.get(node.node_id, 0),
        )

    @staticmethod
    def _normalize_exec_sources(value: object) -> list[str]:
        """Return cleaned exec-source ids from list storage."""
        return _graph_helpers.normalize_exec_sources(value)

    def _exec_source_ids(self, node: AcherionNode) -> list[str]:
        return self._normalize_exec_sources(node.params.get('exec_sources'))

    def _build_exec_targets(self) -> dict[str, list[AcherionNode]]:
        records = [
            (node.node_id, node.params.get('exec_sources'))
            for node in self._ordered_nodes()
        ]
        targets: dict[str, list[AcherionNode]] = {}
        for source_id, node_ids in _graph_helpers.build_exec_targets(records):
            target_nodes = [
                self._node_index[node_id]
                for node_id in node_ids
                if node_id in self._node_index
            ]
            if target_nodes:
                targets[source_id] = target_nodes
        return targets

    def _source_is_known(self, source_id: str) -> bool:
        pure_source = self._pure_source_id(source_id)
        return (
            source_id in self._state.node_vars
            or pure_source in self._state.node_vars
        )

    def _pure_source_id(self, source_id: str) -> str:
        return _graph_helpers.pure_source_id(source_id)

    @staticmethod
    def _source_pin_index(source_id: str) -> int:
        return _graph_helpers.source_pin_index(source_id)

    @staticmethod
    def _else_if_branch_condition_count(node: AcherionNode) -> int:
        try:
            condition_count = int(node.params.get('condition_count', 2) or 2)
        except (TypeError, ValueError):
            condition_count = 2
        return max(_ELSE_IF_BRANCH_MIN_CONDITIONS, condition_count)

    def _var_name(self, node: AcherionNode) -> str:
        index = self._original_index[node.node_id]
        return _node_var_name(index, node)

    def _node_label(self, node_id: str) -> str:
        node = self._node_index.get(node_id)
        if node is None:
            return node_id
        title = str(node.title or '').strip()
        if title:
            return title
        return str(node.kind or node_id).strip() or node_id

    def _raise_data_cycle(self, node_id: str) -> None:
        if node_id in self._dependency_stack:
            start_index = self._dependency_stack.index(node_id)
            cycle_ids = self._dependency_stack[start_index:] + [node_id]
        elif self._dependency_stack:
            cycle_ids = self._dependency_stack + [node_id]
        else:
            cycle_ids = [node_id, node_id]
        cycle_path = ' -> '.join(
            self._node_label(cycle_node_id)
            for cycle_node_id in cycle_ids
        )
        raise ValueError(
            'Cyclic data dependency detected: '
            f'{cycle_path}. Remove one of the value wires.'
        )

    def _indent(self, indent_level: int) -> str:
        return '    ' * indent_level

    def _is_exec_root(self, node: AcherionNode) -> bool:
        if not self._exec_output_pins(node):
            return False
        if self._allow_implicit_roots:
            if (
                acherion_node_behaviors.compiler_is_backward_getter(node)
                and not self._setter_source_id(node)
            ):
                return False
            return (
                acherion_node_behaviors.compiler_is_serial_root(node)
                and not self._exec_source_ids(node)
            )
        if not _template_has_exec_input(node.kind):
            return True
        return not self._exec_source_ids(node)

    def _call_method_return_type(
        self,
        node: AcherionNode,
    ) -> str | None:
        if node.kind != 'call_method':
            return None
        method_name = str(node.params.get('method_name') or '').strip()
        if not method_name:
            return None
        class_path = self._resolve_instance_class_path(
            str(node.params.get('instance') or '').strip()
        )
        if not class_path:
            return None
        entry = _catalog_runtime.method_func_entry(class_path, method_name)
        if entry is None:
            return None
        return str(getattr(entry, 'return_type', '') or '').strip()

    def _source_output_type(
        self,
        node: AcherionNode,
        source_id: str,
    ) -> str:
        pin_index = self._source_pin_index(source_id)
        if node.kind == 'for_each':
            if pin_index == 0:
                list_source_id = str(node.params.get('list') or '').strip()
                source_node = self._node_index.get(
                    self._pure_source_id(list_source_id)
                )
                if source_node is None or source_node.node_id == node.node_id:
                    return 'any'
                list_type = self._source_output_type(source_node, list_source_id)
                item_type = _catalog_types.list_item_type_tag(list_type)
                return item_type or 'any'
            if pin_index == 1:
                return 'int'
            return 'any'
        if pin_index != 0:
            return 'any'
        if node.kind == 'constant':
            value_type = str(node.params.get('value_type') or 'number').strip()
            return _CONSTANT_OUTPUT_TYPE_BY_VALUE_TYPE.get(value_type, 'float')
        if node.kind == 'call_function':
            function_path = str(node.params.get('function_path') or '').strip()
            entry = (
                _catalog_runtime.catalog_entry(function_path)
                if function_path
                else None
            )
            if entry is None:
                return 'any'
            if bool(getattr(entry, 'is_class', False)):
                return str(getattr(entry, 'return_type', '') or 'object')
            return str(getattr(entry, 'return_type', '') or 'any')
        if node.kind == 'call_method':
            return self._call_method_return_type(node) or 'any'
        if node.kind == 'list_index':
            mode = str(node.params.get('mode') or 'index').strip()
            if mode != 'slice':
                return 'any'
            list_source_id = str(node.params.get('source') or '').strip()
            source_node = self._node_index.get(
                self._pure_source_id(list_source_id)
            )
            if source_node is None or source_node.node_id == node.node_id:
                return 'any'
            list_type = self._source_output_type(source_node, list_source_id)
            if _catalog_types.is_list_like_type_tag(list_type):
                return list_type
            return 'any'
        if node.kind == 'list_set':
            list_source_id = str(node.params.get('source') or '').strip()
            source_node = self._node_index.get(
                self._pure_source_id(list_source_id)
            )
            if source_node is None or source_node.node_id == node.node_id:
                return 'any'
            list_type = self._source_output_type(source_node, list_source_id)
            if _catalog_types.is_list_like_type_tag(list_type):
                return list_type
            return 'any'
        if node.kind == 'reroute':
            reroute_source_id = str(node.params.get('source') or '').strip()
            source_node = self._node_index.get(
                self._pure_source_id(reroute_source_id)
            )
            if source_node is None or source_node.node_id == node.node_id:
                return 'any'
            return self._source_output_type(source_node, reroute_source_id)
        return _catalog_types.node_kind_to_type(node.kind)

    def _resolve_instance_class_path(
        self,
        source_id: str,
        _depth: int = 0,
    ) -> str:
        if not source_id or _depth > 5:
            return ''
        node = self._node_index.get(self._pure_source_id(source_id))
        if node is None:
            return ''
        resolved_class_path = _catalog_types.runtime_class_path_for_type_tag(
            self._source_output_type(node, source_id)
        )
        if resolved_class_path:
            return resolved_class_path
        resolved_class_path = _catalog_types.runtime_class_path_for_type_tag(
            _catalog_types.node_kind_to_type(node.kind)
        )
        if resolved_class_path:
            return resolved_class_path
        if node.kind == 'call_function':
            function_path = str(node.params.get('function_path') or '').strip()
            entry = (
                _catalog_runtime.catalog_entry(function_path)
                if function_path
                else None
            )
            if entry is not None and bool(getattr(entry, 'is_class', False)):
                return function_path
        if node.kind in {'call_method', 'get_attribute'}:
            instance_source = str(node.params.get('instance') or '').strip()
            return self._resolve_instance_class_path(
                instance_source,
                _depth + 1,
            )
        return ''

    def _call_method_has_zero_data_exec_output(
        self,
        node: AcherionNode,
    ) -> bool:
        return_type = self._call_method_return_type(node)
        if return_type is None:
            return False
        return not return_type

    def _exec_output_pins(
        self,
        node: AcherionNode,
    ) -> list[tuple[int, str]]:
        if node.kind == 'branch_route':
            return [(0, 'if_true'), (1, 'if_false')]
        if node.kind == 'else_if_branch':
            condition_count = self._else_if_branch_condition_count(node)
            return [
                (0, 'if:0'),
                *[
                    (index, f'elif:{index}')
                    for index in range(1, condition_count)
                ],
                (condition_count, 'else'),
            ]
        if node.kind == 'for_each':
            return [(2, 'loop_body'), (3, 'completed')]
        if node.kind == 'sequencer':
            then_count = max(2, int(node.params.get('then_count', 2) or 2))
            return [
                (index, f'then:{index}')
                for index in range(then_count)
            ]
        if not _template_has_exec_output(node.kind):
            return []
        if node.kind == 'function_box':
            return [(0, 'exec')]
        has_zero_data_exec_output = (
            acherion_node_behaviors.compiler_has_zero_data_exec_output(node)
            or self._call_method_has_zero_data_exec_output(node)
        )
        exec_index = (
            0
            if has_zero_data_exec_output
            else 1
        )
        return [(exec_index, 'exec')]

    def _full_output_source_id(
        self,
        node: AcherionNode,
        pin_index: int,
    ) -> str:
        return f'{node.node_id}@{pin_index}'

    def _exec_successors(
        self,
        node: AcherionNode,
        pin_index: int,
    ) -> list[AcherionNode]:
        source_ids = [self._full_output_source_id(node, pin_index)]
        if pin_index == 0:
            # Older graphs stored pin-zero sources as plain node_id. Accept that
            # alias while new graphs use canonical node_id@pin_index everywhere.
            source_ids.append(node.node_id)
        elif pin_index > 0:
            # Mixed producer/exec nodes historically stored exec wires as plain
            # node_id. Accept that alias for backwards compatibility.
            source_ids.append(node.node_id)

        successors: list[AcherionNode] = []
        seen_node_ids: set[str] = set()
        for source_id in source_ids:
            for successor in self._exec_targets.get(source_id, []):
                if successor.node_id in seen_node_ids:
                    continue
                seen_node_ids.add(successor.node_id)
                successors.append(successor)
        return successors

    def _data_source_ids(self, node: AcherionNode) -> list[str]:
        return [
            source_id
            for source_id in _iter_param_sources(node)
            if self._pure_source_id(source_id) in self._node_index
        ]

    def _setter_source_id(self, node: AcherionNode) -> str:
        """Return the data source that makes one getter node imperative."""
        if not acherion_node_behaviors.compiler_is_backward_getter(node):
            return ''
        return str(node.params.get('source') or '').strip()

    def _seed_unexecuted_producer_none(
        self,
        node: AcherionNode,
        source_id: str,
    ) -> None:
        """Bind unread exec-gated producer outputs to None, not fresh calls."""
        if self._source_is_known(source_id):
            return
        pin_index = self._source_pin_index(source_id)
        self._state.store(node.node_id, 'None', pin=pin_index)
        self._state.store_source(source_id, 'None')

    def _seed_backward_getter_alias(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        """Seed getter-only value aliases without forcing setter exec order."""
        if not acherion_node_behaviors.compiler_is_backward_getter(node):
            return
        if node.node_id in self._seeding_getter_nodes:
            self._raise_data_cycle(node.node_id)
        if self._source_is_known(node.node_id):
            return

        self._seeding_getter_nodes.add(node.node_id)
        self._dependency_stack.append(node.node_id)
        try:
            source_id = self._setter_source_id(node)
            source_expr: str | None = None
            if source_id:
                self.ensure_source(
                    source_id,
                    indent_level=indent_level,
                    emit_node=emit_node,
                )
                source_expr = self._state.source_expr(source_id)
            expr = acherion_node_behaviors.dependency_expr_for_node(
                node,
                source_expr=source_expr,
                owner_name=self._owner_name,
            )
            if expr is None:
                return
            self._state.store(node.node_id, expr)
        finally:
            self._dependency_stack.pop()
            self._seeding_getter_nodes.discard(node.node_id)

    def _ensure_dependencies(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        for source_id in self._data_source_ids(node):
            self.ensure_source(
                source_id,
                indent_level=indent_level,
                emit_node=emit_node,
            )

    def _can_reemit(self, node: AcherionNode) -> bool:
        return acherion_node_behaviors.compiler_can_reemit(node)

    def _can_emit_as_dependency(self, node: AcherionNode) -> bool:
        if acherion_node_behaviors.compiler_is_backward_getter(node):
            if self._setter_source_id(node):
                return False
            return True
        if acherion_node_behaviors.compiler_is_serial_root(node):
            return True
        return not (
            _template_has_exec_input(node.kind)
            or _template_has_exec_output(node.kind)
        )

    def _ensure_value_emitted(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        if node.kind in {
            'branch_route',
            'else_if_branch',
            'for_each',
            'function_entry',
        }:
            return
        if node.kind == 'sequencer':
            return
        previous_level = self._emitted_levels.get(node.node_id)
        if previous_level is not None:
            if previous_level <= indent_level:
                return
            if not self._can_reemit(node):
                return
        if node.node_id in self._emitting_nodes:
            self._raise_data_cycle(node.node_id)
        self._emitting_nodes.add(node.node_id)
        self._dependency_stack.append(node.node_id)
        try:
            self._ensure_dependencies(
                node,
                indent_level=indent_level,
                emit_node=emit_node,
            )
            emit_node(
                node=node,
                params=dict(node.params),
                var_name=self._var_name(node),
                indent=self._indent(indent_level),
            )
            self._emitted_levels[node.node_id] = indent_level
        finally:
            self._dependency_stack.pop()
            self._emitting_nodes.discard(node.node_id)

    def _emit_branch(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        self._ensure_dependencies(
            node,
            indent_level=indent_level,
            emit_node=emit_node,
        )
        indent = self._indent(indent_level)
        cond_expr = _input_param_expr(
            dict(node.params),
            'condition_source',
            self._state.node_vars,
            fallback='False',
        )
        true_target = next(iter(self._exec_successors(node, 0)), None)
        false_target = next(iter(self._exec_successors(node, 1)), None)
        self._state.lines.append(f'{indent}if bool({cond_expr}):')
        if true_target is not None:
            self._emit_exec_node(
                true_target,
                indent_level=indent_level + 1,
                emit_node=emit_node,
            )
        if false_target is not None:
            self._state.lines.append(f'{indent}else:')
            self._emit_exec_node(
                false_target,
                indent_level=indent_level + 1,
                emit_node=emit_node,
            )

    def _emit_else_if_branch(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        self._ensure_dependencies(
            node,
            indent_level=indent_level,
            emit_node=emit_node,
        )
        indent = self._indent(indent_level)
        condition_count = self._else_if_branch_condition_count(node)
        for index in range(condition_count):
            condition_pin_id = f'condition:{index}'
            cond_expr = _input_param_expr(
                dict(node.params),
                condition_pin_id,
                self._state.node_vars,
                fallback='False',
            )
            keyword = 'if' if index == 0 else 'elif'
            self._state.lines.append(f'{indent}{keyword} bool({cond_expr}):')
            target = next(iter(self._exec_successors(node, index)), None)
            if target is not None:
                self._emit_exec_node(
                    target,
                    indent_level=indent_level + 1,
                    emit_node=emit_node,
                )
        else_target = next(iter(self._exec_successors(node, condition_count)), None)
        if else_target is not None:
            self._state.lines.append(f'{indent}else:')
            self._emit_exec_node(
                else_target,
                indent_level=indent_level + 1,
                emit_node=emit_node,
            )

    def _emit_for_each(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        self._ensure_dependencies(
            node,
            indent_level=indent_level,
            emit_node=emit_node,
        )
        indent = self._indent(indent_level)
        list_expr = self._state.source_expr(
            str(node.params.get('list') or ''),
            fallback='[]',
        )
        var_name = self._var_name(node)
        item_var = f'{var_name}_item'
        index_var = f'{var_name}_index'
        self._state.store(node.node_id, item_var)
        self._state.store(node.node_id, item_var, 0)
        self._state.store(node.node_id, index_var, 1)
        self._state.lines.append(
            f'{indent}for {index_var}, {item_var} in enumerate({list_expr} or []):'
        )
        body_target = next(iter(self._exec_successors(node, 2)), None)
        if body_target is not None:
            self._emit_exec_node(
                body_target,
                indent_level=indent_level + 1,
                emit_node=emit_node,
            )
        completed_target = next(iter(self._exec_successors(node, 3)), None)
        if completed_target is not None:
            self._emit_exec_node(
                completed_target,
                indent_level=indent_level,
                emit_node=emit_node,
            )

    def _emit_exec_node(
        self,
        node: AcherionNode,
        *,
        indent_level: int,
        emit_node: _EmitNodeCallback,
    ) -> None:
        if node.node_id in self._emitting_exec_nodes:
            return
        self._emitting_exec_nodes.add(node.node_id)
        try:
            if node.kind == 'function_entry':
                for pin_index, _pin_id in self._exec_output_pins(node):
                    for next_node in self._exec_successors(node, pin_index):
                        self._emit_exec_node(
                            next_node,
                            indent_level=indent_level,
                            emit_node=emit_node,
                        )
                return
            if node.kind == 'branch_route':
                self._emit_branch(
                    node,
                    indent_level=indent_level,
                    emit_node=emit_node,
                )
                return
            if node.kind == 'else_if_branch':
                self._emit_else_if_branch(
                    node,
                    indent_level=indent_level,
                    emit_node=emit_node,
                )
                return
            if node.kind == 'for_each':
                self._emit_for_each(
                    node,
                    indent_level=indent_level,
                    emit_node=emit_node,
                )
                return
            if node.kind == 'sequencer':
                for pin_index, _pin_id in self._exec_output_pins(node):
                    for successor in self._exec_successors(node, pin_index):
                        self._emit_exec_node(
                            successor,
                            indent_level=indent_level,
                            emit_node=emit_node,
                        )
                return
            if node.kind == 'exec_reroute':
                for successor in self._exec_successors(node, 0):
                    self._emit_exec_node(
                        successor,
                        indent_level=indent_level,
                        emit_node=emit_node,
                    )
                return
            self._ensure_dependencies(
                node,
                indent_level=indent_level,
                emit_node=emit_node,
            )
            emit_node(
                node=node,
                params=dict(node.params),
                var_name=self._var_name(node),
                indent=self._indent(indent_level),
            )
            for pin_index, _pin_id in self._exec_output_pins(node):
                for successor in self._exec_successors(node, pin_index):
                    self._emit_exec_node(
                        successor,
                        indent_level=indent_level,
                        emit_node=emit_node,
                    )
        finally:
            self._emitting_exec_nodes.discard(node.node_id)

"""Composed helper-library builders for visual-logic compilation."""

from __future__ import annotations

from acherion.compiler.emit_nodes import (
    _emit_common_compute_node,
    _emit_function_box_node,
)
from acherion.compiler.graph import (
    _FunctionBoxGraphView,
)
from acherion.compiler.scope import (
    _EmitScope,
)
from acherion.compiler.state import (
    EmitState,
    ExternalInput,
)
from acherion.compiler.utils import (
    _add_missing_pass,
    _safe_function_name,
)
from acherion.model import (
    AcherionGraph,
    AcherionNode,
)
import acherion.node_behaviors as acherion_node_behaviors


def _unique_param_name(label: str, fallback: str, used: set[str]) -> str:
    """Return a unique helper parameter name."""
    base_name = _safe_function_name(label, fallback)
    name = base_name
    suffix = 2
    while name in used:
        name = f'{base_name}_{suffix}'
        suffix += 1
    used.add(name)
    return name


def _function_entry_source_id(box_node_id: str) -> str:
    """Return canonical hidden entry source id for one function box."""
    return f'{box_node_id}:entry'


class _FunctionBodyCompiler:
    """Compile one function-box body using composed emit state."""

    def __init__(
        self,
        helper_name: str,
        member_nodes: list[AcherionNode],
        *,
        external_inputs: list[ExternalInput],
        return_source_ids: list[str],
        all_nodes: list[AcherionNode] | None = None,
    ) -> None:
        self._helper_name = helper_name
        self._member_nodes = list(member_nodes)
        self._external_inputs = list(external_inputs)
        self._return_source_ids = list(return_source_ids)
        self._scope_nodes = list(all_nodes or member_nodes)
        self._original_index = {
            node.node_id: index for index, node in enumerate(self._scope_nodes)
        }
        self._state = EmitState()
        self._function_graph = _FunctionBoxGraphView(self._scope_nodes)
        self._parent_function_id = self._resolve_parent_function_id()
        self._input_nodes = self._resolve_input_nodes()
        self._entry_node_id = self._resolve_entry_node_id()
        self._scope = _EmitScope(
            self._member_nodes,
            state=self._state,
            function_graph=self._function_graph,
            original_index=self._original_index,
            entry_node_id=self._entry_node_id,
            owner_name=None,
        )

    def compile(self) -> str:
        """Return the compiled helper source."""
        param_names = self._build_param_names()
        signature = ', '.join(param_names)
        self._state.lines.extend([
            f'def {self._helper_name}({signature}):',
        ])
        self._seed_inputs(param_names)
        self._emit_body()
        self._emit_return()
        return '\n'.join(_add_missing_pass(self._state.lines)) + '\n'

    def _resolve_parent_function_id(self) -> str:
        for node in self._member_nodes:
            parent_id = str(node.params.get('parent_function') or '')
            if parent_id:
                return parent_id
        return ''

    def _resolve_input_nodes(self) -> list[AcherionNode]:
        if not self._parent_function_id:
            return []
        parent_box = self._function_graph.node_index.get(
            self._parent_function_id,
        )
        if parent_box is None:
            return []
        return self._function_graph.ordered_io_nodes(
            self._parent_function_id,
            io_kind='function_input',
            ordered_ids=list(parent_box.params.get('input_order') or []),
        )

    def _resolve_entry_node_id(self) -> str:
        if not self._parent_function_id:
            return ''
        for node in self._member_nodes:
            if node.kind != 'function_entry':
                continue
            if str(node.params.get('parent_function') or '') != self._parent_function_id:
                continue
            return node.node_id
        return _function_entry_source_id(self._parent_function_id)

    def _build_param_names(self) -> list[str]:
        used_param_names: set[str] = set()
        param_names: list[str] = []
        external_input_names = {
            str(target_id or ''): str(name or '')
            for name, target_id in self._external_inputs
        }
        if self._input_nodes:
            for index, input_node in enumerate(self._input_nodes):
                label = external_input_names.get(input_node.node_id) or str(
                    input_node.params.get('label')
                    or input_node.params.get('param_name')
                    or input_node.title
                    or ''
                )
                param_names.append(
                    _unique_param_name(
                        label,
                        f'arg_{index + 1}',
                        used_param_names,
                    )
                )
            return param_names

        for index, (name, _source_id) in enumerate(self._external_inputs):
            fallback = f'arg_{index + 1}'
            param_names.append(
                _unique_param_name(
                    str(name or fallback),
                    fallback,
                    used_param_names,
                )
            )
        return param_names

    def _seed_inputs(self, param_names: list[str]) -> None:
        if self._input_nodes:
            for index, input_node in enumerate(self._input_nodes):
                self._state.store(input_node.node_id, param_names[index])
            return

        for (_name, source_id), param_name in zip(
            self._external_inputs,
            param_names,
        ):
            self._state.store_source(str(source_id or ''), param_name)

    def _emit_body(self) -> None:
        self._scope.emit(self._emit_helper_node)

    def _emit_helper_node(
        self,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> None:
        kind = node.kind
        if (
            str(params.get('parent_function') or '')
            != self._parent_function_id
        ):
            return
        if kind in {
            'function_entry',
            'function_input',
            'function_output',
            'branch_route',
            'for_each',
        }:
            return

        if acherion_node_behaviors.emit_static_node(
            state=self._state,
            node=node,
            params=params,
            indent=indent,
            var_name=var_name,
            owner_name=None,
        ):
            return

        if _emit_function_box_node(
            state=self._state,
            node=node,
            params=params,
            function_graph=self._function_graph,
            indent=indent,
            var_name=var_name,
            runtime_self_name=None,
            helper_as_attribute=False,
        ):
            return

        if _emit_common_compute_node(
            state=self._state,
            node=node,
            params=params,
            indent=indent,
            var_name=var_name,
            method_owner_name=None,
        ):
            return

        if acherion_node_behaviors.function_box_unsupported(node):
            self._state.lines.append(
                f'{indent}# Unsupported inside Function Box: {kind}'
            )
            return

        self._state.lines.append(
            f'{indent}{var_name} = None '
            f'# Unsupported extracted node kind: {kind}'
        )
        self._state.store(node.node_id, var_name)

    def _emit_return(self) -> None:
        for source_id in self._return_source_ids:
            if not source_id:
                continue
            self._scope.ensure_source(
                source_id,
                indent_level=1,
                emit_node=self._emit_helper_node,
            )
        return_exprs = [
            self._state.source_expr(source_id)
            for source_id in self._return_source_ids
            if source_id
        ]
        if not return_exprs:
            self._state.lines.append('    return None')
        elif len(return_exprs) == 1:
            self._state.lines.append(f'    return {return_exprs[0]}')
        else:
            self._state.lines.append(
                f"    return ({', '.join(return_exprs)})"
            )


class _HelperLibraryBuilder:
    """Build graph-local static helper methods in dependency-safe order."""

    def __init__(
        self,
        graph: AcherionGraph,
        *,
        function_graph: _FunctionBoxGraphView,
    ) -> None:
        self._graph = graph
        self._function_graph = function_graph

    def build_lines(self) -> list[str]:
        """Return helper method lines ready to prepend before run()."""
        graph_order = {
            node.node_id: index for index, node in enumerate(self._graph.nodes)
        }
        function_boxes = [
            node for node in self._graph.nodes if node.kind == 'function_box'
        ]
        function_boxes.sort(
            key=lambda box: (
                -self._function_graph.function_box_depth(box),
                graph_order.get(box.node_id, 0),
            )
        )

        lines: list[str] = []
        for box in function_boxes:
            helper_code = self._compile_box_helper(box).strip('\n')
            if not helper_code:
                continue
            lines.extend(helper_code.splitlines())
            lines.append('')
        return lines

    def _compile_box_helper(self, box: AcherionNode) -> str:
        member_nodes = [
            node
            for node in self._graph.nodes
            if str(node.params.get('parent_function') or '') == box.node_id
        ]
        helper_name = _safe_function_name(
            str(
                box.params.get('function_name')
                or box.title
                or box.node_id
            ),
            f'function_{box.node_id}',
        )
        return _FunctionBodyCompiler(
            helper_name,
            member_nodes,
            external_inputs=self._function_graph.external_inputs(box),
            return_source_ids=self._function_graph.return_sources(box),
            all_nodes=self._graph.nodes,
        ).compile()
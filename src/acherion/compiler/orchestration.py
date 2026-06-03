"""Shared orchestration for host-specific graph code compilers."""

from __future__ import annotations

import ast
from typing import Any

from acherion.compiler.emit_nodes import (
    _emit_common_compute_node,
    _emit_function_box_node,
)
from acherion.compiler.graph import _FunctionBoxGraphView
from acherion.compiler.helpers import _HelperLibraryBuilder
from acherion.compiler.scope import _EmitScope
from acherion.compiler.state import EmitState
from acherion.compiler.utils import _add_missing_pass
from acherion.events import (
    EXTERNAL_EVENT_NODE_KIND,
    RUN_EVENT_KEY,
    acherion_event_handler_name,
)
from acherion.model import AcherionGraph, AcherionNode, _system_node_id


def _runtime_user_function_source(source_code: str) -> str:
    """Adapt stored custom-function source for standalone runtime execution."""
    normalized_source = str(source_code or '').strip('\n')
    if not normalized_source.strip():
        return ''
    runtime_source = normalized_source.rstrip() + '\n'
    try:
        module = ast.parse(runtime_source)
    except SyntaxError:
        return runtime_source.rstrip('\n')
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        return runtime_source.rstrip('\n')
    function_def = module.body[0]
    positional_args = list(function_def.args.args)
    if not positional_args or positional_args[0].arg != 'self':
        return runtime_source.rstrip('\n')
    function_name = str(function_def.name or '').strip()
    if not function_name:
        return runtime_source.rstrip('\n')
    impl_name = f'_{function_name}_acherion_impl'
    wrapper_lines = [
        f'{impl_name} = {function_name}',
        f'def {function_name}(*args, __acherion_fn={impl_name}):',
        "    return __acherion_fn(globals().get('self'), *args)",
    ]
    return runtime_source.rstrip('\n') + '\n\n' + '\n'.join(wrapper_lines)


class _GraphNodeEmitterBase:
    """Shared node-emission ladder for host-specific graph compilers."""

    _function_graph: Any
    _state: Any

    def _emit_graph_node(
        self,
        *,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> None:
        if str(params.get('parent_function') or '').strip():
            return
        if node.kind == EXTERNAL_EVENT_NODE_KIND:
            return
        if self._emit_host_static_node(
            node=node,
            params=params,
            var_name=var_name,
            indent=indent,
        ):
            self._after_host_static_node(
                node=node,
                params=params,
                var_name=var_name,
                indent=indent,
            )
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
        if node.kind in {'branch_route', 'else_if_branch', 'for_each'}:
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
        self._emit_host_fallback_node(
            node=node,
            params=params,
            var_name=var_name,
            indent=indent,
        )

    def _emit_host_static_node(
        self,
        *,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> bool:
        del node, params, var_name, indent
        return False

    def _after_host_static_node(
        self,
        *,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> None:
        del node, params, var_name, indent

    def _emit_host_fallback_node(
        self,
        *,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> None:
        del node, params, var_name, indent
        raise NotImplementedError()


class _GraphRunCompilerBase:
    """Shared run-compiler orchestration for host-specific emitters."""

    _EVENT_NODE_ID = _system_node_id(EXTERNAL_EVENT_NODE_KIND, RUN_EVENT_KEY)

    def __init__(self, graph: AcherionGraph) -> None:
        self._graph = graph
        self._state = EmitState()
        self._original_index = {
            node.node_id: index for index, node in enumerate(self._graph.nodes)
        }
        self._function_graph = _FunctionBoxGraphView(self._graph.nodes)
        self._helper_library = _HelperLibraryBuilder(
            self._graph,
            function_graph=self._function_graph,
        )
        self._top_level_nodes = [
            node
            for node in self._graph.nodes
            if not str(node.params.get('parent_function') or '').strip()
        ]
        self._scope = _EmitScope(
            self._top_level_nodes,
            state=self._state,
            function_graph=self._function_graph,
            original_index=self._original_index,
            entry_node_id=self._EVENT_NODE_ID,
            allow_implicit_roots=False,
            owner_name=None,
        )

    def compile(self) -> str:
        """Return host-generated user code for the current graph."""
        self._append_user_functions()
        self._append_function_helpers()
        self._append_run_method()
        self._append_event_methods()
        return '\n'.join(_add_missing_pass(self._state.lines)) + '\n'

    def node_var_map(self) -> dict[str, str]:
        """Return compiled source-id to local-variable bindings."""
        return dict(self._state.node_vars)

    def _append_user_functions(self) -> None:
        for path in sorted(self._graph.user_functions):
            data = self._graph.user_functions.get(path) or {}
            source_code = _runtime_user_function_source(
                str(data.get('source_code') or '')
            )
            if not source_code:
                continue
            self._state.lines.extend(source_code.splitlines())
            self._state.lines.append('')

    def _append_function_helpers(self) -> None:
        self._state.lines.extend(self._helper_library.build_lines())

    def _append_event_methods(self) -> None:
        for event_node in self._top_level_nodes:
            if event_node.kind != EXTERNAL_EVENT_NODE_KIND:
                continue
            event_key = str(event_node.params.get('event_key') or '').strip()
            if event_key == RUN_EVENT_KEY:
                continue
            event_lines = self._create_event_compiler(event_node).compile_lines()
            if not event_lines:
                continue
            if self._state.lines and self._state.lines[-1] != '':
                self._state.lines.append('')
            self._state.lines.extend(event_lines)

    def _append_run_method(self) -> None:
        raise NotImplementedError()

    def _create_event_compiler(
        self,
        event_node: AcherionNode,
    ) -> '_GraphEventCompilerBase':
        raise NotImplementedError()


class _GraphEventCompilerBase:
    """Shared event-compiler orchestration for host-specific emitters."""

    def __init__(
        self,
        graph: AcherionGraph,
        *,
        event_node: AcherionNode,
        function_graph: _FunctionBoxGraphView | None = None,
        original_index: dict[str, int] | None = None,
    ) -> None:
        self._graph = graph
        self._state = EmitState()
        self._function_graph = function_graph or _FunctionBoxGraphView(
            self._graph.nodes
        )
        self._original_index = dict(original_index or {
            node.node_id: index for index, node in enumerate(self._graph.nodes)
        })
        self._event_node = event_node
        self._event_node_id = event_node.node_id
        self._event_key = str(event_node.params.get('event_key') or '').strip()
        handler_name = str(event_node.params.get('handler_name') or '').strip()
        if not handler_name:
            handler_name = acherion_event_handler_name(self._event_key)
        self._handler_name = handler_name
        self._top_level_nodes = [
            node
            for node in self._graph.nodes
            if not str(node.params.get('parent_function') or '').strip()
        ]
        self._scope = _EmitScope(
            self._top_level_nodes,
            state=self._state,
            function_graph=self._function_graph,
            original_index=self._original_index,
            entry_node_id=self._event_node_id,
            allow_implicit_roots=False,
            owner_name=None,
        )

    def compile_lines(self) -> list[str]:
        """Return handler lines for one non-run event, or empty list."""
        if not any(
            self._event_node_id in self._scope._exec_source_ids(node)
            for node in self._top_level_nodes
        ):
            return []
        self._state.lines.extend(self._handler_prelude_lines())
        self._scope.emit(self._emit_graph_node)
        self._state.lines.append('    return dict(locals())')
        return _add_missing_pass(self._state.lines)

    def _handler_prelude_lines(self) -> list[str]:
        raise NotImplementedError()


__all__ = [
    '_GraphEventCompilerBase',
    '_GraphNodeEmitterBase',
    '_GraphRunCompilerBase',
]

"""Standalone host adapter and compiler for generic Acherion."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from acherion.catalog import modules as _catalog_modules
from acherion.compiler.orchestration import (
    _GraphEventCompilerBase,
    _GraphNodeEmitterBase,
    _GraphRunCompilerBase,
)
from acherion.events import (
    AcherionExternalEvent,
    EXTERNAL_EVENT_NODE_KIND,
    RUN_EVENT_KEY,
    acherion_external_event_params,
    collect_acherion_external_events,
    default_acherion_external_events,
    serializable_acherion_external_events,
)
from acherion.model import AcherionGraph, AcherionNode, _system_node_id
from acherion.preview import AcherionPreviewRunResult


_RUNTIME_NORMALIZER_SIGNATURE = 'def _normalize_scoped_bindings(bindings=None):'
_RUNTIME_BINDINGS_LINE = 'bindings = _normalize_scoped_bindings(bindings)'
_RUNTIME_LOCALS_RETURN = 'return dict(locals())'


def _build_system_node(
    *,
    existing: AcherionNode | None,
    kind: str,
    key: str,
    title: str,
    system_group: str,
    params: dict[str, Any],
) -> AcherionNode:
    """Merge one system-node definition onto an existing node."""
    node = existing or AcherionNode(
        node_id=_system_node_id(kind, key),
        kind=kind,
    )
    merged = dict(node.params)
    merged.update(params)
    merged['system_node'] = True
    merged['system_group'] = system_group
    node.node_id = _system_node_id(kind, key)
    node.kind = kind
    node.title = title
    node.params = merged
    return node


class _StandaloneGraphCompilerBase(_GraphNodeEmitterBase):
    """Standalone-specific node-emission hooks."""

    def _emit_host_fallback_node(
        self,
        *,
        node: AcherionNode,
        params: dict[str, object],
        var_name: str,
        indent: str,
    ) -> None:
        del params, var_name
        self._state.lines.append(
            f'{indent}pass  # Unsupported standalone node kind: {node.kind}'
        )


class _StandaloneGraphRunCompiler(
    _GraphRunCompilerBase,
    _StandaloneGraphCompilerBase,
):
    """Compile a generic standalone graph into runnable Python code."""

    def _append_run_method(self) -> None:
        self._state.lines.extend([
            'def run(bindings=None):',
            '    bindings = _normalize_scoped_bindings(bindings)',
            '',
        ])
        manual_nodes = [
            node
            for node in self._graph.nodes
            if not bool(node.params.get('system_node'))
        ]
        if not manual_nodes:
            self._state.lines.append('    return dict(locals())')
            return
        self._scope.emit(self._emit_graph_node)
        self._append_passive_value_roots()
        self._state.lines.append('    return dict(locals())')

    def _append_passive_value_roots(self) -> None:
        for node in self._top_level_nodes:
            if bool(node.params.get('system_node')):
                continue
            self._scope.ensure_source(
                node.node_id,
                indent_level=1,
                emit_node=self._emit_graph_node,
            )

    def _create_event_compiler(
        self,
        event_node: AcherionNode,
    ) -> '_StandaloneGraphEventCompiler':
        return _StandaloneGraphEventCompiler(
            self._graph,
            function_graph=self._function_graph,
            original_index=self._original_index,
            event_node=event_node,
        )


class _StandaloneGraphEventCompiler(
    _GraphEventCompilerBase,
    _StandaloneGraphCompilerBase,
):
    """Compile one non-run external event handler."""

    def _handler_prelude_lines(self) -> list[str]:
        return [
            f'def {self._handler_name}(bindings=None):',
            '    bindings = _normalize_scoped_bindings(bindings)',
            '',
        ]


def _standalone_external_events(
    graph: AcherionGraph,
) -> dict[str, dict[str, str]]:
    """Return generated external-event metadata for one graph."""
    return serializable_acherion_external_events(
        collect_acherion_external_events(graph.nodes)
    )


def _build_standalone_runtime_source(
    *,
    compiled_body: str,
    external_events: dict[str, dict[str, str]],
) -> str:
    """Return full standalone runtime source from compiled graph body."""
    lines = [
        'from __future__ import annotations',
        '',
        'import collections',
        'import logging',
        'import pathlib',
        'import re',
        'import typing',
        '',
        'logger = logging.getLogger(__name__)',
        '',
        f'ACHERION_EXTERNAL_EVENTS = {external_events!r}',
        '',
        'def _normalize_scoped_bindings(bindings=None):',
        '    normalized = {}',
        '    raw_bindings = dict(bindings or {})',
        '    for scope, values in raw_bindings.items():',
        "        clean_scope = str(scope or '').strip()",
        '        if not clean_scope:',
        '            continue',
        '        if isinstance(values, collections.abc.Mapping):',
        '            normalized[clean_scope] = dict(values)',
        '        else:',
        '            normalized[clean_scope] = {}',
        '    return normalized',
        '',
        compiled_body,
    ]
    return '\n'.join(lines).rstrip() + '\n'


def _compile_standalone_runtime(
    graph: AcherionGraph,
) -> tuple[str, dict[str, str], dict[str, dict[str, str]]]:
    """Compile one graph and return source plus preview mapping metadata."""
    external_events = _standalone_external_events(graph)
    compiler = _StandaloneGraphRunCompiler(graph)
    compiled_body = compiler.compile().rstrip()
    source_code = _build_standalone_runtime_source(
        compiled_body=compiled_body,
        external_events=external_events,
    )
    return source_code, compiler.node_var_map(), external_events


def compile_acherion_graph(graph: AcherionGraph) -> str:
    """Compile one Acherion graph into standalone Python source."""
    source_code, _node_var_map, _external_events = _compile_standalone_runtime(
        graph
    )
    del _node_var_map, _external_events
    return source_code


def standalone_editor_visible_code(source_code: str) -> str:
    """Hide generated standalone runtime scaffold in the code pane."""
    lines = str(source_code or '').splitlines()
    normalizer_index = -1
    for index, line in enumerate(lines):
        if line.startswith(_RUNTIME_NORMALIZER_SIGNATURE):
            normalizer_index = index
            break
    if normalizer_index >= 0:
        end_index = normalizer_index + 1
        while end_index < len(lines):
            line = lines[end_index]
            if line and not line.startswith('    '):
                break
            end_index += 1
        lines = lines[end_index:]

    cleaned_lines: list[str] = []
    previous_blank = False
    for line in lines:
        stripped = line.strip()
        if stripped in {
            _RUNTIME_BINDINGS_LINE,
            _RUNTIME_LOCALS_RETURN,
        }:
            continue
        if stripped.startswith('ACHERION_EXTERNAL_EVENTS = '):
            continue
        if '(bindings=None):' in line and line.startswith('def '):
            line = line.replace('(bindings=None):', '():')
        is_blank = not stripped
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank
    return '\n'.join(cleaned_lines).strip()


def load_acherion_graph_namespace(source_code: str) -> dict[str, Any]:
    """Load generated Acherion code into a fresh Python namespace."""
    namespace: dict[str, Any] = {
        '__builtins__': __builtins__,
        '__name__': '_acherion_standalone_runtime',
        **_catalog_modules.runtime_global_bindings(),
    }
    exec(source_code, namespace)  # pylint: disable=exec-used
    return namespace


def execute_acherion_graph(
    source_code: str,
    *,
    event_key: str = RUN_EVENT_KEY,
    bindings: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute one generated Acherion handler and return runtime locals."""
    namespace = load_acherion_graph_namespace(source_code)
    event_map = dict(namespace.get('ACHERION_EXTERNAL_EVENTS') or {})
    default_handler_name = 'run'
    if event_key != RUN_EVENT_KEY:
        default_handler_name = acherion_event_handler_name(event_key)
    event_meta = dict(event_map.get(event_key) or {})
    handler_name = str(
        event_meta.get('handler_name') or default_handler_name
    ).strip()
    handler = namespace.get(handler_name)
    if not callable(handler):
        raise ValueError(
            f'Generated graph does not define a handler for {event_key!r}.'
        )
    result = handler(bindings=bindings)
    if isinstance(result, dict):
        return result
    return {'result': result}


def run_standalone_acherion_preview(
    graph: AcherionGraph,
    *,
    bindings: dict[str, dict[str, Any]] | None = None,
    event_key: str = RUN_EVENT_KEY,
) -> AcherionPreviewRunResult:
    """Execute one standalone graph preview and map values back to nodes."""
    source_code, node_var_map, external_events = _compile_standalone_runtime(
        graph
    )
    local_values = execute_acherion_graph(
        source_code,
        event_key=event_key,
        bindings=bindings,
    )
    reference_values = {
        source_id: local_values[var_name]
        for source_id, var_name in node_var_map.items()
        if var_name in local_values
    }
    event_meta = dict(external_events.get(event_key) or {})
    event_title = str(event_meta.get('title') or event_key).strip()
    if event_title.startswith('Event: '):
        event_title = event_title[7:]
    hint = f'Preview ran for {event_title or event_key}.'
    if not reference_values:
        hint += ' No previewable values were produced.'
    return AcherionPreviewRunResult(
        reference_values=reference_values,
        state_values={
            'hint': hint,
            'acherion.preview_event': event_key,
            'acherion.preview_value_count': len(reference_values),
        },
    )


class StandaloneAcherionHost:
    """Generic host used by the standalone Acherion app."""

    def external_events(self) -> dict[str, AcherionExternalEvent]:
        """Return standalone host events available inside the designer."""
        return default_acherion_external_events()

    def generated_user_code(self, designer: Any) -> str:
        """Compile the current graph into standalone Python source."""
        return compile_acherion_graph(designer.graph_state())

    def generated_runtime_bindings(
        self,
        designer: Any,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Return standalone runtime bindings for generated code."""
        del designer
        return {}

    def sync_manual_schema_keys(self, designer: Any) -> None:
        """No-op for the standalone host."""
        del designer

    def sync_system_nodes(self, designer: Any) -> None:
        """Materialize generic external-event source nodes."""
        manual_nodes = designer._manual_nodes()
        consumed_ids = {node.node_id for node in manual_nodes}
        source_nodes: list[AcherionNode] = []
        for index, event in enumerate(designer._external_events()):
            existing = designer._take_matching_node(
                consumed_ids=consumed_ids,
                kind=EXTERNAL_EVENT_NODE_KIND,
                key=event.event_key,
                param_key='event_key',
            )
            node = _build_system_node(
                existing=existing,
                kind=EXTERNAL_EVENT_NODE_KIND,
                key=event.event_key,
                title=event.title,
                system_group='source',
                params=acherion_external_event_params(event),
            )
            designer._seed_position(node, group='source', index=index)
            source_nodes.append(node)
        designer._graph.nodes = [*source_nodes, *manual_nodes]
        designer._ensure_function_box_entries()
        designer._sync_function_box_ports()

    def render_system_sink_config_fields(
        self,
        designer: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Standalone host defines no system sink config fields."""
        del designer, node, refresh_editor, apply_change
        return False

    def render_node_config_fields(
        self,
        designer: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Standalone host owns no extra node config fields."""
        del designer, node, refresh_editor, apply_change
        return False


__all__ = [
    'StandaloneAcherionHost',
    'compile_acherion_graph',
    'execute_acherion_graph',
    'load_acherion_graph_namespace',
    'run_standalone_acherion_preview',
    'standalone_editor_visible_code',
]

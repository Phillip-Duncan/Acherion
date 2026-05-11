"""Shared helpers for Acherion tests."""

from __future__ import annotations

import ast
from typing import Any

import acherion.embed.render.editor as acherion_render_editor
import acherion.embed.render.pins as acherion_render_pins
import acherion.graphops.catalog as acherion_graphops_catalog
import acherion.graphops.connections as acherion_graphops_connections
import acherion.graphops.pins as acherion_graphops_pins
import acherion.model as acherion_model


class _GraphOwnerBase:
    """Provide shared graph/source helpers for test doubles."""

    def __init__(
        self,
        graph: acherion_model.AcherionGraph | None = None,
    ) -> None:
        self._graph = graph or acherion_model.AcherionGraph(nodes=[])
        self._preview_reference_values: dict[str, Any] = {}

    def _node_by_id(
        self,
        node_id: str,
    ) -> acherion_model.AcherionNode | None:
        pure_id = self._pure_node_id(node_id)
        for node in self._graph.nodes:
            if node.node_id == pure_id:
                return node
        return None

    @staticmethod
    def _pure_node_id(source_id: str) -> str:
        return str(source_id).split('@', 1)[0]

    @staticmethod
    def _source_pin_index(source_id: str) -> int:
        if '@' not in str(source_id):
            return 0
        return int(str(source_id).split('@', 1)[1] or 0)


class CatalogPinsOwner(
    acherion_graphops_catalog._GraphOpsCatalogMixin,
    acherion_graphops_pins._GraphOpsPinsMixin,
    _GraphOwnerBase,
):
    """Own catalog and pin mixins for unit tests."""


class ConnectionsOwner(
    acherion_graphops_catalog._GraphOpsCatalogMixin,
    acherion_graphops_connections._GraphOpsConnectionsMixin,
    acherion_graphops_pins._GraphOpsPinsMixin,
    _GraphOwnerBase,
):
    """Own connection mixins for source-id normalization tests."""


class RenderPinsOwner(
    acherion_render_pins._RenderPinsMixin,
    acherion_graphops_pins._GraphOpsPinsMixin,
    _GraphOwnerBase,
):
    """Own render and pin mixins for source-id rendering tests."""


class PinLiteralRenderer(acherion_render_pins._RenderPinsMixin):
    """Track pin-literal mutation notifications in render-pin tests."""

    def __init__(self) -> None:
        self.change_count = 0

    def _notify_change(self) -> None:
        self.change_count += 1


def capture_editor_number_call(
    monkeypatch: Any,
    node: acherion_model.AcherionNode,
) -> dict[str, object]:
    """Capture the first `ui.number` call for one editor render pass."""
    calls: list[dict[str, object]] = []

    class _StubUiElement:
        def props(self, _value: object) -> '_StubUiElement':
            return self

        def classes(self, _value: object) -> '_StubUiElement':
            return self

    def _fake_number(*args: object, **kwargs: object) -> _StubUiElement:
        calls.append({'args': args, 'kwargs': kwargs})
        return _StubUiElement()

    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        def __init__(self) -> None:
            self._host = None

        def _is_system_sink_node(
            self,
            _node: acherion_model.AcherionNode,
        ) -> bool:
            return False

    monkeypatch.setattr(
        acherion_render_editor,
        'get_acherion_node_definition',
        lambda _kind: None,
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'input',
        lambda *args, **kwargs: _StubUiElement(),
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'label',
        lambda *args, **kwargs: _StubUiElement(),
    )
    monkeypatch.setattr(acherion_render_editor.ui, 'number', _fake_number)

    _StubEditor()._render_node_config_fields(node)

    assert calls
    return calls[0]


def parse_module(source_code: str) -> ast.Module:
    """Return parsed AST module for one generated source blob."""
    return ast.parse(source_code)


def run_function_def(source_code: str) -> ast.FunctionDef:
    """Return the generated `run` function definition."""
    module = parse_module(source_code)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'run':
            return node
    raise AssertionError('Generated source does not define run().')


def run_function_arg_names(source_code: str) -> list[str]:
    """Return positional arg names from generated `run`."""
    return [arg.arg for arg in run_function_def(source_code).args.args]


def run_contains_call(source_code: str, attr_name: str) -> bool:
    """Return True when `run` contains a call to one attribute name."""
    for node in ast.walk(run_function_def(source_code)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == attr_name:
            return True
    return False


def run_has_assigned_method_call(source_code: str, method_name: str) -> bool:
    """Return True when `run` assigns result of one method call."""
    for stmt in ast.walk(run_function_def(source_code)):
        if not isinstance(stmt, ast.Assign):
            continue
        value = stmt.value
        if not isinstance(value, ast.Call):
            continue
        if not isinstance(value.func, ast.Attribute):
            continue
        if value.func.attr == method_name:
            return True
    return False


def run_has_assigned_attribute_read(source_code: str, attr_name: str) -> bool:
    """Return True when `run` assigns from one attribute access."""
    for stmt in ast.walk(run_function_def(source_code)):
        if not isinstance(stmt, ast.Assign):
            continue
        value = stmt.value
        if not isinstance(value, ast.Attribute):
            continue
        if value.attr == attr_name:
            return True
    return False


def run_has_attribute_write(source_code: str, attr_name: str) -> bool:
    """Return True when `run` assigns to one attribute target."""
    for stmt in ast.walk(run_function_def(source_code)):
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Attribute):
                continue
            if target.attr == attr_name:
                return True
    return False


def run_binop_assignment_targets(
    source_code: str,
    op_type: type[ast.operator],
) -> list[str]:
    """Return assignment target names for matching binary ops in `run`."""
    targets: list[str] = []
    for stmt in ast.walk(run_function_def(source_code)):
        if not isinstance(stmt, ast.Assign):
            continue
        value = stmt.value
        if not isinstance(value, ast.BinOp):
            continue
        if not isinstance(value.op, op_type):
            continue
        if len(stmt.targets) != 1:
            continue
        targets.append(ast.unparse(stmt.targets[0]))
    return targets
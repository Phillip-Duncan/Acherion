"""Optional node-definition behavior helpers for compiler and embed code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acherion.model import AcherionNode
from acherion.registry import (
    _template_has_exec_input,
    _template_has_exec_output,
    get_acherion_node_definition,
)


@dataclass(frozen=True, slots=True)
class AcherionPreviewBinding:
    """Transient preview binding metadata provided by one node definition."""

    scope: str
    key: str
    input_kind: str
    file_filter: str = ''
    allow_multiple: bool = False


def _definition_field(
    definition: Any | None,
    field_name: str,
    default: Any = None,
) -> Any:
    """Return one resolved definition field or a default value."""
    if definition is None:
        return default
    reader = getattr(definition, '_definition_field', None)
    if callable(reader):
        value = reader(field_name)
        if value is not None:
            return value
    return getattr(definition, field_name, default)


def _definition_for_kind(kind: str) -> Any | None:
    """Return the registered definition for one node kind, if any."""
    return get_acherion_node_definition(str(kind or '').strip())


def _definition_for_node(node: AcherionNode) -> Any | None:
    """Return the registered definition for one node instance, if any."""
    return _definition_for_kind(node.kind)


def _bool_override(
    definition: Any | None,
    attr_name: str,
) -> bool | None:
    """Return one optional bool override from a definition."""
    if definition is None or not hasattr(definition, attr_name):
        return None
    return bool(getattr(definition, attr_name))


def _string_override(
    definition: Any | None,
    attr_name: str,
) -> str:
    """Return one optional string override from a definition."""
    if definition is None:
        return ''
    value = getattr(definition, attr_name, '')
    if callable(value):
        try:
            value = value()
        except TypeError:
            return ''
    return str(value or '').strip()


def is_ui_node_kind(kind: str) -> bool:
    """Return True when one node kind is registered as a UI node."""
    definition = _definition_for_kind(kind)
    category = str(_definition_field(definition, 'category', '') or '')
    return category == 'ui'


def compiler_is_backward_getter(node: AcherionNode) -> bool:
    """Return True when one node should seed dependency aliases backwards."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'compiler_backward_getter')
    if override is not None:
        return override
    return is_ui_node_kind(node.kind)


def compiler_is_serial_root(node: AcherionNode) -> bool:
    """Return True when one node can start an implicit serial chain."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'compiler_serial_root')
    if override is not None:
        return override
    return is_ui_node_kind(node.kind)


_EXEC_GATED_PRODUCER_KINDS = frozenset({
    'call_function',
    'call_method',
    'custom_function',
})


def compiler_is_exec_gated_producer(node: AcherionNode) -> bool:
    """Return True when one node must exec before its value can be read."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'compiler_exec_gated_producer')
    if override is not None:
        return override
    kind = str(node.kind or '').strip()
    if kind not in _EXEC_GATED_PRODUCER_KINDS:
        return False
    if not bool(_definition_field(definition, 'producer', False)):
        return False
    return (
        _template_has_exec_input(kind)
        and _template_has_exec_output(kind)
    )


def compiler_can_reemit(node: AcherionNode) -> bool:
    """Return True when one node can be emitted again deeper in scope."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'compiler_reemittable')
    if override is not None:
        return override
    flavor = str(_definition_field(definition, 'flavor', '') or '')
    return flavor == 'pure' or is_ui_node_kind(node.kind)


def compiler_has_zero_data_exec_output(node: AcherionNode) -> bool:
    """Return True when exec output occupies pin index zero."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'compiler_zero_data_output')
    if override is not None:
        return override
    return bool(_definition_field(definition, 'exec_out', False)) and not bool(
        _definition_field(definition, 'producer', False)
    )


def function_box_unsupported(node: AcherionNode) -> bool:
    """Return True when one node should not compile inside a Function Box."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'function_box_unsupported')
    if override is not None:
        return override
    category = str(_definition_field(definition, 'category', '') or '')
    return category == 'effect' or bool(
        _definition_field(definition, 'system_sink', False)
    )


def dependency_expr_for_node(
    node: AcherionNode,
    *,
    source_expr: str | None = None,
    owner_name: str | None = 'self',
) -> str | None:
    """Return dependency alias expression for one node, when supported."""
    definition = _definition_for_node(node)
    method = getattr(definition, 'dependency_expr', None)
    if not callable(method):
        return None
    result = method(
        node,
        source_expr=source_expr,
        owner_name=owner_name,
    )
    if result is None:
        return None
    return str(result)


def emit_static_node(
    *,
    state: Any,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    owner_name: str | None = 'self',
) -> bool:
    """Delegate one static node emission to its registered definition."""
    definition = _definition_for_node(node)
    method = getattr(definition, 'emit_static_node', None)
    if not callable(method):
        return False
    return bool(
        method(
            node,
            state=state,
            params=params,
            indent=indent,
            var_name=var_name,
            owner_name=owner_name,
        )
    )


def inline_default_editor_spec_for_node(
    node: AcherionNode,
) -> tuple[str, str, Any] | None:
    """Return compact inline editor metadata for one node, if any."""
    definition = _definition_for_node(node)
    method = getattr(definition, 'inline_default_editor_spec', None)
    if not callable(method):
        return None
    result = method(node)
    if result is None:
        return None
    return result


def render_inline_controls_for_node(
    owner: Any,
    node: AcherionNode,
) -> bool:
    """Delegate compact inline node controls to one registered definition."""
    definition = _definition_for_node(node)
    method = getattr(definition, 'render_inline_controls', None)
    if not callable(method):
        return False
    return bool(method(owner, node))


def preview_binding_for_node(
    node: AcherionNode,
) -> AcherionPreviewBinding | None:
    """Return transient preview input binding for one node, if any."""
    definition = _definition_for_node(node)
    method = getattr(definition, 'preview_binding', None)
    if not callable(method):
        return None
    result = method(node)
    if result is None:
        return None
    return result


def preview_result_reference_for_node(
    node: AcherionNode,
) -> str:
    """Return transient preview result reference for one node, if any."""
    definition = _definition_for_node(node)
    method = getattr(definition, 'preview_result_reference', None)
    if not callable(method):
        return ''
    return str(method(node) or '').strip()


def edit_dialog_preview_enabled_for_node(node: AcherionNode) -> bool:
    """Return True when one node should show preview controls in its editor."""
    definition = _definition_for_node(node)
    override = _bool_override(definition, 'edit_dialog_preview_enabled')
    if override is not None:
        return override
    return True


def node_type_summary(kind: str) -> str:
    """Return human-readable type summary provided by one definition."""
    return _string_override(_definition_for_kind(kind), 'type_summary')


def output_pin_label(kind: str) -> str:
    """Return output-pin label override provided by one definition."""
    return _string_override(_definition_for_kind(kind), 'output_pin_label')


def sink_pin_label(kind: str) -> str:
    """Return sink-pin label override provided by one definition."""
    return _string_override(_definition_for_kind(kind), 'sink_pin_label')


def sink_input_type_tag(kind: str) -> str:
    """Return sink input type override provided by one definition."""
    return _string_override(_definition_for_kind(kind), 'sink_input_type_tag')


__all__ = [
    'AcherionPreviewBinding',
    'compiler_can_reemit',
    'compiler_has_zero_data_exec_output',
    'compiler_is_backward_getter',
    'compiler_is_exec_gated_producer',
    'compiler_is_serial_root',
    'dependency_expr_for_node',
    'edit_dialog_preview_enabled_for_node',
    'emit_static_node',
    'function_box_unsupported',
    'inline_default_editor_spec_for_node',
    'is_ui_node_kind',
    'node_type_summary',
    'output_pin_label',
    'render_inline_controls_for_node',
    'preview_binding_for_node',
    'preview_result_reference_for_node',
    'sink_input_type_tag',
    'sink_pin_label',
]
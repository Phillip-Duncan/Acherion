"""Pin specification helpers for visual-logic graph ops."""

# pyright: reportAttributeAccessIssue=false, reportReturnType=false

from __future__ import annotations

from typing import Any, cast

from acherion.catalog import models as _catalog_models
from acherion.catalog import plotly as _catalog_plotly
from acherion.catalog import runtime as _catalog_runtime
from acherion.catalog import types as _catalog_types
from acherion.preview import preview_value_type_tag
from acherion.registry import (
    get_acherion_node_definition,
    _template_has_exec_input,
    _template_has_exec_output,
)
from acherion.model import AcherionNode


_AcherionPinSpec = dict[str, str]
_AcherionPinSpecs = list[_AcherionPinSpec]

_STATIC_INPUT_PIN_SPECS: dict[str, _AcherionPinSpecs] = {
    'get_attribute': [
        {'pin_id': 'instance', 'label': 'instance', 'type': 'object'},
    ],
    'set_attribute': [
        {'pin_id': 'instance', 'label': 'instance', 'type': 'object'},
        {'pin_id': 'value', 'label': 'value', 'type': 'any'},
    ],
    'for_each': [
        {'pin_id': 'list', 'label': 'list (items)', 'type': 'any'},
    ],
    'collect': [
        {'pin_id': 'value', 'label': 'value', 'type': 'any'},
    ],
    'compare': [
        {'pin_id': 'left_source', 'label': 'Left', 'type': 'any'},
        {'pin_id': 'right_source', 'label': 'Right', 'type': 'any'},
    ],
    'branch_value': [
        {'pin_id': 'condition_source', 'label': 'Condition', 'type': 'bool'},
        {'pin_id': 'true_source', 'label': 'If True', 'type': 'any'},
        {'pin_id': 'false_source', 'label': 'If False', 'type': 'any'},
    ],
    'branch_route': [
        {'pin_id': 'condition_source', 'label': 'Condition', 'type': 'bool'},
    ],
    'op_unary': [
        {
            'pin_id': 'source',
            'label': 'Value',
            'type': 'any',
            'editor_kind': 'number',
        },
    ],
    'op_not': [
        {'pin_id': 'source', 'label': 'Value', 'type': 'bool'},
    ],
    'list_index': [
        {'pin_id': 'source', 'label': 'list', 'type': 'list'},
    ],
    'list_set': [
        {'pin_id': 'source', 'label': 'list', 'type': 'list'},
        {'pin_id': 'value', 'label': 'value', 'type': 'any'},
    ],
}

_STATIC_OUTPUT_PIN_SPECS: dict[str, _AcherionPinSpecs] = {
    'branch_route': [
        {'pin_id': 'if_true', 'label': 'True', 'type': 'exec'},
        {'pin_id': 'if_false', 'label': 'False', 'type': 'exec'},
    ],
    'for_each': [
        {'pin_id': 'item', 'label': 'item', 'type': 'any'},
        {'pin_id': 'index', 'label': 'index', 'type': 'any'},
        {'pin_id': 'loop_body', 'label': 'Loop Body', 'type': 'exec'},
        {'pin_id': 'completed', 'label': 'Completed', 'type': 'exec'},
    ],
    'collect': [
        {'pin_id': 'value', 'label': 'list', 'type': 'list'},
    ],
    'op_arithmetic': [
        {'pin_id': 'value', 'label': 'result', 'type': 'any'},
    ],
    'op_unary': [
        {'pin_id': 'value', 'label': 'result', 'type': 'any'},
    ],
    'op_logic': [
        {'pin_id': 'value', 'label': 'condition', 'type': 'bool'},
    ],
    'op_not': [
        {'pin_id': 'value', 'label': 'condition', 'type': 'bool'},
    ],
    'compare': [
        {'pin_id': 'result', 'label': 'condition', 'type': 'bool'},
    ],
    'branch_value': [
        {'pin_id': 'value', 'label': 'selected', 'type': 'any'},
    ],
    'make_list': [
        {'pin_id': 'value', 'label': 'list', 'type': 'list'},
    ],
    'list_set': [
        {'pin_id': 'value', 'label': 'list', 'type': 'any'},
    ],
    'plot_figure': [
        {'pin_id': 'value', 'label': 'Figure', 'type': 'any'},
    ],
}

_DYNAMIC_INPUT_PIN_BUILDERS: dict[str, str] = {
    'call_function': '_callable_input_pin_specs',
    'custom_function': '_callable_input_pin_specs',
    'plot_figure': '_plot_figure_input_pin_specs',
    'call_method': '_call_method_input_pin_specs',
    'make_list': '_make_list_input_pin_specs',
    'op_arithmetic': '_op_arithmetic_input_pin_specs',
    'op_logic': '_op_logic_input_pin_specs',
}

_DYNAMIC_OUTPUT_PIN_BUILDERS: dict[str, str] = {
    'sequencer': '_sequencer_output_pin_specs',
    'constant': '_constant_output_pin_specs',
    'call_function': '_callable_output_pin_specs',
    'custom_function': '_callable_output_pin_specs',
    'call_method': '_call_method_output_pin_specs',
    'get_attribute': '_get_attribute_output_pin_specs',
    'list_index': '_list_index_output_pin_specs',
    'list_set': '_list_set_output_pin_specs',
}

_CONSTANT_OUTPUT_TYPE_MAP: dict[str, str] = {
    'number': 'float',
    'int': 'int',
    'text': 'str',
    'bool': 'bool',
    'dict': 'dict',
}


class _GraphOpsPinsMixin:
    """Pin specification and pending-output helpers."""

    @staticmethod
    def _exec_input_pin() -> dict[str, str]:
        """Return the standard optional exec-input pin spec."""
        return {
            'pin_id': 'exec_source',
            'label': '',
            'type': 'exec',
        }

    @staticmethod
    def _exec_output_pin(label: str = '') -> dict[str, str]:
        """Return the standard exec-output pin spec."""
        return {
            'pin_id': 'exec',
            'label': label,
            'type': 'exec',
        }

    @staticmethod
    def _ordered_input_pins(
        pins: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Return input pins with required pins before optional pins."""
        required = [
            pin for pin in pins if pin.get('optional') != 'true'
        ]
        optional = [
            pin for pin in pins if pin.get('optional') == 'true'
        ]
        return [*required, *optional]

    @staticmethod
    def _exec_output_label(kind: str) -> str:
        """Return the user-facing label for an exec output pin."""
        del kind
        return ''

    def _finalize_input_pins(
        self: Any,
        node: AcherionNode,
        pins: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Append generic exec input pins and normalize input ordering."""
        final_pins = list(pins)
        if (
            _template_has_exec_input(node.kind)
            and not any(pin.get('pin_id') == 'exec_source' for pin in final_pins)
        ):
            final_pins.append(self._exec_input_pin())
        return cast(list[dict[str, str]], self._ordered_input_pins(final_pins))

    def _finalize_output_pins(
        self: Any,
        node: AcherionNode,
        pins: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Append generic exec output pins after data outputs."""
        final_pins = list(pins)
        if (
            _template_has_exec_output(node.kind)
            and not any(pin.get('pin_id') == 'exec' for pin in final_pins)
        ):
            final_pins.append(
                self._exec_output_pin(self._exec_output_label(node.kind))
            )
        return final_pins

    @staticmethod
    def _clone_pin_specs(pins: _AcherionPinSpecs) -> _AcherionPinSpecs:
        return [dict(pin) for pin in pins]

    def _pin_specs_from_registry(
        self: Any,
        node: AcherionNode,
        *,
        static_specs: dict[str, _AcherionPinSpecs],
        dynamic_builders: dict[str, str],
    ) -> _AcherionPinSpecs:
        builder_name = dynamic_builders.get(node.kind)
        if builder_name:
            return cast(_AcherionPinSpecs, getattr(self, builder_name)(node))
        return self._clone_pin_specs(static_specs.get(node.kind, []))

    @staticmethod
    def _entry_argument_pin_specs(
        entry: _catalog_models.FuncEntry | None,
        *,
        min_args_fallback: int,
        max_args_fallback: int,
    ) -> _AcherionPinSpecs:
        param_names = _catalog_models.param_names_for(entry) if entry else []
        param_types = _catalog_models.param_types_for(entry) if entry else []
        if entry is not None:
            min_args = entry.min_args
            max_args = (
                min(entry.max_args, 8)
                if entry.max_args is not None
                else min(min_args + 4, 8)
            )
        else:
            min_args = min_args_fallback
            max_args = max_args_fallback
        return [
            {
                'pin_id': f'arg:{index}',
                'label': (
                    param_names[index]
                    if index < len(param_names)
                    else f'arg {index + 1}'
                ),
                'type': (
                    param_types[index]
                    if index < len(param_types)
                    else 'any'
                ),
                'optional': 'true' if index >= min_args else 'false',
            }
            for index in range(max_args)
        ]

    def _callable_input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        path = str(node.params.get('function_path') or '')
        entry = self._function_entry(path)
        return self._entry_argument_pin_specs(
            entry,
            min_args_fallback=1,
            max_args_fallback=1,
        )

    def _plot_figure_input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        figure_type = str(node.params.get('figure_type') or 'scatter')
        return cast(
            _AcherionPinSpecs,
            _catalog_plotly.trace_pin_specs(figure_type),
        )

    def _call_method_input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        pins: _AcherionPinSpecs = [
            {'pin_id': 'instance', 'label': 'instance', 'type': 'object'},
        ]
        instance_source = str(node.params.get('instance') or '')
        method_name = str(node.params.get('method_name') or '')
        if not (method_name and instance_source):
            return pins
        class_path = self._resolve_instance_class_path(instance_source)
        if not class_path:
            return pins
        entry = _catalog_runtime.method_func_entry(class_path, method_name)
        if entry is None:
            return pins
        pins.extend(
            self._entry_argument_pin_specs(
                entry,
                min_args_fallback=0,
                max_args_fallback=0,
            )
        )
        return pins

    def _make_list_input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        arg_count = max(0, int(node.params.get('arg_count', 0) or 0))
        return [
            {
                'pin_id': f'arg:{index}',
                'label': f'Item {index + 1}',
                'type': 'any',
            }
            for index in range(arg_count)
        ]

    def _op_arithmetic_input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        operator = str(node.params.get('operator') or '+')
        return [
            {
                'pin_id': 'left_source',
                'label': f'A  (A {operator} B)',
                'type': 'any',
                'editor_kind': 'number',
            },
            {
                'pin_id': 'right_source',
                'label': 'B',
                'type': 'any',
                'editor_kind': 'number',
            },
        ]

    def _op_logic_input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        operator = str(node.params.get('operator') or 'and').upper()
        return [
            {
                'pin_id': 'left_source',
                'label': f'A  (A {operator} B)',
                'type': 'bool',
            },
            {
                'pin_id': 'right_source',
                'label': 'B',
                'type': 'bool',
            },
        ]

    def _sequencer_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        then_count = max(2, int(node.params.get('then_count', 2) or 2))
        return [
            {
                'pin_id': f'then:{index}',
                'label': f'Then {index + 1}',
                'type': 'exec',
            }
            for index in range(then_count)
        ]

    def _constant_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        value_type = str(node.params.get('value_type') or 'number')
        return [
            {
                'pin_id': 'value',
                'label': 'literal',
                'type': _CONSTANT_OUTPUT_TYPE_MAP.get(value_type, 'float'),
            }
        ]

    def _callable_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        path = str(node.params.get('function_path') or '')
        entry = self._function_entry(path) if path else None
        if entry and bool(getattr(entry, 'is_class', False)):
            class_name = path.rsplit('.', 1)[-1] if path else 'instance'
            return_type = entry.return_type or 'object'
            return [
                {'pin_id': 'value', 'label': class_name, 'type': return_type},
            ]
        return_type = entry.return_type if entry else 'any'
        if not return_type:
            return []
        return [
            {'pin_id': 'value', 'label': 'result', 'type': return_type},
        ]

    def _call_method_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        instance_source = str(node.params.get('instance') or '')
        method_name = str(node.params.get('method_name') or '')
        return_type = 'any'
        if instance_source and method_name:
            class_path = self._resolve_instance_class_path(instance_source)
            if class_path:
                entry = _catalog_runtime.method_func_entry(
                    class_path,
                    method_name,
                )
                if entry is not None:
                    return_type = str(entry.return_type)
        if not return_type:
            return []
        return [
            {'pin_id': 'value', 'label': 'result', 'type': return_type},
        ]

    def _get_attribute_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        attribute_name = str(node.params.get('attribute_name') or 'attribute')
        return [
            {
                'pin_id': 'value',
                'label': attribute_name or 'attribute',
                'type': 'any',
            }
        ]

    def _list_index_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        mode = str(node.params.get('mode') or 'index').strip()
        if mode != 'slice':
            return [
                {'pin_id': 'value', 'label': 'item', 'type': 'any'},
            ]

        output_type = 'any'
        source_id = str(node.params.get('source') or '')
        source_node = self._node_by_id(self._pure_node_id(source_id))
        if source_node is not None and source_node.node_id != node.node_id:
            source_pin_index = self._source_pin_index(source_id)
            source_specs = self._output_pin_specs(source_node)
            if source_pin_index < len(source_specs):
                source_type = str(
                    source_specs[source_pin_index].get('type') or 'any'
                )
                if _catalog_types.is_list_like_type_tag(source_type):
                    output_type = source_type
        return [
            {'pin_id': 'value', 'label': 'slice', 'type': output_type},
        ]

    def _list_set_output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionPinSpecs:
        output_type = 'any'
        source_id = str(node.params.get('source') or '')
        source_node = self._node_by_id(self._pure_node_id(source_id))
        if source_node is not None and source_node.node_id != node.node_id:
            source_pin_index = self._source_pin_index(source_id)
            source_specs = self._output_pin_specs(source_node)
            if source_pin_index < len(source_specs):
                source_type = str(
                    source_specs[source_pin_index].get('type') or 'any'
                )
                if _catalog_types.is_list_like_type_tag(source_type):
                    output_type = source_type
        return [
            {'pin_id': 'value', 'label': 'list', 'type': output_type},
        ]

    def _input_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> list[dict[str, str]]:
        definition = get_acherion_node_definition(node.kind)
        if definition is not None:
            definition_pins = definition.input_pins(self, node)
            if definition_pins is not None:
                return cast(
                    list[dict[str, str]],
                    self._finalize_input_pins(node, definition_pins),
                )
        pins = self._pin_specs_from_registry(
            node,
            static_specs=_STATIC_INPUT_PIN_SPECS,
            dynamic_builders=_DYNAMIC_INPUT_PIN_BUILDERS,
        )
        return cast(list[dict[str, str]], self._finalize_input_pins(node, pins))

    def _output_pin_specs(
        self: Any,
        node: AcherionNode,
    ) -> list[dict[str, str]]:
        definition = get_acherion_node_definition(node.kind)
        if definition is not None:
            definition_pins = definition.output_pins(self, node)
            if definition_pins is not None:
                return self._with_preview_output_types(
                    node,
                    cast(
                        list[dict[str, str]],
                        self._finalize_output_pins(node, definition_pins),
                    ),
                )
        pins = self._pin_specs_from_registry(
            node,
            static_specs=_STATIC_OUTPUT_PIN_SPECS,
            dynamic_builders=_DYNAMIC_OUTPUT_PIN_BUILDERS,
        )
        final_pins = cast(list[dict[str, str]], self._finalize_output_pins(node, pins))
        return self._with_preview_output_types(node, final_pins)

    def _with_preview_output_types(
        self: Any,
        node: AcherionNode,
        final_pins: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Refine output pin types using latest runtime preview values."""
        output_count = len(final_pins)
        for index, pin in enumerate(final_pins):
            if str(pin.get('type') or '') == 'exec':
                continue
            source_id = (
                f'{node.node_id}@{index}'
                if output_count > 1 else node.node_id
            )
            preview_value = None
            if source_id in self._preview_reference_values:
                preview_value = self._preview_reference_values.get(source_id)
            elif index == 0 and node.node_id in self._preview_reference_values:
                preview_value = self._preview_reference_values.get(node.node_id)
            if preview_value is None:
                continue
            preview_type = preview_value_type_tag(preview_value)
            if preview_type not in {'', 'any'}:
                pin['type'] = preview_type
        return final_pins

    def _pending_output_type(self: Any) -> str:
        """Return the type tag of the currently pending source output pin."""
        src_id = str(self._pending_source_node_id or '')
        if not src_id:
            return 'any'
        node_id = self._pure_node_id(src_id)
        pin_idx = self._source_pin_index(src_id)
        node = self._node_by_id(node_id)
        if node is None:
            return 'any'
        specs = self._output_pin_specs(node)
        if pin_idx < len(specs):
            return str(specs[pin_idx].get('type') or 'any')
        return 'any'

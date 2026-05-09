"""Built-in compute node definitions for Acherion."""

from __future__ import annotations

import acherion.node as acherion_node


class ConstantNode(acherion_node.ComputeNodeDefinition):
    kind = 'constant'
    label = 'Constant'
    icon = 'pin'
    tooltip = 'Create a number, text, or bool literal.'
    default_params_factory = acherion_node.literal_params({
        'value_type': 'number',
        'number_value': 0.0,
        'text_value': '',
        'bool_value': False,
        'dict_value': '{}',
    })

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        value_type = str(getattr(node, 'params', {}).get('value_type') or 'number')
        type_map = {
            'number': 'float',
            'int': 'int',
            'text': 'str',
            'bool': 'bool',
            'dict': 'dict',
        }
        return [
            acherion_node.pin('value', 'literal', type_map.get(value_type, 'float'))
        ]

    def inline_default_editor_spec(
        self,
        node: object,
    ) -> tuple[str, str, object] | None:
        params = getattr(node, 'params', {})
        value_type = str(params.get('value_type') or 'number').strip()
        if value_type in {'number', 'int'}:
            return ('number', 'number_value', params.get('number_value', 0))
        if value_type == 'text':
            return ('text', 'text_value', str(params.get('text_value') or ''))
        return None


class ArithmeticNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_arithmetic'
    label = 'Arithmetic'
    icon = 'calculate'
    tooltip = 'Add, subtract, multiply, divide, or raise to a power.'
    default_params_factory = acherion_node.literal_params({
        'operator': '+',
        'left_source': '',
        'right_source': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        operator = str(getattr(node, 'params', {}).get('operator') or '+')
        return [
            acherion_node.pin(
                'left_source',
                f'A  (A {operator} B)',
                'any',
                editor_kind='number',
            ),
            acherion_node.pin(
                'right_source',
                'B',
                'any',
                editor_kind='number',
            ),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'result', 'any')]


class MathFunctionNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_unary'
    label = 'Math Function'
    icon = 'exposure'
    tooltip = 'Apply abs, round, ceil, floor, int, float, or negate.'
    default_params_factory = acherion_node.literal_params({
        'function': 'abs',
        'source': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin(
                'source',
                'Value',
                'any',
                editor_kind='number',
            )
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'result', 'any')]


class CompareNode(acherion_node.ComputeNodeDefinition):
    kind = 'compare'
    label = 'Compare'
    icon = 'compare_arrows'
    tooltip = 'Compare two values and produce a boolean condition.'
    default_params_factory = acherion_node.literal_params({
        'left_source': '',
        'operator': '>',
        'right_source': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin('left_source', 'Left', 'any'),
            acherion_node.pin('right_source', 'Right', 'any'),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('result', 'condition', 'any')]


class LogicNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_logic'
    label = 'Logic (And / Or)'
    icon = 'device_hub'
    tooltip = 'Combine two boolean values with AND or OR.'
    default_params_factory = acherion_node.literal_params({
        'operator': 'and',
        'left_source': '',
        'right_source': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        operator = str(getattr(node, 'params', {}).get('operator') or 'and')
        return [
            acherion_node.pin(
                'left_source',
                f'A  (A {operator.upper()} B)',
                'any',
            ),
            acherion_node.pin('right_source', 'B', 'any'),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'condition', 'any')]


class LogicalNotNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_not'
    label = 'Logical NOT'
    icon = 'block'
    tooltip = 'Invert a boolean value.'
    default_params_factory = acherion_node.literal_params({'source': ''})

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('source', 'Value', 'any')]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'condition', 'any')]


class MakeListNode(acherion_node.ComputeNodeDefinition):
    kind = 'make_list'
    label = 'Make List'
    icon = 'format_list_bulleted'
    tooltip = 'Build a list from multiple input values.'
    default_params_factory = acherion_node.literal_params({
        'arg_count': 0,
        'arg_sources': [],
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        arg_count = max(
            0,
            int(getattr(node, 'params', {}).get('arg_count', 0) or 0),
        )
        return [
            acherion_node.pin(f'arg:{index}', f'Item {index + 1}', 'any')
            for index in range(arg_count)
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'list', 'any')]


class ListIndexNode(acherion_node.ComputeNodeDefinition):
    kind = 'list_index'
    label = 'Indexing'
    icon = 'data_array'
    tooltip = (
        'Index into a list or ndarray, or switch to slice mode with optional '
        'bounds.'
    )
    source_param_ids_factory = acherion_node.source_param_ids('source')
    default_params_factory = acherion_node.literal_params({
        'source': '',
        'mode': 'index',
        'index': 0,
        'start': '',
        'stop': '',
        'step': '',
    })


class PlotFigureNode(acherion_node.ComputeNodeDefinition):
    kind = 'plot_figure'
    label = 'Plot Figure'
    icon = 'bar_chart'
    tooltip = (
        'Build a plotly Figure from data (scatter, bar, line, histogram, ...).'
    )
    default_params_factory = acherion_node.literal_params({
        'figure_type': 'scatter',
        'named_sources': {},
        'figure_title': '',
    })


BUILTIN_COMPUTE_NODES = (
    ConstantNode(),
    ArithmeticNode(),
    MathFunctionNode(),
    CompareNode(),
    LogicNode(),
    LogicalNotNode(),
    MakeListNode(),
    ListIndexNode(),
    PlotFigureNode(),
)

__all__ = ['BUILTIN_COMPUTE_NODES']

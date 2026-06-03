"""Built-in compute node definitions for Acherion."""

from __future__ import annotations

import acherion.node as acherion_node


class ConstantNode(acherion_node.ComputeNodeDefinition):
    kind = 'constant'
    category = 'collections'
    label = 'Constant'
    icon = 'pin'
    tooltip = 'Create a number, text, bool, or dict literal.'
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
        if value_type == 'bool':
            return ('bool', 'bool_value', bool(params.get('bool_value', False)))
        if value_type == 'dict':
            return ('dict', 'dict_value', str(params.get('dict_value') or '{}'))
        return None


class ArithmeticNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_arithmetic'
    category = 'math'
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
    category = 'math'
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
    category = 'logic'
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
        return [acherion_node.pin('result', 'condition', 'bool')]


class LogicNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_logic'
    category = 'logic'
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
                'bool',
            ),
            acherion_node.pin('right_source', 'B', 'bool'),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'condition', 'bool')]


class LogicalNotNode(acherion_node.ComputeNodeDefinition):
    kind = 'op_not'
    category = 'logic'
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
        return [acherion_node.pin('source', 'Value', 'bool')]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'condition', 'bool')]


class MakeListNode(acherion_node.ComputeNodeDefinition):
    kind = 'make_list'
    category = 'collections'
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
        return [acherion_node.pin('value', 'list', 'list')]


class MakeDictNode(acherion_node.ComputeNodeDefinition):
    kind = 'make_dict'
    category = 'collections'
    label = 'Make Dict'
    icon = 'account_tree'
    tooltip = 'Build a dict from named input values.'
    default_params_factory = acherion_node.literal_params({
        'arg_count': 0,
        'arg_sources': [],
        'key_names': [],
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        params = getattr(node, 'params', {})
        arg_count = max(0, int(params.get('arg_count', 0) or 0))
        key_names = list(params.get('key_names') or [])
        pins: list[dict[str, str]] = []
        for index in range(arg_count):
            default_key = f'key_{index + 1}'
            label = str(
                key_names[index] if index < len(key_names) else default_key
            ).strip() or default_key
            pins.append(acherion_node.pin(f'arg:{index}', label, 'any'))
        return pins

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'dict', 'dict')]


class ListIndexNode(acherion_node.ComputeNodeDefinition):
    kind = 'list_index'
    category = 'collections'
    label = 'Get List Value(s)'
    icon = 'data_array'
    tooltip = (
        'Read one list or ndarray item, or switch to slice mode with '
        'optional bounds.'
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

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('source', 'list', 'list')]


class ListSetNode(acherion_node.ComputeNodeDefinition):
    kind = 'list_set'
    category = 'collections'
    label = 'Set List Value(s)'
    icon = 'playlist_add_check'
    tooltip = (
        'Return a copied list or ndarray with one item or slice updated.'
    )
    source_param_ids_factory = acherion_node.source_param_ids(
        'source',
        'value',
    )
    default_params_factory = acherion_node.literal_params({
        'source': '',
        'mode': 'index',
        'index': 0,
        'start': '',
        'stop': '',
        'step': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin('source', 'list', 'list'),
            acherion_node.pin('value', 'value', 'any'),
        ]


class DictGetNode(acherion_node.ComputeNodeDefinition):
    kind = 'dict_get'
    category = 'collections'
    label = 'Get Dict Value'
    icon = 'key'
    tooltip = 'Read one value from a dict by key, with optional fallback.'
    default_params_factory = acherion_node.literal_params({
        'source': '',
        'key': '',
        'default': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin('source', 'dict', 'dict'),
            acherion_node.pin('key', 'Key', 'str', editor_kind='text'),
            acherion_node.pin('default', 'Default', 'any', optional=True),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'value', 'any')]


class DictSetNode(acherion_node.ComputeNodeDefinition):
    kind = 'dict_set'
    category = 'collections'
    label = 'Set Dict Value'
    icon = 'edit'
    tooltip = 'Return a dict copy with one key updated.'
    default_params_factory = acherion_node.literal_params({
        'source': '',
        'key': '',
        'value': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin('source', 'dict', 'dict'),
            acherion_node.pin('key', 'Key', 'str', editor_kind='text'),
            acherion_node.pin('value', 'Value', 'any'),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'dict', 'dict')]


class PlotFigureNode(acherion_node.ComputeNodeDefinition):
    kind = 'plot_figure'
    category = 'visualization'
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
    MakeListNode(),
    ListIndexNode(),
    ListSetNode(),
    MakeDictNode(),
    DictGetNode(),
    DictSetNode(),
    ArithmeticNode(),
    MathFunctionNode(),
    CompareNode(),
    LogicNode(),
    LogicalNotNode(),
    PlotFigureNode(),
)

__all__ = ['BUILTIN_COMPUTE_NODES']

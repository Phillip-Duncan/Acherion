"""Built-in flow node definitions for Acherion."""

from __future__ import annotations

import acherion.catalog.types as acherion_catalog_types
import acherion.node as acherion_node


_ELSE_IF_BRANCH_MIN_CONDITIONS = 1


def _else_if_branch_condition_count(node: object) -> int:
    """Return the clamped condition count for an else-if branch node."""
    raw_params = getattr(node, 'params', {})
    params = raw_params if isinstance(raw_params, dict) else {}
    try:
        count = int(params.get('condition_count', 2) or 2)
    except (TypeError, ValueError):
        count = 2
    return max(_ELSE_IF_BRANCH_MIN_CONDITIONS, count)


def _for_each_item_type(owner: object, node: object) -> str:
    params = getattr(node, 'params', None)
    if not isinstance(params, dict):
        return 'any'
    list_source_id = str(params.get('list') or '').strip()
    if not list_source_id:
        return 'any'
    node_by_id = getattr(owner, '_node_by_id', None)
    pure_node_id = getattr(owner, '_pure_node_id', None)
    source_pin_index = getattr(owner, '_source_pin_index', None)
    output_pin_specs = getattr(owner, '_output_pin_specs', None)
    if not all(
        callable(method)
        for method in (
            node_by_id,
            pure_node_id,
            source_pin_index,
            output_pin_specs,
        )
    ):
        return 'any'
    source_node = node_by_id(pure_node_id(list_source_id))
    current_node_id = str(getattr(node, 'node_id', '') or '').strip()
    if source_node is None or source_node.node_id == current_node_id:
        return 'any'
    pin_index = source_pin_index(list_source_id)
    output_specs = output_pin_specs(source_node)
    if pin_index >= len(output_specs):
        return 'any'
    list_type = str(output_specs[pin_index].get('type') or 'any')
    item_type = acherion_catalog_types.list_item_type_tag(list_type)
    return item_type or 'any'


class ForEachNode(acherion_node.FlowNodeDefinition):
    kind = 'for_each'
    label = 'For Each'
    icon = 'loop'
    tooltip = (
        'Iterate over a list. Use Loop Body for each item and Completed '
        'after the loop finishes.'
    )
    flavor = 'control'
    producer = True
    exec_in = True
    default_params_factory = acherion_node.literal_params({'list': ''})

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('list', 'list (items)', 'any')]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        item_type = _for_each_item_type(owner, node)
        return [
            acherion_node.pin('item', 'item', item_type),
            acherion_node.pin('index', 'index', 'any'),
            acherion_node.pin('loop_body', 'Loop Body', 'exec'),
            acherion_node.pin('completed', 'Completed', 'exec'),
        ]


class CollectNode(acherion_node.FlowNodeDefinition):
    kind = 'collect'
    label = 'Collect'
    icon = 'playlist_add'
    tooltip = (
        'Accumulate a value on each loop iteration into a list. Place inside '
        'a For Each loop body.'
    )
    flavor = 'effect'
    producer = True
    exec_in = True
    exec_out = True
    default_params_factory = acherion_node.literal_params({'value': ''})

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'value', 'any')]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'list', 'list')]


class BranchValueNode(acherion_node.FlowNodeDefinition):
    kind = 'branch_value'
    label = 'Select (if/else)'
    icon = 'alt_route'
    tooltip = 'Choose between two values based on a condition.'
    flavor = 'pure'
    producer = True
    default_params_factory = acherion_node.literal_params({
        'condition_source': '',
        'true_source': '',
        'false_source': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin('condition_source', 'Condition', 'bool'),
            acherion_node.pin('true_source', 'If True', 'any'),
            acherion_node.pin('false_source', 'If False', 'any'),
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('value', 'selected', 'any')]


class BranchRouteNode(acherion_node.FlowNodeDefinition):
    kind = 'branch_route'
    label = 'Branch'
    icon = 'call_split'
    tooltip = 'Route execution to True or False based on a condition.'
    flavor = 'control'
    producer = True
    exec_in = True
    default_params_factory = acherion_node.literal_params({'condition_source': ''})

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [acherion_node.pin('condition_source', 'Condition', 'bool')]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return [
            acherion_node.pin('if_true', 'True', 'exec'),
            acherion_node.pin('if_false', 'False', 'exec'),
        ]


class ElseIfBranchNode(acherion_node.FlowNodeDefinition):
    kind = 'else_if_branch'
    label = 'If / Else If Branch'
    icon = 'fork_right'
    tooltip = 'Route execution through if, else-if, and else branches.'
    flavor = 'control'
    producer = True
    exec_in = True
    default_params_factory = acherion_node.literal_params({
        'condition_count': 2,
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        return [
            acherion_node.pin(
                f'condition:{index}',
                f'Condition {index + 1}',
                'bool',
            )
            for index in range(_else_if_branch_condition_count(node))
        ]

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        condition_count = _else_if_branch_condition_count(node)
        pins = [
            acherion_node.pin('if:0', 'If Cond 1', 'exec'),
            *[
                acherion_node.pin(
                    f'elif:{index}',
                    f'Else if Cond {index + 1}',
                    'exec',
                )
                for index in range(1, condition_count)
            ],
        ]
        pins.append(acherion_node.pin('else', 'Else', 'exec'))
        return pins


class SequencerNode(acherion_node.FlowNodeDefinition):
    kind = 'sequencer'
    label = 'Sequencer'
    icon = 'format_list_numbered'
    tooltip = (
        'Run multiple execution paths in order: Then 1, Then 2, Then 3, and '
        'so on.'
    )
    flavor = 'control'
    exec_in = True
    default_params_factory = acherion_node.literal_params({'then_count': 2})

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner
        then_count = max(
            2,
            int(getattr(node, 'params', {}).get('then_count', 2) or 2),
        )
        return [
            acherion_node.pin(f'then:{index}', f'Then {index + 1}', 'exec')
            for index in range(then_count)
        ]


BUILTIN_FLOW_NODES = (
    ForEachNode(),
    CollectNode(),
    BranchValueNode(),
    BranchRouteNode(),
    ElseIfBranchNode(),
    SequencerNode(),
)

__all__ = ['BUILTIN_FLOW_NODES']

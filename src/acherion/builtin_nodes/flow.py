"""Built-in flow node definitions for Acherion."""

from __future__ import annotations

import acherion.node as acherion_node


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
        del owner, node
        return [
            acherion_node.pin('item', 'item', 'any'),
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
            acherion_node.pin('condition_source', 'Condition', 'any'),
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
        return [acherion_node.pin('condition_source', 'Condition', 'any')]

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
    SequencerNode(),
)

__all__ = ['BUILTIN_FLOW_NODES']

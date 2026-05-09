"""Built-in composite node definitions for Acherion."""

from __future__ import annotations

import acherion.node as acherion_node


class CustomFunctionNode(acherion_node.CompositeNodeDefinition):
    kind = 'custom_function'
    label = 'Custom Function'
    icon = 'functions'
    tooltip = 'Define and call a user method from a compact code editor dialog.'
    manual_add = True
    producer = True
    exec_in = True
    exec_out = True
    default_params_factory = acherion_node.custom_function_params


class FunctionEntryNode(acherion_node.CompositeNodeDefinition):
    kind = 'function_entry'
    label = 'Entry'
    icon = 'login'
    tooltip = 'Auto-created entry point for execution inside a Function Box.'
    exec_out = True
    default_params_factory = acherion_node.literal_params({
        'parent_function': '',
        'group': '',
    })


class FunctionBoxNode(acherion_node.CompositeNodeDefinition):
    kind = 'function_box'
    label = 'Function Box'
    icon = 'functions'
    tooltip = 'Composite function container with a compact internal entry exec pin.'
    manual_add = True
    producer = True
    exec_in = True
    exec_out = True
    default_params_factory = acherion_node.literal_params({
        'function_name': '',
    })

    def input_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return []

    def output_pins(
        self,
        owner: object,
        node: object,
    ) -> list[dict[str, str]] | None:
        del owner, node
        return []


BUILTIN_COMPOSITE_NODES = (
    CustomFunctionNode(),
    FunctionEntryNode(),
    FunctionBoxNode(),
)

__all__ = ['BUILTIN_COMPOSITE_NODES']

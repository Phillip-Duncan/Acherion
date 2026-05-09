"""Built-in object node definitions for Acherion."""

from __future__ import annotations

import acherion.node as acherion_node


class FunctionCallNode(acherion_node.ObjectNodeDefinition):
    kind = 'call_function'
    label = 'Function Call / Class Instance'
    icon = 'code'
    tooltip = 'Call any catalog function, or construct a class instance.'
    producer = True
    exec_in = True
    exec_out = True
    default_params_factory = acherion_node.literal_params({
        'function_path': 'list',
        'module': 'builtins',
        'arg_count': 1,
        'arg_sources': [''],
    })


class CallMethodNode(acherion_node.ObjectNodeDefinition):
    kind = 'call_method'
    label = 'Call Method'
    icon = 'call_made'
    tooltip = 'Call a method on an object instance (e.g. instance.analyze()).'
    producer = True
    exec_in = True
    exec_out = True
    source_param_ids_factory = acherion_node.source_param_ids('instance')


class GetAttributeNode(acherion_node.ObjectNodeDefinition):
    kind = 'get_attribute'
    label = 'Get Attribute'
    icon = 'read_more'
    tooltip = (
        'Read a public attribute from an object instance '
        '(e.g. instance.images).'
    )
    producer = True
    exec_in = True
    exec_out = True
    source_param_ids_factory = acherion_node.source_param_ids('instance')


class SetAttributeNode(acherion_node.ObjectNodeDefinition):
    kind = 'set_attribute'
    label = 'Set Attribute'
    icon = 'edit'
    tooltip = (
        'Set a public attribute on an object instance '
        '(e.g. instance.images = value).'
    )
    exec_in = True
    exec_out = True
    source_param_ids_factory = acherion_node.source_param_ids(
        'instance',
        'value',
    )
    default_params_factory = acherion_node.literal_params({
        'instance': '',
        'attribute_name': '',
        'value': '',
    })


BUILTIN_OBJECT_NODES = (
    FunctionCallNode(),
    CallMethodNode(),
    GetAttributeNode(),
    SetAttributeNode(),
)

__all__ = ['BUILTIN_OBJECT_NODES']

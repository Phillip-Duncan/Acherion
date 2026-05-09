"""Type policy helpers for the visual-logic function catalog."""

from __future__ import annotations

import inspect
import re
from typing import Any

import acherion.node_behaviors as acherion_node_behaviors

NDARRAY_TYPE_TAG = 'np.ndarray'

LIST_LIKE_TYPE_TAGS: frozenset[str] = frozenset({
    'list',
    'list[list]',
    'list[np.ndarray]',
    NDARRAY_TYPE_TAG,
})

RUNTIME_CLASS_PATH_BY_TYPE_TAG: dict[str, str] = {
    'bool': 'bool',
    'float': 'float',
    'int': 'int',
    'str': 'str',
    'list': 'list',
    'list[list]': 'list',
    'tuple': 'tuple',
    'set': 'set',
    'dict': 'dict',
    'range': 'range',
    'Figure': 'go.Figure',
    NDARRAY_TYPE_TAG: NDARRAY_TYPE_TAG,
}

RETURN_TYPE_MAP: dict[str, str] = {
    'ndarray': NDARRAY_TYPE_TAG,
    'numpy.ndarray': NDARRAY_TYPE_TAG,
    'np.ndarray': NDARRAY_TYPE_TAG,
    'matrix': NDARRAY_TYPE_TAG,
    'ndarray | None': NDARRAY_TYPE_TAG,
    'int': 'int',
    'float': 'float',
    'bool': 'bool',
    'str': 'str',
    'list': 'list',
    'tuple': 'list',
    'dict': 'dict',
    'None': 'any',
    'Figure': 'Figure',
    'go.Figure': 'Figure',
}

COMPONENT_PYTHON_TYPES: dict[str, str] = {
    'external_event': 'event',
    'plot_figure': 'any',
    'constant': 'float | int | str | bool | dict',
    'call_function': 'any',
    'custom_function': 'any',
    'op_arithmetic': 'any',
    'op_unary': 'any',
    'op_logic': 'any',
    'op_not': 'any',
    'compare': 'any',
    'branch_value': 'any',
    'make_list': 'any',
    'list_index': 'any',
}

OUTPUT_PIN_LABELS: dict[str, str] = {
    'constant': 'literal',
    'call_function': 'result',
    'custom_function': 'result',
    'compare': 'condition',
    'op_arithmetic': 'result',
    'op_unary': 'result',
    'op_logic': 'condition',
    'op_not': 'condition',
    'branch_value': 'selected',
    'make_list': 'list',
    'list_index': 'value',
    'plot_figure': 'Figure',
}

SINK_PIN_LABELS: dict[str, str] = {
}

_PIN_STYLE_TAG_MAP: dict[str, str] = {
    'exec': 'exec',
    'bool': 'bool',
    NDARRAY_TYPE_TAG: 'array',
    'int': 'int',
    'float': 'number',
    'dict': 'dict',
    'str': 'text',
    'Figure': 'figure',
    'image': 'image',
}


def annotation_to_tag(annotation: Any) -> str:
    """Convert a return annotation object to a pin type tag string."""
    if annotation is inspect.Parameter.empty:
        return 'any'
    if isinstance(annotation, type):
        return RETURN_TYPE_MAP.get(annotation.__name__, 'any')
    annotation_text = str(annotation).strip()
    normalized_text = re.sub(r'\s+', ' ', annotation_text)
    normalized_text = normalized_text.replace('typing.', '')
    normalized_text = normalized_text.replace('collections.abc.', '')
    if '|' in normalized_text:
        parts = [
            part.strip()
            for part in normalized_text.split('|')
            if part.strip() and part.strip() != 'None'
        ]
        if len(parts) == 1:
            return annotation_to_tag(parts[0])
    lowered = normalized_text.lower()
    if lowered.startswith(('list[', 'sequence[', 'iterable[')):
        return 'list'
    if lowered.startswith('tuple['):
        return 'list'
    if lowered.startswith('dict['):
        return 'dict'
    if lowered.startswith('set['):
        return 'set'
    return RETURN_TYPE_MAP.get(
        normalized_text,
        RETURN_TYPE_MAP.get(normalized_text.split('.')[-1], 'any'),
    )


def return_annotation_to_tag(annotation: Any) -> str:
    """Convert a return annotation into a pin type, preserving no-return."""
    if annotation is inspect.Parameter.empty:
        return 'any'
    if annotation is None:
        return ''
    annotation_text = str(annotation).strip()
    normalized_text = re.sub(r'\s+', ' ', annotation_text)
    normalized_text = normalized_text.replace('typing.', '')
    normalized_text = normalized_text.replace('collections.abc.', '')
    if normalized_text == 'None':
        return ''
    if '|' in normalized_text:
        parts = [
            part.strip()
            for part in normalized_text.split('|')
            if part.strip() and part.strip() != 'None'
        ]
        if len(parts) == 1:
            return annotation_to_tag(parts[0])
    return annotation_to_tag(annotation)


def node_kind_to_type(kind: str) -> str:
    """Return a Python type hint string for a component or node kind."""
    summary = acherion_node_behaviors.node_type_summary(kind)
    if summary:
        return summary
    return COMPONENT_PYTHON_TYPES.get(kind, 'any')


def output_pin_label(kind: str) -> str:
    """Human-readable label for the output pin of a producer node."""
    override = acherion_node_behaviors.output_pin_label(kind)
    if override:
        return override
    return OUTPUT_PIN_LABELS.get(kind, 'value')


def sink_pin_label(kind: str) -> str:
    """Human-readable label for the input pin of a sink node."""
    override = acherion_node_behaviors.sink_pin_label(kind)
    if override:
        return override
    return SINK_PIN_LABELS.get(kind, 'value')


def pin_style_tag(type_tag: str) -> str:
    """Return a compact style tag used for pin and badge colouring."""
    tag = str(type_tag or '').strip()
    if not tag or tag == 'any':
        return 'any'
    mapped = _PIN_STYLE_TAG_MAP.get(tag)
    if mapped:
        return mapped
    if tag in LIST_LIKE_TYPE_TAGS:
        return 'list'
    if tag == 'object' or runtime_class_path_for_type_tag(tag):
        return 'object'
    return 'any'


def types_compatible(src: str, tgt: str) -> bool:
    """Return True if a source pin of type *src* can connect to *tgt*."""
    clean_src = str(src or '').strip() or 'any'
    clean_tgt = str(tgt or '').strip() or 'any'
    if clean_src == 'any' or clean_tgt == 'any':
        return True
    if clean_src == clean_tgt:
        return True
    if clean_src in LIST_LIKE_TYPE_TAGS and clean_tgt in LIST_LIKE_TYPE_TAGS:
        return True
    if clean_tgt == 'object' and runtime_class_path_for_type_tag(clean_src):
        return True
    if clean_src == 'int' and clean_tgt == 'float':
        return True
    if clean_src == 'dict' and clean_tgt == 'dict':
        return True
    return False


def runtime_class_path_for_type_tag(type_tag: str) -> str:
    """Return runtime class path for a concrete pin type tag, else empty."""
    tag = str(type_tag or '').strip()
    if not tag or tag in {'any', 'object', 'None'}:
        return ''
    return RUNTIME_CLASS_PATH_BY_TYPE_TAG.get(tag, '')


def value_to_type_tag(value: Any) -> str:
    """Return a pin type tag inferred from a runtime value."""
    if value is None:
        return 'any'
    if isinstance(value, bool):
        return 'bool'
    if isinstance(value, int) and not isinstance(value, bool):
        return 'int'
    if isinstance(value, float):
        return 'float'
    if isinstance(value, str):
        return 'str'
    if isinstance(value, dict):
        return 'dict'
    if isinstance(value, list):
        return 'list'
    if isinstance(value, tuple):
        return 'list'
    if isinstance(value, set):
        return 'set'
    if isinstance(value, range):
        return 'range'
    value_type = type(value)
    module_name = str(getattr(value_type, '__module__', '') or '')
    type_name = str(getattr(value_type, '__name__', '') or '')
    if module_name.startswith('numpy') and type_name == 'ndarray':
        return NDARRAY_TYPE_TAG
    if module_name.startswith('plotly') and type_name == 'Figure':
        return 'Figure'
    return 'object'


def return_value_to_type_tag(value: Any) -> str:
    """Return output pin type tag for a runtime return value."""
    if value is None:
        return ''
    return value_to_type_tag(value)


def sink_type_tag(kind: str) -> str:
    """Simple type tag for a sink node input pin."""
    override = acherion_node_behaviors.sink_input_type_tag(kind)
    if override:
        return override
    return 'any'

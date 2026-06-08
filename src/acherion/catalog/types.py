"""Type policy helpers for the visual-logic function catalog."""

from __future__ import annotations

import inspect
import re
from typing import Any

import acherion.node_behaviors as acherion_node_behaviors

NDARRAY_TYPE_TAG = 'np.ndarray'
_RUNTIME_CLASS_PATH_RE = re.compile(
    r'^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$'
)

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
    'reroute': 'any',
    'exec_reroute': 'exec',
    'constant': 'float | int | str | bool | dict',
    'call_function': 'any',
    'custom_function': 'any',
    'op_arithmetic': 'any',
    'op_unary': 'any',
    'op_logic': 'bool',
    'op_not': 'bool',
    'compare': 'bool',
    'branch_value': 'any',
    'make_list': 'list',
    'make_dict': 'dict',
    'list_index': 'any',
    'list_set': 'any',
    'dict_get': 'any',
    'dict_set': 'dict',
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
    'make_dict': 'dict',
    'list_index': 'value',
    'list_set': 'list',
    'dict_get': 'value',
    'dict_set': 'dict',
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


def _normalized_annotation_text(annotation_text: str) -> str:
    normalized_text = re.sub(r'\s+', ' ', str(annotation_text or '').strip())
    normalized_text = normalized_text.replace('typing.', '')
    normalized_text = normalized_text.replace('collections.abc.', '')
    return normalized_text


def _generic_inner_text(annotation_text: str) -> str:
    if '[' not in annotation_text or not annotation_text.endswith(']'):
        return ''
    return annotation_text[annotation_text.find('[') + 1:-1].strip()


def _split_generic_parts(annotation_text: str) -> list[str]:
    """Split one generic parameter list while respecting nested brackets."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in annotation_text:
        if char == ',' and depth == 0:
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        if char == '[':
            depth += 1
        elif char == ']':
            depth = max(0, depth - 1)
        current.append(char)
    part = ''.join(current).strip()
    if part:
        parts.append(part)
    return parts


def _tuple_type_tag(annotation_text: str) -> str:
    """Return one conservative list-like tag for a tuple annotation."""
    item_text = _generic_inner_text(annotation_text)
    if not item_text:
        return 'list'
    tuple_parts = [
        part for part in _split_generic_parts(item_text)
        if part and part != '...'
    ]
    if not tuple_parts:
        return 'list'
    item_tags = {
        annotation_to_tag(part)
        for part in tuple_parts
    }
    item_tags.discard('any')
    if len(item_tags) == 1:
        return f'list[{next(iter(item_tags))}]'
    return 'list'


def _runtime_class_type_tag(annotation: type) -> str:
    mapped_type_tag = RETURN_TYPE_MAP.get(annotation.__name__)
    if mapped_type_tag:
        return mapped_type_tag
    module_name = str(getattr(annotation, '__module__', '') or '').strip()
    if module_name and module_name not in {'builtins', '__main__'}:
        return f'{module_name}.{annotation.__name__}'
    return 'any'


def is_list_like_type_tag(type_tag: str) -> bool:
    """Return True when one type tag describes a list-like value."""
    clean_tag = str(type_tag or '').strip()
    return clean_tag in LIST_LIKE_TYPE_TAGS or (
        clean_tag.startswith('list[') and clean_tag.endswith(']')
    )


def list_item_type_tag(type_tag: str) -> str:
    """Return inferred item type for one list-like type tag."""
    clean_tag = str(type_tag or '').strip()
    if clean_tag == 'list[list]':
        return 'list'
    if clean_tag == f'list[{NDARRAY_TYPE_TAG}]':
        return NDARRAY_TYPE_TAG
    if clean_tag.startswith('list[') and clean_tag.endswith(']'):
        return clean_tag[5:-1].strip() or 'any'
    return 'any'


def _iterable_item_type_tag(value: list[Any] | tuple[Any, ...]) -> str:
    if not value:
        return ''
    item_tags: set[str] = set()
    for item in value[:8]:
        item_tag = value_to_type_tag(item)
        if not item_tag or item_tag == 'any':
            return ''
        item_tags.add(item_tag)
        if len(item_tags) > 1:
            return ''
    return next(iter(item_tags), '')


def annotation_to_tag(annotation: Any) -> str:
    """Convert a return annotation object to a pin type tag string."""
    if annotation is inspect.Parameter.empty:
        return 'any'
    if isinstance(annotation, type):
        return _runtime_class_type_tag(annotation)
    normalized_text = _normalized_annotation_text(str(annotation))
    if not normalized_text:
        return 'any'
    if '|' in normalized_text:
        parts = [
            part.strip()
            for part in normalized_text.split('|')
            if part.strip() and part.strip() != 'None'
        ]
        if len(parts) == 1:
            return annotation_to_tag(parts[0])
    lowered = normalized_text.lower()
    if lowered.startswith('optional['):
        return annotation_to_tag(_generic_inner_text(normalized_text))
    if lowered.startswith(('list[', 'sequence[', 'iterable[')):
        item_tag = annotation_to_tag(_generic_inner_text(normalized_text))
        if item_tag and item_tag != 'any':
            return f'list[{item_tag}]'
        return 'list'
    if lowered.startswith('tuple['):
        return _tuple_type_tag(normalized_text)
    if lowered.startswith('dict['):
        return 'dict'
    if lowered.startswith('set['):
        return 'set'
    mapped_type_tag = RETURN_TYPE_MAP.get(
        normalized_text,
        RETURN_TYPE_MAP.get(normalized_text.split('.')[-1], 'any'),
    )
    if mapped_type_tag != 'any':
        return mapped_type_tag
    if _RUNTIME_CLASS_PATH_RE.match(normalized_text):
        return normalized_text
    return 'any'


def return_annotation_to_tag(annotation: Any) -> str:
    """Convert a return annotation into a pin type, preserving no-return."""
    if annotation is inspect.Parameter.empty:
        return 'any'
    if annotation is None:
        return ''
    normalized_text = _normalized_annotation_text(str(annotation))
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
    if is_list_like_type_tag(tag):
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
    if is_list_like_type_tag(clean_src) and is_list_like_type_tag(clean_tgt):
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
    mapped_class_path = RUNTIME_CLASS_PATH_BY_TYPE_TAG.get(tag)
    if mapped_class_path:
        return mapped_class_path
    if _RUNTIME_CLASS_PATH_RE.match(tag):
        return tag
    return ''


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
        item_tag = _iterable_item_type_tag(value)
        if item_tag:
            return f'list[{item_tag}]'
        return 'list'
    if isinstance(value, tuple):
        item_tag = _iterable_item_type_tag(value)
        if item_tag:
            return f'list[{item_tag}]'
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
    if module_name and module_name not in {'builtins', '__main__'} and type_name:
        return f'{module_name}.{type_name}'
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

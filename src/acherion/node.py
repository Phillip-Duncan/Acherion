"""Base Acherion node-definition types and shared public helpers."""

from __future__ import annotations

from abc import ABC
from collections.abc import Callable
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from acherion.events import AcherionExternalEvent


_NodeParamsFactory = Callable[[str], dict[str, Any]]
_NodePinsFactory = Callable[[Any, Any], list[dict[str, str]]]
_NodeEditorRenderer = Callable[..., Any]
_NodeSourceParamIdsFactory = Callable[[Any], list[str] | tuple[str, ...]]

_IDENTIFIER_RE = re.compile(r'[^a-zA-Z0-9_]+')
_SOURCE_PARAM_SENTINEL = object()


def literal_params(value: dict[str, Any]) -> _NodeParamsFactory:
    """Return a params factory that copies one static mapping per node."""

    def _factory(_node_id: str) -> dict[str, Any]:
        return dict(value)

    return _factory


def source_param_ids(
    *param_names: str,
) -> _NodeSourceParamIdsFactory:
    """Return a factory that exposes fixed source-param ids for one node."""
    cleaned_names = tuple(
        str(name or '').strip()
        for name in param_names
        if str(name or '').strip()
    )

    def _factory(_node: Any) -> tuple[str, ...]:
        return cleaned_names

    return _factory


def acherion_node_identifier(kind: str, node: Any) -> str | None:
    """Return host-defined stable identifier for one node, when present."""
    from acherion.registry import (
        get_acherion_node_definition,
    )

    definition = get_acherion_node_definition(str(kind or '').strip())
    if definition is None:
        return None
    identifier = str(definition.node_identifier(node) or '').strip()
    return identifier or None


def acherion_auto_identifier(text: str, fallback: str = 'field') -> str:
    """Return a snake_case identifier derived from UI text."""
    identifier = _IDENTIFIER_RE.sub('_', str(text or '').strip().lower())
    identifier = re.sub(r'_+', '_', identifier).strip('_')
    if not identifier:
        identifier = fallback
    if identifier[0].isdigit():
        identifier = f'field_{identifier}'
    return identifier


def source_key_params(_node_id: str) -> dict[str, Any]:
    """Return the default source-key params payload for schema nodes."""
    return {'source_key': ''}


def custom_function_params(node_id: str) -> dict[str, Any]:
    """Return default params for a new custom-function node."""
    del node_id
    return {
        'function_path': '',
        'module': 'user',
        'arg_count': 0,
        'arg_sources': [],
    }


def pin(
    pin_id: str,
    label: str,
    pin_type: str,
    *,
    optional: bool = False,
    editor_kind: str = '',
) -> dict[str, str]:
    """Return one normalized pin specification."""
    pin = {
        'pin_id': pin_id,
        'label': label,
        'type': pin_type,
    }
    if optional:
        pin['optional'] = 'true'
    if editor_kind:
        pin['editor_kind'] = editor_kind
    return pin


_NODE_DEFINITION_OVERRIDE_FIELDS: frozenset[str] = frozenset({
    'kind',
    'label',
    'icon',
    'tooltip',
    'category',
    'flavor',
    'manual_add',
    'producer',
    'system_source',
    'system_sink',
    'exec_in',
    'exec_out',
    'default_params_factory',
    'source_param_ids_factory',
    'input_pins_factory',
    'output_pins_factory',
    'config_fields_renderer',
})


class AcherionNodeDefinition(ABC):
    """Subclassable definition object for one Acherion node type."""

    kind: str = ''
    label: str = ''
    icon: str = ''
    tooltip: str = ''
    category: str = ''
    flavor: str = ''
    manual_add: bool = False
    producer: bool = False
    system_source: bool = False
    system_sink: bool = False
    exec_in: bool = False
    exec_out: bool = False
    default_params_factory: _NodeParamsFactory | None = source_key_params
    source_param_ids_factory: _NodeSourceParamIdsFactory | None = None
    input_pins_factory: _NodePinsFactory | None = None
    output_pins_factory: _NodePinsFactory | None = None
    config_fields_renderer: _NodeEditorRenderer | None = None

    def __init__(self, **overrides: Any) -> None:
        unknown = sorted(
            key
            for key in overrides
            if key not in _NODE_DEFINITION_OVERRIDE_FIELDS
        )
        if unknown:
            unknown_fields = ', '.join(unknown)
            raise TypeError(
                f'Unknown node definition field(s): {unknown_fields}'
            )
        for key, value in overrides.items():
            setattr(self, key, value)
        self._validate_definition_metadata()

    def _definition_field(self, field_name: str) -> Any:
        if field_name in self.__dict__:
            return self.__dict__[field_name]
        return getattr(type(self), field_name)

    def _validate_definition_metadata(self) -> None:
        required_fields = ('kind', 'label', 'icon', 'category', 'flavor')
        missing = [
            field_name
            for field_name in required_fields
            if not str(self._definition_field(field_name) or '').strip()
        ]
        if missing:
            missing_text = ', '.join(missing)
            raise ValueError(
                f'Node definition is missing required field(s): '
                f'{missing_text}'
            )

    def default_title(self) -> str:
        """Return the default display title for new nodes."""
        return str(self._definition_field('label'))

    def default_params(self, *, node_id: str) -> dict[str, Any]:
        """Return initial params for a new node instance."""
        factory = self._definition_field('default_params_factory')
        if factory is None:
            params: dict[str, Any] = {}
        else:
            params = dict(factory(node_id))
        if bool(self._definition_field('exec_in')):
            params.setdefault('exec_sources', [])
        return params

    def runtime_contract(self, params: dict[str, Any]) -> dict[str, Any]:
        """Return a placeholder runtime contract for future previews."""
        return {
            'kind': str(self._definition_field('kind')),
            'params': dict(params),
            'producer': bool(self._definition_field('producer')),
            'exec_in': bool(self._definition_field('exec_in')),
            'exec_out': bool(self._definition_field('exec_out')),
        }

    def node_identifier(self, node: Any) -> str | None:
        """Return a stable identifier for one node, when applicable."""
        del node
        return None

    def schema_key_binding(self, node: Any) -> tuple[str, str] | None:
        """Return the schema namespace and param key for one node."""
        del node
        return None

    def source_param_ids(
        self,
        node: Any,
    ) -> tuple[str, ...]:
        """Return params on this node that store connected source ids."""
        factory = self._definition_field('source_param_ids_factory')
        raw_param_ids: list[str] = []
        if factory is not None:
            raw_param_ids = [
                str(param_id or '').strip()
                for param_id in factory(node)
            ]
        else:
            pins = self.input_pins(_SOURCE_PARAM_SENTINEL, node)
            if pins is not None:
                raw_param_ids = [
                    str(pin.get('pin_id') or '').strip()
                    for pin in pins
                ]

        param_ids: list[str] = []
        seen_param_ids: set[str] = set()
        for param_id in raw_param_ids:
            if not param_id or param_id in seen_param_ids:
                continue
            if param_id == 'exec_source':
                continue
            if param_id.startswith('arg:'):
                continue
            if param_id.startswith('named:'):
                continue
            if param_id.startswith('fin:'):
                continue
            seen_param_ids.add(param_id)
            param_ids.append(param_id)
        return tuple(param_ids)

    def input_pins(
        self,
        owner: Any,
        node: Any,
    ) -> list[dict[str, str]] | None:
        """Return custom input pins for one node instance, if any."""
        factory = self._definition_field('input_pins_factory')
        if factory is None:
            return None
        return [dict(pin) for pin in factory(owner, node)]

    def output_pins(
        self,
        owner: Any,
        node: Any,
    ) -> list[dict[str, str]] | None:
        """Return custom output pins for one node instance, if any."""
        factory = self._definition_field('output_pins_factory')
        if factory is None:
            return None
        return [dict(pin) for pin in factory(owner, node)]

    def render_config_fields(
        self,
        owner: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Render custom config UI for one node and return handled state."""
        renderer = self._definition_field('config_fields_renderer')
        if renderer is None:
            return False
        result = renderer(
            owner,
            node,
            refresh_editor=refresh_editor,
            apply_change=apply_change,
        )
        return result is not False

    def render_inline_controls(
        self,
        owner: Any,
        node: Any,
    ) -> bool:
        """Render compact inline node controls and return handled state."""
        del owner, node
        return False

    def external_events(
        self,
        owner: Any,
        node: Any,
    ) -> tuple[AcherionExternalEvent, ...]:
        """Return external events emitted by one node instance, if any."""
        del owner, node
        return ()


class SystemSourceNodeDefinition(AcherionNodeDefinition):
    """Base class for built-in runtime source nodes."""

    category = 'source'
    system_source = True


class UINodeDefinition(AcherionNodeDefinition):
    """Base class for UI component nodes."""

    category = 'ui'
    flavor = 'source'
    manual_add = True
    producer = True
    exec_in = True
    exec_out = True


class ComputeNodeDefinition(AcherionNodeDefinition):
    """Base class for compute nodes."""

    category = 'compute'
    flavor = 'pure'
    manual_add = True
    producer = True


class FlowNodeDefinition(AcherionNodeDefinition):
    """Base class for flow-control nodes."""

    category = 'flow'
    manual_add = True


class ObjectNodeDefinition(AcherionNodeDefinition):
    """Base class for object and method nodes."""

    category = 'object'
    flavor = 'object'
    manual_add = True


class CompositeNodeDefinition(AcherionNodeDefinition):
    """Base class for composite nodes."""

    category = 'composite'
    flavor = 'composite'


class EffectNodeDefinition(AcherionNodeDefinition):
    """Base class for effect and sink nodes."""

    category = 'effect'
    flavor = 'effect'


class SystemSinkNodeDefinition(EffectNodeDefinition):
    """Base class for built-in sink nodes."""

    system_sink = True
    exec_in = True


__all__ = [
    'AcherionNodeDefinition',
    'CompositeNodeDefinition',
    'ComputeNodeDefinition',
    'EffectNodeDefinition',
    'FlowNodeDefinition',
    'ObjectNodeDefinition',
    'SystemSinkNodeDefinition',
    'SystemSourceNodeDefinition',
    'UINodeDefinition',
    'acherion_auto_identifier',
    'acherion_node_identifier',
    'custom_function_params',
    'literal_params',
    'pin',
    'source_param_ids',
    'source_key_params',
]
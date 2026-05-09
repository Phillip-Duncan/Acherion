"""Acherion node-definition registry and palette helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from acherion.node import AcherionNodeDefinition


_PALETTE_CATEGORY_ORDER: tuple[str, ...] = (
    'ui',
    'source',
    'compute',
    'flow',
    'object',
    'composite',
    'effect',
)

_PALETTE_CATEGORY_LABELS: dict[str, str] = {
    'ui': 'UI',
    'source': 'Runtime',
    'compute': 'Compute',
    'flow': 'Flow',
    'object': 'Objects',
    'composite': 'Composite',
    'effect': 'Effects',
}

_PALETTE_CATEGORY_ICONS: dict[str, str] = {
    'ui': 'widgets',
    'source': 'input',
    'compute': 'calculate',
    'flow': 'alt_route',
    'object': 'code',
    'composite': 'functions',
    'effect': 'bolt',
}

class AcherionNodeRegistry:
    """Mutable registry of node definitions."""

    def __init__(
        self,
        definitions: Iterable[AcherionNodeDefinition] | None = None,
    ) -> None:
        self._definitions: dict[str, AcherionNodeDefinition] = {}
        self._order: list[str] = []
        self._disabled_kinds: set[str] = set()
        for definition in definitions or ():
            self.register(definition)

    def register(
        self,
        definition: AcherionNodeDefinition,
        *,
        replace: bool = False,
    ) -> None:
        """Register one node definition."""
        if not isinstance(definition, AcherionNodeDefinition):
            raise TypeError('Definition must be a node definition instance')
        definition_instance = definition
        existing = self._definitions.get(definition_instance.kind)
        if existing is not None and not replace:
            raise ValueError(
                f'Node definition already registered: '
                f'{definition_instance.kind}'
            )
        self._definitions[definition_instance.kind] = definition_instance
        if existing is None:
            self._order.append(definition_instance.kind)

    def get(self, kind: str) -> AcherionNodeDefinition | None:
        """Return one node definition by kind."""
        return self._definitions.get(kind)

    def definitions(self) -> tuple[AcherionNodeDefinition, ...]:
        """Return all registered definitions in stable order."""
        return tuple(self._definitions[kind] for kind in self._order)

    def enabled_definitions(self) -> tuple[AcherionNodeDefinition, ...]:
        """Return definitions that are enabled for palette/manual add."""
        return tuple(
            self._definitions[kind]
            for kind in self._order
            if kind not in self._disabled_kinds
        )

    def disabled_kinds(self) -> tuple[str, ...]:
        """Return currently disabled node kinds in stable order."""
        return tuple(
            kind for kind in self._order
            if kind in self._disabled_kinds
        )

    def is_enabled(self, kind: str) -> bool:
        """Return whether one registered kind is enabled."""
        clean_kind = str(kind or '').strip()
        return bool(
            clean_kind
            and clean_kind in self._definitions
            and clean_kind not in self._disabled_kinds
        )

    def disable_kind(self, kind: str) -> None:
        """Disable one registered kind for palette/manual add."""
        clean_kind = str(kind or '').strip()
        if clean_kind not in self._definitions:
            raise ValueError(f'Unknown node kind: {clean_kind}')
        self._disabled_kinds.add(clean_kind)

    def enable_kind(self, kind: str) -> None:
        """Re-enable one registered kind for palette/manual add."""
        clean_kind = str(kind or '').strip()
        if clean_kind not in self._definitions:
            raise ValueError(f'Unknown node kind: {clean_kind}')
        self._disabled_kinds.discard(clean_kind)

    def set_disabled_kinds(self, kinds: Iterable[str]) -> None:
        """Replace the disabled node-kind set with the provided kinds."""
        next_disabled = {
            str(kind or '').strip()
            for kind in kinds
            if str(kind or '').strip()
        }
        unknown_kinds = sorted(next_disabled - set(self._definitions))
        if unknown_kinds:
            raise ValueError(
                'Unknown node kinds: ' + ', '.join(unknown_kinds)
            )
        self._disabled_kinds = next_disabled

    def palette_sections(
        self,
        category_order: Iterable[str] | None = None,
    ) -> tuple[tuple[str, tuple[AcherionNodeDefinition, ...]], ...]:
        """Return manual-add definitions grouped by palette category."""
        sections: list[tuple[str, tuple[AcherionNodeDefinition, ...]]] = []
        for category in category_order or _PALETTE_CATEGORY_ORDER:
            items = tuple(
                definition
                for definition in self.enabled_definitions()
                if definition.manual_add and definition.category == category
            )
            if items:
                sections.append((category, items))
        return tuple(sections)

    def is_manual_add_kind(self, kind: str) -> bool:
        """Return True when a kind can be added from the current palette."""
        definition = self.get(kind)
        return bool(
            definition is not None
            and definition.manual_add
            and self.is_enabled(kind)
        )


def _builtin_node_definitions() -> tuple[AcherionNodeDefinition, ...]:
    """Return built-in node-definition instances."""
    import acherion.builtin_nodes as _builtin_nodes

    return cast(
        tuple[AcherionNodeDefinition, ...],
        _builtin_nodes.BUILTIN_NODE_DEFINITIONS,
    )


_NODE_REGISTRY = AcherionNodeRegistry(_builtin_node_definitions())


def get_acherion_node_registry() -> AcherionNodeRegistry:
    """Return the shared mutable node-definition registry."""
    return _NODE_REGISTRY


def register_acherion_node_definition(
    definition: AcherionNodeDefinition,
    *,
    replace: bool = False,
) -> None:
    """Register one node definition on the shared registry."""
    _NODE_REGISTRY.register(definition, replace=replace)


def get_acherion_node_definition(kind: str) -> AcherionNodeDefinition | None:
    """Return one node definition by kind."""
    return _NODE_REGISTRY.get(kind)


def get_acherion_node_definitions() -> tuple[AcherionNodeDefinition, ...]:
    """Return all registered node definitions in stable order."""
    return _NODE_REGISTRY.definitions()


def get_acherion_enabled_node_definitions() -> tuple[AcherionNodeDefinition, ...]:
    """Return node definitions enabled for palette/manual add."""
    return _NODE_REGISTRY.enabled_definitions()


def get_acherion_disabled_node_kinds() -> tuple[str, ...]:
    """Return disabled node kinds from the shared registry."""
    return _NODE_REGISTRY.disabled_kinds()


def disable_acherion_node_kind(kind: str) -> None:
    """Disable one registered node kind for palette/manual add."""
    _NODE_REGISTRY.disable_kind(kind)


def enable_acherion_node_kind(kind: str) -> None:
    """Re-enable one registered node kind for palette/manual add."""
    _NODE_REGISTRY.enable_kind(kind)


def set_acherion_disabled_node_kinds(kinds: Iterable[str]) -> None:
    """Replace the disabled shared node-kind set."""
    _NODE_REGISTRY.set_disabled_kinds(kinds)


def is_acherion_node_kind_enabled(kind: str) -> bool:
    """Return whether one registered kind is enabled."""
    return _NODE_REGISTRY.is_enabled(kind)


def _node_template(kind: str) -> AcherionNodeDefinition | None:
    """Return metadata for one node kind, if known."""
    return get_acherion_node_definition(kind)


def _template_category(kind: str) -> str:
    """Return the palette category for a node kind."""
    template = _node_template(kind)
    return template.category if template is not None else 'compute'


def _template_category_label(kind: str) -> str:
    """Return the human-readable palette category for a node kind."""
    return _PALETTE_CATEGORY_LABELS.get(_template_category(kind), 'Compute')


def _palette_category_icon(category: str) -> str:
    """Return the activity-bar icon for one palette category."""
    return _PALETTE_CATEGORY_ICONS.get(category, 'widgets')


def _template_flavor(kind: str) -> str:
    """Return the visual flavor for a node kind."""
    template = _node_template(kind)
    return template.flavor if template is not None else 'pure'


def _template_has_exec_input(kind: str) -> bool:
    """Return True when a node kind supports an optional exec input."""
    template = _node_template(kind)
    return bool(template and template.exec_in)


def _template_has_exec_output(kind: str) -> bool:
    """Return True when a node kind supports an exec output."""
    template = _node_template(kind)
    return bool(template and template.exec_out)


def _palette_sections() -> tuple[tuple[str, tuple[AcherionNodeDefinition, ...]], ...]:
    """Return manual-add node definitions grouped into palette sections."""
    return _NODE_REGISTRY.palette_sections()


def is_acherion_producer_kind(kind: str) -> bool:
    """Return True when the kind produces a value binding."""
    definition = get_acherion_node_definition(kind)
    return bool(definition and definition.producer)


def is_acherion_manual_add_kind(kind: str) -> bool:
    """Return True when the kind can be added directly from the palette."""
    return _NODE_REGISTRY.is_manual_add_kind(kind)


def is_acherion_system_source_kind(kind: str) -> bool:
    """Return True when the kind is a built-in system source node."""
    definition = get_acherion_node_definition(kind)
    return bool(definition and definition.system_source)


def is_acherion_system_sink_kind(kind: str) -> bool:
    """Return True when the kind is a built-in system sink node."""
    definition = get_acherion_node_definition(kind)
    return bool(definition and definition.system_sink)


__all__ = [
    'AcherionNodeRegistry',
    'disable_acherion_node_kind',
    'enable_acherion_node_kind',
    'get_acherion_disabled_node_kinds',
    'get_acherion_node_definition',
    'get_acherion_node_definitions',
    'get_acherion_enabled_node_definitions',
    'get_acherion_node_registry',
    'is_acherion_manual_add_kind',
    'is_acherion_node_kind_enabled',
    'is_acherion_producer_kind',
    'is_acherion_system_sink_kind',
    'is_acherion_system_source_kind',
    'register_acherion_node_definition',
    'set_acherion_disabled_node_kinds',
]
"""Typed host contracts for embedded Acherion designers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from acherion.events import AcherionExternalEvent, default_acherion_external_events


AcherionRuntimeBindings = dict[str, dict[str, dict[str, Any]]]
AcherionExternalEventsHook = Callable[[], dict[str, AcherionExternalEvent]]
AcherionCodegenHook = Callable[[Any], str]
AcherionRuntimeBindingsHook = Callable[[Any], AcherionRuntimeBindings]
AcherionGraphSyncHook = Callable[[Any], None]
AcherionConfigRenderHook = Callable[..., bool]


def _default_external_events() -> dict[str, AcherionExternalEvent]:
    """Return default Acherion external events for one host."""
    return default_acherion_external_events()


def _default_runtime_bindings(designer: Any) -> AcherionRuntimeBindings:
    """Return empty runtime bindings for hosts that do not need them."""
    del designer
    return {}


def _noop_graph_sync(designer: Any) -> None:
    """Perform no graph sync for hosts that do not need it."""
    del designer


def _noop_config_render(
    designer: Any,
    node: Any,
    *,
    refresh_editor: Callable[[], None] | None,
    apply_change: Callable[..., None],
) -> bool:
    """Render no host-owned config UI by default."""
    del designer, node, refresh_editor, apply_change
    return False


class AcherionCodegenHost(Protocol):
    """Compile graph state into host-owned runtime artifacts."""

    def external_events(self) -> dict[str, AcherionExternalEvent]:
        """Return host-owned external events visible inside the designer."""

    def generated_user_code(self, designer: Any) -> str:
        """Compile the current graph into user code."""

    def generated_runtime_bindings(
        self,
        designer: Any,
    ) -> AcherionRuntimeBindings:
        """Collect runtime bindings for generated graph code."""


class AcherionGraphSyncHost(Protocol):
    """Normalize host-owned schema and system-node state."""

    def sync_manual_schema_keys(self, designer: Any) -> None:
        """Assign schema keys to manual nodes before sync."""

    def sync_system_nodes(self, designer: Any) -> None:
        """Rebuild system-owned nodes around the current manual graph."""


class AcherionConfigRenderHost(Protocol):
    """Render host-owned editor controls for configured nodes."""

    def render_system_sink_config_fields(
        self,
        designer: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Render host-owned config UI for system sink nodes."""

    def render_node_config_fields(
        self,
        designer: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Render host-owned config UI for manual nodes."""


class AcherionHost(
    AcherionCodegenHost,
    AcherionGraphSyncHost,
    AcherionConfigRenderHost,
    Protocol,
):
    """Compose full host behavior from smaller host responsibilities."""


@dataclass(slots=True)
class ComposedAcherionHost:
    """Concrete host object built from small host callback hooks."""

    _generated_user_code: AcherionCodegenHook
    _external_events: AcherionExternalEventsHook = _default_external_events
    _generated_runtime_bindings: AcherionRuntimeBindingsHook = (
        _default_runtime_bindings
    )
    _sync_manual_schema_keys: AcherionGraphSyncHook = _noop_graph_sync
    _sync_system_nodes: AcherionGraphSyncHook = _noop_graph_sync
    _render_system_sink_config_fields: AcherionConfigRenderHook = (
        _noop_config_render
    )
    _render_node_config_fields: AcherionConfigRenderHook = _noop_config_render

    def external_events(self) -> dict[str, AcherionExternalEvent]:
        """Return host-owned external events visible inside the designer."""
        return dict(self._external_events())

    def generated_user_code(self, designer: Any) -> str:
        """Compile the current graph into user code."""
        return str(self._generated_user_code(designer))

    def generated_runtime_bindings(
        self,
        designer: Any,
    ) -> AcherionRuntimeBindings:
        """Collect runtime bindings for generated graph code."""
        return dict(self._generated_runtime_bindings(designer))

    def sync_manual_schema_keys(self, designer: Any) -> None:
        """Assign schema keys to manual nodes before sync."""
        self._sync_manual_schema_keys(designer)

    def sync_system_nodes(self, designer: Any) -> None:
        """Rebuild system-owned nodes around the current manual graph."""
        self._sync_system_nodes(designer)

    def render_system_sink_config_fields(
        self,
        designer: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Render host-owned config UI for system sink nodes."""
        return bool(
            self._render_system_sink_config_fields(
                designer,
                node,
                refresh_editor=refresh_editor,
                apply_change=apply_change,
            )
        )

    def render_node_config_fields(
        self,
        designer: Any,
        node: Any,
        *,
        refresh_editor: Callable[[], None] | None,
        apply_change: Callable[..., None],
    ) -> bool:
        """Render host-owned config UI for manual nodes."""
        return bool(
            self._render_node_config_fields(
                designer,
                node,
                refresh_editor=refresh_editor,
                apply_change=apply_change,
            )
        )


def compose_acherion_host(
    *,
    generated_user_code: AcherionCodegenHook,
    external_events: AcherionExternalEventsHook | None = None,
    generated_runtime_bindings: AcherionRuntimeBindingsHook | None = None,
    sync_manual_schema_keys: AcherionGraphSyncHook | None = None,
    sync_system_nodes: AcherionGraphSyncHook | None = None,
    render_system_sink_config_fields: AcherionConfigRenderHook | None = None,
    render_node_config_fields: AcherionConfigRenderHook | None = None,
) -> ComposedAcherionHost:
    """Compose one embeddable Acherion host from small callback hooks."""
    return ComposedAcherionHost(
        _generated_user_code=generated_user_code,
        _external_events=external_events or _default_external_events,
        _generated_runtime_bindings=(
            generated_runtime_bindings or _default_runtime_bindings
        ),
        _sync_manual_schema_keys=sync_manual_schema_keys or _noop_graph_sync,
        _sync_system_nodes=sync_system_nodes or _noop_graph_sync,
        _render_system_sink_config_fields=(
            render_system_sink_config_fields or _noop_config_render
        ),
        _render_node_config_fields=(
            render_node_config_fields or _noop_config_render
        ),
    )


__all__ = [
    'AcherionCodegenHost',
    'AcherionConfigRenderHost',
    'AcherionGraphSyncHost',
    'AcherionHost',
    'AcherionRuntimeBindings',
    'ComposedAcherionHost',
    'compose_acherion_host',
]
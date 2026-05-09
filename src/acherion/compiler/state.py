"""Shared state objects for visual-logic compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from acherion.compiler.utils import _source_expr

ExternalInput: TypeAlias = tuple[str, str]


@dataclass
class EmitState:
    """Mutable line and source-tracking state for one compile pass."""

    lines: list[str] = field(default_factory=list)
    node_vars: dict[str, str] = field(default_factory=dict)

    def store(self, nid: str, vname: str, pin: int = 0) -> None:
        """Register a node output variable, including optional pin index."""
        if pin == 0:
            self.node_vars[nid] = vname
        self.node_vars[f'{nid}@{pin}'] = vname

    def store_source(self, source_id: str, vname: str) -> None:
        """Alias one source id to an emitted Python expression."""
        if source_id:
            self.node_vars[str(source_id)] = vname

    def source_expr(
        self,
        source_id: str | None,
        *,
        fallback: str = 'None',
    ) -> str:
        """Resolve a source id using this state's stored node vars."""
        return _source_expr(source_id, self.node_vars, fallback=fallback)
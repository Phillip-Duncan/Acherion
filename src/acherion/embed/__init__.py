"""NiceGUI embedding helpers for standalone or hosted Acherion."""

from __future__ import annotations

from acherion.embed.code_editor import (
    build_python_code_editor,
    inject_python_autocomplete,
)
from acherion.embed.designer.component import (
    AcherionDesigner,
)
from acherion.embed.workbench import (
    AcherionWorkbench,
)
from acherion.embed.schema_fields import (
    normalise_event_emitters,
    register_schema_component_field_renderer,
    register_schema_component_field_renderers,
    render_event_emitter_fields,
    render_schema_component_fields,
    schema_label,
)

__all__ = [
    'AcherionDesigner',
    'AcherionWorkbench',
    'build_python_code_editor',
    'inject_python_autocomplete',
    'normalise_event_emitters',
    'register_schema_component_field_renderer',
    'register_schema_component_field_renderers',
    'render_event_emitter_fields',
    'render_schema_component_fields',
    'schema_label',
]
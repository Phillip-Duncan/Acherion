# Embedding Acherion

Use `acherion.embed` when you want the graph designer or workbench inside your
own NiceGUI application.

## Main components

### `AcherionDesigner`

The raw visual editor component. Use it if you want full control over layout and
surrounding UI.

### `AcherionWorkbench`

The higher-level wrapper used by the standalone app. It layers a code view and
common callbacks on top of `AcherionDesigner`.

## Minimal embedded workbench

```python
from nicegui import ui

from acherion import StandaloneAcherionHost
from acherion.embed import AcherionWorkbench


persisted_graph: dict[str, object] = {}


@ui.page('/')
def index() -> None:
    workbench: AcherionWorkbench | None = None

    def handle_change() -> None:
        if workbench is None:
            return
        persisted_graph.clear()
        persisted_graph.update(workbench.designer.to_dict())

    workbench = AcherionWorkbench(
        host=StandaloneAcherionHost(),
        on_change=handle_change,
        refresh_code_after_build=True,
        theme_overrides={
            'surface': '#111827',
            'text': '#f9fafb',
            'primary': '#22c55e',
            'sidebar_panel_bg': 'rgba(255,255,255,0.05)',
        },
    )
    workbench.build()
    workbench.designer.set_graph_from_dict(persisted_graph)


ui.run()
```

This is the simplest way to embed Acherion with the generic standalone behavior.

## Embedded theming

`AcherionWorkbench` accepts `theme_overrides` for per-instance theme control.
When provided, Acherion injects a scoped copy of its packaged theme CSS against
that workbench root instead of globally styling the entire app.

Supported override keys include common aliases such as:

- `bg`
- `surface`
- `border`
- `text`
- `muted`
- `primary`
- `secondary`
- `accent`
- `positive`
- `negative`
- `warning`
- `info`
- `sidebar_glass_bg`
- `sidebar_panel_bg`
- `sidebar_panel_bg_strong`

You can also pass raw CSS custom-property names directly, for example:

```python
workbench = AcherionWorkbench(
    host=StandaloneAcherionHost(),
    theme_overrides={
        '--oe-bg': '#0b1020',
        '--oe-text': '#e2e8f0',
        '--oe-blue': '#7c3aed',
    },
)
```

Pass `theme_overrides={}` if you want the default Acherion embedded theme but
still want it scoped to the workbench rather than applied globally.

## Switching themes at runtime

You can update the theme on an already-built workbench.

```python
workbench.set_theme_overrides({
        'surface': '#ffffff',
        'text': '#0f172a',
        'primary': '#2563eb',
})

workbench.set_theme_overrides({
        'surface': '#0f172a',
        'text': '#e2e8f0',
        'primary': '#38bdf8',
})
```

That is the intended path for host-controlled light/dark switching.

- pass a mapping to `set_theme_overrides(...)` to enable or replace the scoped
    Acherion theme
- pass `{}` to keep the default Acherion token set but still scope it to this
    workbench instance
- call `clear_theme_overrides()` to disable the scoped Acherion theme and fall
    back to the host application's styling

Example toggle handler:

```python
def apply_dark_mode(enabled: bool) -> None:
        if enabled:
                workbench.set_theme_overrides({
                        'surface': '#0f172a',
                        'text': '#e2e8f0',
                        'muted': '#94a3b8',
                        'primary': '#38bdf8',
                })
                return
        workbench.set_theme_overrides({
                'surface': '#ffffff',
                'text': '#0f172a',
                'muted': '#475569',
                'primary': '#2563eb',
        })
```

## Supplying your own host

Hosts are the integration contract between Acherion and your application.
An `AcherionHost` provides:

- `external_events()`
- `generated_user_code(designer)`
- `generated_runtime_bindings(designer)`
- `sync_manual_schema_keys(designer)`
- `sync_system_nodes(designer)`
- `render_system_sink_config_fields(...)`
- `render_node_config_fields(...)`

If you do not want to implement the protocol manually, use
`compose_acherion_host`.

```python
from acherion import (
    AcherionExternalEvent,
    compile_acherion_graph,
    compose_acherion_external_events,
    compose_acherion_host,
)


host = compose_acherion_host(
    generated_user_code=lambda designer: compile_acherion_graph(
        designer.graph_state()
    ),
    external_events=lambda: compose_acherion_external_events({
        'save': AcherionExternalEvent(
            event_key='save',
            title='Event: Save',
            handler_name='on_save',
            description='Triggered by the host application.',
        ),
    }),
)
```

This composition helper is a good fit when you want to override only a small
subset of host behavior.

## Useful workbench hooks

`AcherionWorkbench` accepts callbacks that let hosts integrate with their own
storage and runtime flow.

- `on_change` for persistence or external synchronization
- `on_apply_to_code` when the host owns the code-pane update behavior
- `on_run_preview` to launch host-specific preview logic
- `on_validate` to run host-defined validation
- `build_code_view` to replace the default code editor
- `before_build` to inject CSS or prepare page-level state

The workbench also supports host-side display control through:

- `code_transform`
- `refresh_code_on_change`
- `refresh_code_after_build`
- `validate_generated_code`

## Persistence and restore

The most common embedding pattern is host-owned persistence:

- save with `workbench.designer.to_dict()`
- restore with `workbench.designer.set_graph_from_dict(...)`
- compile with `workbench.generated_user_code()` or `designer.graph_state()`

That keeps Acherion focused on editing and compilation while your application
decides where graph state lives.
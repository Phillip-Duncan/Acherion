# Acherion

Acherion is an embeddable flow-graph editor and runtime workbench for Python.
It provides a NiceGUI-based visual designer, a typed graph/runtime API, and a
standalone host that compiles graphs into executable Python code.

## What Acherion provides

- A standalone workbench you can launch with `acherion` or `python -m acherion`
- A reusable NiceGUI workbench component for embedding inside your own app
- A typed graph model for saving, restoring, compiling, and executing graphs
- Preview execution hooks with transient runtime bindings and value summaries
- Extension points for custom hosts, catalog modules, preview adapters, and
	validation helpers

## Installation

Install the published package:

```bash
pip install acherion
```

Install from source for local development:

```bash
pip install -e ".[dev]"
```

Python 3.11 or newer is required.

## Standalone quick start

Run the packaged standalone workbench:

```bash
acherion
```

Equivalent entry points:

```bash
python -m acherion
```

```python
from acherion.app import main

main(host='127.0.0.1', port=8081, reload=False)
```

The standalone app mounts a full-screen Acherion workbench with:

- the graph designer
- the generated-code pane
- live preview execution for the default `run` event
- graph-to-Python validation through the standalone host

## Embedding quick start

The core API lives in `acherion`. The NiceGUI embedding layer lives in
`acherion.embed`.

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

This uses the generic standalone host, but the workbench can also run against
your own host implementation through `AcherionHost` or `compose_acherion_host`.

Passing `theme_overrides` opts the embedded workbench into Acherion's scoped
theme CSS without restyling the rest of the host application. Keys can be the
semantic aliases shown above or raw CSS variable names like `--oe-bg` and
`--ach-sidebar-panel-bg`. Pass an empty dict if you want the default Acherion
embedded theme with no overrides.

You can also switch themes after `build()`:

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

workbench.clear_theme_overrides()
```

`clear_theme_overrides()` disables the scoped embedded Acherion theme and lets
the surrounding host application styling take over again.

## Core concepts

### Graph model

- `AcherionGraph` is the serializable top-level graph object.
- `AcherionNode` stores one node's kind, title, id, and params.
- `AcherionDesigner.to_dict()` returns a JSON-safe representation.
- `AcherionDesigner.set_graph_from_dict()` restores persisted state.

### Workbench layer

- `AcherionWorkbench` wraps `AcherionDesigner` with code-view and validation
	behavior.
- `AcherionWorkbench.generated_user_code()` returns the current compiled code.
- `AcherionWorkbench` supports callbacks for change handling, validation,
	preview execution, and custom code views.

### Host layer

An `AcherionHost` is responsible for integrating the designer with your app.
Hosts provide:

- external event definitions
- code generation
- runtime bindings for previews or generated code
- graph normalization/system-node sync
- host-owned configuration UI for special nodes

### Runtime helpers

The standalone runtime helpers in `acherion` are useful even outside the UI:

```python
from acherion import compile_acherion_graph, execute_acherion_graph
```

They compile a graph into Python source and execute the generated event handler
with optional scoped bindings.

## Extension points

Acherion exposes several host-facing registration hooks:

- `register_catalog_module_specs` to expose Python modules in the function catalog
- `register_preview_value_adapter` to customize preview summaries/type tags
- `register_acherion_validation_extension` to extend validation globals
- `register_acherion_node_definition` to add or replace node metadata

Custom node definitions are only part of the story: if you introduce a new node
kind, your host/compiler also needs to know how to emit runtime code for it.

## Documentation set

Repository documentation is split into focused guides:

- `docs/overview.md` for architecture and feature overview
- `docs/standalone.md` for standalone usage and persistence patterns
- `docs/embedding.md` for NiceGUI embedding and host composition
- `docs/extending.md` for catalogs, validation, preview, and node extension hooks
- `docs/releasing.md` for local packaging checks and GitHub/PyPI release flow

## Contributing

Contributions are welcome, especially changes that improve the public runtime API,
embedded workbench behavior, packaging flow, and documentation.

For local development:

```bash
pip install -e ".[dev]"
python -m pytest
python -m build --sdist --wheel
python -m twine check dist/*
```

When adding regression coverage, prefer behavior-focused tests over brittle UI
snapshots. The most useful tests in this repository usually validate:

- public API behavior
- graph compile and execution paths
- theme override normalization and generated CSS contracts
- extension and registration hooks

This repository uses conventional commits and semantic versioning. Pull request
titles and merge commits should follow the same convention, for example:

- `feat: add preview regression coverage`
- `fix: preserve theme override aliases`
- `docs: clarify embedded host setup`

In general:

- use `feat:` for user-visible capabilities or meaningful public API expansion
- use `fix:` or `perf:` for patch-level runtime changes
- add or update focused regression tests when changing behavior that users rely on

## Packaging and release

Build distributions locally with:

```bash
python -m build --sdist --wheel
python -m twine check dist/*
```

This repository includes GitHub Actions workflows for CI, conventional-commit
enforcement, semantic versioned GitHub releases, and trusted publisher releases
to PyPI. See `docs/releasing.md` for the operational flow.

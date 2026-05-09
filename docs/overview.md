# Acherion Overview

Acherion is a NiceGUI-based visual programming environment that compiles
node-based graphs into Python source code. It is designed to support two main
deployment styles:

- standalone use through the packaged `acherion` application
- embedding inside a larger NiceGUI application through reusable workbench and
  host abstractions

## Architecture

The package has three practical layers.

### Core graph/runtime API

The top-level `acherion` package exposes the framework-agnostic pieces:

- `AcherionGraph` and `AcherionNode` for persistence and programmatic control
- registry and node-definition helpers for palette/runtime metadata
- compiler/runtime helpers such as `compile_acherion_graph` and
  `execute_acherion_graph`
- host contracts like `AcherionHost` and `compose_acherion_host`
- preview, validation, and external-event helpers

Use this layer when you need to persist graphs, compile them, execute generated
handlers, or wire Acherion into a host application.

### NiceGUI embedding layer

The `acherion.embed` package contains the UI components used by both embedded
and standalone modes:

- `AcherionDesigner` is the visual graph editor
- `AcherionWorkbench` wraps the designer with a code pane and common callbacks
- code-editor and schema-field helpers support host customization

### Standalone host

The standalone app composes the shared workbench with `StandaloneAcherionHost`.
That host provides a generic runtime with a default `run` external event and a
graph-to-Python compilation path suitable for local experimentation.

## Main capabilities

### Visual graph editing

The designer maintains a serializable `AcherionGraph`, supports palette-driven
node creation, keeps preview state separate from persisted graph state, and
offers graph/code presentation modes through the workbench shell.

### Python code generation

Hosts decide how graphs become code. The bundled standalone host compiles a
graph into Python functions, emits one handler per external event, and injects
runtime metadata such as `ACHERION_EXTERNAL_EVENTS`.

### Preview execution

Previews are driven by scoped bindings and return an
`AcherionPreviewRunResult`, which carries:

- `reference_values` keyed by opaque runtime references for node previews
- `state_values` keyed by host-defined metadata such as preview hints

### Persistence

The designer intentionally separates persisted graph state from transient
preview state:

- persist with `designer.to_dict()`
- restore with `designer.set_graph_from_dict(...)`
- access the normalized snapshot with `designer.graph_state()`

## Built-in node surface

The shared registry groups node definitions into palette categories. The current
built-in distribution centers around these categories:

- `source` for runtime/event inputs
- `compute` for values, arithmetic, comparisons, and logic
- `flow` for execution routing and iteration
- `object` for function calls, attributes, and object interaction
- `composite` for custom functions and function-box behavior

`ui` and `effect` are part of the category model but are not yet populated by a
substantial built-in set in this repository.

## When to use each entry point

Use `acherion` directly when you need to:

- manipulate or serialize graphs
- compile graphs into Python source
- execute generated code programmatically
- register catalogs, preview adapters, or validation extensions

Use `acherion.embed` when you need to:

- render the designer in a NiceGUI page
- add a generated-code pane or custom code viewer
- hook graph changes into your own persistence or runtime flow

Use `acherion.app` or the `acherion` console script when you need a ready-made
standalone workbench for experimentation or host integration testing.
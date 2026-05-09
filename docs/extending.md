# Extending Acherion

Acherion exposes several registration hooks that let hosts adapt the catalog,
preview behavior, validation environment, and node metadata.

## Catalog modules

Use `register_catalog_module_specs` to add Python modules to the callable object
catalog.

```python
from acherion import CatalogModuleSpec, CatalogScanSpec, register_catalog_module_specs


register_catalog_module_specs((
    CatalogModuleSpec(
        key='statistics',
        label='statistics',
        import_path='statistics',
        scans=(CatalogScanSpec(prefix='statistics.'),),
        path_prefixes=('statistics.',),
    ),
), replace=False)
```

Catalog module specs are the safest extension point for exposing extra Python
functions without inventing new node kinds.

## Preview value adapters

Preview adapters control how runtime values are summarized and typed in the UI.

```python
from acherion import AcherionPreviewValueAdapter, register_preview_value_adapter


register_preview_value_adapter(
    AcherionPreviewValueAdapter(
        name='bytes-preview',
        matcher=lambda value: isinstance(value, bytes),
        summary=lambda value: f'bytes[{len(value)}]',
        type_tag=lambda _value: 'bytes',
    )
)
```

## Validation extensions

Validation extensions add runtime globals and reserved names that are available
to custom-function validation.

```python
from acherion import AcherionValidationExtension, register_acherion_validation_extension


register_acherion_validation_extension(
    AcherionValidationExtension(
        name='numpy-validation',
        protected_names=frozenset({'np'}),
        runtime_global_loaders={'np': lambda: __import__('numpy')},
    )
)
```

## External events

Hosts can extend the graph runtime with extra external events.

```python
from acherion import (
    AcherionExternalEvent,
    compose_acherion_external_events,
)


events = compose_acherion_external_events({
    'save': AcherionExternalEvent(
        event_key='save',
        title='Event: Save',
        handler_name='on_save',
        description='Host save request.',
    ),
})
```

For component-style events, use `build_component_external_event` to normalize
keys and handler names.

## Node definitions

You can register node definitions with `register_acherion_node_definition`, but
that only updates the registry and palette metadata. A custom node kind also
needs compiler/runtime support from your host.

That means a complete custom-node implementation usually involves two parts:

1. register the node metadata and editor behavior
2. ensure your host/compiler knows how to emit code for that kind

If you only need to expose more callable Python functionality, prefer catalog
module specs over entirely new node kinds.

## Replacing or disabling built-ins

The shared registry also supports:

- `disable_acherion_node_kind`
- `enable_acherion_node_kind`
- `set_acherion_disabled_node_kinds`

Those are useful when you want to ship a more tightly-scoped host experience.
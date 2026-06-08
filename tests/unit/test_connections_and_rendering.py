"""Unit tests for source-id and render-pin helpers."""

from __future__ import annotations

import pytest

import acherion.graphops.catalog as acherion_graphops_catalog
import acherion.graphops.connections as acherion_graphops_connections
import acherion.graphops.ops as acherion_graphops_ops
import acherion.graphops.pins as acherion_graphops_pins
import acherion.model as acherion_model
import acherion.registry as acherion_registry

import tests.helpers as test_helpers

pytestmark = pytest.mark.unit


class _DeleteNodeOwner(
    acherion_graphops_ops._GraphOpsMixin,
    acherion_graphops_catalog._GraphOpsCatalogMixin,
    acherion_graphops_connections._GraphOpsConnectionsMixin,
    acherion_graphops_pins._GraphOpsPinsMixin,
    test_helpers._GraphOwnerBase,
):
    """Small graph owner for exercising real node deletion behavior."""

    def __init__(self, graph: acherion_model.AcherionGraph) -> None:
        test_helpers._GraphOwnerBase.__init__(self, graph)
        self._host = None
        self._pending_source_node_id = None
        self.change_count = 0

    def _is_system_node(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _is_system_source_node(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _is_system_sink_node(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _is_function_entry(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _is_function_box(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _function_parent_id(self, node: acherion_model.AcherionNode) -> str:
        del node
        return ""

    def _ensure_function_box_entries(self) -> None:
        return

    def _sync_function_box_ports(self) -> None:
        return

    def _cleanup_custom_function_entries(self) -> None:
        return

    def _prune_box_io_metadata(
        self,
        node: acherion_model.AcherionNode,
    ) -> None:
        del node
        return

    def _notify_change(self) -> None:
        self.change_count += 1


class _PatchConnectionOwner(
    acherion_graphops_connections._GraphOpsConnectionsMixin,
    acherion_graphops_pins._GraphOpsPinsMixin,
    test_helpers._GraphOwnerBase,
):
    """Small owner that exposes the browser-side connection patch hook."""

    def __init__(self, graph: acherion_model.AcherionGraph) -> None:
        test_helpers._GraphOwnerBase.__init__(self, graph)
        self._preview_reference_values = {}
        self._pending_source_node_id: str | None = None
        self._graph_cache_revision = 1
        self._connection_specs_cache_revision = -1
        self._connection_specs_cache = None
        self._outgoing_source_refs_cache = set()
        self._input_pin_specs_cache = {}
        self._output_pin_specs_cache = {}
        self.patches: list[dict[str, object]] = []
        self.notify_core_calls: list[dict[str, object]] = []
        self.change_count = 0
        self.refresh_count = 0
        self.ui_state_changes: list[dict[str, object]] = []

    @staticmethod
    def _connection_id(
        target_node_id: str,
        pin_id: str,
        *,
        source_id: str = "",
    ) -> str:
        if pin_id == "exec_source" and source_id:
            return f"{target_node_id}@@{pin_id}@@{source_id}"
        return f"{target_node_id}@@{pin_id}"

    def _invalidate_graph_render_caches(self) -> None:
        self._graph_cache_revision += 1
        self._connection_specs_cache_revision = -1
        self._connection_specs_cache = None
        self._outgoing_source_refs_cache = set()
        self._input_pin_specs_cache = {}
        self._output_pin_specs_cache = {}

    def _apply_client_connection_patch(self, patch: dict[str, object]) -> None:
        self.patches.append(patch)

    def _notify_change_core(
        self,
        *,
        refresh_graph: bool,
        emit_callback: bool,
        graph_changed: bool = True,
        sync_client: bool = True,
    ) -> None:
        self.notify_core_calls.append(
            {
                "refresh_graph": refresh_graph,
                "emit_callback": emit_callback,
                "graph_changed": graph_changed,
                "sync_client": sync_client,
            }
        )

    def _notify_change(self) -> None:
        self.change_count += 1

    def refresh(self) -> None:
        self.refresh_count += 1

    def _notify_ui_state_change(
        self,
        *,
        refresh_graph: bool = False,
    ) -> None:
        self.ui_state_changes.append({"refresh_graph": refresh_graph})


class _RerouteInsertOwner(
    acherion_graphops_ops._GraphOpsMixin,
    acherion_graphops_connections._GraphOpsConnectionsMixin,
    acherion_graphops_pins._GraphOpsPinsMixin,
    test_helpers._GraphOwnerBase,
):
    """Small owner for exercising wire-splitting reroute insertion."""

    def __init__(self, graph: acherion_model.AcherionGraph) -> None:
        test_helpers._GraphOwnerBase.__init__(self, graph)
        self._host = None
        self._pending_source_node_id = None
        self._selected_connection_id = None
        self._preview_reference_values = {}
        self._graph_cache_revision = 1
        self._connection_specs_cache_revision = -1
        self._connection_specs_cache = None
        self._outgoing_source_refs_cache = set()
        self._input_pin_specs_cache = {}
        self._output_pin_specs_cache = {}
        self.change_count = 0

    @staticmethod
    def _connection_id(
        target_node_id: str,
        pin_id: str,
        *,
        source_id: str = "",
    ) -> str:
        if pin_id == "exec_source" and source_id:
            return f"{target_node_id}@@{pin_id}@@{source_id}"
        return f"{target_node_id}@@{pin_id}"

    def _resolve_centered_manual_position(
        self,
        node: acherion_model.AcherionNode,
        *,
        center_x: int,
        center_y: int,
    ) -> tuple[int, int]:
        del node
        return (center_x - 37, center_y - 15)

    def _containing_function_box_id(self, center_x: int, center_y: int) -> str:
        del center_x, center_y
        return ""

    def _is_system_node(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _is_system_source_node(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _is_system_sink_node(self, node: acherion_model.AcherionNode) -> bool:
        del node
        return False

    def _ensure_function_box_entries(self) -> None:
        return

    def _sync_function_box_ports(self) -> None:
        return

    @staticmethod
    def _full_output_source_id(
        node: acherion_model.AcherionNode,
        pin_index: int,
    ) -> str:
        return f"{node.node_id}@{pin_index}"

    def _notify_change(self) -> None:
        self.change_count += 1


def test_render_source_ids_always_use_indexed_form() -> None:
    owner = test_helpers.RenderPinsOwner()

    assert (
        owner._full_output_source_id(
            acherion_model.AcherionNode(
                node_id="constant_1",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
            0,
        )
        == "constant_1@0"
    )


def test_prune_invalid_exec_connections_canonicalizes_old_plain_aliases() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="m1",
                kind="call_method",
                params={
                    "instance": "f1",
                    "method_name": "update_layout",
                    "arg_sources": [],
                    "exec_sources": ["f1@1"],
                },
            ),
            acherion_model.AcherionNode(
                node_id="a1",
                kind="get_attribute",
                params={
                    "instance": "m1",
                    "attribute_name": "layout",
                    "exec_sources": ["m1"],
                },
            ),
        ]
    )
    owner = test_helpers.ConnectionsOwner(graph)

    owner._prune_invalid_exec_connections()

    assert graph.nodes[1].params["exec_sources"] == ["m1@1"]


def test_connection_specs_cache_uses_graph_revision_and_outgoing_lookup() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
            *[
                acherion_model.AcherionNode(
                    node_id=f"consumer_{index}",
                    kind="op_arithmetic",
                    params={
                        "operator": "+",
                        "left_source": "source@0",
                        "right_source": "source@0",
                    },
                )
                for index in range(128)
            ],
        ]
    )
    owner = test_helpers.ConnectionsOwner(graph)
    owner._graph_cache_revision = 1
    owner._connection_specs_cache_revision = -1
    owner._connection_specs_cache = None
    owner._outgoing_source_refs_cache = set()
    owner._connection_id = (  # type: ignore[attr-defined]
        lambda target_node_id, pin_id, *, source_id="": (
            f"{target_node_id}@@{pin_id}@@{source_id}"
            if pin_id == "exec_source" and source_id
            else f"{target_node_id}@@{pin_id}"
        )
    )

    first_specs = owner._connection_specs()
    second_specs = owner._connection_specs()

    assert first_specs is second_specs
    assert len(first_specs) == 256
    assert owner._has_outgoing_connection("source@0") is True
    assert owner._has_outgoing_connection("missing@0") is False


def test_connect_input_pin_uses_client_patch_without_full_refresh() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="old_source",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 2},
            ),
            acherion_model.AcherionNode(
                node_id="target",
                kind="op_arithmetic",
                params={
                    "operator": "+",
                    "left_source": "old_source@0",
                    "right_source": "",
                },
            ),
        ]
    )
    owner = _PatchConnectionOwner(graph)
    owner._pending_source_node_id = "source@0"

    owner._connect_input_pin(graph.nodes[2], "left_source")

    assert graph.nodes[2].params["left_source"] == "source@0"
    assert owner.refresh_count == 0
    assert owner.change_count == 0
    assert owner.notify_core_calls == [
        {
            "refresh_graph": False,
            "emit_callback": True,
            "graph_changed": True,
            "sync_client": False,
        }
    ]
    assert len(owner.patches) == 1
    patch = owner.patches[0]
    assert patch["remove_connection_ids"] == ["target@@left_source"]
    assert patch["add_connections"] == [
        {
            "connection_id": "target@@left_source",
            "source_node_id": "source",
            "target_node_id": "target",
            "output_index": 0,
            "input_index": 0,
            "style_tag": "any",
        }
    ]


def test_start_connection_uses_ui_state_sync_without_full_refresh() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
        ]
    )
    owner = _PatchConnectionOwner(graph)

    owner._start_connection("source@0")

    assert owner._pending_source_node_id == "source@0"
    assert owner.refresh_count == 0
    assert owner.ui_state_changes == [{"refresh_graph": False}]


def test_insert_data_reroute_splits_existing_connection() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 2},
            ),
            acherion_model.AcherionNode(
                node_id="target",
                kind="op_unary",
                params={"operator": "negate", "source": "source@0"},
            ),
        ]
    )
    owner = _RerouteInsertOwner(graph)

    owner._insert_reroute_on_connection(
        "target@@source",
        center_x=120,
        center_y=80,
    )

    reroute = graph.nodes[-1]
    assert reroute.kind == "reroute"
    assert reroute.params["source"] == "source@0"
    assert graph.nodes[1].params["source"] == f"{reroute.node_id}@0"
    assert owner.change_count == 1


def test_insert_exec_reroute_splits_existing_connection() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="branch",
                kind="branch_route",
                params={"condition_source": ""},
            ),
            acherion_model.AcherionNode(
                node_id="target",
                kind="custom_function",
                params={
                    "function_path": "user.mark",
                    "arg_sources": [],
                    "exec_sources": ["branch@0"],
                },
            ),
        ]
    )
    owner = _RerouteInsertOwner(graph)

    owner._insert_reroute_on_connection(
        "target@@exec_source@@branch@0",
        center_x=160,
        center_y=96,
    )

    reroute = graph.nodes[-1]
    assert reroute.kind == "exec_reroute"
    assert reroute.params["exec_sources"] == ["branch@0"]
    assert graph.nodes[1].params["exec_sources"] == [f"{reroute.node_id}@0"]
    assert owner.change_count == 1


def test_insert_data_reroute_from_pending_source_keeps_connection_pending() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 2},
            ),
        ]
    )
    owner = _RerouteInsertOwner(graph)
    owner._pending_source_node_id = "source@0"

    owner._insert_reroute_from_pending_source(center_x=120, center_y=80)

    reroute = graph.nodes[-1]
    assert reroute.kind == "reroute"
    assert reroute.params["source"] == "source@0"
    assert owner._pending_source_node_id == f"{reroute.node_id}@0"
    assert owner.change_count == 1


def test_insert_exec_reroute_from_pending_source_keeps_connection_pending() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="branch",
                kind="branch_route",
                params={"condition_source": ""},
            ),
        ]
    )
    owner = _RerouteInsertOwner(graph)
    owner._pending_source_node_id = "branch@0"

    owner._insert_reroute_from_pending_source(center_x=120, center_y=80)

    reroute = graph.nodes[-1]
    assert reroute.kind == "exec_reroute"
    assert reroute.params["exec_sources"] == ["branch@0"]
    assert owner._pending_source_node_id == f"{reroute.node_id}@0"
    assert owner.change_count == 1


def test_delete_node_clears_data_refs_to_removed_output_node() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
            acherion_model.AcherionNode(
                node_id="left",
                kind="constant",
                params={"value_type": "int", "number_value": 2},
            ),
            acherion_model.AcherionNode(
                node_id="target",
                kind="op_arithmetic",
                params={
                    "operator": "+",
                    "left_source": "source@0",
                    "right_source": "left",
                },
            ),
            acherion_model.AcherionNode(
                node_id="list",
                kind="make_list",
                params={
                    "arg_count": 2,
                    "arg_sources": ["source@0", "left"],
                },
            ),
        ]
    )
    owner = _DeleteNodeOwner(graph)

    owner._delete_node("source")

    remaining = {node.node_id: node for node in graph.nodes}
    assert set(remaining) == {"left", "target", "list"}
    assert remaining["target"].params["left_source"] == ""
    assert remaining["target"].params["right_source"] == "left"
    assert remaining["list"].params["arg_sources"] == ["", "left"]
    assert owner.change_count == 1


def test_delete_nodes_batch_clears_data_refs_to_removed_output_nodes() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
            acherion_model.AcherionNode(
                node_id="other_source",
                kind="constant",
                params={"value_type": "int", "number_value": 2},
            ),
            acherion_model.AcherionNode(
                node_id="target",
                kind="plot_figure",
                params={
                    "figure_type": "scatter",
                    "named_sources": {
                        "x": "source@0",
                        "y": "other_source",
                    },
                },
            ),
        ]
    )
    owner = _DeleteNodeOwner(graph)

    owner._delete_nodes_batch({"source"})

    remaining = {node.node_id: node for node in graph.nodes}
    assert set(remaining) == {"other_source", "target"}
    assert remaining["target"].params["named_sources"]["x"] == ""
    assert remaining["target"].params["named_sources"]["y"] == "other_source"
    assert owner.change_count == 1


def test_clear_node_pins_clears_incoming_outgoing_exec_and_literals() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id="source",
                kind="constant",
                params={"value_type": "int", "number_value": 1},
            ),
            acherion_model.AcherionNode(
                node_id="other",
                kind="constant",
                params={"value_type": "int", "number_value": 2},
            ),
            acherion_model.AcherionNode(
                node_id="math",
                kind="op_arithmetic",
                params={
                    "operator": "+",
                    "left_source": "source@0",
                    "right_source": "other@0",
                    "pin_literals": {"left_source": 10},
                },
            ),
            acherion_model.AcherionNode(
                node_id="branch",
                kind="branch_route",
                params={
                    "condition_source": "source@0",
                    "pin_literals": {"condition_source": False},
                },
            ),
            acherion_model.AcherionNode(
                node_id="consumer",
                kind="op_arithmetic",
                params={
                    "operator": "+",
                    "left_source": "math@0",
                    "right_source": "other@0",
                },
            ),
            acherion_model.AcherionNode(
                node_id="setter",
                kind="set_attribute",
                params={
                    "exec_sources": ["branch@0", "branch@1"],
                    "instance": "math@0",
                    "attribute_name": "value",
                    "value": "other@0",
                },
            ),
        ]
    )
    owner = _DeleteNodeOwner(graph)

    changed = owner._clear_node_pins({"math", "branch"})

    nodes = {node.node_id: node for node in graph.nodes}
    assert changed is True
    assert nodes["math"].params["left_source"] == ""
    assert nodes["math"].params["right_source"] == ""
    assert "pin_literals" not in nodes["math"].params
    assert nodes["branch"].params["condition_source"] == ""
    assert "pin_literals" not in nodes["branch"].params
    assert nodes["consumer"].params["left_source"] == ""
    assert nodes["consumer"].params["right_source"] == "other@0"
    assert nodes["setter"].params["exec_sources"] == []
    assert nodes["setter"].params["instance"] == ""
    assert nodes["setter"].params["value"] == "other@0"
    assert owner.change_count == 0


def test_int_typed_pin_literals_are_coerced_before_preview_runtime() -> None:
    renderer = test_helpers.PinLiteralRenderer()
    node = acherion_model.AcherionNode(
        node_id="call",
        kind="call_function",
        params={"pin_literals": {}},
    )

    renderer._set_pin_literal_value(
        node,
        pin_id="arg:2",
        input_kind="number",
        pin_type="int",
        value=250.0,
    )
    renderer._set_pin_literal_value(
        node,
        pin_id="arg:3",
        input_kind="number",
        pin_type="float",
        value=2,
    )

    assert node.params["pin_literals"]["arg:2"] == 250
    assert isinstance(node.params["pin_literals"]["arg:2"], int)
    assert node.params["pin_literals"]["arg:3"] == 2.0
    assert isinstance(node.params["pin_literals"]["arg:3"], float)
    assert renderer.change_count == 2


def test_bool_typed_pin_literals_preserve_false_values() -> None:
    renderer = test_helpers.PinLiteralRenderer()
    node = acherion_model.AcherionNode(
        node_id="branch",
        kind="else_if_branch",
        params={"pin_literals": {}},
    )

    renderer._set_pin_literal_value(
        node,
        pin_id="condition:0",
        input_kind="bool",
        pin_type="bool",
        value=False,
    )
    renderer._set_pin_literal_value(
        node,
        pin_id="condition:1",
        input_kind="bool",
        pin_type="bool",
        value=True,
    )

    assert node.params["pin_literals"]["condition:0"] is False
    assert node.params["pin_literals"]["condition:1"] is True
    assert renderer.change_count == 2


def test_dict_typed_pin_literals_store_dict_values() -> None:
    renderer = test_helpers.PinLiteralRenderer()
    node = acherion_model.AcherionNode(
        node_id="dict_get",
        kind="dict_get",
        params={"pin_literals": {}},
    )

    renderer._set_pin_literal_value(
        node,
        pin_id="source",
        input_kind="dict",
        pin_type="dict",
        value="{'alpha': 1}",
    )
    renderer._set_pin_literal_value(
        node,
        pin_id="fallback",
        input_kind="dict",
        pin_type="dict",
        value="not a dict",
    )

    assert node.params["pin_literals"]["source"] == {"alpha": 1}
    assert node.params["pin_literals"]["fallback"] == {}
    assert renderer.change_count == 2


def test_dict_get_output_pin_uses_preview_runtime_type() -> None:
    owner = test_helpers.RenderPinsOwner()
    owner._preview_reference_values = {"dict_get": 2}
    node = acherion_model.AcherionNode(
        node_id="dict_get",
        kind="dict_get",
        params={},
    )

    assert owner._output_pin_specs(node)[0]["type"] == "int"


def test_list_nodes_expose_index_and_slice_bounds_as_int_pins() -> None:
    owner = test_helpers.RenderPinsOwner()
    get_index = acherion_model.AcherionNode(
        node_id="get",
        kind="list_index",
        params={"mode": "index"},
    )
    set_slice = acherion_model.AcherionNode(
        node_id="set",
        kind="list_set",
        params={"mode": "slice"},
    )

    get_pins = owner._input_pin_specs(get_index)
    set_pins = owner._input_pin_specs(set_slice)

    assert [(pin["pin_id"], pin["type"]) for pin in get_pins] == [
        ("source", "list"),
        ("index", "int"),
    ]
    assert [(pin["pin_id"], pin["type"]) for pin in set_pins] == [
        ("source", "list"),
        ("value", "any"),
        ("start", "int"),
        ("stop", "int"),
        ("step", "int"),
    ]


def test_boolean_logic_pins_are_typed_for_checkbox_fallbacks() -> None:
    owner = test_helpers.RenderPinsOwner()
    logic = acherion_model.AcherionNode(
        node_id="logic",
        kind="op_logic",
        params={"operator": "and"},
    )
    op_not = acherion_model.AcherionNode(
        node_id="not",
        kind="op_not",
        params={},
    )
    compare = acherion_model.AcherionNode(
        node_id="compare",
        kind="compare",
        params={},
    )

    assert [pin["type"] for pin in owner._input_pin_specs(logic)] == [
        "bool",
        "bool",
    ]
    assert owner._output_pin_specs(logic)[0]["type"] == "bool"
    assert owner._input_pin_specs(op_not)[0]["type"] == "bool"
    assert owner._output_pin_specs(op_not)[0]["type"] == "bool"
    assert owner._output_pin_specs(compare)[0]["type"] == "bool"


def test_constant_inline_default_spec_exposes_bool_and_dict_values() -> None:
    definition = acherion_registry.get_acherion_node_definition("constant")
    assert definition is not None

    bool_node = acherion_model.AcherionNode(
        node_id="bool",
        kind="constant",
        params={"value_type": "bool", "bool_value": True},
    )
    dict_node = acherion_model.AcherionNode(
        node_id="dict",
        kind="constant",
        params={"value_type": "dict", "dict_value": "{'alpha': 1}"},
    )

    assert definition.inline_default_editor_spec(bool_node) == (
        "bool",
        "bool_value",
        True,
    )
    assert definition.inline_default_editor_spec(dict_node) == (
        "dict",
        "dict_value",
        "{'alpha': 1}",
    )


def test_else_if_branch_uses_bool_conditions_and_shifted_exec_rows() -> None:
    owner = test_helpers.RenderPinsOwner()
    node = acherion_model.AcherionNode(
        node_id="branch",
        kind="else_if_branch",
        params={"condition_count": 3},
    )

    condition_pins = [
        pin
        for pin in owner._input_pin_specs(node)
        if pin["pin_id"].startswith("condition:")
    ]
    output_pins = owner._output_pin_specs(node)

    assert [pin["type"] for pin in condition_pins] == ["bool", "bool", "bool"]
    assert [pin["label"] for pin in output_pins] == [
        "If Cond 1",
        "Else if Cond 2",
        "Else if Cond 3",
        "Else",
    ]
    assert owner._body_pin_row_count(node) == 3
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=1,
        )
        == 0
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=3,
        )
        == 2
    )


def test_for_each_exec_outputs_use_shifted_rows() -> None:
    owner = test_helpers.RenderPinsOwner()
    node = acherion_model.AcherionNode(
        node_id="for_each",
        kind="for_each",
        params={"list": ""},
    )

    input_pins = owner._input_pin_specs(node)
    output_pins = owner._output_pin_specs(node)

    assert input_pins[0]["pin_id"] == "list"
    assert input_pins[1]["pin_id"] == "exec_source"
    assert [pin["label"] for pin in output_pins] == [
        "item",
        "index",
        "Loop Body",
        "Completed",
    ]
    assert owner._body_pin_row_count(node) == 3
    assert (
        owner._body_pin_row_index(
            node,
            direction="in",
            pin_index=0,
        )
        == 0
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=2,
        )
        == 0
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=3,
        )
        == 0
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=0,
        )
        == 1
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=1,
        )
        == 2
    )


def test_sequencer_exec_outputs_use_shifted_rows() -> None:
    owner = test_helpers.RenderPinsOwner()
    node = acherion_model.AcherionNode(
        node_id="sequence",
        kind="sequencer",
        params={"then_count": 4},
    )

    input_pins = owner._input_pin_specs(node)
    output_pins = owner._output_pin_specs(node)

    assert input_pins[0]["pin_id"] == "exec_source"
    assert [pin["label"] for pin in output_pins] == [
        "Then 1",
        "Then 2",
        "Then 3",
        "Then 4",
    ]
    assert owner._body_pin_row_count(node) == 3
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=0,
        )
        == 0
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=1,
        )
        == 0
    )
    assert (
        owner._body_pin_row_index(
            node,
            direction="out",
            pin_index=3,
        )
        == 2
    )

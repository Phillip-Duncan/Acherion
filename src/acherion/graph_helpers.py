"""Graph compilation and source-reference helpers."""

from __future__ import annotations

from typing import Any


def pure_source_id(source_id: str) -> str:
    """Return the node-id portion of a source reference."""
    text = str(source_id or '')
    return text.split('@', 1)[0] if '@' in text else text


def source_pin_index(source_id: str) -> int:
    """Return the output pin index encoded in a source id."""
    text = str(source_id or '')
    if '@' not in text:
        return 0
    try:
        return int(text.split('@', 1)[1] or 0)
    except ValueError:
        return 0


def normalize_exec_sources(value: object) -> list[str]:
    """Return cleaned exec-source ids from stored list/string data."""
    if isinstance(value, str):
        cleaned = str(value or '').strip()
        return [cleaned] if cleaned else []
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw_source in value:
        cleaned = str(raw_source or '').strip()
        if not cleaned or cleaned in seen:
            continue
        out.append(cleaned)
        seen.add(cleaned)
    return out


def iter_param_sources(
    params: dict[str, Any],
    source_param_ids: list[str],
) -> list[str]:
    """Return all source-id strings referenced by stored node params."""
    out: list[str] = []
    for source_id in list(params.get('arg_sources') or []):
        if source_id:
            out.append(str(source_id))
    for source_id in dict(params.get('box_input_sources') or {}).values():
        if source_id:
            out.append(str(source_id))
    for source_id in dict(params.get('named_sources') or {}).values():
        if source_id:
            out.append(str(source_id))
    for param_id in source_param_ids:
        source_id = str(params.get(param_id) or '').strip()
        if source_id:
            out.append(source_id)
    return out


def add_missing_pass(lines: list[str]) -> list[str]:
    """Insert pass after any block header that has no indented body."""
    result: list[str] = []
    for i, line in enumerate(lines):
        result.append(line)
        if not line.rstrip().endswith(':') or not line.strip():
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        header_indent = len(line) - len(line.lstrip())
        if j >= len(lines):
            result.append(' ' * (header_indent + 4) + 'pass')
        else:
            next_indent = len(lines[j]) - len(lines[j].lstrip())
            if next_indent <= header_indent:
                result.append(' ' * (header_indent + 4) + 'pass')
    return result


def build_exec_targets(
    records: list[tuple[str, object]],
) -> list[tuple[str, list[str]]]:
    """Build ordered source-id to target-node-id fan-in entries."""
    targets: dict[str, list[str]] = {}
    for node_id, raw_sources in records:
        for source_id in normalize_exec_sources(raw_sources):
            targets.setdefault(source_id, []).append(str(node_id))
    return [(source_id, node_ids) for source_id, node_ids in targets.items()]


_BoundaryRecord = tuple[str, str, str, dict[str, Any], list[str]]


def _record_sources(record: _BoundaryRecord) -> list[str]:
    _node_id, _kind, _parent_id, params, source_param_ids = record
    return iter_param_sources(params, source_param_ids)


def _node_has_function_ancestor(
    node_id: str,
    ancestor_box_id: str,
    records_by_id: dict[str, _BoundaryRecord],
) -> bool:
    seen: set[str] = set()
    current = records_by_id.get(node_id)
    while current is not None:
        parent_id = current[2]
        if not parent_id or parent_id in seen:
            return False
        if parent_id == ancestor_box_id:
            return True
        seen.add(parent_id)
        current = records_by_id.get(parent_id)
    return False


def _fallback_function_box_boundary_sources(
    records: list[_BoundaryRecord],
    box_node_id: str,
) -> tuple[list[str], list[str]]:
    records_by_id = {record[0]: record for record in records}
    input_sources: list[str] = []
    output_sources: list[str] = []
    seen_input_sources: set[str] = set()
    seen_output_sources: set[str] = set()

    for record in records:
        node_id, kind, _parent_id, _params, _source_param_ids = record
        if kind in {'function_input', 'function_output'}:
            continue
        node_inside = _node_has_function_ancestor(
            node_id,
            box_node_id,
            records_by_id,
        )
        if node_inside:
            for source_id in _record_sources(record):
                pure_id = pure_source_id(source_id)
                if not pure_id or source_id in seen_input_sources:
                    continue
                source_record = records_by_id.get(pure_id)
                if source_record is None or source_record[0] == box_node_id:
                    continue
                if _node_has_function_ancestor(
                    source_record[0],
                    box_node_id,
                    records_by_id,
                ):
                    continue
                seen_input_sources.add(source_id)
                input_sources.append(source_id)
            continue

        for source_id in _record_sources(record):
            pure_id = pure_source_id(source_id)
            if not pure_id or source_id in seen_output_sources:
                continue
            source_record = records_by_id.get(pure_id)
            if source_record is None:
                continue
            if not _node_has_function_ancestor(
                source_record[0],
                box_node_id,
                records_by_id,
            ):
                continue
            seen_output_sources.add(source_id)
            output_sources.append(source_id)
    return input_sources, output_sources


def function_box_boundary_sources(
    records: list[_BoundaryRecord],
    box_node_id: str,
) -> tuple[list[str], list[str]]:
    """Return sources crossing into and out of one function box."""
    return _fallback_function_box_boundary_sources(
        records,
        str(box_node_id or ''),
    )

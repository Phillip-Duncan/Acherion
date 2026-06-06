"""Graph JavaScript for the Acherion render surface."""

from __future__ import annotations

GRAPH_JS = """
        selectorLiteral(value) {
            return JSON.stringify(String(value ?? '')).slice(1, -1);
        },
        pinLookupKey(nodeId, direction, pinIndex) {
            return [
                String(nodeId ?? ''),
                String(direction ?? ''),
                String(pinIndex ?? ''),
            ].join('|');
        },
        connectionPaths(stage, nodeIds) {
            if (!stage) return [];
            if (nodeIds === undefined || nodeIds === null) {
                return Array.from(stage.querySelectorAll('[data-connection-id]'));
            }
            if (!nodeIds.size) return [];
            const seen = new Set();
            const paths = [];
            nodeIds.forEach(nodeId => {
                const selector =
                    '[data-source-node-id="'
                    + this.selectorLiteral(nodeId)
                    + '"],[data-target-node-id="'
                    + this.selectorLiteral(nodeId)
                    + '"]';
                stage.querySelectorAll(selector).forEach(path => {
                    if (seen.has(path)) return;
                    seen.add(path);
                    paths.push(path);
                });
            });
            return paths;
        },
        findNode(stage, nodeId) {
            if (!stage) return null;
            return stage.querySelector(
                '.ach-node[data-node-id="'
                + this.selectorLiteral(nodeId)
                + '"]'
            );
        },
        findPin(stage, nodeId, direction, pinIndex) {
            if (!stage) return null;
            return stage.querySelector(
                '.ach-pin-anchor[data-node-id="'
                + this.selectorLiteral(nodeId)
                + '"][data-pin-direction="'
                + this.selectorLiteral(direction)
                + '"][data-pin-index="'
                + this.selectorLiteral(pinIndex)
                + '"]'
            );
        },
        worldPoint(viewport, clientX, clientY) {
            const stage = this.stage(viewport);
            if (!stage) return {x: 0, y: 0};
            const rect = stage.getBoundingClientRect();
            const sc = this.scale(viewport);
            const origin = this.origin(stage);
            return {
                x: (clientX - rect.left) / sc - origin.x,
                y: (clientY - rect.top) / sc - origin.y,
            };
        },
        pinCenter(stage, nodeId, direction, pinIndex) {
            const viewport = stage.closest('.ach-shell');
            const sc = this.scale(viewport);
            const stageRect = stage.getBoundingClientRect();
            const pin = this.findPin(stage, nodeId, direction, pinIndex);
            if (!pin) return null;
            const rect = pin.getBoundingClientRect();
            return {
                x: (rect.left + rect.width / 2 - stageRect.left) / sc,
                y: (rect.top + rect.height / 2 - stageRect.top) / sc,
            };
        },
        curve(sx, sy, ex, ey) {
            const dist = Math.abs(ex - sx);
            const t = Math.max(96, Math.min(240, dist * 0.55 || 96));
            let c1 = sx + t;
            let c2 = ex - t;
            if (ex < sx) {
                const loop = Math.max(140, Math.min(300, (sx - ex) * 0.7 || 140));
                c1 = sx + loop;
                c2 = ex - loop;
            }
            return `M ${sx} ${sy} C ${c1} ${sy}, ${c2} ${ey}, ${ex} ${ey}`;
        },
        queueConnectionUpdate(stage) {
            if (!stage) return;
            if (stage.__oeAcherionDirtyConnectionNodeIds === undefined) {
                stage.__oeAcherionDirtyConnectionNodeIds = new Set();
            }
            const rawNodeIds = arguments.length > 1 ? arguments[1] : undefined;
            if (rawNodeIds === undefined || rawNodeIds === null) {
                stage.__oeAcherionDirtyConnectionNodeIds = null;
            } else if (stage.__oeAcherionDirtyConnectionNodeIds !== null) {
                const nextDirty = stage.__oeAcherionDirtyConnectionNodeIds;
                const values = Array.isArray(rawNodeIds) ? rawNodeIds : [rawNodeIds];
                values.forEach(nodeId => {
                    const cleanId = String(nodeId || '');
                    if (cleanId) nextDirty.add(cleanId);
                });
            }
            if (stage.__oeAcherionConnectionUpdateQueued) return;
            stage.__oeAcherionConnectionUpdateQueued = true;
            requestAnimationFrame(() => {
                const dirtyNodeIds = stage.__oeAcherionDirtyConnectionNodeIds;
                stage.__oeAcherionConnectionUpdateQueued = false;
                stage.__oeAcherionDirtyConnectionNodeIds = new Set();
                this.updateConnections(stage, dirtyNodeIds);
            });
        },
        updateConnections(stage) {
            if (!stage) return;
            const viewport = stage.closest('.ach-shell');
            if (!viewport) return;
            const sc = this.scale(viewport);
            const stageRect = stage.getBoundingClientRect();
            const pinCenters = new Map();
            const rawNodeIds = arguments.length > 1 ? arguments[1] : undefined;
            const paths = this.connectionPaths(stage, rawNodeIds);
            if (!paths.length) return;
            const pinCenter = (nodeId, direction, pinIndex) => {
                const key = this.pinLookupKey(nodeId, direction, pinIndex);
                if (pinCenters.has(key)) return pinCenters.get(key);
                const pin = this.findPin(stage, nodeId, direction, pinIndex);
                if (!pin) {
                    pinCenters.set(key, null);
                    return null;
                }
                const rect = pin.getBoundingClientRect();
                const center = {
                    x: (rect.left + rect.width / 2 - stageRect.left) / sc,
                    y: (rect.top + rect.height / 2 - stageRect.top) / sc,
                };
                pinCenters.set(key, center);
                return center;
            };
            paths.forEach(path => {
                const src = path.dataset.sourceNodeId || '';
                const tgt = path.dataset.targetNodeId || '';
                const inIdx = parseInt(path.dataset.inputIndex || '0', 10);
                const outIdx = parseInt(path.dataset.outputIndex || '0', 10);
                const sourcePin = pinCenter(src, 'out', outIdx);
                const targetPin = pinCenter(tgt, 'in', inIdx);
                if (!sourcePin || !targetPin) return;
                const nextPath = this.curve(
                    sourcePin.x,
                    sourcePin.y,
                    targetPin.x,
                    targetPin.y
                );
                if (path.getAttribute('d') !== nextPath) {
                    path.setAttribute('d', nextPath);
                }
            });
        },
        moveNode(stage, nodeId, left, top) {
            const node = this.findNode(stage, nodeId);
            if (!node) return;
            const origin = this.origin(stage);
            node.style.left = `${Math.round(left + origin.x)}px`;
            node.style.top = `${Math.round(top + origin.y)}px`;
            this.queueConnectionUpdate(stage, [nodeId]);
        },
        applySelectionState(stage, state) {
            if (!stage) return;
            const selectedNodeIds = new Set(
                Array.isArray(state?.selected_node_ids)
                    ? state.selected_node_ids.map(value => String(value || ''))
                    : []
            );
            const selectedConnectionId = String(
                state?.selected_connection_id || ''
            );
            stage.querySelectorAll('.ach-node').forEach(node => {
                const nodeId = node.dataset.nodeId || '';
                node.classList.toggle(
                    'ach-node-selected',
                    selectedNodeIds.has(nodeId)
                );
            });
            stage.querySelectorAll('.ach-link-path').forEach(path => {
                path.classList.toggle(
                    'ach-link-path-selected',
                    !!selectedConnectionId
                    && (path.dataset.connectionId || '') === selectedConnectionId
                );
            });
        },
        applyPendingConnectionState(stage, state) {
            if (!stage) return;
            stage.querySelectorAll('.ach-pin-btn-active').forEach(pin => {
                pin.classList.remove('ach-pin-btn-active');
            });
            stage.querySelectorAll('.ach-pin-incompatible').forEach(row => {
                row.classList.remove('ach-pin-incompatible');
            });
            const pendingNodeId = String(state?.pending_node_id || '');
            const pendingPinIndex = String(state?.pending_pin_index ?? '');
            if (pendingNodeId && pendingPinIndex) {
                const activePin = this.findPin(
                    stage,
                    pendingNodeId,
                    'out',
                    pendingPinIndex
                );
                if (activePin) activePin.classList.add('ach-pin-btn-active');
            }
            const incompatibleInputs = Array.isArray(state?.incompatible_inputs)
                ? state.incompatible_inputs
                : [];
            incompatibleInputs.forEach(item => {
                const nodeId = String(item?.node_id || '');
                const pinIndex = String(item?.pin_index ?? '');
                if (!nodeId || !pinIndex) return;
                const pin = this.findPin(stage, nodeId, 'in', pinIndex);
                const row = pin ? pin.closest('.ach-wire-row') : null;
                if (row) row.classList.add('ach-pin-incompatible');
            });
        },
        applyInteractionState(stage, state) {
            this.applySelectionState(stage, state);
            this.applyPendingConnectionState(stage, state);
        },
        ensureLinksSvg(stage) {
            if (!stage) return null;
            let svg = stage.querySelector('.ach-links');
            if (svg) return svg;
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.classList.add('ach-links');
            stage.insertBefore(svg, stage.firstChild);
            return svg;
        },
        refreshConnectionFillState(stage) {
            if (!stage) return;
            stage.querySelectorAll('.ach-pin-anchor').forEach(pin => {
                pin.classList.remove('ach-pin-btn-filled');
            });
            stage.querySelectorAll('.ach-link-path').forEach(path => {
                const src = path.dataset.sourceNodeId || '';
                const tgt = path.dataset.targetNodeId || '';
                const outIdx = path.dataset.outputIndex || '0';
                const inIdx = path.dataset.inputIndex || '0';
                const sourcePin = this.findPin(stage, src, 'out', outIdx);
                const targetPin = this.findPin(stage, tgt, 'in', inIdx);
                if (sourcePin) sourcePin.classList.add('ach-pin-btn-filled');
                if (targetPin) targetPin.classList.add('ach-pin-btn-filled');
            });
        },
        appendConnectionPath(svg, spec, hitbox) {
            const path = document.createElementNS(
                'http://www.w3.org/2000/svg',
                'path'
            );
            const styleTag = String(spec.style_tag || 'any');
            path.classList.add(
                hitbox ? 'ach-link-hitbox' : 'ach-link-path'
            );
            if (!hitbox) path.classList.add(`ach-link-path-type-${styleTag}`);
            path.dataset.connectionId = String(spec.connection_id || '');
            path.dataset.sourceNodeId = String(spec.source_node_id || '');
            path.dataset.outputIndex = String(spec.output_index ?? 0);
            path.dataset.targetNodeId = String(spec.target_node_id || '');
            path.dataset.inputIndex = String(spec.input_index ?? 0);
            path.setAttribute('d', '');
            svg.appendChild(path);
        },
        applyConnectionPatch(stage, patch) {
            if (!stage || !patch) return;
            const removeIds = Array.isArray(patch.remove_connection_ids)
                ? patch.remove_connection_ids
                : [];
            removeIds.forEach(rawId => {
                const connectionId = String(rawId || '');
                if (!connectionId) return;
                const selector = '[data-connection-id="'
                    + this.selectorLiteral(connectionId)
                    + '"]';
                stage.querySelectorAll(selector).forEach(path => path.remove());
            });
            const added = Array.isArray(patch.add_connections)
                ? patch.add_connections
                : [];
            if (added.length) {
                const svg = this.ensureLinksSvg(stage);
                if (svg) {
                    added.forEach(spec => {
                        this.appendConnectionPath(svg, spec, false);
                        this.appendConnectionPath(svg, spec, true);
                    });
                }
            }
            this.queueConnectionUpdate(stage);
            this.refreshConnectionFillState(stage);
            if (patch.state) this.applyInteractionState(stage, patch.state);
        },
        updateRubberBand(vp, x1, y1, x2, y2) {
            let rb = vp.querySelector('.ach-rubber-band');
            if (!rb) {
                rb = document.createElement('div');
                rb.className = 'ach-rubber-band';
                vp.appendChild(rb);
            }
            const stage = this.stage(vp);
            if (!stage) return;
            const sc = this.scale(vp);
            const origin = this.origin(stage);
            const sr = stage.getBoundingClientRect();
            const vr = vp.getBoundingClientRect();
            const sx = (Math.min(x1, x2) + origin.x) * sc + (sr.left - vr.left);
            const sy = (Math.min(y1, y2) + origin.y) * sc + (sr.top - vr.top);
            rb.style.display = 'block';
            rb.style.left = sx + 'px';
            rb.style.top = sy + 'px';
            rb.style.width = (Math.abs(x2 - x1) * sc) + 'px';
            rb.style.height = (Math.abs(y2 - y1) * sc) + 'px';
        },
        clearRubberBand(vp) {
            const rb = vp.querySelector('.ach-rubber-band');
            if (rb) rb.style.display = 'none';
        },
        nodesInRect(stage, x1, y1, x2, y2) {
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            const minY = Math.min(y1, y2);
            const maxY = Math.max(y1, y2);
            const origin = this.origin(stage);
            const ids = [];
            stage.querySelectorAll('.ach-node').forEach(node => {
                const nodeLeft = parseFloat(node.style.left || '0');
                const nodeTop = parseFloat(node.style.top || '0');
                const centerX = nodeLeft - origin.x + node.offsetWidth / 2;
                const centerY = nodeTop - origin.y + node.offsetHeight / 2;
                if (centerX >= minX && centerX <= maxX && centerY >= minY && centerY <= maxY)
                    ids.push(node.dataset.nodeId);
            });
            return ids;
        },
"""

__all__ = ['GRAPH_JS']

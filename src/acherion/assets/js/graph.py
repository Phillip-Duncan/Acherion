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
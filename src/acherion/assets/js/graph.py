"""Graph JavaScript for the Acherion render surface."""

from __future__ import annotations

GRAPH_JS = """
        findNode(stage, nodeId) {
            return Array.from(stage.querySelectorAll('.ach-node')).find(
                node => node.dataset.nodeId === String(nodeId)
            ) || null;
        },
        findPin(stage, nodeId, direction, pinIndex) {
            return Array.from(stage.querySelectorAll('.ach-pin-anchor')).find(
                pin =>
                    pin.dataset.nodeId === String(nodeId) &&
                    pin.dataset.pinDirection === String(direction) &&
                    pin.dataset.pinIndex === String(pinIndex)
            ) || null;
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
        updateConnections(stage) {
            if (!stage) return;
            stage.querySelectorAll('[data-connection-id]').forEach(path => {
                const src = path.dataset.sourceNodeId || '';
                const tgt = path.dataset.targetNodeId || '';
                const inIdx = parseInt(path.dataset.inputIndex || '0', 10);
                const outIdx = parseInt(path.dataset.outputIndex || '0', 10);
                const sourcePin = this.pinCenter(stage, src, 'out', outIdx);
                const targetPin = this.pinCenter(stage, tgt, 'in', inIdx);
                if (!sourcePin || !targetPin) return;
                path.setAttribute(
                    'd',
                    this.curve(sourcePin.x, sourcePin.y, targetPin.x, targetPin.y)
                );
            });
        },
        moveNode(stage, nodeId, left, top) {
            const node = this.findNode(stage, nodeId);
            if (!node) return;
            const origin = this.origin(stage);
            node.style.left = `${Math.round(left + origin.x)}px`;
            node.style.top = `${Math.round(top + origin.y)}px`;
            this.updateConnections(stage);
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
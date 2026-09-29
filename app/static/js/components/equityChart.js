/**
 * Özkaynak Eğrisi Grafik Bileşeni (Equity Curve Canvas Chart).
 * Harici ağır kütüphaneler olmadan hafif, keskin ve yüksek performanslı Canvas çizimi.
 */

import { store } from '../state/store.js';

export class EquityChart {
    constructor(canvasId, tooltipId) {
        this.canvas = document.getElementById(canvasId);
        this.tooltip = document.getElementById(tooltipId);
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.dataPoints = [];
        this.init();
    }

    init() {
        if (!this.canvas) return;
        this.resize();
        window.addEventListener('resize', () => this.resize());

        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseleave', () => this.handleMouseLeave());

        store.subscribe('backtestResult', (result) => {
            if (result && result.equity_curve && result.equity_curve.length > 0) {
                this.dataPoints = result.equity_curve;
                this.draw();
            } else {
                this.dataPoints = [];
                this.drawEmpty();
            }
        });
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.draw();
    }

    drawEmpty() {
        if (!this.ctx) return;
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;

        this.ctx.clearRect(0, 0, width, height);
        this.ctx.fillStyle = '#545d68';
        this.ctx.font = '12px var(--font-mono)';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Backtest çalıştırıldığında Özkaynak Eğrisi (Equity Curve) burada görüntülenecektir.', width / 2, height / 2);
    }

    draw() {
        if (!this.ctx || this.dataPoints.length === 0) {
            this.drawEmpty();
            return;
        }

        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;
        const padding = { top: 20, right: 30, bottom: 25, left: 60 };

        this.ctx.clearRect(0, 0, width, height);

        const values = this.dataPoints.map(d => d.equity);
        const minVal = Math.min(...values) * 0.98;
        const maxVal = Math.max(...values) * 1.02;
        const range = maxVal - minVal || 1;

        // Arka Plan Kılavuz Çizgileri
        this.ctx.strokeStyle = '#1c2738';
        this.ctx.lineWidth = 1;
        const gridLines = 4;
        for (let i = 0; i <= gridLines; i++) {
            const y = padding.top + (i / gridLines) * (height - padding.top - padding.bottom);
            this.ctx.beginPath();
            this.ctx.moveTo(padding.left, y);
            this.ctx.lineTo(width - padding.right, y);
            this.ctx.stroke();

            // Y Ekseni Etiketi
            const val = maxVal - (i / gridLines) * range;
            this.ctx.fillStyle = '#8b949e';
            this.ctx.font = '10px var(--font-mono)';
            this.ctx.textAlign = 'right';
            this.ctx.fillText(val.toFixed(0) + ' $', padding.left - 8, y + 3);
        }

        // Çizgi ve Alan Koordinatlarını Hesaplama
        const points = this.dataPoints.map((d, idx) => {
            const x = padding.left + (idx / (this.dataPoints.length - 1 || 1)) * (width - padding.left - padding.right);
            const y = padding.top + (1 - (d.equity - minVal) / range) * (height - padding.top - padding.bottom);
            return { x, y, data: d };
        });

        // Gradyan Alan Dolgusu
        const isProfitable = values[values.length - 1] >= values[0];
        const lineColor = isProfitable ? '#3fb950' : '#f85149';
        const gradColor = isProfitable ? 'rgba(46, 160, 67, 0.15)' : 'rgba(248, 81, 73, 0.15)';

        const gradient = this.ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
        gradient.addColorStop(0, gradColor);
        gradient.addColorStop(1, 'rgba(15, 20, 31, 0.0)');

        this.ctx.beginPath();
        this.ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            this.ctx.lineTo(points[i].x, points[i].y);
        }
        this.ctx.lineTo(points[points.length - 1].x, height - padding.bottom);
        this.ctx.lineTo(points[0].x, height - padding.bottom);
        this.ctx.closePath();
        this.ctx.fillStyle = gradient;
        this.ctx.fill();

        // Özkaynak Çizgisi
        this.ctx.beginPath();
        this.ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            this.ctx.lineTo(points[i].x, points[i].y);
        }
        this.ctx.strokeStyle = lineColor;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        this.calculatedPoints = points;
    }

    handleMouseMove(e) {
        if (!this.calculatedPoints || this.calculatedPoints.length === 0 || !this.tooltip) return;
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;

        let closest = this.calculatedPoints[0];
        let minDist = Math.abs(mouseX - closest.x);

        for (let i = 1; i < this.calculatedPoints.length; i++) {
            const dist = Math.abs(mouseX - this.calculatedPoints[i].x);
            if (dist < minDist) {
                minDist = dist;
                closest = this.calculatedPoints[i];
            }
        }

        if (minDist < 30) {
            this.tooltip.style.display = 'block';
            this.tooltip.style.left = `${closest.x + 10}px`;
            this.tooltip.style.top = `${closest.y - 15}px`;
            this.tooltip.innerHTML = `
                <div><strong>Bakiye:</strong> ${closest.data.equity.toFixed(2)} USDT</div>
                <div style="font-size:10px; color:#8b949e;">${closest.data.timestamp}</div>
            `;
        } else {
            this.tooltip.style.display = 'none';
        }
    }

    handleMouseLeave() {
        if (this.tooltip) this.tooltip.style.display = 'none';
    }
}

/**
 * Quantitative metrics panel component.
 */

import { store } from '../state/store.js';

export class MetricsPanel {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.init();
    }

    init() {
        store.subscribe('backtestResult', (result) => this.render(result));
    }

    render(result) {
        if (!this.container) return;

        if (!result) {
            this.container.innerHTML = `
                <div class="metric-card">
                    <span class="metric-label">Net Kâr / Zarar</span>
                    <span class="metric-value">-- %</span>
                    <span class="metric-sub">0.00 USDT</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Kazanma Oranı</span>
                    <span class="metric-value">-- %</span>
                    <span class="metric-sub">0 / 0 İşlem</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Kâr Faktörü (PF)</span>
                    <span class="metric-value">--</span>
                    <span class="metric-sub">Gross Win / Loss</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Sharpe Oranı</span>
                    <span class="metric-value">--</span>
                    <span class="metric-sub">Risk-Adjusted Return</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Maksimum Drawdown</span>
                    <span class="metric-value">-- %</span>
                    <span class="metric-sub">0.00 USDT</span>
                </div>
            `;
            return;
        }

        const isProfit = result.net_profit_pct >= 0;
        const profitClass = isProfit ? 'profit' : 'loss';
        const sign = isProfit ? '+' : '';

        this.container.innerHTML = `
            <div class="metric-card ${profitClass}">
                <span class="metric-label">Net Kâr / Zarar</span>
                <span class="metric-value ${profitClass}">${sign}${result.net_profit_pct.toFixed(2)}%</span>
                <span class="metric-sub">${sign}${result.net_profit_usd.toFixed(2)} USDT</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Kazanma Oranı</span>
                <span class="metric-value">${result.win_rate_pct.toFixed(1)}%</span>
                <span class="metric-sub">${result.winning_trades} K / ${result.losing_trades} Z (${result.total_trades} Toplam)</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Kâr Faktörü (PF)</span>
                <span class="metric-value">${result.profit_factor.toFixed(2)}</span>
                <span class="metric-sub">Kazanma / Kaybetme Oranı</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Sharpe Oranı</span>
                <span class="metric-value">${result.sharpe_ratio.toFixed(2)}</span>
                <span class="metric-sub">Yıllıklandırılmış Risk Skoru</span>
            </div>
            <div class="metric-card loss">
                <span class="metric-label">Maksimum Drawdown</span>
                <span class="metric-value loss">-%${result.max_drawdown_pct.toFixed(2)}</span>
                <span class="metric-sub">-${result.max_drawdown_usd.toFixed(2)} USDT</span>
            </div>
        `;
    }
}

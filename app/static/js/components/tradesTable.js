/**
 * Trades ledger table component.
 */

import { store } from '../state/store.js';

export class TradesTable {
    constructor(tbodyId, countId) {
        this.tbody = document.getElementById(tbodyId);
        this.countElem = document.getElementById(countId);
        this.trades = [];
        this.init();
    }

    init() {
        store.subscribe('backtestResult', (result) => {
            this.trades = result && result.trades ? result.trades : [];
            this.render();
        });
    }

    render() {
        if (!this.tbody) return;

        if (this.countElem) {
            this.countElem.textContent = `${this.trades.length} İşlem`;
        }

        if (this.trades.length === 0) {
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        Henüz backtest işlemi kaydedilmedi. Lütfen yukarıdan "Backtest Çalıştır" butonuna basınız.
                    </td>
                </tr>
            `;
            return;
        }

        this.tbody.innerHTML = this.trades.map(trade => {
            const isProfit = trade.pnl_usd >= 0;
            const pnlColor = isProfit ? 'var(--color-profit-text)' : 'var(--color-loss-text)';
            const sign = isProfit ? '+' : '';
            const badgeClass = trade.type === 'LONG' ? 'badge-long' : 'badge-short';

            return `
                <tr>
                    <td>#${trade.trade_id}</td>
                    <td><span class="badge ${badgeClass}">${trade.type}</span></td>
                    <td style="color:var(--text-muted); font-size:11px;">${trade.entry_time || '--'}</td>
                    <td style="color:var(--text-muted); font-size:11px;">${trade.exit_time || '--'}</td>
                    <td>${trade.entry_price.toFixed(2)} $</td>
                    <td>${trade.exit_price.toFixed(2)} $</td>
                    <td style="color:${pnlColor}; font-weight:700;">
                        ${sign}${trade.pnl_pct.toFixed(2)}% (${sign}${trade.pnl_usd.toFixed(2)} $)
                    </td>
                    <td><span style="font-size:10px; color:var(--text-muted);">${trade.exit_reason}</span></td>
                </tr>
            `;
        }).join('');
    }
}

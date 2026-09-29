/**
 * Backtest simulation API endpoints.
 */

import { ApiClient } from './apiClient.js';

export const BacktestApi = {
    /**
     * Tekil sembol için anlık MTF backtest çalıştırır.
     */
    async runBacktest(params) {
        return ApiClient.post('/api/backtest/run', {
            symbol: params.symbol || 'BTC/USDT:USDT',
            timeframe: params.timeframe || '15m',
            strategy: params.strategy || 'A',
            capital: parseFloat(params.capital) || 10000.0,
            leverage: parseFloat(params.leverage) || 10.0,
            days: parseInt(params.days, 10) || 60
        });
    },

    /**
     * Arka planda çoklu piyasa taraması başlatır.
     */
    async startBulkScan() {
        return ApiClient.post('/api/backtest/scan/start', {});
    }
};

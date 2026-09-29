/**
 * Market data API endpoints.
 */

import { ApiClient } from './apiClient.js';

export const MarketApi = {
    /**
     * Vadeli işlem sembol listesini getirir.
     */
    async getSymbols(quote = 'USDT') {
        return ApiClient.get('/api/market/symbols', { quote });
    },

    /**
     * Belirli bir sembol ve periyota ait kline verisini getirir.
     */
    async getOhlcv(symbol, timeframe = '1h', days = 30) {
        return ApiClient.get(`/api/market/ohlcv/${encodeURIComponent(symbol)}`, { timeframe, days });
    }
};

/**
 * Central state management store.
 */

class StateStore {
    constructor() {
        this.state = {
            symbols: [],
            selectedSymbol: 'BTC/USDT:USDT',
            selectedTimeframe: '15m',
            selectedStrategy: 'A',
            capital: 10000.0,
            leverage: 10.0,
            lookbackDays: 60,
            
            // Backtest Çalışma Sonuçları
            backtestResult: null,
            isLoadingBacktest: false,
            
            // Sosyal Durum
            socialFeed: [],
            leaderboard: [],
            activeSocialTab: 'feed'
        };

        this.listeners = new Map();
    }

    /**
     * Durumdaki bir alanın değişimini dinler.
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);

        // Aboneliği sonlandırmak için unsubscribe fonksiyonu döner
        return () => {
            this.listeners.get(key).delete(callback);
        };
    }

    /**
     * Durumu günceller ve ilgili dinleyicileri tetikler.
     */
    setState(updates) {
        const changedKeys = [];

        Object.keys(updates).forEach(key => {
            if (this.state[key] !== updates[key]) {
                this.state[key] = updates[key];
                changedKeys.push(key);
            }
        });

        changedKeys.forEach(key => {
            if (this.listeners.has(key)) {
                this.listeners.get(key).forEach(cb => cb(this.state[key], this.state));
            }
        });

        // Genel dinleyiciler için '*' anahtarı
        if (this.listeners.has('*') && changedKeys.length > 0) {
            this.listeners.get('*').forEach(cb => cb(this.state, changedKeys));
        }
    }

    getState() {
        return { ...this.state };
    }
}

export const store = new StateStore();

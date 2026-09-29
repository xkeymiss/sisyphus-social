/**
 * Sisyphus Bot Frontend Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    const AVAILABLE_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h'];
    const STRATEGY_OPTIONS = [
        { key: 'A', name: 'Strateji A (Bollinger/POC)' },
        { key: 'B', name: 'Strateji B (Aks. SL/TP)' },
        { key: 'C', name: 'Strateji C (Rahat Sisyphus)' },
        { key: 'D', name: 'Strateji D (Momentum EMA)' },
        { key: 'E', name: 'Strateji E (Mean Reversion)' }
    ];

    let botState = {
        isRunning: false,
        allSymbols: [],
        coinConfigs: {} // { "BTC/USDT": { "15m": "A", "30m": "B" }, "ETH/USDT": { "1h": "C" } }
    };

    let allTrades = [];
    let currentTradesTab = 'active';

    // UI Referansları
    const btnToggle = document.getElementById('btn-toggle-bot');
    const toggleIcon = document.getElementById('bot-toggle-icon');
    const toggleLabel = document.getElementById('bot-toggle-label');
    const statusPill = document.getElementById('bot-status-pill');
    const statusText = document.getElementById('status-text');

    const statLastScan = document.getElementById('stat-last-scan');
    const statCoinsCount = document.getElementById('stat-coins-count');
    const statRulesCount = document.getElementById('stat-rules-count');
    const statActiveTrades = document.getElementById('stat-active-trades');

    const searchInput = document.getElementById('input-search-coin');
    const coinScrollRoot = document.getElementById('coin-scroll-root');
    const selectedCoinsBadge = document.getElementById('selected-coins-badge');
    const coinMatrixRoot = document.getElementById('coin-matrix-root');

    const btnSelectTopBacktest = document.getElementById('btn-select-top-backtest');
    const btnSelectTop20 = document.getElementById('btn-select-top20');
    const btnSelectAll = document.getElementById('btn-select-all');
    const btnClearAll = document.getElementById('btn-clear-all');
    const btnQuickTest = document.getElementById('btn-quick-test-signal');
    const btnRefresh = document.getElementById('btn-refresh-trades');

    const tabActive = document.getElementById('tab-active-trades');
    const tabCompleted = document.getElementById('tab-completed-trades');
    const countActive = document.getElementById('count-tab-active');
    const countCompleted = document.getElementById('count-tab-completed');
    const tbody = document.getElementById('bot-trades-tbody');

    // 1. Binance Vadeli Sembollerini Yükle
    async function loadSymbols() {
        try {
            const res = await fetch('/api/bot/available-symbols');
            const data = await res.json();
            if (data.status === 'success' && data.symbols) {
                botState.allSymbols = data.symbols;
                renderCoinList();
            }
        } catch (e) {
            console.error('Semboller yüklenemedi:', e);
        }
    }

    // 2. Bot Durumu ve Kayıtlı Konfigürasyonu Yükle
    async function loadBotStatus() {
        try {
            const res = await fetch('/api/bot/status');
            if (res.status === 403) {
                window.location.href = '/';
                return;
            }
            const data = await res.json();
            if (data.status === 'success' && data.data) {
                const d = data.data;
                botState.isRunning = d.is_running;
                updateHeaderStatus(d);

                // Rules -> coinConfigs haritasına dönüştür
                botState.coinConfigs = {};
                (d.rules || []).forEach(r => {
                    if (!botState.coinConfigs[r.symbol]) {
                        botState.coinConfigs[r.symbol] = {};
                    }
                    botState.coinConfigs[r.symbol][r.timeframe] = r.strategy_key;
                });

                renderCoinList();
                renderMatrixCards();
                updateCounts();
            }
        } catch (e) {
            console.error('Bot durumu çekilemedi:', e);
        }
    }

    // 3. Bot İşlemlerini Yükle
    async function loadBotTrades() {
        try {
            const res = await fetch('/api/bot/trades');
            const data = await res.json();
            if (data.status === 'success') {
                allTrades = data.trades || [];
                renderTradesTable();
            }
        } catch (e) {
            console.error('İşlemler çekilemedi:', e);
        }
    }

    function updateHeaderStatus(d) {
        if (d.is_running) {
            statusPill.className = 'bot-live-status-pill running';
            statusText.textContent = 'CANLI TARANIYOR';
            btnToggle.className = 'btn-bot-toggle btn-bot-stop';
            toggleIcon.textContent = '⏹';
            toggleLabel.textContent = 'Botu Durdur';
        } else {
            statusPill.className = 'bot-live-status-pill stopped';
            statusText.textContent = 'DURDURULDU';
            btnToggle.className = 'btn-bot-toggle btn-bot-start';
            toggleIcon.textContent = '▶';
            toggleLabel.textContent = 'Botu Başlat';
        }

        statLastScan.textContent = d.last_scan_time || '--:--:--';
        statActiveTrades.textContent = d.active_trades_count || '0';
        countActive.textContent = d.active_trades_count || '0';
        countCompleted.textContent = d.completed_trades_count || '0';
    }

    function updateCounts() {
        const selectedCoins = Object.keys(botState.coinConfigs);
        statCoinsCount.textContent = `${selectedCoins.length} Coin`;
        selectedCoinsBadge.textContent = `${selectedCoins.length} Seçildi`;

        let totalRules = 0;
        selectedCoins.forEach(coin => {
            totalRules += Object.keys(botState.coinConfigs[coin] || {}).length;
        });
        statRulesCount.textContent = `${totalRules} Kural`;
    }

    // 4. Sol Panel: Coin Listesini Çiz
    function renderCoinList() {
        if (!coinScrollRoot) return;
        const filter = (searchInput.value || '').trim().toUpperCase();

        const filtered = botState.allSymbols.filter(s => s.includes(filter));
        coinScrollRoot.innerHTML = filtered.map(sym => {
            const isSelected = Boolean(botState.coinConfigs[sym]);
            return `
                <div class="coin-list-row ${isSelected ? 'selected' : ''}" data-symbol="${sym}">
                    <input type="checkbox" class="coin-check-input" ${isSelected ? 'checked' : ''}>
                    <span class="coin-name-label">${sym}</span>
                </div>
            `;
        }).join('');

        coinScrollRoot.querySelectorAll('.coin-list-row').forEach(row => {
            row.addEventListener('click', (e) => {
                const sym = row.getAttribute('data-symbol');
                if (botState.coinConfigs[sym]) {
                    delete botState.coinConfigs[sym];
                } else {
                    // Varsayılan olarak 15m -> A ata
                    botState.coinConfigs[sym] = { '15m': 'A' };
                }
                renderCoinList();
                renderMatrixCards();
                updateCounts();
                syncConfigToBackend();
            });
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', renderCoinList);
    }

    // 5. Sağ Panel: Seçili Coinlerin Zaman Dilimi & Strateji Matrisini Çiz
    function renderMatrixCards() {
        if (!coinMatrixRoot) return;
        const selectedCoins = Object.keys(botState.coinConfigs);

        if (selectedCoins.length === 0) {
            coinMatrixRoot.innerHTML = `
                <div class="matrix-empty-placeholder">
                    <div style="font-size:28px; margin-bottom:8px;">👈</div>
                    <p>Soldaki listeden coin seçiniz. Seçilen her coinin zaman dilimleri ve stratejileri burada açılacaktır.</p>
                </div>
            `;
            return;
        }

        coinMatrixRoot.innerHTML = selectedCoins.map(coin => {
            const tfMap = botState.coinConfigs[coin] || {};
            const activeTfs = Object.keys(tfMap);

            const tfChipsHtml = AVAILABLE_TIMEFRAMES.map(tf => {
                const isActive = Boolean(tfMap[tf]);
                return `
                    <button class="tf-pill-chip ${isActive ? 'active' : ''}" data-coin="${coin}" data-tf="${tf}">
                        ${tf}
                    </button>
                `;
            }).join('');

            const tfStrategyRowsHtml = activeTfs.map(tf => {
                const currentStrat = tfMap[tf] || 'A';
                const stratOptionsHtml = STRATEGY_OPTIONS.map(opt => `
                    <option value="${opt.key}" ${opt.key === currentStrat ? 'selected' : ''}>
                        ${opt.name}
                    </option>
                `).join('');

                return `
                    <div class="coin-tf-strat-row">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="badge-timeframe">${tf}</span>
                            <span style="font-size:12px; color:var(--text-secondary);">için strateji:</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px; flex:1;">
                            <select class="select-tf-strategy" data-coin="${coin}" data-tf="${tf}">
                                ${stratOptionsHtml}
                            </select>
                            <button class="btn-remove-tf-row" data-coin="${coin}" data-tf="${tf}" title="Bu zaman dilimini kaldır">✕</button>
                        </div>
                    </div>
                `;
            }).join('');

            return `
                <div class="coin-config-card" data-coin="${coin}">
                    <div class="coin-config-card-header">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span class="coin-card-icon">⚡</span>
                            <strong style="font-size:14.5px; color:var(--text-primary); font-family:var(--font-mono);">${coin}</strong>
                            <span class="coin-active-rule-count">${activeTfs.length} Zaman Dilimi Aktif</span>
                        </div>
                        <button class="btn-remove-coin-card" data-coin="${coin}" title="Pariteyi Kaldır">✕</button>
                    </div>

                    <div class="coin-config-body">
                        <div style="margin-bottom:10px;">
                            <span class="tf-section-title">Zaman Dilimi Seç:</span>
                            <div class="tf-chips-group">
                                ${tfChipsHtml}
                            </div>
                        </div>

                        ${activeTfs.length > 0 ? `
                            <div class="active-tfs-strat-box">
                                ${tfStrategyRowsHtml}
                            </div>
                        ` : `
                            <p style="font-size:11.5px; color:var(--text-muted); margin:4px 0;">Yukarıdaki butonlardan bu coine zaman dilimi ekleyiniz.</p>
                        `}
                    </div>
                </div>
            `;
        }).join('');

        // Zaman Dilimi Butonlarına Tıklama (Aç / Kapat)
        coinMatrixRoot.querySelectorAll('.tf-pill-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const coin = chip.getAttribute('data-coin');
                const tf = chip.getAttribute('data-tf');

                if (botState.coinConfigs[coin][tf]) {
                    delete botState.coinConfigs[coin][tf];
                } else {
                    botState.coinConfigs[coin][tf] = 'A'; // Varsayılan Strateji A
                }
                renderMatrixCards();
                updateCounts();
                syncConfigToBackend();
            });
        });

        // Strateji Dropdown Değişimi
        coinMatrixRoot.querySelectorAll('.select-tf-strategy').forEach(sel => {
            sel.addEventListener('change', () => {
                const coin = sel.getAttribute('data-coin');
                const tf = sel.getAttribute('data-tf');
                const stratKey = sel.value;

                botState.coinConfigs[coin][tf] = stratKey;
                syncConfigToBackend();
            });
        });

        // Tekil Zaman Dilimi Satırını Kaldır
        coinMatrixRoot.querySelectorAll('.btn-remove-tf-row').forEach(btn => {
            btn.addEventListener('click', () => {
                const coin = btn.getAttribute('data-coin');
                const tf = btn.getAttribute('data-tf');
                delete botState.coinConfigs[coin][tf];
                renderMatrixCards();
                updateCounts();
                syncConfigToBackend();
            });
        });

        // Tüm Coini Kaldır
        coinMatrixRoot.querySelectorAll('.btn-remove-coin-card').forEach(btn => {
            btn.addEventListener('click', () => {
                const coin = btn.getAttribute('data-coin');
                delete botState.coinConfigs[coin];
                renderCoinList();
                renderMatrixCards();
                updateCounts();
                syncConfigToBackend();
            });
        });
    }

    // 6. Konfigürasyonu Backend'e Kaydet
    async function syncConfigToBackend() {
        const payloadList = [];
        Object.keys(botState.coinConfigs).forEach(coin => {
            payloadList.push({
                coin: coin,
                timeframe_strategies: botState.coinConfigs[coin]
            });
        });

        try {
            await fetch('/api/bot/coin-configs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({coin_configs: payloadList})
            });
        } catch (e) {
            console.error('Konfigürasyon kaydedilemedi:', e);
        }
    }

    // 7. Hızlı Seçim Butonları
    if (btnSelectTopBacktest) {
        btnSelectTopBacktest.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/bot/load-top-backtest', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({limit: 15})
                });
                const data = await res.json();
                if (data.status === 'success') {
                    botState.coinConfigs = {};
                    (data.rules || []).forEach(r => {
                        if (!botState.coinConfigs[r.symbol]) {
                            botState.coinConfigs[r.symbol] = {};
                        }
                        botState.coinConfigs[r.symbol][r.timeframe] = r.strategy_key;
                    });
                    renderCoinList();
                    renderMatrixCards();
                    updateCounts();
                }
            } catch (e) {
                console.error('Backtest kuralları yüklenemedi:', e);
            }
        });
    }

    if (btnSelectTop20) {
        btnSelectTop20.addEventListener('click', () => {
            const top20 = botState.allSymbols.slice(0, 20);
            botState.coinConfigs = {};
            top20.forEach(sym => {
                botState.coinConfigs[sym] = { '15m': 'A' };
            });
            renderCoinList();
            renderMatrixCards();
            updateCounts();
            syncConfigToBackend();
        });
    }

    if (btnSelectAll) {
        btnSelectAll.addEventListener('click', () => {
            botState.coinConfigs = {};
            botState.allSymbols.forEach(sym => {
                botState.coinConfigs[sym] = { '15m': 'A' };
            });
            renderCoinList();
            renderMatrixCards();
            updateCounts();
            syncConfigToBackend();
        });
    }

    if (btnClearAll) {
        btnClearAll.addEventListener('click', () => {
            botState.coinConfigs = {};
            renderCoinList();
            renderMatrixCards();
            updateCounts();
            syncConfigToBackend();
        });
    }

    // 8. Botu Başlat / Durdur
    if (btnToggle) {
        btnToggle.addEventListener('click', async () => {
            const endpoint = botState.isRunning ? '/api/bot/stop' : '/api/bot/start';
            btnToggle.disabled = true;
            try {
                await fetch(endpoint, {method: 'POST'});
                await loadBotStatus();
                await loadBotTrades();
            } catch (e) {
                console.error('Bot toggle hatası:', e);
            } finally {
                btnToggle.disabled = false;
            }
        });
    }

    // 9. Anlık Test Sinyali
    if (btnQuickTest) {
        btnQuickTest.addEventListener('click', async () => {
            btnQuickTest.disabled = true;
            btnQuickTest.textContent = '⚡ Sinyal Gönderiliyor...';
            try {
                const coins = Object.keys(botState.coinConfigs);
                let targetCoin = 'BTC/USDT';
                let targetTf = '15m';
                let targetStrat = 'Strateji A (Bollinger/POC)';

                if (coins.length > 0) {
                    targetCoin = coins[Math.floor(Math.random() * coins.length)];
                    const tfs = Object.keys(botState.coinConfigs[targetCoin] || {});
                    if (tfs.length > 0) {
                        targetTf = tfs[Math.floor(Math.random() * tfs.length)];
                        const stratKey = botState.coinConfigs[targetCoin][targetTf];
                        const found = STRATEGY_OPTIONS.find(o => o.key === stratKey);
                        if (found) targetStrat = found.name;
                    }
                }

                const side = Math.random() > 0.5 ? 'LONG' : 'SHORT';

                await fetch('/api/bot/test-signal', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        symbol: targetCoin,
                        timeframe: targetTf,
                        side: side,
                        strategy_name: targetStrat
                    })
                });
                await loadBotStatus();
                await loadBotTrades();
            } catch (e) {
                console.error('Test sinyali hatası:', e);
            } finally {
                btnQuickTest.disabled = false;
                btnQuickTest.textContent = '⚡ Anlık Test Sinyali Gönder';
            }
        });
    }

    // 10. İşlemler Tablosu Çizimi
    if (tabActive) {
        tabActive.addEventListener('click', () => {
            currentTradesTab = 'active';
            tabActive.classList.add('active');
            tabCompleted.classList.remove('active');
            renderTradesTable();
        });
    }

    if (tabCompleted) {
        tabCompleted.addEventListener('click', () => {
            currentTradesTab = 'completed';
            tabCompleted.classList.add('active');
            tabActive.classList.remove('active');
            renderTradesTable();
        });
    }

    if (btnRefresh) {
        btnRefresh.addEventListener('click', () => {
            loadBotStatus();
            loadBotTrades();
        });
    }

    function renderTradesTable() {
        if (!tbody) return;
        const thead = document.querySelector('.bot-trades-table thead');
        const isCompletedTab = (currentTradesTab === 'completed');

        if (thead) {
            if (isCompletedTab) {
                thead.innerHTML = `
                    <tr>
                        <th>Parite & Yön</th>
                        <th>Strateji</th>
                        <th>Zaman Dilimi</th>
                        <th>Giriş Fiyatı</th>
                        <th style="color:#38bdf8;">Çıkış Fiyatı</th>
                        <th>Güncel Fiyat</th>
                        <th>Kapatılmış PnL (20x)</th>
                        <th>Durum</th>
                        <th>Saat</th>
                        <th style="text-align:right;">İşlem</th>
                    </tr>
                `;
            } else {
                thead.innerHTML = `
                    <tr>
                        <th>Parite & Yön</th>
                        <th>Strateji</th>
                        <th>Zaman Dilimi</th>
                        <th>Giriş Fiyatı</th>
                        <th>Güncel Fiyat</th>
                        <th>Canlı PnL (20x)</th>
                        <th>Durum</th>
                        <th>Saat</th>
                        <th style="text-align:right;">İşlem</th>
                    </tr>
                `;
            }
        }

        const filtered = allTrades.filter(t => {
            if (currentTradesTab === 'active') return t.status === 'ACTIVE';
            return t.status !== 'ACTIVE';
        });

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="${isCompletedTab ? 10 : 9}" style="text-align:center; padding:32px; color:var(--text-muted); font-size:12.5px;">
                        ${currentTradesTab === 'active' ? 'Henüz açık bir pozisyon bulunmuyor.' : 'Henüz tamamlanmış bir işlem geçmişi yok.'}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = filtered.map(t => {
            const isLong = t.side === 'LONG';
            const sideClass = isLong ? 'badge-long' : 'badge-short';
            const pnl = t.current_pnl_pct || 0;
            const pnlColor = pnl >= 0 ? 'var(--color-green)' : 'var(--color-red)';
            const pnlSign = pnl >= 0 ? '+' : '';

            let statusBadge = '<span style="color:#60a5fa; font-weight:700;">🟢 Aktif</span>';
            if (t.status === 'TP_HIT') {
                statusBadge = '<span style="color:var(--color-green); font-weight:700;">🎯 TP Alındı</span>';
            } else if (t.status === 'SL_HIT' || t.status === 'CLOSED') {
                statusBadge = '<span style="color:var(--color-red); font-weight:700;">🛑 Kapatıldı</span>';
            }

            const formatCryptoPrice = (val) => {
                if (val === null || val === undefined || isNaN(val)) return '0.00';
                const num = Number(val);
                if (num === 0) return '0.00';
                const absNum = Math.abs(num);
                if (absNum >= 100) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                if (absNum >= 1) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
                if (absNum >= 0.01) return num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 6 });
                return num.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 8 });
            };

            const closePrice = t.close_price || t.exit_price || t.current_price || t.entry_price;

            return `
                <tr>
                    <td>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <strong style="color:var(--text-primary); font-family:var(--font-mono);">${t.symbol}</strong>
                            <span class="trade-side-pill ${sideClass}">${t.side} 20x</span>
                        </div>
                    </td>
                    <td style="color:#94a3b8; font-weight:600; font-size:12px;">${t.strategy_name}</td>
                    <td><span class="badge-timeframe">${t.timeframe || '15m'}</span></td>
                    <td style="font-family:var(--font-mono); font-weight:600;">$${formatCryptoPrice(t.entry_price)}</td>
                    ${isCompletedTab ? `
                        <td style="font-family:var(--font-mono); font-weight:700; color:#38bdf8;">$${formatCryptoPrice(closePrice)}</td>
                    ` : ''}
                    <td style="font-family:var(--font-mono); font-weight:600;">$${formatCryptoPrice(t.current_price || closePrice)}</td>
                    <td style="font-family:var(--font-mono); font-weight:800; color:${pnlColor};">
                        ${pnlSign}${pnl.toFixed(2)}%
                    </td>
                    <td>${statusBadge}</td>
                    <td style="color:var(--text-muted); font-size:11.5px; font-family:var(--font-mono);">${isCompletedTab ? (t.closed_display || t.closed_at || t.created_at || '—') : (t.created_at || t.created_display || t.opened_at || 'Şimdi')}</td>
                    <td style="text-align:right;">
                        <button class="btn-delete-bot-trade" data-id="${t.id}" title="Bu işlemi kaldır">🗑️ Kaldır</button>
                    </td>
                </tr>
            `;
        }).join('');

        tbody.querySelectorAll('.btn-delete-bot-trade').forEach(btn => {
            btn.addEventListener('click', async () => {
                const tradeId = btn.getAttribute('data-id');
                btn.disabled = true;
                btn.textContent = '...';
                try {
                    await fetch(`/api/bot/trades/${tradeId}/delete`, {method: 'POST'});
                    allTrades = allTrades.filter(t => t.id !== tradeId);
                    renderTradesTable();
                    loadBotStatus();
                } catch (e) {
                    console.error('İşlem silinemedi:', e);
                }
            });
        });
    }

    // İlk Yükleme
    loadSymbols();
    loadBotStatus();
    loadBotTrades();

    // 4 Saniyede bir otomatik canlı güncelleme
    setInterval(() => {
        if (botState.isRunning) {
            loadBotStatus();
            loadBotTrades();
        }
    }, 4000);
});

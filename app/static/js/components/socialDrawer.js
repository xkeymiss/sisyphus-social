/**
 * Sisyphus Social — İşlem Paylaşım, Pozisyon Yönetimi ve Düzenleme Modülü.
 */

import { ApiClient } from '../api/apiClient.js';
import { Toast } from './toast.js';

export class SocialDrawer {
    constructor() {
        this.trades = [];
        this.activeTab = 'latest'; // 'latest' | 'following' | 'my_trades'
        this.followedTraders = new Set();
        this.selectedEditStatus = 'ACTIVE';

        this.init();
    }

    init() {
        this.bindEvents();
        this.bindSearchEvents();
        this.bindEditModalEvents();
        this.bindLeaderboardEvents();
        this.loadTrades();
        this.loadLeaderboard();
    }

    formatPrice(price) {
        if (price === null || price === undefined || isNaN(price)) return '0.00';
        const num = Number(price);
        if (num === 0) return '0.00';
        const absNum = Math.abs(num);
        if (absNum >= 100) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (absNum >= 1) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
        if (absNum >= 0.01) return num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 6 });
        return num.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 8 });
    }

    bindEvents() {
        // Akış Sekme Butonları
        const tabBtns = document.querySelectorAll('.social-tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeTab = btn.getAttribute('data-tab') || 'latest';
                this.loadTrades();
            });
        });

        const btnOpen = document.getElementById('btn-open-share-modal');
        const btnClose = document.getElementById('btn-close-share-modal');
        const modal = document.getElementById('share-trade-modal');

        if (btnOpen && modal) {
            btnOpen.addEventListener('click', async () => {
                try {
                    const authRes = await ApiClient.get('/auth/status');
                    if (!authRes || !authRes.is_authenticated) {
                        Toast.show('İşlem paylaşabilmek için lütfen oturum açınız.', 'info');
                        setTimeout(() => {
                            window.location.href = '/auth/login';
                        }, 400);
                        return;
                    }
                } catch (e) {
                    // pass
                }
                modal.style.display = 'flex';
            });
        }
        if (btnClose && modal) {
            btnClose.addEventListener('click', () => modal.style.display = 'none');
        }

        // Aktif Pozisyon mu, Bekleyen Emir mi?
        const btnStatusActive = document.getElementById('toggle-status-active');
        const btnStatusPending = document.getElementById('toggle-status-pending');
        const inputStatus = document.getElementById('input-trade-status');

        if (btnStatusActive && btnStatusPending && inputStatus) {
            btnStatusActive.addEventListener('click', () => {
                btnStatusActive.classList.add('active');
                btnStatusPending.classList.remove('active');
                inputStatus.value = 'ACTIVE';
            });
            btnStatusPending.addEventListener('click', () => {
                btnStatusPending.classList.add('active');
                btnStatusActive.classList.remove('active');
                inputStatus.value = 'PENDING';
            });
        }

        // LONG / SHORT Seçimi
        const btnLong = document.getElementById('toggle-side-long');
        const btnShort = document.getElementById('toggle-side-short');
        const inputSide = document.getElementById('input-trade-side');

        if (btnLong && btnShort && inputSide) {
            btnLong.addEventListener('click', () => {
                btnLong.classList.add('active-long');
                btnShort.classList.remove('active-short');
                inputSide.value = 'LONG';
            });
            btnShort.addEventListener('click', () => {
                btnShort.classList.add('active-short');
                btnLong.classList.remove('active-long');
                inputSide.value = 'SHORT';
            });
        }

        // Form Gönderme Butonu
        const btnSubmit = document.getElementById('btn-submit-share-trade');
        if (btnSubmit) {
            btnSubmit.addEventListener('click', () => this.handleShareTrade());
        }
    }

    bindEditModalEvents() {
        const editModal = document.getElementById('edit-trade-modal');
        const btnCloseEdit = document.getElementById('btn-close-edit-modal');
        const btnSaveEdit = document.getElementById('btn-save-edit-trade');
        const btnDeleteTrade = document.getElementById('btn-delete-trade');

        if (btnCloseEdit && editModal) {
            btnCloseEdit.addEventListener('click', () => editModal.style.display = 'none');
        }

        // Durum Seçenek Butonları
        document.querySelectorAll('.btn-status-option').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.btn-status-option').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedEditStatus = btn.getAttribute('data-status') || 'ACTIVE';
            });
        });

        // Değişiklikleri Kaydet
        if (btnSaveEdit) {
            btnSaveEdit.addEventListener('click', async () => {
                const tradeId = document.getElementById('edit-trade-id')?.value;
                const tp = parseFloat(document.getElementById('edit-tp')?.value || '0');
                const sl = parseFloat(document.getElementById('edit-sl')?.value || '0');
                const closeInputVal = document.getElementById('edit-close-price')?.value?.trim();
                const closePrice = closeInputVal ? parseFloat(closeInputVal) : 0;

                if (!tradeId) return;

                try {
                    const payload = {
                        status: this.selectedEditStatus
                    };
                    if (tp) payload.target_tp = tp;
                    if (sl) payload.stop_loss = sl;
                    if (closePrice > 0) payload.close_price = closePrice;

                    await ApiClient.post(`/api/social/trades/${tradeId}/update`, payload);
                    Toast.show('Pozisyon durumu başarıyla güncellendi!', 'success');
                    if (editModal) editModal.style.display = 'none';
                    this.loadTrades();
                    this.loadLeaderboard();
                } catch (err) {
                    Toast.show(`Güncelleme hatası: ${err.message}`, 'error');
                }
            });
        }

        // İşlemi Sil
        if (btnDeleteTrade) {
            btnDeleteTrade.addEventListener('click', async () => {
                const tradeId = document.getElementById('edit-trade-id')?.value;
                if (!tradeId) return;

                if (!confirm('Bu işlemi silmek istediğinize emin misiniz?')) return;

                try {
                    await ApiClient.post(`/api/social/trades/${tradeId}/delete`, {});
                    Toast.show('İşlem silindi.', 'info');
                    if (editModal) editModal.style.display = 'none';
                    this.loadTrades();
                    this.loadLeaderboard();
                } catch (err) {
                    Toast.show(`Silme hatası: ${err.message}`, 'error');
                }
            });
        }
    }

    async loadTrades() {
        const container = document.getElementById('social-feed-root');
        if (!container) return;

        container.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:12px;">İşlemler yükleniyor...</div>';

        try {
            const data = await ApiClient.get('/api/social/trades', {
                tab: this.activeTab
            });

            if (!data || data.status !== 'success') {
                container.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:12px;">İşlemler yüklenemedi.</div>';
                return;
            }

            if (data.followed_traders && Array.isArray(data.followed_traders)) {
                this.followedTraders = new Set(data.followed_traders);
            }
            this.trades = data.trades || [];
            this.renderTrades(this.trades);
        } catch (err) {
            container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--color-red); font-size:12px;">Hata: ${err.message}</div>`;
        }
    }

    renderTrades(trades) {
        const container = document.getElementById('social-feed-root');
        if (!container) return;

        if (trades.length === 0) {
            container.innerHTML = `
                <div style="text-align:center; padding:40px; color:var(--text-muted); font-size:13px; background:var(--bg-card); border:1px dashed var(--border-light); border-radius:12px;">
                    Bu sekmede henüz paylaşılan bir işlem bulunmuyor.
                </div>
            `;
            return;
        }

        container.innerHTML = trades.map(t => {
            const isMine = t.is_mine;
            const isLong = (t.side || '').toUpperCase().includes('LONG');
            const sideClass = isLong ? 'badge-long' : 'badge-short';
            const isFollowing = Boolean(t.is_following || this.followedTraders.has(t.trader_handle));
            const followBtnText = isFollowing ? '✔ Takip Ediliyor' : '+ Takip Et';
            const followBtnClass = isFollowing ? 'btn-follow-toggle following' : 'btn-follow-toggle';

            const isClosed = ['TP_HIT', 'CLOSED', 'SL_HIT'].includes(t.status) || Boolean(t.close_price && t.close_price > 0);
            const closeVal = t.close_price || t.target_tp || t.entry_price;
            const rawPnl = Number(t.raw_pnl_pct || 0);
            const rawPnlSign = rawPnl >= 0 ? '+' : '';
            const pnlColor = rawPnl >= 0 ? 'var(--color-green)' : 'var(--color-red)';

            const cleanHandle = (t.trader_handle || 'utku').replace(/^@/, '');
            const profileUrl = `/profil/${cleanHandle}`;

            return `
                <div class="trade-post-card" data-id="${t.id}">
                    <!-- Kart Üst Başlık: Profil Resmi, İsim, @kullanıcı adı, Zaman (Yan Yana & Tıklanabilir) -->
                    <div class="trade-card-header">
                        <a href="${profileUrl}" class="user-meta-left user-profile-link" title="${t.trader_name} profilini görüntüle">
                            <div class="user-avatar-circle">
                                ${(t.trader_name || 'U').charAt(0).toUpperCase()}
                            </div>
                            <div class="user-info-row">
                                <strong class="user-display-name">${t.trader_name}</strong>
                                <span class="user-handle-tag">${t.trader_handle}</span>
                                <span class="user-time-dot">•</span>
                                <span class="user-time-text">${t.created_at || 'Şimdi'}</span>
                            </div>
                        </a>

                        <div>
                            ${isMine ? `
                                <button class="btn-manage-trade" data-id="${t.id}">
                                    ⚙️ Düzenle
                                </button>
                            ` : `
                                <button class="${followBtnClass}" data-handle="${t.trader_handle}">
                                    ${followBtnText}
                                </button>
                            `}
                        </div>
                    </div>

                    <!-- Pozisyon Detay Kutusu -->
                    <div class="position-details-box">
                        <div class="pos-box-top">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span class="trade-side-pill ${sideClass}">${t.side} ${t.leverage || '20x'}</span>
                                <strong class="trade-symbol-text">${t.symbol}</strong>
                                <span class="badge-timeframe">${t.timeframe || '15m'}</span>
                            </div>
                            <span class="pos-status-pill ${this.getStatusClass(t.status)}">${t.status_label || '🟢 Aktif Pozisyon'}</span>
                        </div>

                        <!-- Seviyeler & Kapanış Detayı -->
                        ${isClosed ? `
                            <div class="pos-grid-levels">
                                <div class="level-item">
                                    <span class="level-lbl">Giriş</span>
                                    <span class="level-val">$${this.formatPrice(t.entry_price)}</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-lbl" style="color:#38bdf8;">Kapanış Fiyatı</span>
                                    <span class="level-val" style="color:#38bdf8; font-weight:700;">$${this.formatPrice(closeVal)}</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-lbl" style="color:${pnlColor};">Net Kâr / Zarar</span>
                                    <span class="level-val" style="color:${pnlColor}; font-weight:800;">${rawPnlSign}${rawPnl.toFixed(2)}%</span>
                                </div>
                            </div>
                            <div style="margin-top:8px; font-size:11.5px; color:var(--text-secondary); display:flex; justify-content:space-between; align-items:center;">
                                <span>Strateji: <strong style="color:#93c5fd;">${t.strategy_name || 'Otomatik Sisyphus'}</strong></span>
                                <span class="badge-timeframe" style="font-size:10px;">${t.timeframe || '15m'}</span>
                            </div>
                        ` : `
                            <div class="pos-grid-levels">
                                <div class="level-item">
                                    <span class="level-lbl">Giriş</span>
                                    <span class="level-val">$${this.formatPrice(t.entry_price)}</span>
                                </div>
                                ${(t.strategy_name && t.strategy_name !== 'Manuel İşlem') || (!t.target_tp && !t.stop_loss) ? `
                                    <div class="level-item">
                                        <span class="level-lbl" style="color:#60a5fa;">Zaman Dilimi</span>
                                        <span class="level-val" style="color:#93c5fd; font-weight:700;">${t.timeframe || '15m'}</span>
                                    </div>
                                    <div class="level-item">
                                        <span class="level-lbl" style="color:#38bdf8;">Strateji</span>
                                        <span class="level-val" style="color:#38bdf8; font-weight:700; font-size:12.5px;">${t.strategy_name || 'Otomatik Bot'}</span>
                                    </div>
                                ` : `
                                    <div class="level-item">
                                        <span class="level-lbl" style="color:var(--color-green);">Hedef (TP)</span>
                                        <span class="level-val" style="color:var(--color-green);">$${this.formatPrice(t.target_tp)}</span>
                                    </div>
                                    <div class="level-item">
                                        <span class="level-lbl" style="color:var(--color-red);">Stop (SL)</span>
                                        <span class="level-val" style="color:var(--color-red);">$${this.formatPrice(t.stop_loss)}</span>
                                    </div>
                                `}
                            </div>
                        `}
                    </div>

                    <!-- Alt Butonlar -->
                    <div class="trade-card-footer">
                        <div class="card-action-group">
                            <button class="btn-card-action btn-like-trade ${t.is_liked ? 'liked' : ''}" data-id="${t.id}">
                                ${t.is_liked ? '❤️' : '🤍'} <span>${t.likes_count} Beğeni</span>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        this.bindDynamicCardEvents();
    }

    getStatusClass(status) {
        const s = (status || '').toUpperCase();
        if (s === 'PENDING') return 'status-pending';
        if (s === 'TP_HIT') return 'status-tp';
        if (s === 'SL_HIT') return 'status-sl';
        if (s === 'CLOSED' || s.startsWith('PARTIAL')) return 'status-closed';
        return 'status-active';
    }

    bindDynamicCardEvents() {
        // Düzenle Butonu (Kendi İşlemleri İçin)
        document.querySelectorAll('.btn-manage-trade').forEach(btn => {
            btn.addEventListener('click', () => {
                const tradeId = btn.getAttribute('data-id');
                const trade = this.trades.find(t => t.id === tradeId);
                if (!trade) return;

                const editModal = document.getElementById('edit-trade-modal');
                const titleSub = document.getElementById('edit-modal-subtitle');
                const inputId = document.getElementById('edit-trade-id');
                const inputTp = document.getElementById('edit-tp');
                const inputSl = document.getElementById('edit-sl');
                const inputClose = document.getElementById('edit-close-price');

                if (inputId) inputId.value = trade.id;
                if (titleSub) titleSub.textContent = `${trade.symbol} (${trade.side} ${trade.leverage})`;
                if (inputTp) inputTp.value = trade.target_tp || '';
                if (inputSl) inputSl.value = trade.stop_loss || '';
                if (inputClose) inputClose.value = trade.close_price || '';

                this.selectedEditStatus = trade.status || 'ACTIVE';
                document.querySelectorAll('.btn-status-option').forEach(b => {
                    b.classList.toggle('active', b.getAttribute('data-status') === this.selectedEditStatus);
                });

                if (editModal) editModal.style.display = 'flex';
            });
        });

        // Takip Butonu
        document.querySelectorAll('.btn-follow-toggle').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const handle = btn.getAttribute('data-handle');
                if (!handle) return;

                btn.disabled = true;
                try {
                    const res = await ApiClient.post('/api/social/follow/toggle', { handle });
                    if (res && res.status === 'success') {
                        const isNowFollowing = res.is_following;
                        if (isNowFollowing) {
                            this.followedTraders.add(handle);
                            Toast.show(`${handle} takip edildi`, 'success');
                        } else {
                            this.followedTraders.delete(handle);
                            Toast.show(`${handle} takipten çıkarıldı`, 'info');
                        }

                        // Sayfadaki bu kullanıcıya ait TÜM takip butonlarını senkronize güncelle
                        document.querySelectorAll(`.btn-follow-toggle[data-handle="${handle}"]`).forEach(otherBtn => {
                            if (isNowFollowing) {
                                otherBtn.classList.add('following');
                                otherBtn.textContent = '✔ Takip Ediliyor';
                            } else {
                                otherBtn.classList.remove('following');
                                otherBtn.textContent = '+ Takip Et';
                            }
                        });
                    }
                } catch (err) {
                    Toast.show('Takip işlemi başarısız', 'error');
                } finally {
                    btn.disabled = false;
                }
            });
        });



        // Beğeni Butonu
        document.querySelectorAll('.btn-like-trade').forEach(btn => {
            btn.addEventListener('click', async () => {
                const tradeId = btn.getAttribute('data-id');
                try {
                    const res = await ApiClient.post(`/api/social/trade/${tradeId}/like`, {});
                    btn.classList.toggle('liked', res.is_liked);
                    btn.innerHTML = `${res.is_liked ? '❤️' : '🤍'} <span>${res.likes_count} Beğeni</span>`;
                } catch (err) {
                    Toast.show('Beğeni işlemi başarısız', 'error');
                }
            });
        });
    }

    async handleShareTrade() {
        const symbol = document.getElementById('share-symbol')?.value.trim() || 'BTC/USDT';
        const side = document.getElementById('input-trade-side')?.value || 'LONG';
        const status = document.getElementById('input-trade-status')?.value || 'ACTIVE';
        const leverage = document.getElementById('share-leverage')?.value || '10';
        const entryPrice = parseFloat(document.getElementById('share-entry')?.value || '0');
        const targetTp = parseFloat(document.getElementById('share-tp')?.value || '0');
        const stopLoss = parseFloat(document.getElementById('share-sl')?.value || '0');

        if (!entryPrice || !targetTp || !stopLoss) {
            Toast.show('Lütfen Giriş, Kâr Al (TP) ve Stop (SL) fiyatlarını giriniz.', 'error');
            return;
        }

        try {
            await ApiClient.post('/api/social/trades/share', {
                trader_name: 'Utku',
                trader_handle: '@utku',
                symbol,
                side,
                status,
                leverage: `${leverage}x`,
                timeframe: '15m',
                entry_price: entryPrice,
                target_tp: targetTp,
                stop_loss: stopLoss,
                strategy_name: 'Manuel İşlem',
                notes: ''
            });

            Toast.show(status === 'PENDING' ? 'Bekleyen emir paylaşıldı!' : 'Aktif pozisyon paylaşıldı!', 'success');
            const modal = document.getElementById('share-trade-modal');
            if (modal) modal.style.display = 'none';

            // Formu temizle
            const entryInput = document.getElementById('share-entry');
            const tpInput = document.getElementById('share-tp');
            const slInput = document.getElementById('share-sl');
            if (entryInput) entryInput.value = '';
            if (tpInput) tpInput.value = '';
            if (slInput) slInput.value = '';

            this.loadTrades();
            this.loadLeaderboard();
        } catch (err) {
            Toast.show(`Hata: ${err.message}`, 'error');
        }
    }

    bindLeaderboardEvents() {
        const periodBtns = document.querySelectorAll('.leader-period-btn');
        periodBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                periodBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.leaderboardPeriod = btn.getAttribute('data-period') || 'today';
                this.loadLeaderboard();
            });
        });
    }

    async loadLeaderboard() {
        const root = document.getElementById('leaderboard-list-root');
        if (!root) return;

        try {
            const res = await ApiClient.get(`/api/social/leaderboard?period=${this.leaderboardPeriod || 'today'}&limit=8`);
            if (res && res.status === 'success') {
                this.renderLeaderboard(res.leaderboard || []);
            }
        } catch (err) {
            if (root) {
                root.innerHTML = '<div style="color:var(--text-muted); font-size:12px; text-align:center; padding:16px;">Sıralama yüklenemedi.</div>';
            }
        }
    }

    renderLeaderboard(items) {
        const root = document.getElementById('leaderboard-list-root');
        if (!root) return;

        if (!items || items.length === 0) {
            root.innerHTML = `
                <div class="leaderboard-empty">
                    <span>⏳</span>
                    <p>${this.leaderboardPeriod === 'today' ? 'Bugün henüz kapanmış kârlı bir işlem bulunmuyor.' : 'Bu periyotta henüz kapanmış kârlı bir işlem bulunmuyor.'}</p>
                </div>
            `;
            return;
        }

        root.innerHTML = items.map((t, idx) => {
            let rankBadge = `<span class="rank-badge rank-other">#${idx + 1}</span>`;
            if (idx === 0) rankBadge = `<span class="rank-badge rank-gold">🥇 #1</span>`;
            else if (idx === 1) rankBadge = `<span class="rank-badge rank-silver">🥈 #2</span>`;
            else if (idx === 2) rankBadge = `<span class="rank-badge rank-bronze">🥉 #3</span>`;

            const isLong = (t.side || '').toUpperCase() === 'LONG';
            const sideClass = isLong ? 'badge-long' : 'badge-short';
            const rawPnl = Number(t.raw_pnl_pct || 0);
            const isProfit = rawPnl >= 0;
            const pnlPillClass = isProfit ? 'leader-pnl-pos' : 'leader-pnl-neg';
            const pnlText = isProfit ? `+${rawPnl.toFixed(2)}% Net Kâr` : `${rawPnl.toFixed(2)}% Net Zarar`;

            const entryFormatted = this.formatPrice(t.entry_price);
            const closePrice = t.close_price || t.target_tp || t.entry_price;
            const closeFormatted = this.formatPrice(closePrice);

            const cleanLeaderHandle = (t.trader_handle || 'utku').replace(/^@/, '');
            const leaderProfileUrl = `/profil/${cleanLeaderHandle}`;

            return `
                <div class="leaderboard-item-card ${idx === 0 ? 'leader-top1-glow' : ''}">
                    <div class="leader-item-top">
                        <a href="${leaderProfileUrl}" class="leader-user-profile-link" title="${t.trader_name} profilini görüntüle">
                            <div style="display:flex; align-items:center; gap:8px;">
                                ${rankBadge}
                                <span class="leader-trader-name">${t.trader_name || 'Trader'}</span>
                                <span class="leader-trader-handle">${t.trader_handle || '@utku'}</span>
                            </div>
                        </a>
                        <span class="leader-closed-time">${t.closed_display || t.created_at || 'Bugün'}</span>
                    </div>

                    <div class="leader-item-mid">
                        <div style="display:flex; align-items:center; gap:6px;">
                            <strong class="leader-symbol">${t.symbol}</strong>
                            <span class="trade-side-pill ${sideClass}">${t.side}</span>
                            <span class="badge-timeframe" style="font-size:10px; padding:1px 5px;">${t.timeframe || '15m'}</span>
                        </div>

                        <!-- Kaldıraçsız Net Fiyat Kârı / Zararı -->
                        <div class="leader-pnl-pill ${pnlPillClass}">
                            <span>${pnlText}</span>
                        </div>
                    </div>

                    <div class="leader-item-bottom">
                        <span class="leader-price-flow">Giriş: <strong>$${entryFormatted}</strong> ➔ Çıkış: <strong>$${closeFormatted}</strong></span>
                        <span class="leader-strat-name">${t.strategy_name || 'Strateji'}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    bindSearchEvents() {
        const searchInput = document.getElementById('social-trader-search-input');
        const clearBtn = document.getElementById('btn-clear-trader-search');
        const dropdown = document.getElementById('social-trader-search-dropdown');
        const resultsList = document.getElementById('social-search-results-list');

        if (!searchInput || !dropdown || !resultsList) return;

        let searchTimeout = null;

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (clearBtn) clearBtn.style.display = query.length > 0 ? 'block' : 'none';

            clearTimeout(searchTimeout);
            if (query.length < 1) {
                dropdown.style.display = 'none';
                return;
            }

            searchTimeout = setTimeout(async () => {
                try {
                    const data = await ApiClient.get('/api/social/users/search', { q: query });
                    if (!data || !data.results || data.results.length === 0) {
                        resultsList.innerHTML = `
                            <div class="search-empty-state">
                                <span>🔍</span>
                                <p>"${query}" ile eşleşen kullanıcı bulunamadı.</p>
                            </div>
                        `;
                    } else {
                        resultsList.innerHTML = data.results.map(u => `
                            <a href="${u.profile_url}" class="search-result-item">
                                <div class="search-avatar-circle">${u.avatar_letter}</div>
                                <div class="search-user-info">
                                    <div class="search-user-top">
                                        <strong class="search-user-name">${u.name}</strong>
                                        <span class="search-user-handle">${u.handle}</span>
                                    </div>
                                    <div class="search-user-bottom">
                                        <span class="search-badge">${u.badge}</span>
                                        <span class="search-followers">• ${u.followers_count} Takipçi</span>
                                    </div>
                                </div>
                                <span class="search-arrow-icon">➔</span>
                            </a>
                        `).join('');
                    }
                    dropdown.style.display = 'block';
                } catch (err) {
                    console.error('Kullanıcı arama hatası:', err);
                }
            }, 250);
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                clearBtn.style.display = 'none';
                dropdown.style.display = 'none';
                searchInput.focus();
            });
        }

        // Dropdown dışına tıklandığında kapat
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim().length > 0) {
                dropdown.style.display = 'block';
            }
        });
    }
}


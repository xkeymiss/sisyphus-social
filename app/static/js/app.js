/**
 * Sisyphus Social — Ana İstemci Modülü, Responsive Router ve Kimlik Doğrulama (Auth).
 */

import { ApiClient } from './api/apiClient.js';
import { SocialDrawer } from './components/socialDrawer.js?v=6.4';
import { Toast } from './components/toast.js';

class ScannerApp {
    constructor() {
        this.currentView = 'summary'; // 'summary' (/) | 'full-table' (/islemsonuclari) | 'social' (/sosyal)
        this.currentStrategy = 'A';
        this.currentSummaryStrategy = 'A';
        this.currentSort = { key: 'total_pnl_pct', desc: true };
        this.currentUser = (typeof window !== 'undefined' && window.__CURRENT_USER__) ? window.__CURRENT_USER__ : null;
        
        this.scanData = {
            results_a: [],
            results_b: [],
            results_c: [],
            results_d: [],
            results_e: []
        };

        this.socialDrawer = null;
    }

    async init() {
        if (!document.getElementById('summary-view')) {
            return;
        }
        console.log('🚀 Sisyphus Social başlatılıyor...');

        this.updateAuthUI();
        this.bindNavigation();
        this.bindSummaryTabs();
        this.bindStrategyTabs();
        this.bindFiltersAndSorting();
        this.bindModalsAndJsonActions();
        this.bindUserManagementModal();

        this.socialDrawer = new SocialDrawer();
        
        // 1. URL'ye göre doğru sekmeyi ANINDA senkron aç
        this.handleInitialRoute(false);

        // 2. Verileri yükle
        await this.loadInitialResults();
        this.checkAuthStatus();
    }

    // Auth status & logout
    async checkAuthStatus() {
        try {
            const res = await ApiClient.get('/auth/status');
            if (res && res.status === 'success' && res.is_authenticated && res.user) {
                this.currentUser = res.user;
            }
        } catch (err) {
            // pass
        }

        this.updateAuthUI();
    }

    updateAuthUI() {
        const navLetter = document.getElementById('nav-avatar-letter');
        const mobLabel = document.getElementById('mobile-nav-account-label');

        const dropAvatar = document.getElementById('dropdown-avatar-letter');
        const dropName = document.getElementById('dropdown-user-name');
        const dropHandle = document.getElementById('dropdown-user-handle');
        const dropBadge = document.getElementById('dropdown-user-badge');
        const dropAdminSection = document.getElementById('dropdown-admin-section');

        const initial = this.currentUser ? ((this.currentUser.name || this.currentUser.username || 'U')[0].toUpperCase()) : 'U';

        if (navLetter) navLetter.textContent = initial;
        if (dropAvatar) dropAvatar.textContent = initial;

        if (this.currentUser) {
            if (mobLabel) mobLabel.textContent = 'Profil';
            if (dropName) dropName.textContent = this.currentUser.name;
            if (dropHandle) dropHandle.textContent = this.currentUser.handle;
            if (dropBadge) dropBadge.textContent = this.currentUser.badge || '👑 Sistem Yöneticisi & Trader';

            if (dropAdminSection) {
                dropAdminSection.style.display = this.currentUser.role === 'admin' ? 'block' : 'none';
            }
        }
    }

    // Navigation
    bindNavigation() {
        const btnSummary = document.getElementById('btn-nav-summary');
        const btnFullTable = document.getElementById('btn-nav-full-table');
        const btnSocial = document.getElementById('btn-nav-social');
        const btnGoToTable = document.getElementById('btn-go-to-islemsonuclari');
        const btnBackSummary = document.getElementById('btn-back-to-summary');
        const brandHome = document.getElementById('brand-home-link');

        const btnMobSummary = document.getElementById('btn-mobile-nav-summary');
        const btnMobFullTable = document.getElementById('btn-mobile-nav-full-table');
        const btnMobSocial = document.getElementById('btn-mobile-nav-social');
        const btnMobAccount = document.getElementById('btn-mobile-nav-account');

        if (btnSummary) btnSummary.addEventListener('click', () => this.switchView('summary', '/'));
        if (btnFullTable) btnFullTable.addEventListener('click', () => this.switchView('full-table', '/islemsonuclari'));
        if (btnSocial) btnSocial.addEventListener('click', () => this.switchView('social', '/sosyal'));

        if (btnMobSummary) btnMobSummary.addEventListener('click', () => this.switchView('summary', '/'));
        if (btnMobFullTable) btnMobFullTable.addEventListener('click', () => this.switchView('full-table', '/islemsonuclari'));
        if (btnMobSocial) btnMobSocial.addEventListener('click', () => this.switchView('social', '/sosyal'));
        
        if (btnMobAccount) {
            btnMobAccount.addEventListener('click', (e) => {
                window.location.href = '/profil';
            });
        }

        if (btnGoToTable) btnGoToTable.addEventListener('click', () => this.switchView('full-table', '/islemsonuclari'));
        if (btnBackSummary) btnBackSummary.addEventListener('click', () => this.switchView('summary', '/'));
        if (brandHome) brandHome.addEventListener('click', () => this.switchView('summary', '/'));

        // Tarayıcı Geri/İleri Tuşları
        window.addEventListener('popstate', () => this.handleInitialRoute(false));
    }

    handleInitialRoute(pushHistory = true) {
        const path = window.location.pathname.toLowerCase();
        if (path === '/islemsonuclari') {
            this.switchView('full-table', '/islemsonuclari', pushHistory);
        } else if (path === '/sosyal') {
            this.switchView('social', '/sosyal', pushHistory);
        } else {
            this.switchView('summary', '/', pushHistory);
        }
    }

    switchView(viewName, routePath, pushHistory = true) {
        this.currentView = viewName;

        const summaryView = document.getElementById('summary-view');
        const fullTableView = document.getElementById('full-table-view');
        const socialView = document.getElementById('social-view');

        const btnSummary = document.getElementById('btn-nav-summary');
        const btnFullTable = document.getElementById('btn-nav-full-table');
        const btnSocial = document.getElementById('btn-nav-social');

        const btnMobSummary = document.getElementById('btn-mobile-nav-summary');
        const btnMobFullTable = document.getElementById('btn-mobile-nav-full-table');
        const btnMobSocial = document.getElementById('btn-mobile-nav-social');

        [btnSummary, btnFullTable, btnSocial, btnMobSummary, btnMobFullTable, btnMobSocial].forEach(b => b && b.classList.remove('active'));
        [summaryView, fullTableView, socialView].forEach(v => v && (v.style.display = 'none'));

        if (viewName === 'summary') {
            if (summaryView) summaryView.style.display = 'block';
            if (btnSummary) btnSummary.classList.add('active');
            if (btnMobSummary) btnMobSummary.classList.add('active');
            document.title = 'Sisyphus Social — İndikatör Özeti';
            this.renderSummarySection();
        } else if (viewName === 'full-table') {
            if (fullTableView) fullTableView.style.display = 'block';
            if (btnFullTable) btnFullTable.classList.add('active');
            if (btnMobFullTable) btnMobFullTable.classList.add('active');
            document.title = 'Sisyphus Social — Tüm İşlem Sonuçları';
            this.applyFiltersAndRender();
        } else if (viewName === 'social') {
            if (socialView) socialView.style.display = 'block';
            if (btnSocial) btnSocial.classList.add('active');
            if (btnMobSocial) btnMobSocial.classList.add('active');
            document.title = 'Sisyphus Social — Sosyal İşlemler';
            if (this.socialDrawer) this.socialDrawer.loadTrades();
        }

        if (pushHistory && routePath && window.location.pathname !== routePath) {
            window.history.pushState({ view: viewName }, '', routePath);
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Strategy summary tabs
    bindSummaryTabs() {
        document.querySelectorAll('.sum-pill-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.sum-pill-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentSummaryStrategy = btn.getAttribute('data-sum-strat') || 'A';
                this.renderSummarySection();
            });
        });
    }

    // Strategy table tabs
    bindStrategyTabs() {
        const tabCards = document.querySelectorAll('.strat-card-tab');
        tabCards.forEach(card => {
            card.addEventListener('click', () => {
                tabCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                this.currentStrategy = card.getAttribute('data-strategy') || 'A';
                this.applyFiltersAndRender();
            });
        });
    }

    // Filters & sorting
    bindFiltersAndSorting() {
        const minTradesInput = document.getElementById('filter-min-trades');
        const minWinrateInput = document.getElementById('filter-min-winrate');
        const tfSelect = document.getElementById('filter-timeframe');

        [minTradesInput, minWinrateInput, tfSelect].forEach(elem => {
            if (elem) {
                elem.addEventListener('input', () => this.applyFiltersAndRender());
                elem.addEventListener('change', () => this.applyFiltersAndRender());
            }
        });

        document.querySelectorAll('.scan-table thead th').forEach(th => {
            th.addEventListener('click', () => {
                const sortKey = th.getAttribute('data-sort');
                if (!sortKey || sortKey === 'index') return;

                if (this.currentSort.key === sortKey) {
                    this.currentSort.desc = !this.currentSort.desc;
                } else {
                    this.currentSort.key = sortKey;
                    this.currentSort.desc = true;
                }
                this.applyFiltersAndRender();
            });
        });
    }

    // Modals
    bindModalsAndJsonActions() {
        const jsonInput = document.getElementById('input-json-file');
        if (jsonInput) {
            jsonInput.addEventListener('change', (e) => this.handleJsonUpload(e));
        }

        const btnExport = document.getElementById('btn-export-json');
        if (btnExport) {
            btnExport.addEventListener('click', () => this.exportCurrentJson());
        }

        const btnOpenAccount = document.getElementById('btn-open-account');
        const btnLogout = document.getElementById('btn-logout-action');
        const accountDropdown = document.getElementById('account-dropdown');

        if (btnOpenAccount) {
            btnOpenAccount.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleAccountButtonClick();
            });
        }

        // Dropdown dışına tıklanınca kapat
        document.addEventListener('click', (e) => {
            if (accountDropdown && accountDropdown.style.display === 'block') {
                if (!accountDropdown.contains(e.target) && !btnOpenAccount.contains(e.target)) {
                    accountDropdown.style.display = 'none';
                }
            }
        });

        // Oturumu Kapat
        if (btnLogout) {
            btnLogout.addEventListener('click', async () => {
                try {
                    await ApiClient.post('/auth/logout', {});
                } catch (err) {
                    // pass
                }
                window.location.href = '/auth/login';
            });
        }

        const detailModal = document.getElementById('coin-detail-modal');
        const btnCloseDetail = document.getElementById('btn-close-detail-modal');
        if (btnCloseDetail && detailModal) {
            btnCloseDetail.addEventListener('click', () => detailModal.style.display = 'none');
        }

        // Modal Dışı Tıklamada Kapatma (Sürükleme ve metin seçimlerinde kazara kapanmayı önleme)
        [detailModal, document.getElementById('share-trade-modal'), document.getElementById('edit-trade-modal')].forEach(m => {
            if (m) {
                let isMouseDownOnBackdrop = false;
                m.addEventListener('mousedown', (e) => {
                    isMouseDownOnBackdrop = (e.target === m);
                });
                m.addEventListener('mouseup', (e) => {
                    if (isMouseDownOnBackdrop && e.target === m) {
                        m.style.display = 'none';
                    }
                    isMouseDownOnBackdrop = false;
                });
            }
        });
    }

    // User management
    bindUserManagementModal() {
        const btnOpen = document.getElementById('btn-open-user-management');
        const modal = document.getElementById('user-management-modal');
        const btnClose = document.getElementById('btn-close-user-management');
        const btnCloseFooter = document.getElementById('btn-close-user-management-footer');
        const searchInput = document.getElementById('input-filter-admin-users');
        const dropdown = document.getElementById('account-dropdown');

        if (btnOpen && modal) {
            btnOpen.addEventListener('click', () => {
                if (dropdown) dropdown.style.display = 'none';
                modal.style.display = 'flex';
                this.loadAdminUsers();
            });
        }

        const closeModal = () => {
            if (modal) modal.style.display = 'none';
        };

        if (btnClose) btnClose.addEventListener('click', closeModal);
        if (btnCloseFooter) btnCloseFooter.addEventListener('click', closeModal);

        if (modal) {
            let isMouseDownOnBackdrop = false;
            modal.addEventListener('mousedown', (e) => {
                isMouseDownOnBackdrop = (e.target === modal);
            });
            modal.addEventListener('mouseup', (e) => {
                if (isMouseDownOnBackdrop && e.target === modal) {
                    closeModal();
                }
                isMouseDownOnBackdrop = false;
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const q = e.target.value.toLowerCase().trim();
                const rows = document.querySelectorAll('#admin-users-table-tbody tr.admin-user-row');
                let matchCount = 0;
                rows.forEach(row => {
                    const text = row.getAttribute('data-search-text') || '';
                    if (text.includes(q)) {
                        row.style.display = '';
                        matchCount++;
                    } else {
                        row.style.display = 'none';
                    }
                });
                const countBadge = document.getElementById('badge-admin-users-count');
                if (countBadge) countBadge.textContent = `${matchCount} üye listelendi`;
            });
        }

        const btnSaveAll = document.getElementById('btn-save-all-admin-users');
        if (btnSaveAll) {
            btnSaveAll.addEventListener('click', async () => {
                const rows = document.querySelectorAll('#admin-users-table-tbody tr.admin-user-row');
                if (rows.length === 0) return;
                btnSaveAll.disabled = true;
                btnSaveAll.textContent = '⏳ Kaydediliyor...';
                let savedCount = 0;
                for (const row of rows) {
                    const userId = row.getAttribute('data-user-id');
                    const saveBtn = row.querySelector('.btn-save-admin-user');
                    await this.saveUserAdmin(userId, saveBtn, false);
                    savedCount++;
                }
                Toast.success(`Tüm üye bilgileri başarıyla güncellendi!`);
                btnSaveAll.disabled = false;
                btnSaveAll.textContent = '💾 Değişiklikleri Kaydet';
            });
        }
    }

    async loadAdminUsers() {
        const tbody = document.getElementById('admin-users-table-tbody');
        const countBadge = document.getElementById('badge-admin-users-count');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">⏳ Üye listesi yükleniyor...</td></tr>';
        }

        try {
            const res = await ApiClient.get('/auth/admin/users');
            if (res && res.status === 'success') {
                const users = res.users || [];
                if (countBadge) countBadge.textContent = `${users.length} Kayıtlı Üye`;
                this.renderAdminUsersTable(users);
            }
        } catch (err) {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--color-red);">❌ Hata: ${err.message}</td></tr>`;
            }
        }
    }

    renderAdminUsersTable(users) {
        const tbody = document.getElementById('admin-users-table-tbody');
        if (!tbody) return;

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">Kayıtlı üye bulunamadı.</td></tr>';
            return;
        }

        tbody.innerHTML = users.map((u, idx) => {
            const isAdmin = u.role === 'admin';
            const initial = (u.name || u.username || 'U')[0].toUpperCase();
            const searchText = `${u.name} ${u.username} ${u.email} ${u.handle}`.toLowerCase();

            return `
                <tr class="admin-user-row" data-user-id="${u.id}" data-search-text="${searchText}" style="border-bottom:1px solid rgba(255,255,255,0.06);">
                    <td style="color:var(--text-muted); font-size:11px; padding:10px 8px;">#${idx + 1}</td>
                    <td style="padding:10px 8px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg, rgba(56,189,248,0.2), rgba(99,102,241,0.2)); border:1px solid rgba(56,189,248,0.3); display:flex; align-items:center; justify-content:center; font-weight:800; font-size:12px; color:#38bdf8;">
                                ${initial}
                            </div>
                            <div>
                                <div style="font-weight:700; color:var(--text-primary); font-size:13px;">${u.name} ${u.is_self ? '<span style="font-size:10.5px; color:#34d399; font-weight:800;">(Siz)</span>' : ''}</div>
                                <div style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono);">${u.handle}</div>
                            </div>
                        </div>
                    </td>
                    <td style="font-size:12px; color:var(--text-muted); font-family:var(--font-mono); padding:10px 8px;">${u.email}</td>
                    <td style="font-size:11.5px; color:var(--text-muted); padding:10px 8px;">${u.created_at || '—'}</td>
                    <td style="padding:10px 8px;">
                        <select class="admin-user-role-select" data-user-id="${u.id}" style="background:rgba(15,23,42,0.95); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:6px 10px; border-radius:6px; font-size:12px; font-weight:700; outline:none; cursor:pointer;">
                            <option value="admin" ${isAdmin ? 'selected' : ''}>👑 Admin</option>
                            <option value="user" ${!isAdmin ? 'selected' : ''}>⚡ Standart Üye</option>
                        </select>
                    </td>
                    <td style="padding:10px 8px;">
                        <input type="text" class="admin-user-badge-input" data-user-id="${u.id}" value="${u.badge || ''}" placeholder="Rozet (Örn: ⚡ PRO Trader)" style="width:145px; background:rgba(15,23,42,0.95); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:6px 10px; border-radius:6px; font-size:11.5px; outline:none;">
                    </td>
                    <td style="padding:10px 8px;">
                        <select class="admin-user-active-select" data-user-id="${u.id}" style="background:rgba(15,23,42,0.95); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:6px 10px; border-radius:6px; font-size:12px; outline:none; cursor:pointer;">
                            <option value="true" ${u.is_active ? 'selected' : ''}>🟢 Aktif</option>
                            <option value="false" ${!u.is_active ? 'selected' : ''}>🔴 Pasif</option>
                        </select>
                    </td>
                    <td style="text-align:right; position:sticky; right:0; background:rgba(15,23,42,0.98); padding:10px 8px;">
                        <div style="display:flex; justify-content:flex-end; gap:6px; align-items:center;">
                            <button class="btn btn-save-admin-user" data-user-id="${u.id}" style="padding:6px 12px; font-size:11.5px; font-weight:800; border-radius:5px; background:#10b981; color:#fff; border:none; cursor:pointer; display:inline-flex; align-items:center; gap:4px; box-shadow:0 2px 6px rgba(16,185,129,0.3);">
                                💾 Kaydet
                            </button>
                            <button class="btn btn-delete-admin-user" data-user-id="${u.id}" data-username="${u.username}" ${u.is_self ? 'disabled style="opacity:0.25; cursor:not-allowed; padding:6px 8px; font-size:11.5px;"' : 'style="padding:6px 8px; font-size:11.5px; background:rgba(248,113,113,0.15); border:1px solid rgba(248,113,113,0.3); color:var(--color-red); border-radius:5px; cursor:pointer;"'}>
                                🗑️
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Kaydet Butonları Dinleyicisi
        tbody.querySelectorAll('.btn-save-admin-user').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const userId = e.currentTarget.getAttribute('data-user-id');
                await this.saveUserAdmin(userId, e.currentTarget, true);
            });
        });

        // Sil Butonları Dinleyicisi
        tbody.querySelectorAll('.btn-delete-admin-user').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (btn.hasAttribute('disabled')) return;
                const userId = e.currentTarget.getAttribute('data-user-id');
                const username = e.currentTarget.getAttribute('data-username');
                await this.deleteUserAdmin(userId, username);
            });
        });
    }

    async saveUserAdmin(userId, btnElement, showToast = true) {
        const row = document.querySelector(`tr[data-user-id="${userId}"]`);
        if (!row) return;

        const roleSelect = row.querySelector('.admin-user-role-select');
        const badgeInput = row.querySelector('.admin-user-badge-input');
        const activeSelect = row.querySelector('.admin-user-active-select');

        const role = roleSelect ? roleSelect.value : 'user';
        const badge = badgeInput ? badgeInput.value : '';
        const is_active = activeSelect ? (activeSelect.value === 'true') : true;

        if (btnElement) {
            btnElement.disabled = true;
            btnElement.textContent = '⏳...';
        }

        try {
            const res = await ApiClient.post(`/auth/admin/users/${userId}/update`, {
                role,
                badge,
                is_active
            });

            if (res && res.status === 'success') {
                if (showToast) {
                    Toast.success(res.message || 'Üye bilgileri güncellendi!');
                }
                if (btnElement) {
                    btnElement.textContent = '✓ Kaydedildi';
                    setTimeout(() => {
                        btnElement.disabled = false;
                        btnElement.textContent = '💾 Kaydet';
                    }, 1500);
                }
            }
        } catch (err) {
            if (showToast) {
                Toast.error(`Hata: ${err.message}`);
            }
            if (btnElement) {
                btnElement.disabled = false;
                btnElement.textContent = '💾 Kaydet';
            }
        }
    }

    async deleteUserAdmin(userId, username) {
        if (!confirm(`"${username}" kullanıcısını sistemden kalıcı olarak silmek istediğinize emin misiniz?`)) {
            return;
        }

        try {
            const res = await ApiClient.delete(`/auth/admin/users/${userId}`);
            if (res && res.status === 'success') {
                Toast.success(res.message || 'Kullanıcı silindi.');
                this.loadAdminUsers();
            }
        } catch (err) {
            Toast.error(`Silme hatası: ${err.message}`);
        }
    }

    handleAccountButtonClick() {
        const dropdown = document.getElementById('account-dropdown');
        if (dropdown) {
            dropdown.style.display = (dropdown.style.display === 'none' || !dropdown.style.display) ? 'block' : 'none';
        }
    }

    // Data loading
    async loadInitialResults() {
        const badge = document.getElementById('results-count-badge');
        if (badge) badge.textContent = 'Yükleniyor...';

        const listProfit = document.getElementById('summary-profit-list');
        const listLoss = document.getElementById('summary-loss-list');
        if (listProfit && this.scanData.results_a.length === 0) {
            listProfit.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted); font-size:12px;">⏳ 17,000+ Tarama Sonucu Yükleniyor...</div>';
        }
        if (listLoss && this.scanData.results_a.length === 0) {
            listLoss.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted); font-size:12px;">⏳ 17,000+ Tarama Sonucu Yükleniyor...</div>';
        }

        try {
            const data = await ApiClient.get('/api/backtest/results');
            if (data && data.status === 'success') {
                this.scanData.results_a = data.results_a || [];
                this.scanData.results_b = data.results_b || [];
                this.scanData.results_c = data.results_c || [];
                this.scanData.results_d = data.results_d || [];
                this.scanData.results_e = data.results_e || [];
            }
        } catch (err) {
            console.error('Veri yükleme hatası:', err);
        }

        this.renderSummarySection();
        this.applyFiltersAndRender();
    }

    async handleJsonUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const parsed = JSON.parse(e.target.result);
                await ApiClient.post('/api/backtest/import', parsed);

                this.scanData.results_a = parsed.results_a || [];
                this.scanData.results_b = parsed.results_b || [];
                this.scanData.results_c = parsed.results_c || [];
                this.scanData.results_d = parsed.results_d || [];
                this.scanData.results_e = parsed.results_e || [];

                Toast.show(`Yeni tarama sonuçları aktarıldı! (${file.name})`, 'success');
                const accountModal = document.getElementById('account-modal');
                if (accountModal) accountModal.style.display = 'none';

                this.renderSummarySection();
                this.applyFiltersAndRender();
            } catch (err) {
                Toast.show(`JSON format hatası: ${err.message}`, 'error');
            }
        };
        reader.readAsText(file);
    }

    exportCurrentJson() {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.scanData, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `sisyphus_social_export_${new Date().toISOString().slice(0, 10)}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
        Toast.show('Tarama sonuçları JSON olarak indirildi', 'success');
    }

    // Render summary
    renderSummarySection() {
        const strat = this.currentSummaryStrategy;
        const key = `results_${strat.toLowerCase()}`;
        const source = this.scanData[key] || [];

        const titleProfit = document.getElementById('summary-profit-title');
        const titleLoss = document.getElementById('summary-loss-title');
        const listProfit = document.getElementById('summary-profit-list');
        const listLoss = document.getElementById('summary-loss-list');

        if (titleProfit) titleProfit.textContent = `Strateji ${strat} — En Çok Kâr Eden 10 Coin`;
        if (titleLoss) titleLoss.textContent = `Strateji ${strat} — En Çok Zarar Eden 10 Coin`;

        if (source.length === 0) {
            if (listProfit) listProfit.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted);">Veri yükleniyor...</div>';
            if (listLoss) listLoss.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted);">Veri yükleniyor...</div>';
            return;
        }

        const sorted = [...source].sort((a, b) => (b.total_pnl_pct || 0) - (a.total_pnl_pct || 0));
        const top10 = sorted.slice(0, 10);
        const bottom10 = sorted.slice(-10).reverse();

        if (listProfit) {
            listProfit.innerHTML = top10.map((r, idx) => {
                const rank = idx + 1;
                const medal = rank === 1 ? '🥇' : (rank === 2 ? '🥈' : (rank === 3 ? '🥉' : `${rank}.`));
                const pnlSign = (r.total_pnl_pct || 0) >= 0 ? '+' : '';
                const winRate = Number(r.win_rate || 0).toFixed(0);

                return `
                    <div class="summary-item-row" data-symbol="${r.symbol}" data-tf="${r.timeframe}" data-strat="${strat}">
                        <span class="sum-col-rank">${medal}</span>
                        <span class="sum-col-symbol">${r.symbol}</span>
                        <div class="sum-col-tf"><span class="cell-tf-badge">${r.timeframe}</span></div>
                        <span class="sum-col-pnl cell-pnl-pos">${pnlSign}${Number(r.total_pnl_pct).toFixed(2)}%</span>
                        <span class="sum-col-trades">${r.total_trades} işlem</span>
                        <span class="sum-col-wr">${winRate}% WR</span>
                    </div>
                `;
            }).join('');
        }

        if (listLoss) {
            listLoss.innerHTML = bottom10.map((r, idx) => {
                const rank = idx + 1;
                const pnlSign = (r.total_pnl_pct || 0) >= 0 ? '+' : '';
                const winRate = Number(r.win_rate || 0).toFixed(0);

                return `
                    <div class="summary-item-row" data-symbol="${r.symbol}" data-tf="${r.timeframe}" data-strat="${strat}">
                        <span class="sum-col-rank">${rank}.</span>
                        <span class="sum-col-symbol">${r.symbol}</span>
                        <div class="sum-col-tf"><span class="cell-tf-badge">${r.timeframe}</span></div>
                        <span class="sum-col-pnl cell-pnl-neg">${pnlSign}${Number(r.total_pnl_pct).toFixed(2)}%</span>
                        <span class="sum-col-trades">${r.total_trades} işlem</span>
                        <span class="sum-col-wr">${winRate}% WR</span>
                    </div>
                `;
            }).join('');
        }

        document.querySelectorAll('.summary-item-row').forEach(row => {
            row.addEventListener('click', () => {
                const sym = row.getAttribute('data-symbol');
                const tf = row.getAttribute('data-tf');
                const st = row.getAttribute('data-strat');
                this.currentStrategy = st;
                this.openCoinDetails(sym, tf);
            });
        });
    }

    // Render table
    applyFiltersAndRender() {
        const key = `results_${this.currentStrategy.toLowerCase()}`;
        const source = this.scanData[key] || [];

        const minTrades = parseInt(document.getElementById('filter-min-trades')?.value || '0', 10);
        const minWinrate = parseFloat(document.getElementById('filter-min-winrate')?.value || '0');
        const filterTf = document.getElementById('filter-timeframe')?.value || 'all';

        let filtered = source.filter(r => {
            if ((r.total_trades || 0) < minTrades) return false;
            if ((r.win_rate || 0) < minWinrate) return false;
            if (filterTf !== 'all' && r.timeframe !== filterTf) return false;
            return true;
        });

        const sortKey = this.currentSort.key;
        const isDesc = this.currentSort.desc;

        filtered.sort((a, b) => {
            let va = a[sortKey];
            let vb = b[sortKey];

            if (typeof va === 'string') {
                return isDesc ? vb.localeCompare(va) : va.localeCompare(vb);
            }
            return isDesc ? (vb - va) : (va - vb);
        });

        const countBadge = document.getElementById('results-count-badge');
        if (countBadge) countBadge.textContent = `${filtered.length} sonuç`;

        this.renderTable(filtered);
        this.renderMobileCards(filtered);
    }

    renderTable(results) {
        const tbody = document.getElementById('scan-results-tbody');
        if (!tbody) return;

        if (results.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="11" style="text-align:center; padding:40px; color:var(--text-muted);">
                        Filtreye uygun sonuç bulunamadı.
                    </td>
                </tr>
            `;
            return;
        }

        const visibleResults = results.slice(0, 300);

        tbody.innerHTML = visibleResults.map((r, idx) => {
            const isProfit = (r.total_pnl_pct || 0) >= 0;
            const pnlClass = isProfit ? 'cell-pnl-pos' : 'cell-pnl-neg';
            const pnlSign = isProfit ? '+' : '';

            const winRate = (r.win_rate !== undefined ? r.win_rate : r.win_rate_pct) || 0;
            const longCount = r.long_trades !== undefined ? r.long_trades : 0;
            const shortCount = r.short_trades !== undefined ? r.short_trades : 0;

            const profitFactor = r.profit_factor !== undefined ? r.profit_factor : 0.0;
            const maxDD = r.max_drawdown !== undefined ? r.max_drawdown : 0.0;

            const bestTrade = r.best_trade !== undefined ? r.best_trade : 0.0;
            const worstTrade = r.worst_trade !== undefined ? r.worst_trade : 0.0;
            const finalCapital = r.final_capital || 1000.0;

            return `
                <tr>
                    <td>${idx + 1}</td>
                    <td class="cell-coin">${r.symbol}</td>
                    <td><span class="cell-tf-badge">${r.timeframe}</span></td>
                    <td class="${pnlClass}">${pnlSign}${Number(r.total_pnl_pct).toFixed(2)}%</td>
                    <td style="font-weight:700;">${Number(winRate).toFixed(1)}%</td>
                    <td>
                        <span>${r.total_trades}</span>
                        <span style="color:var(--text-muted); font-size:11px;">(${longCount}L/${shortCount}S)</span>
                        <button class="btn-row-details" data-symbol="${r.symbol}" data-tf="${r.timeframe}">Detaylar</button>
                    </td>
                    <td>${Number(profitFactor).toFixed(2)}</td>
                    <td class="cell-pnl-neg">${Number(maxDD).toFixed(1)}%</td>
                    <td class="cell-pnl-pos">+${Number(bestTrade).toFixed(2)}%</td>
                    <td class="cell-pnl-neg">${Number(worstTrade).toFixed(2)}%</td>
                    <td style="color:var(--color-green); font-weight:700;">$${Number(finalCapital).toFixed(0)}</td>
                </tr>
            `;
        }).join('');

        tbody.querySelectorAll('.btn-row-details').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sym = e.target.getAttribute('data-symbol');
                const tf = e.target.getAttribute('data-tf');
                this.openCoinDetails(sym, tf);
            });
        });
    }

    renderMobileCards(results) {
        const container = document.getElementById('scan-results-mobile-cards');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = `
                <div style="text-align:center; padding:30px; color:var(--text-muted); font-size:12px;">
                    Filtreye uygun sonuç bulunamadı.
                </div>
            `;
            return;
        }

        const visibleResults = results.slice(0, 150);

        container.innerHTML = visibleResults.map((r, idx) => {
            const isProfit = (r.total_pnl_pct || 0) >= 0;
            const pnlClass = isProfit ? 'cell-pnl-pos' : 'cell-pnl-neg';
            const pnlSign = isProfit ? '+' : '';
            const winRate = (r.win_rate !== undefined ? r.win_rate : r.win_rate_pct) || 0;
            const profitFactor = r.profit_factor !== undefined ? r.profit_factor : 0.0;
            const maxDD = r.max_drawdown !== undefined ? r.max_drawdown : 0.0;
            const finalCapital = r.final_capital || 1000.0;

            return `
                <div class="mobile-scan-card" data-symbol="${r.symbol}" data-tf="${r.timeframe}">
                    <div class="m-card-header">
                        <div class="m-card-symbol-row">
                            <span style="font-size:11px; font-weight:700; color:var(--text-muted);">#${idx + 1}</span>
                            <span class="m-card-symbol">${r.symbol}</span>
                            <span class="cell-tf-badge">${r.timeframe}</span>
                        </div>
                        <div class="m-card-pnl ${pnlClass}">
                            ${pnlSign}${Number(r.total_pnl_pct).toFixed(2)}%
                        </div>
                    </div>

                    <div class="m-card-grid">
                        <div class="m-card-stat">
                            <span class="m-stat-lbl">Win Rate</span>
                            <span class="m-stat-val">${Number(winRate).toFixed(1)}%</span>
                        </div>
                        <div class="m-card-stat">
                            <span class="m-stat-lbl">İşlemler</span>
                            <span class="m-stat-val">${r.total_trades}</span>
                        </div>
                        <div class="m-card-stat">
                            <span class="m-stat-lbl">PF / Max DD</span>
                            <span class="m-stat-val">${Number(profitFactor).toFixed(1)} / <span style="color:var(--color-red)">${Number(maxDD).toFixed(1)}%</span></span>
                        </div>
                    </div>

                    <div class="m-card-footer">
                        <span>Bakiye: <strong style="color:var(--color-green); font-family:var(--font-mono);">$${Number(finalCapital).toFixed(0)}</strong></span>
                        <span style="color:#38bdf8; font-weight:700; font-size:11.5px;">Detayları Aç →</span>
                    </div>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.mobile-scan-card').forEach(card => {
            card.addEventListener('click', () => {
                const sym = card.getAttribute('data-symbol');
                const tf = card.getAttribute('data-tf');
                this.openCoinDetails(sym, tf);
            });
        });
    }

    // Detail modal
    async openCoinDetails(symbol, timeframe) {
        const modal = document.getElementById('coin-detail-modal');
        const title = document.getElementById('modal-coin-title');
        const tradesTbody = document.getElementById('modal-trades-tbody');

        if (title) title.textContent = `${symbol} (${timeframe} — Strateji ${this.currentStrategy})`;
        if (tradesTbody) tradesTbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px;">İşlem kayıtları yükleniyor...</td></tr>';
        if (modal) modal.style.display = 'flex';

        try {
            const res = await ApiClient.get('/api/backtest/details', {
                strategy: this.currentStrategy,
                symbol,
                timeframe
            });

            if (res && res.status === 'success') {
                const item = res.data;

                if (tradesTbody) {
                    const trades = item.trades || [];
                    if (trades.length === 0) {
                        tradesTbody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:var(--text-muted); padding:20px;">İşlem kaydı bulunamadı.</td></tr>';
                    } else {
                        tradesTbody.innerHTML = trades.map((t, idx) => {
                            const isLong = (t.type || 'long').toLowerCase() === 'long';
                            const typeClass = isLong ? 'cell-pnl-pos' : 'cell-pnl-neg';
                            const pnlPos = (t.pnl_pct || 0) >= 0;
                            const pnlSign = pnlPos ? '+' : '';
                            const pnlUsd = t.pnl_usd !== undefined ? Math.abs(t.pnl_usd) : (Math.abs(t.pnl_pct || 0) * 5);

                            const entryTime = (t.entry_time || '').replace('T', ' ').slice(0, 16);
                            const exitTime = (t.exit_time || '').replace('T', ' ').slice(0, 16);

                            const formatModalPrice = (v) => {
                                const num = Number(v || 0);
                                if (num === 0) return '0.00';
                                const abs = Math.abs(num);
                                if (abs >= 100) return num.toFixed(2);
                                if (abs >= 1) return num.toFixed(4);
                                if (abs >= 0.01) return num.toFixed(6);
                                return num.toFixed(8);
                            };
                            const ep = formatModalPrice(t.entry_price);
                            const xp = formatModalPrice(t.exit_price);

                            return `
                                <tr>
                                    <td>#${idx + 1}</td>
                                    <td class="${typeClass}" style="font-weight:800;">${(t.type || 'LONG').toUpperCase()}</td>
                                    <td>$${ep}</td>
                                    <td>$${xp}</td>
                                    <td style="color:${pnlPos ? 'var(--color-green)' : 'var(--color-red)'}; font-weight:700;">
                                        ${pnlSign}${Number(t.pnl_pct || 0).toFixed(2)}%
                                    </td>
                                    <td style="color:${pnlPos ? 'var(--color-green)' : 'var(--color-red)'}; font-weight:700;">
                                        ${pnlSign}$${Number(pnlUsd).toFixed(2)}
                                    </td>
                                    <td style="color:var(--text-muted); font-size:11.5px;">${entryTime}</td>
                                    <td style="color:var(--text-muted); font-size:11.5px;">${exitTime}</td>
                                    <td class="col-exit-reason">${t.exit_reason || 'BB30/POC'}</td>
                                </tr>
                            `;
                        }).join('');
                    }
                }

                setTimeout(() => {
                    this.drawModalEquity(item.equity_curve || []);
                }, 50);
            }
        } catch (err) {
            if (tradesTbody) tradesTbody.innerHTML = `<tr><td colspan="9" style="color:var(--color-red); padding:20px;">Hata: ${err.message}</td></tr>`;
        }
    }

    drawModalEquity(equityCurve) {
        const canvas = document.getElementById('modal-equity-canvas');
        if (!canvas) return;

        const container = canvas.parentElement;
        const width = container.clientWidth || 800;
        const height = 160;

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, width, height);

        if (!equityCurve || equityCurve.length === 0) {
            ctx.fillStyle = '#64748b';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Özkaynak eğrisi verisi mevcut değil', width / 2, height / 2);
            return;
        }

        const values = equityCurve.map(d => Number(d.equity || 1000));
        let minVal = Math.min(...values);
        let maxVal = Math.max(...values);
        if (minVal === maxVal) {
            minVal *= 0.95;
            maxVal *= 1.05;
        }
        const range = maxVal - minVal || 1;

        const padLeft = 55;
        const padRight = 20;
        const padTop = 20;
        const padBottom = 25;
        const plotW = width - padLeft - padRight;
        const plotH = height - padTop - padBottom;

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 3; i++) {
            const y = padTop + (plotH / 3) * i;
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(width - padRight, y);
            ctx.stroke();

            const val = maxVal - (range / 3) * i;
            ctx.fillStyle = '#64748b';
            ctx.font = '10px monospace';
            ctx.textAlign = 'right';
            ctx.fillText(`$${val.toFixed(0)}`, padLeft - 6, y + 3);
        }

        const points = equityCurve.map((d, idx) => ({
            x: padLeft + (idx / (equityCurve.length - 1 || 1)) * plotW,
            y: padTop + (1 - (Number(d.equity) - minVal) / range) * plotH
        }));

        const isOverallProfit = values[values.length - 1] >= values[0];
        const lineColor = isOverallProfit ? '#34d399' : '#f87171';
        const gradTop = isOverallProfit ? 'rgba(52, 211, 153, 0.25)' : 'rgba(248, 113, 113, 0.25)';

        const grad = ctx.createLinearGradient(0, padTop, 0, height - padBottom);
        grad.addColorStop(0, gradTop);
        grad.addColorStop(1, 'rgba(0, 0, 0, 0.0)');

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
        ctx.lineTo(points[points.length - 1].x, height - padBottom);
        ctx.lineTo(points[0].x, height - padBottom);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.stroke();

        points.forEach((p, idx) => {
            if (idx === 0 || idx === points.length - 1 || points.length <= 10) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
                ctx.fillStyle = lineColor;
                ctx.fill();
            }
        });
    }
}

const initScannerApp = () => {
    if (!window.__SCANNER_APP__) {
        window.__SCANNER_APP__ = new ScannerApp();
        window.__SCANNER_APP__.init();
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScannerApp);
} else {
    initScannerApp();
}

/**
 * Sisyphus Social Profile Page Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Profil Filtre Sekmeleri (Tümü / Aktif Pozisyonlar / Emirler / Kapananlar)
    const filterTabs = document.querySelectorAll('.profile-tab-btn');
    const tradeCards = document.querySelectorAll('.profile-trade-item');

    filterTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            filterTabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const targetFilter = btn.getAttribute('data-filter');

            tradeCards.forEach(card => {
                const status = card.getAttribute('data-status');
                if (targetFilter === 'all') {
                    card.style.display = 'block';
                } else if (targetFilter === 'active' && status === 'active') {
                    card.style.display = 'block';
                } else if (targetFilter === 'pending' && status === 'pending') {
                    card.style.display = 'block';
                } else if (targetFilter === 'completed' && status === 'completed') {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // 2. Takip Et / Takipten Çık Butonu
    const followBtn = document.getElementById('btn-toggle-follow-profile');
    if (followBtn) {
        followBtn.addEventListener('click', async () => {
            const handle = followBtn.getAttribute('data-handle');
            try {
                const res = await fetch(`/api/social/trader/${encodeURIComponent(handle)}/follow`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.status === 'success') {
                    if (data.is_following) {
                        followBtn.className = 'btn btn-following';
                        followBtn.textContent = '✓ Takip Ediliyor';
                    } else {
                        followBtn.className = 'btn btn-follow';
                        followBtn.textContent = '+ Takip Et';
                    }
                    // Takipçi sayısını canlı güncelle
                    const followersElem = document.getElementById('val-followers-count');
                    if (followersElem) {
                        let currentCount = parseInt(followersElem.textContent, 10) || 0;
                        followersElem.textContent = data.is_following ? currentCount + 1 : Math.max(0, currentCount - 1);
                    }
                }
            } catch (err) {
                console.error('Takip işlemi hatası:', err);
            }
        });
    }

    // 3. Şifre Değiştirme Modalı
    const btnOpenPwd = document.getElementById('btn-open-change-password');
    const pwdModal = document.getElementById('change-password-modal');
    const btnClosePwd = document.getElementById('btn-close-pwd-modal');
    const btnCancelPwd = document.getElementById('btn-cancel-pwd');
    const formPwd = document.getElementById('form-change-password');
    const pwdAlert = document.getElementById('pwd-alert');

    if (btnOpenPwd && pwdModal) {
        btnOpenPwd.addEventListener('click', () => {
            pwdModal.style.display = 'flex';
            if (pwdAlert) pwdAlert.style.display = 'none';
        });
        [btnClosePwd, btnCancelPwd].forEach(b => {
            if (b) b.addEventListener('click', () => { pwdModal.style.display = 'none'; });
        });

        // Şifre Göster/Gizle Butonları
        document.querySelectorAll('.btn-toggle-password').forEach(b => {
            b.addEventListener('click', () => {
                const targetId = b.getAttribute('data-target');
                const inp = document.getElementById(targetId);
                if (inp) {
                    inp.type = inp.type === 'password' ? 'text' : 'password';
                }
            });
        });

        if (formPwd) {
            formPwd.addEventListener('submit', async (e) => {
                e.preventDefault();
                const oldPwd = document.getElementById('input-old-pwd').value;
                const newPwd = document.getElementById('input-new-pwd').value;
                const confirmPwd = document.getElementById('input-confirm-pwd').value;

                if (newPwd !== confirmPwd) {
                    showPwdAlert('Yeni şifreler birbiriyle eşleşmiyor.', 'error');
                    return;
                }

                try {
                    const res = await fetch('/auth/change-password', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ old_password: oldPwd, new_password: newPwd, confirm_password: confirmPwd })
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        showPwdAlert(data.message || 'Şifreniz başarıyla güncellendi.', 'success');
                        formPwd.reset();
                        setTimeout(() => { pwdModal.style.display = 'none'; }, 1500);
                    } else {
                        showPwdAlert(data.message || 'Şifre güncellenemedi.', 'error');
                    }
                } catch (err) {
                    showPwdAlert('Sunucu bağlantı hatası.', 'error');
                }
            });
        }

        function showPwdAlert(msg, type) {
            if (!pwdAlert) return;
            pwdAlert.style.display = 'block';
            pwdAlert.textContent = msg;
            if (type === 'success') {
                pwdAlert.style.background = 'rgba(16, 185, 129, 0.15)';
                pwdAlert.style.border = '1px solid rgba(16, 185, 129, 0.3)';
                pwdAlert.style.color = '#34d399';
            } else {
                pwdAlert.style.background = 'rgba(239, 68, 68, 0.15)';
                pwdAlert.style.border = '1px solid rgba(239, 68, 68, 0.3)';
                pwdAlert.color = '#f87171';
            }
        }
    }
});

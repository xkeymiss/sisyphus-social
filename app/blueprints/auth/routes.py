"""
Authentication and user session routes.
"""

from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from app.blueprints.auth import auth_bp
from app.models.user import User
from app.extensions import db


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect('/')
        session.pop('_flashes', None)
        return render_template('auth/login.html')


    is_json = request.is_json or request.headers.get('Accept') == 'application/json'
    data = request.get_json(silent=True) or request.form

    identity = (data.get('email') or data.get('username') or '').strip()
    password = data.get('password', '')
    remember = bool(data.get('remember', True))

    if not identity or not password:
        msg = 'Lütfen e-posta / kullanıcı adı ve şifrenizi giriniz.'
        if is_json:
            return jsonify({'status': 'error', 'code': 400, 'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/login.html', identity=identity), 400


    user = User.query.filter(
        (User.email == identity.lower()) | (User.username == identity)
    ).first()

    if not user or not user.check_password(password):
        msg = 'Hatalı kullanıcı bilgisi veya şifre.'
        if is_json:
            return jsonify({'status': 'error', 'code': 401, 'message': msg}), 401
        flash(msg, 'error')
        return render_template('auth/login.html', identity=identity), 401

    if not user.is_active:
        msg = 'Bu hesap devre dışı bırakılmıştır.'
        if is_json:
            return jsonify({'status': 'error', 'code': 403, 'message': msg}), 403
        flash(msg, 'error')
        return render_template('auth/login.html', identity=identity), 403

    login_user(user, remember=remember)

    if is_json:
        return jsonify({
            'status': 'success',
            'message': 'Giriş başarılı!',
            'user': user.to_dict()
        }), 200

    return redirect('/')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('core.index'))
        session.pop('_flashes', None)
        return render_template('auth/register.html')

    is_json = request.is_json or request.headers.get('Accept') == 'application/json'
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip().lower()
    name = (data.get('name') or (username.capitalize() if username else '')).strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')
    password_confirm = data.get('password_confirm', password)

    # Validasyonlar
    if not username or not email or not password:
        msg = 'Lütfen tüm zorunlu alanları doldurunuz.'
        if is_json:
            return jsonify({'status': 'error', 'code': 400, 'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html', username=username, email=email), 400

    if len(password) < 6:
        msg = 'Şifreniz en az 6 karakter olmalıdır.'
        if is_json:
            return jsonify({'status': 'error', 'code': 400, 'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html', username=username, email=email), 400

    if password != password_confirm:
        msg = 'Girilen şifreler birbiriyle eşleşmiyor.'
        if is_json:
            return jsonify({'status': 'error', 'code': 400, 'message': msg}), 400
        flash(msg, 'error')
        return render_template('auth/register.html', username=username, email=email), 400

    # Benzersizlik Kontrolleri
    if User.query.filter_by(email=email).first():
        msg = 'Bu e-posta adresi zaten kullanımda.'
        if is_json:
            return jsonify({'status': 'error', 'code': 409, 'message': msg}), 409
        flash(msg, 'error')
        return render_template('auth/register.html', username=username, email=email), 409

    if User.query.filter_by(username=username).first():
        msg = 'Bu kullanıcı adı zaten kullanımda.'
        if is_json:
            return jsonify({'status': 'error', 'code': 409, 'message': msg}), 409
        flash(msg, 'error')
        return render_template('auth/register.html', username=username, email=email), 409

    # Yeni Kullanıcı Oluşturma
    user = User(
        name=name or username.capitalize(),
        username=username,
        email=email,
        handle=f"@{username}",
        badge='Trader',
        role='user',
        is_active=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    login_user(user)

    if is_json:
        return jsonify({
            'status': 'success',
            'message': 'Hesabınız başarıyla oluşturuldu ve oturum açıldı!',
            'user': user.to_dict()
        }), 201

    return redirect('/')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """User logout route."""
    if current_user.is_authenticated:
        logout_user()
    session.pop('_flashes', None)

    if request.method == 'POST' or request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'status': 'success',
            'message': 'Oturum başarıyla kapatıldı.'
        }), 200

    return redirect('/auth/login')


@auth_bp.route('/status', methods=['GET'])
@auth_bp.route('/me', methods=['GET'])
def auth_status():
    """Get current user authentication status."""
    if current_user.is_authenticated:
        return jsonify({
            'status': 'success',
            'is_authenticated': True,
            'user': current_user.to_dict()
        }), 200
    else:
        return jsonify({
            'status': 'success',
            'is_authenticated': False,
            'user': None
        }), 200


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change current user password."""
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'code': 401, 'message': 'Oturum açmanız gerekiyor.'}), 401

    data = request.get_json(silent=True) or request.form

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    new_password_confirm = data.get('new_password_confirm', '')

    if not old_password or not new_password or not new_password_confirm:
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Lütfen tüm şifre alanlarını eksiksiz doldurunuz.'
        }), 400

    if not current_user.check_password(old_password):
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Mevcut (eski) şifrenizi hatalı girdiniz.'
        }), 401

    if len(new_password) < 6:
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Yeni şifreniz en az 6 karakter olmalıdır.'
        }), 400

    if new_password != new_password_confirm:
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Yeni şifreler birbiriyle eşleşmiyor.'
        }), 400

    if old_password == new_password:
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Yeni şifreniz eski şifrenizle aynı olamaz.'
        }), 400

    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Şifreniz başarıyla güncellendi!'
    }), 200


@auth_bp.route('/admin/users', methods=['GET'])
def get_all_users_admin():
    """List all registered users (admin only)."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    users = User.query.order_by(User.id.asc()).all()
    users_list = []
    for u in users:
        from app.utils.time_utils import format_tr_datetime
        users_list.append({
            'id': u.id,
            'name': u.name,
            'username': u.username,
            'email': u.email,
            'handle': u.handle,
            'role': u.role,
            'badge': u.badge or ('👑 Sistem Yöneticisi & Trader' if u.role == 'admin' else 'Trader'),
            'is_active': u.is_active,
            'created_at': format_tr_datetime(getattr(u, 'created_at', None)),
            'is_self': (u.id == current_user.id)
        })

    return jsonify({
        'status': 'success',
        'count': len(users_list),
        'users': users_list
    }), 200


@auth_bp.route('/admin/users/<int:user_id>/update', methods=['POST'])
def update_user_admin(user_id: int):
    """Update user profile and permissions (admin only)."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    user = db.session.get(User, user_id) if hasattr(db.session, 'get') else User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Kullanıcı bulunamadı.'}), 404

    data = request.get_json(silent=True) or request.form

    if 'role' in data:
        new_role = data['role'].strip().lower()
        if new_role in ['admin', 'user']:
            user.role = new_role
            if new_role == 'admin' and (not user.badge or user.badge == 'Trader' or user.badge == '⚡ PRO Trader'):
                user.badge = '👑 Sistem Yöneticisi & Trader'
            elif new_role == 'user' and user.badge == '👑 Sistem Yöneticisi & Trader':
                user.badge = '⚡ PRO Trader'

    if 'badge' in data and data['badge'].strip():
        user.badge = data['badge'].strip()

    if 'name' in data and data['name'].strip():
        user.name = data['name'].strip()

    if 'is_active' in data:
        val = data['is_active']
        user.is_active = bool(val is True or str(val).lower() == 'true')

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f"{user.username} kullanıcısı başarıyla güncellendi.",
        'user': user.to_dict()
    }), 200


@auth_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user_admin(user_id: int):
    """Delete user (admin)."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'status': 'error', 'code': 403, 'message': 'Yetkisiz erişim.'}), 403

    if user_id == current_user.id:
        return jsonify({'status': 'error', 'message': 'Kendi yönetici hesabınızı silemezsiniz.'}), 400

    user = db.session.get(User, user_id) if hasattr(db.session, 'get') else User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Kullanıcı bulunamadı.'}), 404

    username = user.username
    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f"{username} kullanıcısı sistemden silindi."
    }), 200


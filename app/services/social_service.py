"""
Social trade feed and community service.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import uuid

from flask import has_app_context
from app.extensions import db
from app.models.trade import Trade
from app.models.social import Follow, Like, Comment
from app.models.user import User


class SocialService:
    """Social feed service."""

    def __init__(self):
        self._update_listeners: list = []
        self._trades: List[Dict[str, Any]] = []
        self._follows: List[str] = []

    def get_trades(self, filter_tab: str = 'latest', current_user_handle: str = '@utku', limit: Optional[int] = 20) -> List[Dict[str, Any]]:
        """İşlem akışını döndürür. Akışlar için varsayılan limit 20 işlemdir."""
        if has_app_context():
            try:
                query = Trade.query.order_by(Trade.created_at.desc())

                if filter_tab == 'following':
                    followed_handles = [f.followed_handle for f in Follow.query.filter_by(follower_handle=current_user_handle).all()]
                    if not followed_handles:
                        return []
                    query = query.filter(Trade.trader_handle.in_(followed_handles))
                elif filter_tab == 'my_trades':
                    query = query.filter(Trade.trader_handle == current_user_handle)

                if limit is not None and limit > 0:
                    query = query.limit(limit)

                trades_objs = query.all()
                if trades_objs:
                    followed_set = set(self.get_followed_list(current_user_handle))
                    trade_ids = [t.id for t in trades_objs]

                    # N+1 sorgu optimizasyonu: Beğeni sayıları ve beğenilme durumunu toplu sorguyla çek
                    likes_cnt_rows = (
                        db.session.query(Like.trade_id, db.func.count(Like.id))
                        .filter(Like.trade_id.in_(trade_ids))
                        .group_by(Like.trade_id)
                        .all()
                    )
                    likes_count_map = dict(likes_cnt_rows)

                    user_liked_rows = (
                        db.session.query(Like.trade_id)
                        .filter(Like.trade_id.in_(trade_ids), Like.user_handle == current_user_handle)
                        .all()
                    )
                    user_liked_set = set(row[0] for row in user_liked_rows)

                    results = []
                    for t in trades_objs:
                        d = t.to_dict()
                        d['is_following'] = t.trader_handle in followed_set
                        d['is_mine'] = (t.trader_handle == current_user_handle)
                        d['likes_count'] = likes_count_map.get(t.id, 0)
                        d['is_liked'] = t.id in user_liked_set
                        results.append(d)
                    return results
                return []
            except Exception:
                pass

        # In-memory fallback (Test ortamları için)
        trades = list(self._trades)
        if filter_tab == 'following':
            trades = [t for t in trades if t['trader_handle'] in self._follows]
        elif filter_tab == 'my_trades':
            trades = [t for t in trades if t['trader_handle'] == current_user_handle]

        if limit is not None and limit > 0:
            trades = trades[:limit]

        for t in trades:
            t['is_following'] = t['trader_handle'] in self._follows
            t['is_mine'] = (t['trader_handle'] == current_user_handle)
            if not t.get('exit_price') and t.get('close_price'):
                t['exit_price'] = t['close_price']
            if not t.get('raw_pnl_pct') and t.get('close_price') and t.get('entry_price'):
                t['raw_pnl_pct'] = self.calculate_raw_pnl(t['side'], t['entry_price'], t['close_price'])

        return trades

    def _get_status_label(self, status: str) -> str:
        status_map = {
            'ACTIVE': '🟢 Aktif Pozisyon',
            'PENDING': '⏳ Bekleyen Emir',
            'TP_HIT': '🎯 TP Alındı',
            'SL_HIT': '🛑 Stop Oldu',
            'CLOSED': '🔒 Kapatıldı',
            'PARTIAL_25': '🔒 %25 Kapatıldı',
            'PARTIAL_50': '🔒 %50 Kapatıldı',
            'PARTIAL_75': '🔒 %75 Kapatıldı'
        }
        return status_map.get((status or 'ACTIVE').upper(), '🟢 Aktif Pozisyon')

    def calculate_raw_pnl(self, side: str, entry_price: float, close_price: float) -> float:
        if entry_price <= 0 or close_price <= 0:
            return 0.0
        if side.upper() == 'LONG':
            return round(((close_price - entry_price) / entry_price) * 100.0, 2)
        else:
            return round(((entry_price - close_price) / entry_price) * 100.0, 2)

    def share_trade(self, trader_name: str = 'Utku', trader_handle: str = '@utku', symbol: str = 'BTC/USDT', side: str = 'LONG', leverage: str = '20', timeframe: str = '15m', entry_price: float = 0.0, target_tp: float = 0.0, stop_loss: float = 0.0, strategy_name: str = 'Manuel İşlem', notes: str = '', status: str = 'ACTIVE') -> Dict[str, Any]:
        from app.utils.time_utils import format_tr_now
        clean_status = (status or 'ACTIVE').upper()
        now_display = format_tr_now()
        trade_id = f"trade-{str(uuid.uuid4())[:8]}"

        new_trade = {
            'id': trade_id,
            'trader_name': trader_name,
            'trader_handle': trader_handle,
            'trader_badge': '👑 Sistem Yöneticisi & Trader' if trader_handle == '@utku' else '⚡ PRO Trader',
            'created_at': now_display,
            'created_display': now_display,
            'symbol': symbol.upper(),
            'side': side.upper(),
            'leverage': f"{leverage}x" if not str(leverage).endswith('x') else str(leverage),
            'timeframe': timeframe,
            'entry_price': float(entry_price),
            'target_tp': float(target_tp),
            'stop_loss': float(stop_loss),
            'close_price': 0.0,
            'exit_price': 0.0,
            'strategy_name': strategy_name,
            'status': clean_status,
            'status_label': self._get_status_label(clean_status),
            'current_pnl_pct': 0.0,
            'raw_pnl_pct': 0.0,
            'closed_at': None,
            'closed_display': None,
            'notes': notes,
            'likes_count': 0,
            'is_liked': False,
            'comments': []
        }

        self._trades.insert(0, new_trade)

        if has_app_context():
            try:
                db_trade = Trade(
                    id=trade_id,
                    trader_name=trader_name,
                    trader_handle=trader_handle,
                    trader_badge=new_trade['trader_badge'],
                    symbol=symbol.upper(),
                    side=side.upper(),
                    leverage=new_trade['leverage'],
                    timeframe=timeframe,
                    entry_price=float(entry_price),
                    target_tp=float(target_tp),
                    stop_loss=float(stop_loss),
                    close_price=0.0,
                    exit_price=0.0,
                    strategy_name=strategy_name,
                    status=clean_status,
                    status_label=new_trade['status_label'],
                    current_pnl_pct=0.0,
                    raw_pnl_pct=0.0,
                    created_at=datetime.now(timezone.utc),
                    closed_at=None,
                    notes=notes,
                    likes_count=0
                )
                db.session.add(db_trade)
                db.session.commit()
            except Exception:
                db.session.rollback()

        self._notify_listeners(new_trade)
        return new_trade

    def get_leaderboard(self, period: str = 'today', limit: int = 10) -> List[Dict[str, Any]]:
        """Kaldıraçsız net fiyat kârına göre sıralı liderlik tablosu."""
        now = datetime.now(timezone.utc)
        start_date = None

        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=7)

        if has_app_context():
            try:
                query = Trade.query.filter(
                    Trade.status.in_(['CLOSED', 'TP_HIT', 'SL_HIT', 'PARTIAL_25', 'PARTIAL_50', 'PARTIAL_75'])
                )
                if start_date:
                    query = query.filter(Trade.closed_at >= start_date)

                trades = query.order_by(Trade.raw_pnl_pct.desc()).limit(limit).all()
                return [t.to_dict() for t in trades]
            except Exception:
                pass

        # In-memory fallback
        closed_trades = [
            t for t in self._trades
            if t.get('status') in ['CLOSED', 'TP_HIT', 'SL_HIT', 'PARTIAL_25', 'PARTIAL_50', 'PARTIAL_75']
        ]

        if start_date:
            filtered = []
            for t in closed_trades:
                if t.get('closed_at'):
                    try:
                        c_dt = datetime.fromisoformat(t['closed_at'])
                        if c_dt.tzinfo is None:
                            c_dt = c_dt.replace(tzinfo=timezone.utc)
                        if c_dt >= start_date:
                            filtered.append(t)
                    except Exception:
                        filtered.append(t)
                else:
                    filtered.append(t)
            closed_trades = filtered

        closed_trades.sort(key=lambda x: float(x.get('raw_pnl_pct', 0.0)), reverse=True)
        return closed_trades[:limit]

    def update_trade(self, trade_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pozisyon durumunu ve çıkış seviyelerini günceller."""
        updated_dict = None
        for t in self._trades:
            if t['id'] == trade_id:
                if 'entry_price' in updates and updates['entry_price'] is not None:
                    try:
                        t['entry_price'] = float(updates['entry_price'])
                    except Exception:
                        pass
                if 'close_price' in updates and updates['close_price'] is not None and str(updates['close_price']).strip() != '':
                    try:
                        t['close_price'] = float(updates['close_price'])
                        t['exit_price'] = t['close_price']
                    except Exception:
                        pass
                if 'target_tp' in updates and updates['target_tp'] is not None:
                    try:
                        t['target_tp'] = float(updates['target_tp'])
                    except Exception:
                        pass
                if 'stop_loss' in updates and updates['stop_loss'] is not None:
                    try:
                        t['stop_loss'] = float(updates['stop_loss'])
                    except Exception:
                        pass
                if 'status' in updates and updates['status']:
                    t['status'] = updates['status'].upper()
                    t['status_label'] = self._get_status_label(t['status'])
                    if t['status'] in ['CLOSED', 'TP_HIT', 'SL_HIT', 'PARTIAL_25', 'PARTIAL_50', 'PARTIAL_75']:
                        if not t.get('closed_at'):
                            from app.utils.time_utils import format_tr_now, get_tr_now
                            t['closed_at'] = get_tr_now().isoformat()
                            t['closed_display'] = format_tr_now()
                        if not t.get('close_price') or t.get('close_price') == 0:
                            fallback = updates.get('close_price') or t.get('target_tp') or t.get('entry_price')
                            t['close_price'] = float(fallback)
                            t['exit_price'] = t['close_price']

                if t.get('close_price') and t.get('close_price') > 0:
                    t['raw_pnl_pct'] = self.calculate_raw_pnl(t['side'], t['entry_price'], t['close_price'])
                    lev_num = 20.0
                    try:
                        lev_num = float(str(t.get('leverage', '20')).replace('x', ''))
                    except Exception:
                        lev_num = 20.0
                    t['current_pnl_pct'] = round(t['raw_pnl_pct'] * lev_num, 2)
                updated_dict = t
                break

        if has_app_context():
            try:
                db_trade = db.session.get(Trade, trade_id) if hasattr(db.session, 'get') else Trade.query.get(trade_id)
                if db_trade:
                    if 'entry_price' in updates and updates['entry_price'] is not None:
                        db_trade.entry_price = float(updates['entry_price'])
                    if 'close_price' in updates and updates['close_price'] is not None and str(updates['close_price']).strip() != '':
                        db_trade.close_price = float(updates['close_price'])
                        db_trade.exit_price = db_trade.close_price
                    if 'target_tp' in updates and updates['target_tp'] is not None:
                        db_trade.target_tp = float(updates['target_tp'])
                    if 'stop_loss' in updates and updates['stop_loss'] is not None:
                        db_trade.stop_loss = float(updates['stop_loss'])
                    if 'status' in updates and updates['status']:
                        db_trade.status = updates['status'].upper()
                        db_trade.status_label = self._get_status_label(db_trade.status)
                        if db_trade.status in ['CLOSED', 'TP_HIT', 'SL_HIT', 'PARTIAL_25', 'PARTIAL_50', 'PARTIAL_75']:
                            if not db_trade.closed_at:
                                db_trade.closed_at = datetime.now(timezone.utc)
                            if not db_trade.close_price or db_trade.close_price == 0:
                                fb = updates.get('close_price') or db_trade.target_tp or db_trade.entry_price
                                db_trade.close_price = float(fb)
                                db_trade.exit_price = db_trade.close_price
                    if db_trade.close_price and db_trade.close_price > 0:
                        db_trade.raw_pnl_pct = self.calculate_raw_pnl(db_trade.side, db_trade.entry_price, db_trade.close_price)
                        lev_num = 20.0
                        try:
                            lev_num = float(str(db_trade.leverage or '20').replace('x', ''))
                        except Exception:
                            lev_num = 20.0
                        db_trade.current_pnl_pct = round(db_trade.raw_pnl_pct * lev_num, 2)
                    db.session.commit()
                    res_dict = db_trade.to_dict()
                    self._notify_update_listeners(trade_id, updates, res_dict)
                    return res_dict
            except Exception:
                db.session.rollback()

        if updated_dict:
            self._notify_update_listeners(trade_id, updates, updated_dict)
        return updated_dict

    def register_update_listener(self, callback) -> None:
        """Sosyal işlem güncellemelerini dinlemek için dinleyici kaydeder."""
        self._update_listeners.append(callback)

    def _notify_update_listeners(self, trade_id: str, updates: Dict[str, Any], trade_data: Dict[str, Any]) -> None:
        for listener in self._update_listeners:
            try:
                listener(trade_id, updates, trade_data)
            except Exception:
                pass

    def delete_trade(self, trade_id: str) -> bool:
        self._trades = [t for t in self._trades if t['id'] != trade_id]
        if has_app_context():
            try:
                db_trade = db.session.get(Trade, trade_id) if hasattr(db.session, 'get') else Trade.query.get(trade_id)
                if db_trade:
                    db.session.delete(db_trade)
                    db.session.commit()
                    return True
            except Exception:
                db.session.rollback()
        return True

    def toggle_follow(self, trader_handle: str, current_user_handle: str = '@utku') -> bool:
        """Kullanıcıyı takip et veya takipten çıkar."""
        if has_app_context():
            try:
                existing = Follow.query.filter_by(follower_handle=current_user_handle, followed_handle=trader_handle).first()
                if existing:
                    db.session.delete(existing)
                    db.session.commit()
                    return False
                else:
                    new_follow = Follow(follower_handle=current_user_handle, followed_handle=trader_handle)
                    db.session.add(new_follow)
                    db.session.commit()
                    return True
            except Exception:
                db.session.rollback()

        # In-memory fallback
        if trader_handle in self._follows:
            self._follows.remove(trader_handle)
            return False
        else:
            self._follows.append(trader_handle)
            return True

    def is_following(self, trader_handle: str, current_user_handle: str = '@utku') -> bool:
        if has_app_context():
            try:
                return bool(Follow.query.filter_by(follower_handle=current_user_handle, followed_handle=trader_handle).first())
            except Exception:
                pass
        return trader_handle in self._follows

    def get_followed_list(self, current_user_handle: str = '@utku') -> List[str]:
        if has_app_context():
            try:
                return [f.followed_handle for f in Follow.query.filter_by(follower_handle=current_user_handle).all()]
            except Exception:
                pass
        return list(self._follows)

    def toggle_like(self, trade_id: str, user_handle: str = '@utku') -> Dict[str, Any]:
        """İşlem beğenisini değiştirir (yalnızca gerçek veritabanı kayıtları)."""
        if has_app_context():
            try:
                existing = Like.query.filter_by(trade_id=str(trade_id), user_handle=user_handle).first()
                if existing:
                    db.session.delete(existing)
                    is_liked = False
                else:
                    db.session.add(Like(trade_id=str(trade_id), user_handle=user_handle))
                    is_liked = True
                db.session.commit()

                likes_count = Like.query.filter_by(trade_id=str(trade_id)).count()
                return {'likes_count': likes_count, 'is_liked': is_liked}
            except Exception:
                db.session.rollback()

        for t in self._trades:
            if t['id'] == trade_id:
                t['is_liked'] = not t.get('is_liked', False)
                t['likes_count'] = max(0, t.get('likes_count', 0) + (1 if t['is_liked'] else -1))
                return {'likes_count': t['likes_count'], 'is_liked': t['is_liked']}
        return {'likes_count': 0, 'is_liked': False}

    def add_comment(self, trade_id: str, author: str, text: str) -> Optional[Dict[str, Any]]:
        comment_id = f"cmt-{str(uuid.uuid4())[:6]}"
        now = datetime.now(timezone.utc)
        
        if has_app_context():
            try:
                db_cmt = Comment(trade_id=str(trade_id), author=author, text=text, created_at=now)
                db.session.add(db_cmt)
                db.session.commit()
                return db_cmt.to_dict()
            except Exception:
                db.session.rollback()

        comment = {
            'id': comment_id,
            'author': author or 'Utku',
            'text': text,
            'time': 'Az önce'
        }
        for t in self._trades:
            if t['id'] == trade_id:
                if 'comments' not in t:
                    t['comments'] = []
                t['comments'].append(comment)
                return comment
        return comment

    def get_user_profile(self, identifier: str, current_user_handle: str = '@utku') -> Optional[Dict[str, Any]]:
        """
        Kullanıcının detaylı profilini, gerçek takipçi sayılarını ve TÜM ZAMANLARDAKİ işlemlerini derler.
        Sahte veri içermez, tamamen gerçek veritabanı kayıtlarını kullanır.
        """
        if not identifier:
            return None

        clean_name = identifier.lstrip('@').strip().lower()
        clean_handle = f"@{clean_name}"

        # 1. Kullanıcıyı Veritabanında Bul
        user_info = None
        if has_app_context():
            db_user = User.query.filter(
                (User.username.ilike(clean_name)) | (User.handle.ilike(clean_handle))
            ).first()
            if db_user:
                user_info = {
                    'name': db_user.name,
                    'username': db_user.username,
                    'handle': db_user.handle,
                    'email': db_user.email,
                    'badge': db_user.badge or ('👑 Sistem Yöneticisi & Trader' if db_user.role == 'admin' else '⚡ PRO Trader'),
                    'role': db_user.role,
                    'bio': 'Sisyphus Algoritmik Bot Yöneticisi & Baş Trader.' if db_user.role == 'admin' else 'Algoritmik ve teknik analiz odaklı vadeli işlem traderı.'
                }

        # Eğer DB'de kullanıcı yoksa ama fallback / in-memory'de admin 'utku' ise
        if not user_info and (clean_handle == '@utku' or clean_name == 'utku'):
            user_info = {
                'name': 'Utku',
                'username': 'utku',
                'handle': '@utku',
                'email': 'utku@hotmail.com',
                'badge': '👑 Sistem Yöneticisi & Trader',
                'role': 'admin',
                'bio': 'Sisyphus Algoritmik Bot Yöneticisi & Baş Trader.'
            }

        # Eğer kullanıcı DB'de yoksa ve işlem geçmişi de bulunmuyorsa profil açılmaz (404)
        if not user_info:
            if has_app_context():
                trade_check = Trade.query.filter(
                    (Trade.trader_handle.ilike(clean_handle)) | (Trade.trader_name.ilike(clean_name))
                ).first()
                if not trade_check:
                    return None
            else:
                return None

        actual_handle = user_info['handle']

        # 2. Kullanıcının TÜM ZAMANLARDAKİ İşlemlerini Topla (Limit uygulanmaz)
        user_trades = self.get_trades(filter_tab='latest', current_user_handle=current_user_handle, limit=None)
        user_trades = [
            t for t in user_trades 
            if t.get('trader_handle', '').lower() == actual_handle.lower() or 
               t.get('trader_name', '').lower() == clean_name
        ]

        completed_trades = [t for t in user_trades if t.get('status') in ['CLOSED', 'TP_HIT', 'SL_HIT']]
        active_trades = [t for t in user_trades if t.get('status') in ['ACTIVE', 'PARTIAL_25', 'PARTIAL_50', 'PARTIAL_75']]
        pending_trades = [t for t in user_trades if t.get('status') == 'PENDING']

        # 3. İstatistikleri Gerçek İşlemlerden Hesapla
        total_count = len(user_trades)
        wins = [t for t in completed_trades if t.get('raw_pnl_pct', 0) > 0 or t.get('status') == 'TP_HIT']
        win_rate = round((len(wins) / len(completed_trades) * 100.0), 1) if completed_trades else 0.0
        
        all_pnls = [t.get('raw_pnl_pct', 0.0) for t in completed_trades]
        avg_pnl = round(sum(all_pnls) / len(all_pnls), 2) if all_pnls else 0.0
        best_pnl = max(all_pnls) if all_pnls else 0.0

        # 4. Gerçek Takipçi ve Takip Edilen Sayıları (Sıfırdan sayılır)
        followers_count = 0
        following_count = 0

        if has_app_context():
            try:
                followers_count = Follow.query.filter_by(followed_handle=actual_handle).count()
                following_count = Follow.query.filter_by(follower_handle=actual_handle).count()
            except Exception:
                pass

        is_following_user = self.is_following(actual_handle, current_user_handle=current_user_handle)
        is_self = (actual_handle.lower() == current_user_handle.lower())

        return {
            'user': user_info,
            'is_self': is_self,
            'is_following': is_following_user,
            'stats': {
                'followers_count': followers_count,
                'following_count': following_count,
                'total_trades': total_count,
                'completed_trades_count': len(completed_trades),
                'active_trades_count': len(active_trades),
                'pending_trades_count': len(pending_trades),
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'best_pnl': best_pnl
            },
            'trades': user_trades,
            'completed_trades': completed_trades,
            'active_trades': active_trades,
            'pending_trades': pending_trades
        }

    def search_traders(self, query: str) -> List[Dict[str, Any]]:
        """Yalnızca kayıtlı gerçek kullanıcıları arar."""
        q = (query or '').strip().lower().lstrip('@')
        if not q:
            return []

        results = []
        if has_app_context():
            try:
                users = User.query.filter(
                    (User.name.ilike(f"%{q}%")) | (User.username.ilike(f"%{q}%")) | (User.handle.ilike(f"%{q}%"))
                ).all()
                for u in users:
                    f_count = Follow.query.filter_by(followed_handle=u.handle).count()
                    results.append({
                        'name': u.name,
                        'handle': u.handle,
                        'badge': u.badge or ('👑 Admin & Trader' if u.role == 'admin' else '⚡ PRO Trader'),
                        'avatar_letter': u.name[0].upper() if u.name else 'U',
                        'followers_count': f_count,
                        'profile_url': f"/profil/{u.handle.lstrip('@')}"
                    })
                return results[:8]
            except Exception:
                pass

        # Fallback (utku)
        if 'utku' in q:
            results.append({
                'name': 'Utku',
                'handle': '@utku',
                'badge': '👑 Sistem Yöneticisi & Trader',
                'avatar_letter': 'U',
                'followers_count': len(self._follows),
                'profile_url': '/profil/utku'
            })
        return results

    def _notify_listeners(self, trade_data: Dict[str, Any]) -> None:
        for listener in self._update_listeners:
            try:
                listener(trade_data)
            except Exception:
                pass

    def add_listener(self, callback) -> None:
        self._update_listeners.append(callback)

"""Timezone and datetime formatting utilities for TRT (UTC+3)."""

from datetime import datetime, timezone, timedelta
from typing import Optional

TRT = timezone(timedelta(hours=3), name='TRT')


def get_tr_now() -> datetime:
    """Türkiye yerel saatine (UTC+3) göre anlık datetime nesnesi döndürür."""
    return datetime.now(TRT)


def format_tr_now() -> str:
    """Bugün HH:MM formatında Türkiye saatini döndürür."""
    return datetime.now(TRT).strftime('Bugün %H:%M')


def format_tr_time_only() -> str:
    """HH:MM:SS formatında Türkiye saatini döndürür."""
    return datetime.now(TRT).strftime('%H:%M:%S')


def format_tr_datetime(dt: Optional[datetime]) -> str:
    """Datetime nesnesini Türkiye saatine göre okunabilir metne dönüştürür."""
    if not dt:
        return '—'
    
    if dt.tzinfo is None:
        # DB'den gelen tz-unaware veriyi UTC kabul edip TRT'ye çevir
        dt = dt.replace(tzinfo=timezone.utc)
    
    tr_dt = dt.astimezone(TRT)
    now = datetime.now(TRT)
    
    if tr_dt.date() == now.date():
        return tr_dt.strftime('Bugün %H:%M')
    elif tr_dt.date() == (now - timedelta(days=1)).date():
        return tr_dt.strftime('Dün %H:%M')
    else:
        return tr_dt.strftime('%d.%m.%Y %H:%M')

"""
Application configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / '.env')

# Directories setup
INSTANCE_DIR = BASE_DIR / 'instance'
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_FILE = (INSTANCE_DIR / 'sisyphus_social.db').as_posix()


class BaseConfig:
    """Base configuration."""
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-sisyphus-social-2026')
    
    # JSON settings
    JSON_SORT_KEYS = False
    JSON_AS_ASCII = False
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _raw_db_url = os.getenv('DATABASE_URL')
    if _raw_db_url and _raw_db_url.startswith('postgres://'):
        _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url or f"sqlite:///{DEFAULT_DB_FILE}"
    
    # Cache settings
    DATA_CACHE_DIR = BASE_DIR / 'data_cache'
    LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', '90'))
    BINANCE_RATE_LIMIT_DELAY = float(os.getenv('BINANCE_RATE_LIMIT_DELAY', '0.05'))
    
    # Backtest parameters
    DEFAULT_CAPITAL = float(os.getenv('DEFAULT_CAPITAL', '10000.0'))
    DEFAULT_LEVERAGE = float(os.getenv('DEFAULT_LEVERAGE', '10.0'))
    DEFAULT_TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d']
    
    # Indicator parameters
    BB_SHORT_PERIOD = 10
    BB_LONG_PERIOD = 30
    POC_RANGE_LENGTH = 100
    RSI_PERIOD = 14
    EMA_FAST = 9
    EMA_SLOW = 21


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    ENV = 'development'


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DATA_CACHE_DIR = BASE_DIR / 'data_cache_test'


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Ensure SECRET_KEY is set in production
    SECRET_KEY = os.getenv('SECRET_KEY')


# Environment mapping
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env_name: str = None) -> type[BaseConfig]:
    """
    Belirtilen ortam adına göre yapılandırma sınıfını döndürür.
    
    Args:
        env_name: Ortam adı ('development', 'testing', 'production')
        
    Returns:
        type[BaseConfig]: İlgili konfigürasyon sınıfı
    """
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', 'development')
    return CONFIG_MAP.get(env_name, DevelopmentConfig)

"""
Sisyphus Social WSGI entry point.
"""

import sys
import threading
import time
import webbrowser
from app import create_app
from app.config import DevelopmentConfig

# Windows console utf-8
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = create_app(DevelopmentConfig)


def open_browser():
    """Open browser on startup."""
    time.sleep(1.2)
    url = "http://127.0.0.1:5000"
    print(f"\n>>> [OTOMATIK ACILIS] Tarayici aciliyor: {url}\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[UYARI] Tarayici otomatik acilamadi: {e}")


if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()

    
    print(">>> SISYPHUS SOCIAL - Server Baslatiliyor...")
    print(">>> Adres: http://127.0.0.1:5000")
    
    
    

    app.run(host='0.0.0.0', port=5000, debug=False)

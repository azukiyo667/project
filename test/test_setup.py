#!/usr/bin/env python3
"""
Tests de base pour le Trading Bot Premium
Vérifie les imports et la configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test des importations principales"""
    try:
        import discord
        print("✅ Discord.py importé")
    except ImportError as e:
        print(f"❌ Discord.py: {e}")
        return False

    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv importé")
    except ImportError as e:
        print(f"❌ python-dotenv: {e}")
        return False

    try:
        import pandas as pd
        print("✅ Pandas importé")
    except ImportError as e:
        print(f"❌ Pandas: {e}")
        return False

    try:
        import numpy as np
        print("✅ NumPy importé")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False

    try:
        import ccxt
        print("✅ CCXT importé")
    except ImportError as e:
        print(f"❌ CCXT: {e}")
        return False

    return True

def test_modules():
    """Test des modules locaux"""
    try:
        from src.database.db_manager import DatabaseManager
        print("✅ DatabaseManager importé")
    except ImportError as e:
        print(f"❌ DatabaseManager: {e}")
        return False

    try:
        from src.trading.analyzer import TradingAnalyzer
        print("✅ TradingAnalyzer importé")
    except ImportError as e:
        print(f"❌ TradingAnalyzer: {e}")
        return False

    try:
        from src.utils.permissions import PermissionManager
        print("✅ PermissionManager importé")
    except ImportError as e:
        print(f"❌ PermissionManager: {e}")
        return False

    return True

def test_config():
    """Test de la configuration"""
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        'DISCORD_TOKEN',
        'BINANCE_API_KEY',
        'ALERT_CHANNEL_ID',
        'PREMIUM_ROLE_ID'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️  Variables manquantes dans .env: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Configuration .env valide")
        return True

def test_database():
    """Test de la base de données"""
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.init_database()
        print("✅ Base de données initialisée")
        return True
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 Tests du Trading Bot Premium")
    print("=" * 40)

    tests = [
        ("Importations principales", test_imports),
        ("Modules locaux", test_modules),
        ("Configuration", test_config),
        ("Base de données", test_database)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append(False)

    print("\n" + "=" * 40)
    print("📊 Résultats des tests:")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 Tous les tests réussis ({passed}/{total})")
        print("✅ Le bot est prêt à démarrer!")
        sys.exit(0)
    else:
        print(f"⚠️  Tests réussis: {passed}/{total}")
        print("❌ Veuillez corriger les erreurs avant de démarrer le bot")
        sys.exit(1)

if __name__ == "__main__":
    main()

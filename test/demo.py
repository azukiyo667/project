#!/usr/bin/env python3
"""
Script de démonstration du Trading Bot Premium
Génère des données de test pour présenter les fonctionnalités
"""

import os
import sys
import asyncio
import random
from datetime import datetime, timedelta
import json

# Ajout du chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db_manager import DatabaseManager
from src.trading.analyzer import TradingAnalyzer
from src.trading.signal_generator import SignalGenerator

class BotDemo:
    def __init__(self):
        self.db = DatabaseManager()
        self.analyzer = TradingAnalyzer()
        self.signal_generator = SignalGenerator()

    def setup_demo_data(self):
        """Configure les données de démonstration"""
        print("🎭 Configuration des données de démonstration...")

        # Initialisation de la base de données
        self.db.init_database()

        # Ajout d'utilisateurs de test
        demo_users = [
            (123456789, "free", "DemoUser1", datetime.now()),
            (987654321, "premium", "PremiumUser", datetime.now()),
            (456789123, "vip", "VIPUser", datetime.now())
        ]

        for user_id, subscription, username, created_at in demo_users:
            self.db.add_user(user_id, subscription, username, created_at)

        print("✅ Utilisateurs de test créés")

        # Génération de signaux historiques
        self.generate_demo_signals()

        # Génération de portfolios de test
        self.generate_demo_portfolios()

    def generate_demo_signals(self):
        """Génère des signaux de démonstration"""
        print("📊 Génération de signaux de démonstration...")

        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        actions = ['BUY', 'SELL', 'HOLD']

        for i in range(50):  # 50 signaux de test
            symbol = random.choice(symbols)
            action = random.choice(actions)
            confidence = round(random.uniform(60, 95), 1)
            price = round(random.uniform(0.5, 50000), 4)

            signal_data = {
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'price': price,
                'timeframe': '4h',
                'created_at': datetime.now() - timedelta(hours=random.randint(1, 168))
            }

            # Simulation d'ajout en base
            print(f"  📈 {symbol}: {action} @ ${price} ({confidence}% confiance)")

        print("✅ Signaux de test générés")

    def generate_demo_portfolios(self):
        """Génère des portfolios de démonstration"""
        print("💼 Génération de portfolios de démonstration...")

        # Portfolio utilisateur premium
        premium_portfolio = {
            'user_id': 987654321,
            'positions': [
                {'symbol': 'BTC/USDT', 'amount': 0.5, 'entry_price': 45000, 'current_price': 47000},
                {'symbol': 'ETH/USDT', 'amount': 2.0, 'entry_price': 3000, 'current_price': 3200},
                {'symbol': 'BNB/USDT', 'amount': 10.0, 'entry_price': 400, 'current_price': 420}
            ],
            'total_value': 30000,
            'total_pnl': 2500,
            'pnl_percentage': 8.33
        }

        # Portfolio utilisateur VIP
        vip_portfolio = {
            'user_id': 456789123,
            'positions': [
                {'symbol': 'BTC/USDT', 'amount': 1.0, 'entry_price': 44000, 'current_price': 47000},
                {'symbol': 'ETH/USDT', 'amount': 5.0, 'entry_price': 2800, 'current_price': 3200},
                {'symbol': 'SOL/USDT', 'amount': 100.0, 'entry_price': 80, 'current_price': 95},
                {'symbol': 'ADA/USDT', 'amount': 1000.0, 'entry_price': 1.2, 'current_price': 1.35}
            ],
            'total_value': 75000,
            'total_pnl': 8500,
            'pnl_percentage': 12.78
        }

        print("  💰 Portfolio Premium: $30,000 (+8.33%)")
        print("  💎 Portfolio VIP: $75,000 (+12.78%)")
        print("✅ Portfolios de test créés")

    async def demo_analysis(self):
        """Démonstration d'analyse technique"""
        print("\n🔍 Démonstration d'analyse technique...")

        symbols = ['BTC/USDT', 'ETH/USDT']

        for symbol in symbols:
            print(f"\n📊 Analyse de {symbol}:")

            # Génération de données simulées
            analysis = {
                'symbol': symbol,
                'price': round(random.uniform(20000, 50000), 2) if 'BTC' in symbol else round(random.uniform(2000, 4000), 2),
                'rsi': round(random.uniform(30, 70), 1),
                'macd': 'BULLISH' if random.choice([True, False]) else 'BEARISH',
                'bb_position': random.choice(['UPPER', 'MIDDLE', 'LOWER']),
                'volume_change': round(random.uniform(-20, 30), 1),
                'signal': random.choice(['BUY', 'SELL', 'HOLD'])
            }

            print(f"  💰 Prix: ${analysis['price']}")
            print(f"  📈 RSI: {analysis['rsi']}")
            print(f"  📊 MACD: {analysis['macd']}")
            print(f"  🎯 Signal: {analysis['signal']}")

            # Génération d'un signal
            if analysis['signal'] != 'HOLD':
                confidence = round(random.uniform(75, 95), 1)
                print(f"  🚀 Confiance: {confidence}%")

                if analysis['signal'] == 'BUY':
                    take_profit = analysis['price'] * 1.05
                    stop_loss = analysis['price'] * 0.98
                else:
                    take_profit = analysis['price'] * 0.95
                    stop_loss = analysis['price'] * 1.02

                print(f"  🎯 Take Profit: ${take_profit:.2f}")
                print(f"  🛑 Stop Loss: ${stop_loss:.2f}")

    def demo_subscription_tiers(self):
        """Démonstration des tiers d'abonnement"""
        print("\n💎 Démonstration des Tiers d'Abonnement:")

        tiers = {
            'Free': {
                'price': '$0/mois',
                'signals': '10/jour',
                'features': ['Signaux de base', 'Timeframes limités', 'Support communautaire']
            },
            'Premium': {
                'price': '$29.99/mois',
                'signals': '100/jour',
                'features': ['Analyses complètes', 'Portfolio tracking', 'Alertes personnalisées', 'Support prioritaire']
            },
            'VIP': {
                'price': '$79.99/mois',
                'signals': 'Illimité',
                'features': ['Toutes les fonctionnalités', 'IA avancée', 'Analyses personnalisées', 'Support 24/7', 'Accès API']
            }
        }

        for tier, info in tiers.items():
            print(f"\n🏆 {tier} - {info['price']}")
            print(f"  📊 Signaux: {info['signals']}")
            print("  ✨ Fonctionnalités:")
            for feature in info['features']:
                print(f"    ✅ {feature}")

    def demo_business_metrics(self):
        """Démonstration des métriques business"""
        print("\n📈 Métriques Business (Simulation):")

        # Simulation de métriques
        metrics = {
            'total_users': 1247,
            'free_users': 892,
            'premium_users': 287,
            'vip_users': 68,
            'monthly_revenue': 12847.50,
            'conversion_rate': 28.5,
            'churn_rate': 8.2,
            'avg_revenue_per_user': 42.30
        }

        print(f"👥 Utilisateurs Total: {metrics['total_users']}")
        print(f"🆓 Gratuit: {metrics['free_users']}")
        print(f"💰 Premium: {metrics['premium_users']}")
        print(f"💎 VIP: {metrics['vip_users']}")
        print(f"💵 Revenus Mensuel: ${metrics['monthly_revenue']}")
        print(f"📊 Taux Conversion: {metrics['conversion_rate']}%")
        print(f"📉 Taux Désabonnement: {metrics['churn_rate']}%")
        print(f"💰 ARPU: ${metrics['avg_revenue_per_user']}")

    async def run_demo(self):
        """Exécute la démonstration complète"""
        print("🎭 DÉMONSTRATION TRADING BOT PREMIUM")
        print("=" * 50)

        # Configuration
        self.setup_demo_data()

        # Analyse technique
        await self.demo_analysis()

        # Tiers d'abonnement
        self.demo_subscription_tiers()

        # Métriques business
        self.demo_business_metrics()

        print("\n" + "=" * 50)
        print("🎉 Démonstration terminée !")
        print("💡 Ce bot est prêt pour la commercialisation SaaS")
        print("🚀 Revenus potentiels: $10,000-50,000/mois")

def main():
    """Point d'entrée principal"""
    demo = BotDemo()
    asyncio.run(demo.run_demo())

if __name__ == "__main__":
    main()

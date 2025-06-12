# Gestionnaire de base de données pour le bot de trading

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os

class DatabaseManager:
    def __init__(self, db_path: str = "trading_bot.db"):
        """Initialisation du gestionnaire de base de données"""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialise la base de données avec toutes les tables nécessaires"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Table des utilisateurs
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    subscription_tier TEXT DEFAULT 'free',
                    subscription_start DATE,
                    subscription_end DATE,
                    total_spent REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
                ''')

                # Table des signaux
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    price REAL NOT NULL,
                    timeframe TEXT NOT NULL,
                    take_profit REAL,
                    stop_loss REAL,
                    risk_reward REAL,
                    priority TEXT DEFAULT 'MEDIUM',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    indicators TEXT,
                    patterns TEXT,
                    recommendations TEXT,
                    market_context TEXT,
                    is_sent INTEGER DEFAULT 0,
                    performance_updated INTEGER DEFAULT 0,
                    actual_outcome TEXT,
                    profit_loss REAL
                )
                ''')

                # Table des portfolios utilisateurs
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                ''')

                # Table des transactions
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                ''')

                # Table des alertes utilisateur
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    target_price REAL,
                    condition_type TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                ''')

                # Table des statistiques de performance
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    buy_signals INTEGER DEFAULT 0,
                    sell_signals INTEGER DEFAULT 0,
                    successful_signals INTEGER DEFAULT 0,
                    total_profit_loss REAL DEFAULT 0.0,
                    active_users INTEGER DEFAULT 0,
                    premium_users INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Table des logs d'activité
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Index pour améliorer les performances
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_tier)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')

                conn.commit()
                logging.info("Base de données initialisée avec succès")

        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise

    # GESTION DES UTILISATEURS

    def add_user(self, user_id: int, username: str, subscription_tier: str = 'free') -> bool:
        """Ajoute un nouvel utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, subscription_tier, created_at, last_active)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, subscription_tier, datetime.utcnow(), datetime.utcnow()))
                conn.commit()
                logging.info(f"Utilisateur {username} ({user_id}) ajouté avec le tier {subscription_tier}")
                return True
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de l'utilisateur {user_id}: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Récupère les informations d'un utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None

        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'utilisateur {user_id}: {e}")
            return None

    def update_subscription(self, user_id: int, tier: str, duration_days: int = 30) -> bool:
        """Met à jour l'abonnement d'un utilisateur"""
        try:
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=duration_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE users
                SET subscription_tier = ?, subscription_start = ?, subscription_end = ?
                WHERE user_id = ?
                ''', (tier, start_date, end_date, user_id))
                conn.commit()

                logging.info(f"Abonnement mis à jour pour l'utilisateur {user_id}: {tier} jusqu'au {end_date}")
                return True

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de l'abonnement pour {user_id}: {e}")
            return False

    def get_premium_users(self) -> List[int]:
        """Récupère la liste des utilisateurs premium actifs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT user_id FROM users
                WHERE subscription_tier IN ('premium', 'vip')
                AND subscription_end > ?
                AND is_active = 1
                ''', (datetime.utcnow(),))

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des utilisateurs premium: {e}")
            return []

    def update_user_activity(self, user_id: int):
        """Met à jour la dernière activité d'un utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE users SET last_active = ? WHERE user_id = ?
                ''', (datetime.utcnow(), user_id))
                conn.commit()

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de l'activité pour {user_id}: {e}")

    # GESTION DES SIGNAUX

    def save_signal(self, signal: Dict) -> bool:
        """Sauvegarde un signal en base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO signals (
                    id, symbol, action, confidence, price, timeframe,
                    take_profit, stop_loss, risk_reward, priority,
                    created_at, indicators, patterns, recommendations, market_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal['id'],
                    signal['symbol'],
                    signal['action'],
                    signal['confidence'],
                    signal['price'],
                    signal['timeframe'],
                    signal.get('take_profit'),
                    signal.get('stop_loss'),
                    signal.get('risk_reward'),
                    signal.get('priority', 'MEDIUM'),
                    signal['timestamp'],
                    json.dumps(signal.get('indicators', {})),
                    json.dumps(signal.get('patterns', {})),
                    json.dumps(signal.get('recommendations', [])),
                    json.dumps(signal.get('market_context', {}))
                ))
                conn.commit()
                return True

        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du signal {signal.get('id', 'unknown')}: {e}")
            return False

    def get_signals(self, limit: int = 50, symbol: str = None, days: int = 7) -> List[Dict]:
        """Récupère les signaux récents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = '''
                SELECT * FROM signals
                WHERE created_at > ?
                '''
                params = [datetime.utcnow() - timedelta(days=days)]

                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)

                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                columns = [description[0] for description in cursor.description]
                signals = []

                for row in rows:
                    signal = dict(zip(columns, row))
                    # Conversion des champs JSON
                    for field in ['indicators', 'patterns', 'recommendations', 'market_context']:
                        if signal.get(field):
                            try:
                                signal[field] = json.loads(signal[field])
                            except:
                                signal[field] = {}
                    signals.append(signal)

                return signals

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des signaux: {e}")
            return []

    def update_signal_performance(self, signal_id: str, outcome: str, profit_loss: float) -> bool:
        """Met à jour la performance d'un signal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE signals
                SET actual_outcome = ?, profit_loss = ?, performance_updated = 1
                WHERE id = ?
                ''', (outcome, profit_loss, signal_id))
                conn.commit()
                return True

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de performance du signal {signal_id}: {e}")
            return False

    # GESTION DES PORTFOLIOS

    def add_portfolio_position(self, user_id: int, symbol: str, quantity: float, entry_price: float) -> bool:
        """Ajoute une position au portfolio d'un utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO portfolios (user_id, symbol, quantity, entry_price, current_price)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, symbol, quantity, entry_price, entry_price))
                conn.commit()
                return True

        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de position pour {user_id}: {e}")
            return False

    def get_user_portfolio(self, user_id: int) -> List[Dict]:
        """Récupère le portfolio d'un utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM portfolios
                WHERE user_id = ? AND is_active = 1
                ORDER BY entry_date DESC
                ''', (user_id,))

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logging.error(f"Erreur lors de la récupération du portfolio pour {user_id}: {e}")
            return []

    def update_portfolio_prices(self, price_updates: Dict[str, float]) -> bool:
        """Met à jour les prix actuels des positions en portfolio"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for symbol, price in price_updates.items():
                    cursor.execute('''
                    UPDATE portfolios
                    SET current_price = ?, last_updated = ?
                    WHERE symbol = ? AND is_active = 1
                    ''', (price, datetime.utcnow(), symbol))

                conn.commit()
                return True

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour des prix du portfolio: {e}")
            return False

    # GESTION DES TRANSACTIONS

    def add_transaction(self, user_id: int, transaction_type: str, amount: float, description: str = None) -> bool:
        """Ajoute une transaction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO transactions (user_id, transaction_type, amount, description)
                VALUES (?, ?, ?, ?)
                ''', (user_id, transaction_type, amount, description))
                conn.commit()

                # Met à jour le total dépensé si c'est un paiement
                if transaction_type == 'payment':
                    cursor.execute('''
                    UPDATE users SET total_spent = total_spent + ? WHERE user_id = ?
                    ''', (amount, user_id))
                    conn.commit()

                return True

        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de transaction pour {user_id}: {e}")
            return False

    def get_user_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Récupère les transactions d'un utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''', (user_id, limit))

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des transactions pour {user_id}: {e}")
            return []

    # GESTION DES ALERTES

    def add_user_alert(self, user_id: int, symbol: str, alert_type: str, target_price: float = None, condition_type: str = None) -> bool:
        """Ajoute une alerte utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition_type)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, symbol, alert_type, target_price, condition_type))
                conn.commit()
                return True

        except Exception as e:
            logging.error(f"Erreur lors de l'ajout d'alerte pour {user_id}: {e}")
            return False

    def get_active_alerts(self) -> List[Dict]:
        """Récupère toutes les alertes actives"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT * FROM user_alerts
                WHERE is_active = 1 AND triggered_at IS NULL
                ORDER BY created_at DESC
                ''')

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des alertes actives: {e}")
            return []

    # STATISTIQUES ET RAPPORTS

    def save_daily_stats(self, stats: Dict) -> bool:
        """Sauvegarde les statistiques quotidiennes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO performance_stats (
                    date, total_signals, buy_signals, sell_signals,
                    successful_signals, total_profit_loss, active_users, premium_users
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.utcnow().date(),
                    stats.get('total_signals', 0),
                    stats.get('buy_signals', 0),
                    stats.get('sell_signals', 0),
                    stats.get('successful_signals', 0),
                    stats.get('total_profit_loss', 0.0),
                    stats.get('active_users', 0),
                    stats.get('premium_users', 0)
                ))
                conn.commit()
                return True

        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des statistiques: {e}")
            return False

    def get_performance_stats(self, days: int = 30) -> Dict:
        """Récupère les statistiques de performance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Statistiques générales
                cursor.execute('''
                SELECT
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
                    SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
                    SUM(CASE WHEN actual_outcome = 'profitable' THEN 1 ELSE 0 END) as successful_signals,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN profit_loss IS NOT NULL THEN profit_loss ELSE 0 END) as total_profit_loss
                FROM signals
                WHERE created_at > ?
                ''', (datetime.utcnow() - timedelta(days=days),))

                stats = cursor.fetchone()

                # Statistiques par symbole
                cursor.execute('''
                SELECT symbol, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM signals
                WHERE created_at > ?
                GROUP BY symbol
                ORDER BY count DESC
                LIMIT 10
                ''', (datetime.utcnow() - timedelta(days=days),))

                symbol_stats = cursor.fetchall()

                return {
                    'period_days': days,
                    'total_signals': stats[0] or 0,
                    'buy_signals': stats[1] or 0,
                    'sell_signals': stats[2] or 0,
                    'successful_signals': stats[3] or 0,
                    'success_rate': (stats[3] / stats[0] * 100) if stats[0] > 0 else 0,
                    'avg_confidence': round(stats[4] or 0, 2),
                    'total_profit_loss': round(stats[5] or 0, 2),
                    'top_symbols': [{'symbol': s[0], 'count': s[1], 'avg_confidence': round(s[2], 2)} for s in symbol_stats]
                }

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {}

    def log_activity(self, user_id: int, action: str, details: str = None, ip_address: str = None):
        """Enregistre une activité utilisateur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO activity_logs (user_id, action, details, ip_address)
                VALUES (?, ?, ?, ?)
                ''', (user_id, action, details, ip_address))
                conn.commit()

        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité: {e}")

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Nettoyage des anciennes données"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Suppression des anciens logs
                cursor.execute('DELETE FROM activity_logs WHERE timestamp < ?', (cutoff_date,))

                # Suppression des anciennes statistiques
                cursor.execute('DELETE FROM performance_stats WHERE date < ?', (cutoff_date.date(),))

                # Archivage des anciens signaux (garde seulement ceux avec performance)
                cursor.execute('''
                DELETE FROM signals
                WHERE created_at < ? AND performance_updated = 0
                ''', (cutoff_date,))

                conn.commit()
                logging.info(f"Nettoyage effectué: données antérieures au {cutoff_date.date()} supprimées")

        except Exception as e:
            logging.error(f"Erreur lors du nettoyage des données: {e}")

    def get_database_stats(self) -> Dict:
        """Récupère les statistiques de la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                stats = {}

                # Nombre d'enregistrements par table
                tables = ['users', 'signals', 'portfolios', 'transactions', 'user_alerts', 'performance_stats', 'activity_logs']

                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f'{table}_count'] = cursor.fetchone()[0]

                # Taille de la base de données
                stats['db_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)

                return stats

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des statistiques de la DB: {e}")
            return {}

    def backup_database(self, backup_path: str = None) -> bool:
        """Créer une sauvegarde de la base de données"""
        try:
            if not backup_path:
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                backup_path = f"backup_trading_bot_{timestamp}.db"

            # Copie de sécurité
            import shutil
            shutil.copy2(self.db_path, backup_path)

            logging.info(f"Sauvegarde créée: {backup_path}")
            return True

        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde: {e}")
            return False

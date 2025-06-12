# Générateur de signaux de trading avancés

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import json

class SignalGenerator:
    def __init__(self):
        """Initialisation du générateur de signaux"""
        self.signal_history = []
        self.performance_tracker = {}

        # Configuration des seuils de confiance
        self.confidence_thresholds = {
            'high': 80,
            'medium': 60,
            'low': 40
        }

        # Configuration des niveaux de risk management
        self.risk_configs = {
            'conservative': {'risk_pct': 1.0, 'reward_ratio': 2.0},
            'moderate': {'risk_pct': 2.0, 'reward_ratio': 1.5},
            'aggressive': {'risk_pct': 3.0, 'reward_ratio': 1.2}
        }

    async def generate_signal(self, symbol: str, analysis: Dict) -> Dict:
        """
        Génère un signal de trading complet basé sur l'analyse

        Args:
            symbol (str): Symbole de la crypto
            analysis (Dict): Résultats de l'analyse technique

        Returns:
            Dict: Signal de trading complet
        """
        try:
            signal = {
                'id': self._generate_signal_id(),
                'timestamp': datetime.utcnow(),
                'symbol': symbol,
                'action': analysis.get('signal', 'HOLD'),
                'confidence': analysis.get('confidence', 0),
                'price': analysis.get('price', 0),
                'timeframe': analysis.get('timeframe', '1h'),
                'indicators': analysis.get('indicators', {}),
                'patterns': analysis.get('patterns', {}),
                'volume_analysis': analysis.get('volume_analysis', {}),
                'ml_prediction': analysis.get('ml_prediction', {})
            }

            # Ajout des niveaux de take profit et stop loss
            signal.update(self._calculate_risk_levels(signal))

            # Ajout du contexte de marché
            signal['market_context'] = await self._get_market_context(symbol)

            # Ajout des recommandations
            signal['recommendations'] = self._generate_recommendations(signal)

            # Calcul de la priorité du signal
            signal['priority'] = self._calculate_priority(signal)

            # Calcul du sizing de position recommandé
            signal['position_sizing'] = self._calculate_position_sizing(signal)

            # Sauvegarde du signal
            self._save_signal(signal)

            return signal

        except Exception as e:
            logging.error(f"Erreur lors de la génération du signal pour {symbol}: {e}")
            return self._get_error_signal(symbol, str(e))

    def _generate_signal_id(self) -> str:
        """Génère un ID unique pour le signal"""
        return f"SIG_{int(datetime.utcnow().timestamp())}_{np.random.randint(1000, 9999)}"

    def _calculate_risk_levels(self, signal: Dict) -> Dict:
        """Calcul des niveaux de risk management"""
        try:
            action = signal['action']
            price = signal['price']
            confidence = signal['confidence']

            if action == 'HOLD' or price <= 0:
                return {
                    'take_profit': None,
                    'stop_loss': None,
                    'risk_reward': None,
                    'max_risk_pct': None
                }

            # Sélection du profil de risque basé sur la confiance
            if confidence >= self.confidence_thresholds['high']:
                risk_profile = 'aggressive'
            elif confidence >= self.confidence_thresholds['medium']:
                risk_profile = 'moderate'
            else:
                risk_profile = 'conservative'

            config = self.risk_configs[risk_profile]

            # Calcul des niveaux pour position longue (BUY)
            if action == 'BUY':
                stop_loss_pct = config['risk_pct'] / 100
                take_profit_pct = stop_loss_pct * config['reward_ratio']

                stop_loss = price * (1 - stop_loss_pct)
                take_profit = price * (1 + take_profit_pct)

            # Calcul des niveaux pour position courte (SELL)
            else:  # action == 'SELL'
                stop_loss_pct = config['risk_pct'] / 100
                take_profit_pct = stop_loss_pct * config['reward_ratio']

                stop_loss = price * (1 + stop_loss_pct)
                take_profit = price * (1 - take_profit_pct)

            return {
                'take_profit': round(take_profit, 6),
                'stop_loss': round(stop_loss, 6),
                'risk_reward': config['reward_ratio'],
                'max_risk_pct': config['risk_pct'],
                'risk_profile': risk_profile
            }

        except Exception as e:
            logging.error(f"Erreur lors du calcul des niveaux de risque: {e}")
            return {}

    async def _get_market_context(self, symbol: str) -> Dict:
        """Récupère le contexte général du marché"""
        try:
            # Simulation du contexte de marché
            # Dans un vrai système, cela devrait récupérer:
            # - Sentiment général du marché crypto
            # - Volume global
            # - Dominance Bitcoin
            # - Nouvelles importantes

            market_contexts = [
                {'trend': 'bullish', 'strength': 'strong', 'volatility': 'high'},
                {'trend': 'bearish', 'strength': 'moderate', 'volatility': 'medium'},
                {'trend': 'sideways', 'strength': 'weak', 'volatility': 'low'},
                {'trend': 'bullish', 'strength': 'moderate', 'volatility': 'medium'},
                {'trend': 'bearish', 'strength': 'strong', 'volatility': 'high'}
            ]

            # Sélection aléatoire pour la simulation
            context = np.random.choice(market_contexts)

            return {
                'overall_trend': context['trend'],
                'trend_strength': context['strength'],
                'market_volatility': context['volatility'],
                'btc_dominance': np.random.uniform(40, 60),
                'total_market_cap_change': np.random.uniform(-5, 5),
                'fear_greed_index': np.random.randint(20, 80)
            }

        except Exception as e:
            logging.error(f"Erreur lors de la récupération du contexte de marché: {e}")
            return {}

    def _generate_recommendations(self, signal: Dict) -> List[str]:
        """Génère des recommandations contextuelles"""
        recommendations = []

        try:
            action = signal['action']
            confidence = signal['confidence']
            market_context = signal.get('market_context', {})

            # Recommandations basées sur l'action
            if action == 'BUY':
                recommendations.append("💚 Signal d'achat détecté")
                if confidence >= 80:
                    recommendations.append("🔥 Confiance très élevée - Signal fort")
                elif confidence >= 60:
                    recommendations.append("⚡ Confiance modérée - Signal valide")
                else:
                    recommendations.append("⚠️ Confiance faible - Attendez confirmation")

            elif action == 'SELL':
                recommendations.append("❤️ Signal de vente détecté")
                if confidence >= 80:
                    recommendations.append("🔥 Confiance très élevée - Signal fort")
                else:
                    recommendations.append("⚠️ Surveillez l'évolution avant de vendre")

            else:  # HOLD
                recommendations.append("😴 Aucun signal clair - Restez en attente")
                recommendations.append("📊 Surveillez les niveaux clés")

            # Recommandations basées sur le contexte de marché
            overall_trend = market_context.get('overall_trend', 'unknown')

            if overall_trend == 'bullish' and action == 'BUY':
                recommendations.append("🚀 Tendance de marché favorable à l'achat")
            elif overall_trend == 'bearish' and action == 'SELL':
                recommendations.append("📉 Tendance de marché favorable à la vente")
            elif overall_trend == 'sideways':
                recommendations.append("↔️ Marché latéral - Privilégiez le trading de range")

            # Recommandations de risk management
            if signal.get('risk_profile') == 'aggressive':
                recommendations.append("⚡ Profil agressif - Potential de gain élevé mais risqué")
            elif signal.get('risk_profile') == 'conservative':
                recommendations.append("🛡️ Profil conservateur - Risque limité")

            # Recommandations techniques
            indicators = signal.get('indicators', {})
            rsi = indicators.get('rsi', 50)

            if rsi > 70:
                recommendations.append("📈 RSI en surachat - Attention aux corrections")
            elif rsi < 30:
                recommendations.append("📉 RSI en survente - Opportunité de rebond")

            # Recommandations de volume
            volume_analysis = signal.get('volume_analysis', {})
            if volume_analysis.get('volume_confirmation', False):
                recommendations.append("📊 Volume confirme le signal")
            else:
                recommendations.append("⚠️ Volume faible - Attendez confirmation")

        except Exception as e:
            logging.error(f"Erreur lors de la génération des recommandations: {e}")
            recommendations = ["❓ Erreur lors de l'analyse - Soyez prudent"]

        return recommendations

    def _calculate_priority(self, signal: Dict) -> str:
        """Calcule la priorité du signal"""
        try:
            confidence = signal['confidence']
            action = signal['action']

            if action == 'HOLD':
                return 'LOW'

            if confidence >= 85:
                return 'CRITICAL'
            elif confidence >= 70:
                return 'HIGH'
            elif confidence >= 55:
                return 'MEDIUM'
            else:
                return 'LOW'

        except Exception as e:
            logging.error(f"Erreur lors du calcul de priorité: {e}")
            return 'LOW'

    def _calculate_position_sizing(self, signal: Dict) -> Dict:
        """Calcule la taille de position recommandée"""
        try:
            confidence = signal['confidence']
            risk_profile = signal.get('risk_profile', 'conservative')

            # Pourcentage du capital à risquer basé sur la confiance
            if confidence >= 85:
                base_risk = 0.05  # 5% du capital
            elif confidence >= 70:
                base_risk = 0.03  # 3% du capital
            elif confidence >= 55:
                base_risk = 0.02  # 2% du capital
            else:
                base_risk = 0.01  # 1% du capital

            # Ajustement selon le profil de risque
            risk_multiplier = {
                'conservative': 0.5,
                'moderate': 1.0,
                'aggressive': 1.5
            }

            final_risk = base_risk * risk_multiplier.get(risk_profile, 1.0)

            return {
                'recommended_risk_pct': round(final_risk * 100, 2),
                'max_portfolio_pct': min(final_risk * 100, 10),  # Max 10% du portfolio
                'sizing_rationale': f"Basé sur confiance {confidence}% et profil {risk_profile}"
            }

        except Exception as e:
            logging.error(f"Erreur lors du calcul de position sizing: {e}")
            return {'recommended_risk_pct': 1.0, 'max_portfolio_pct': 1.0}

    def _save_signal(self, signal: Dict):
        """Sauvegarde le signal dans l'historique"""
        try:
            # Limitation de la taille de l'historique
            if len(self.signal_history) >= 1000:
                self.signal_history = self.signal_history[-800:]  # Garde les 800 plus récents

            self.signal_history.append(signal)

            # Mise à jour des statistiques de performance
            symbol = signal['symbol']
            if symbol not in self.performance_tracker:
                self.performance_tracker[symbol] = {
                    'total_signals': 0,
                    'profitable_signals': 0,
                    'total_return': 0.0,
                    'last_update': datetime.utcnow()
                }

            self.performance_tracker[symbol]['total_signals'] += 1

            logging.info(f"Signal sauvegardé: {signal['id']} - {signal['symbol']} - {signal['action']}")

        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du signal: {e}")

    def _get_error_signal(self, symbol: str, error_msg: str) -> Dict:
        """Signal d'erreur standardisé"""
        return {
            'id': f"ERR_{int(datetime.utcnow().timestamp())}",
            'timestamp': datetime.utcnow(),
            'symbol': symbol,
            'action': 'HOLD',
            'confidence': 0,
            'error': True,
            'error_message': error_msg,
            'priority': 'LOW',
            'recommendations': [f"❌ Erreur d'analyse: {error_msg}"]
        }

    def get_signal_performance(self, symbol: str = None) -> Dict:
        """Récupère les performances des signaux"""
        try:
            if symbol:
                return self.performance_tracker.get(symbol, {})
            else:
                # Statistiques globales
                total_signals = sum(stats['total_signals'] for stats in self.performance_tracker.values())
                total_profitable = sum(stats['profitable_signals'] for stats in self.performance_tracker.values())

                return {
                    'total_signals': total_signals,
                    'total_profitable': total_profitable,
                    'success_rate': (total_profitable / total_signals * 100) if total_signals > 0 else 0,
                    'tracked_symbols': len(self.performance_tracker)
                }

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des performances: {e}")
            return {}

    def get_signal_history(self, limit: int = 50, symbol: str = None) -> List[Dict]:
        """Récupère l'historique des signaux"""
        try:
            history = self.signal_history

            if symbol:
                history = [s for s in history if s['symbol'] == symbol]

            # Tri par timestamp décroissant et limitation
            history = sorted(history, key=lambda x: x['timestamp'], reverse=True)

            return history[:limit]

        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []

    async def update_signal_performance(self, signal_id: str, actual_outcome: str, profit_loss: float):
        """Met à jour la performance d'un signal après exécution"""
        try:
            # Trouve le signal dans l'historique
            signal = None
            for s in self.signal_history:
                if s['id'] == signal_id:
                    signal = s
                    break

            if not signal:
                logging.warning(f"Signal {signal_id} non trouvé dans l'historique")
                return

            # Met à jour les statistiques
            symbol = signal['symbol']
            if symbol in self.performance_tracker:
                stats = self.performance_tracker[symbol]

                if actual_outcome == 'profitable':
                    stats['profitable_signals'] += 1

                stats['total_return'] += profit_loss
                stats['last_update'] = datetime.utcnow()

                # Ajoute les données de performance au signal
                signal['actual_outcome'] = actual_outcome
                signal['profit_loss'] = profit_loss
                signal['performance_updated'] = datetime.utcnow()

                logging.info(f"Performance mise à jour pour {signal_id}: {actual_outcome} ({profit_loss:+.2f}%)")

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de performance: {e}")

    def generate_performance_report(self) -> Dict:
        """Génère un rapport de performance des signaux"""
        try:
            global_stats = self.get_signal_performance()

            # Analyse par symbole
            symbol_performances = []
            for symbol, stats in self.performance_tracker.items():
                success_rate = (stats['profitable_signals'] / stats['total_signals'] * 100) if stats['total_signals'] > 0 else 0

                symbol_performances.append({
                    'symbol': symbol,
                    'total_signals': stats['total_signals'],
                    'success_rate': round(success_rate, 1),
                    'total_return': round(stats['total_return'], 2),
                    'avg_return': round(stats['total_return'] / stats['total_signals'], 2) if stats['total_signals'] > 0 else 0
                })

            # Tri par performance
            symbol_performances.sort(key=lambda x: x['success_rate'], reverse=True)

            # Signaux récents
            recent_signals = self.get_signal_history(limit=10)

            return {
                'generated_at': datetime.utcnow(),
                'global_stats': global_stats,
                'top_performing_symbols': symbol_performances[:5],
                'recent_signals': [
                    {
                        'symbol': s['symbol'],
                        'action': s['action'],
                        'confidence': s['confidence'],
                        'timestamp': s['timestamp'].strftime('%Y-%m-%d %H:%M')
                    } for s in recent_signals
                ]
            }

        except Exception as e:
            logging.error(f"Erreur lors de la génération du rapport de performance: {e}")
            return {'error': str(e)}

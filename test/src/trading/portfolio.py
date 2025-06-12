# Gestionnaire de portfolio pour le suivi des positions

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import numpy as np

class PortfolioManager:
    def __init__(self, db_manager=None, analyzer=None):
        """Initialisation du gestionnaire de portfolio"""
        self.db_manager = db_manager
        self.analyzer = analyzer

        # Configuration des alertes
        self.alert_thresholds = {
            'profit_target': 0.05,    # 5% de profit
            'stop_loss': -0.03,       # -3% de perte
            'large_move': 0.1,        # 10% de mouvement
            'volume_spike': 2.0       # 2x le volume normal
        }

    async def update_portfolio(self, user_id: int) -> Dict:
        """Met à jour le portfolio d'un utilisateur"""
        try:
            # Récupération du portfolio depuis la DB
            positions = self.db_manager.get_user_portfolio(user_id)

            if not positions:
                return {
                    'user_id': user_id,
                    'total_value': 0,
                    'total_pnl': 0,
                    'positions': [],
                    'alerts': []
                }

            # Récupération des prix actuels
            symbols = list(set([pos['symbol'] for pos in positions]))
            current_prices = await self._get_current_prices(symbols)

            # Mise à jour des prix en base
            self.db_manager.update_portfolio_prices(current_prices)

            # Calcul des métriques
            updated_positions = []
            total_value = 0
            total_invested = 0
            alerts = []

            for position in positions:
                symbol = position['symbol']
                quantity = position['quantity']
                entry_price = position['entry_price']
                current_price = current_prices.get(symbol, entry_price)

                # Calculs
                position_value = quantity * current_price
                invested_value = quantity * entry_price
                pnl_absolute = position_value - invested_value
                pnl_percentage = (pnl_absolute / invested_value) * 100 if invested_value > 0 else 0

                # Position mise à jour
                updated_position = {
                    **position,
                    'current_price': current_price,
                    'position_value': position_value,
                    'invested_value': invested_value,
                    'pnl_absolute': pnl_absolute,
                    'pnl_percentage': pnl_percentage,
                    'last_updated': datetime.utcnow()
                }

                updated_positions.append(updated_position)

                # Accumulation des totaux
                total_value += position_value
                total_invested += invested_value

                # Vérification des alertes
                position_alerts = self._check_position_alerts(updated_position)
                alerts.extend(position_alerts)

            # Calcul du P&L global
            total_pnl_absolute = total_value - total_invested
            total_pnl_percentage = (total_pnl_absolute / total_invested) * 100 if total_invested > 0 else 0

            # Métriques de diversification
            diversification = self._calculate_diversification(updated_positions)

            # Métriques de risque
            risk_metrics = self._calculate_risk_metrics(updated_positions)

            portfolio_data = {
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                'total_value': round(total_value, 2),
                'total_invested': round(total_invested, 2),
                'total_pnl_absolute': round(total_pnl_absolute, 2),
                'total_pnl_percentage': round(total_pnl_percentage, 2),
                'positions_count': len(updated_positions),
                'positions': updated_positions,
                'alerts': alerts,
                'diversification': diversification,
                'risk_metrics': risk_metrics,
                'performance': self._calculate_performance_metrics(updated_positions)
            }

            return portfolio_data

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour du portfolio pour {user_id}: {e}")
            return {'error': str(e)}

    async def _get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Récupère les prix actuels des cryptomonnaies"""
        prices = {}

        try:
            # Simulation des prix - dans un vrai système, utiliser une API crypto
            for symbol in symbols:
                # Prix simulé avec variation aléatoire
                base_prices = {
                    'BTC/USDT': 45000,
                    'ETH/USDT': 3000,
                    'BNB/USDT': 300,
                    'ADA/USDT': 0.5,
                    'SOL/USDT': 100,
                    'MATIC/USDT': 0.8,
                    'DOT/USDT': 7,
                    'LINK/USDT': 15
                }

                base_price = base_prices.get(symbol, 100)
                # Variation aléatoire de -5% à +5%
                variation = np.random.uniform(-0.05, 0.05)
                prices[symbol] = base_price * (1 + variation)

            return prices

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des prix: {e}")
            return {}

    def _check_position_alerts(self, position: Dict) -> List[Dict]:
        """Vérifie les alertes pour une position"""
        alerts = []

        try:
            pnl_pct = position['pnl_percentage']
            symbol = position['symbol']

            # Alerte de profit
            if pnl_pct >= self.alert_thresholds['profit_target'] * 100:
                alerts.append({
                    'type': 'profit_target',
                    'symbol': symbol,
                    'message': f"🎯 {symbol}: Objectif de profit atteint ({pnl_pct:+.2f}%)",
                    'pnl': pnl_pct,
                    'priority': 'medium'
                })

            # Alerte de perte
            elif pnl_pct <= self.alert_thresholds['stop_loss'] * 100:
                alerts.append({
                    'type': 'stop_loss',
                    'symbol': symbol,
                    'message': f"🛑 {symbol}: Stop loss déclenché ({pnl_pct:+.2f}%)",
                    'pnl': pnl_pct,
                    'priority': 'high'
                })

            # Alerte de mouvement important
            elif abs(pnl_pct) >= self.alert_thresholds['large_move'] * 100:
                direction = "hausse" if pnl_pct > 0 else "baisse"
                alerts.append({
                    'type': 'large_move',
                    'symbol': symbol,
                    'message': f"📈 {symbol}: Mouvement important en {direction} ({pnl_pct:+.2f}%)",
                    'pnl': pnl_pct,
                    'priority': 'medium'
                })

            return alerts

        except Exception as e:
            logging.error(f"Erreur lors de la vérification des alertes: {e}")
            return []

    def _calculate_diversification(self, positions: List[Dict]) -> Dict:
        """Calcule les métriques de diversification"""
        try:
            if not positions:
                return {'score': 0, 'concentration_risk': 'low'}

            # Calcul des poids de chaque position
            total_value = sum(pos['position_value'] for pos in positions)

            if total_value <= 0:
                return {'score': 0, 'concentration_risk': 'low'}

            weights = []
            position_weights = []

            for position in positions:
                weight = position['position_value'] / total_value
                weights.append(weight)
                position_weights.append({
                    'symbol': position['symbol'],
                    'weight': weight * 100,
                    'value': position['position_value']
                })

            # Score de diversification (indice de Herfindahl inversé)
            herfindahl_index = sum(w ** 2 for w in weights)
            diversification_score = (1 - herfindahl_index) * 100

            # Évaluation du risque de concentration
            max_weight = max(weights) if weights else 0

            if max_weight > 0.5:
                concentration_risk = 'high'
            elif max_weight > 0.3:
                concentration_risk = 'medium'
            else:
                concentration_risk = 'low'

            return {
                'score': round(diversification_score, 2),
                'concentration_risk': concentration_risk,
                'max_position_weight': round(max_weight * 100, 2),
                'position_weights': sorted(position_weights, key=lambda x: x['weight'], reverse=True)
            }

        except Exception as e:
            logging.error(f"Erreur lors du calcul de diversification: {e}")
            return {'score': 0, 'concentration_risk': 'unknown'}

    def _calculate_risk_metrics(self, positions: List[Dict]) -> Dict:
        """Calcule les métriques de risque du portfolio"""
        try:
            if not positions:
                return {'var_95': 0, 'max_drawdown': 0, 'risk_level': 'low'}

            # Calcul simplifié du VaR (Value at Risk) à 95%
            pnl_values = [pos['pnl_percentage'] for pos in positions]

            if pnl_values:
                var_95 = np.percentile(pnl_values, 5)  # 5e percentile
                max_loss = min(pnl_values)
                avg_pnl = np.mean(pnl_values)
                volatility = np.std(pnl_values)
            else:
                var_95 = max_loss = avg_pnl = volatility = 0

            # Évaluation du niveau de risque
            if abs(var_95) > 15 or volatility > 10:
                risk_level = 'high'
            elif abs(var_95) > 8 or volatility > 5:
                risk_level = 'medium'
            else:
                risk_level = 'low'

            return {
                'var_95': round(var_95, 2),
                'max_drawdown': round(max_loss, 2),
                'volatility': round(volatility, 2),
                'avg_pnl': round(avg_pnl, 2),
                'risk_level': risk_level
            }

        except Exception as e:
            logging.error(f"Erreur lors du calcul des métriques de risque: {e}")
            return {'var_95': 0, 'max_drawdown': 0, 'risk_level': 'unknown'}

    def _calculate_performance_metrics(self, positions: List[Dict]) -> Dict:
        """Calcule les métriques de performance"""
        try:
            if not positions:
                return {
                    'winning_positions': 0,
                    'losing_positions': 0,
                    'win_rate': 0,
                    'best_performer': None,
                    'worst_performer': None
                }

            winning_positions = [pos for pos in positions if pos['pnl_percentage'] > 0]
            losing_positions = [pos for pos in positions if pos['pnl_percentage'] < 0]
            neutral_positions = [pos for pos in positions if pos['pnl_percentage'] == 0]

            win_rate = (len(winning_positions) / len(positions)) * 100 if positions else 0

            # Meilleure et pire performance
            best_performer = max(positions, key=lambda x: x['pnl_percentage']) if positions else None
            worst_performer = min(positions, key=lambda x: x['pnl_percentage']) if positions else None

            # Métriques avancées
            if winning_positions:
                avg_win = np.mean([pos['pnl_percentage'] for pos in winning_positions])
                avg_win_value = np.mean([pos['pnl_absolute'] for pos in winning_positions])
            else:
                avg_win = avg_win_value = 0

            if losing_positions:
                avg_loss = np.mean([pos['pnl_percentage'] for pos in losing_positions])
                avg_loss_value = np.mean([pos['pnl_absolute'] for pos in losing_positions])
            else:
                avg_loss = avg_loss_value = 0

            # Ratio profit/perte
            profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')

            return {
                'total_positions': len(positions),
                'winning_positions': len(winning_positions),
                'losing_positions': len(losing_positions),
                'neutral_positions': len(neutral_positions),
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'avg_win_value': round(avg_win_value, 2),
                'avg_loss_value': round(avg_loss_value, 2),
                'profit_loss_ratio': round(profit_loss_ratio, 2) if profit_loss_ratio != float('inf') else 'N/A',
                'best_performer': {
                    'symbol': best_performer['symbol'],
                    'pnl': round(best_performer['pnl_percentage'], 2)
                } if best_performer else None,
                'worst_performer': {
                    'symbol': worst_performer['symbol'],
                    'pnl': round(worst_performer['pnl_percentage'], 2)
                } if worst_performer else None
            }

        except Exception as e:
            logging.error(f"Erreur lors du calcul des métriques de performance: {e}")
            return {}

    async def add_position(self, user_id: int, symbol: str, quantity: float, entry_price: float) -> bool:
        """Ajoute une position au portfolio"""
        try:
            success = self.db_manager.add_portfolio_position(user_id, symbol, quantity, entry_price)

            if success:
                logging.info(f"Position ajoutée pour {user_id}: {quantity} {symbol} à ${entry_price}")

                # Log de l'activité
                self.db_manager.log_activity(
                    user_id,
                    'position_added',
                    f"Ajout: {quantity} {symbol} @ ${entry_price}"
                )

            return success

        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de position: {e}")
            return False

    async def remove_position(self, user_id: int, position_id: int) -> bool:
        """Supprime une position du portfolio"""
        try:
            # Dans un vrai système, implémenter la suppression
            # Pour l'instant, on marque comme inactive
            success = True  # Simulation

            if success:
                logging.info(f"Position {position_id} supprimée pour {user_id}")

                self.db_manager.log_activity(
                    user_id,
                    'position_removed',
                    f"Suppression position ID: {position_id}"
                )

            return success

        except Exception as e:
            logging.error(f"Erreur lors de la suppression de position: {e}")
            return False

    def generate_portfolio_report(self, user_id: int, portfolio_data: Dict) -> Dict:
        """Génère un rapport détaillé du portfolio"""
        try:
            report = {
                'user_id': user_id,
                'generated_at': datetime.utcnow(),
                'summary': {
                    'total_value': portfolio_data.get('total_value', 0),
                    'total_pnl': portfolio_data.get('total_pnl_percentage', 0),
                    'positions_count': portfolio_data.get('positions_count', 0),
                    'risk_level': portfolio_data.get('risk_metrics', {}).get('risk_level', 'unknown')
                },
                'performance': portfolio_data.get('performance', {}),
                'risk_analysis': portfolio_data.get('risk_metrics', {}),
                'diversification': portfolio_data.get('diversification', {}),
                'recommendations': self._generate_portfolio_recommendations(portfolio_data),
                'alerts': portfolio_data.get('alerts', [])
            }

            return report

        except Exception as e:
            logging.error(f"Erreur lors de la génération du rapport portfolio: {e}")
            return {'error': str(e)}

    def _generate_portfolio_recommendations(self, portfolio_data: Dict) -> List[str]:
        """Génère des recommandations basées sur l'analyse du portfolio"""
        recommendations = []

        try:
            diversification = portfolio_data.get('diversification', {})
            risk_metrics = portfolio_data.get('risk_metrics', {})
            performance = portfolio_data.get('performance', {})

            # Recommandations de diversification
            concentration_risk = diversification.get('concentration_risk', 'unknown')
            if concentration_risk == 'high':
                recommendations.append("⚠️ Risque de concentration élevé - Diversifiez vos positions")
                recommendations.append("💡 Réduisez la taille de votre position principale")

            # Recommandations de risque
            risk_level = risk_metrics.get('risk_level', 'unknown')
            if risk_level == 'high':
                recommendations.append("🛑 Niveau de risque élevé - Considérez réduire l'exposition")
                recommendations.append("📉 Implémentez des stops loss sur vos positions")

            # Recommandations de performance
            win_rate = performance.get('win_rate', 0)
            if win_rate < 40:
                recommendations.append("📊 Taux de réussite faible - Revoyez votre stratégie")
                recommendations.append("🎯 Considérez utiliser plus de signaux Premium")
            elif win_rate > 70:
                recommendations.append("🎉 Excellente performance - Maintenez votre stratégie!")

            # Recommandations générales
            total_positions = performance.get('total_positions', 0)
            if total_positions < 3:
                recommendations.append("🔄 Augmentez la diversification avec plus de positions")
            elif total_positions > 20:
                recommendations.append("📋 Simplifiez votre portfolio - trop de positions à gérer")

            # Si pas de recommandations spécifiques
            if not recommendations:
                recommendations.append("✅ Portfolio bien équilibré - Continuez sur cette voie!")

        except Exception as e:
            logging.error(f"Erreur lors de la génération des recommandations: {e}")
            recommendations = ["❓ Impossible de générer des recommandations"]

        return recommendations

    async def get_portfolio_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Récupère l'historique du portfolio"""
        try:
            # Dans un vrai système, récupérer depuis la DB
            # Pour l'instant, génération simulée
            history = []

            for i in range(days):
                date = datetime.utcnow() - timedelta(days=i)

                # Données simulées
                history.append({
                    'date': date,
                    'total_value': np.random.uniform(1000, 5000),
                    'pnl_percentage': np.random.uniform(-5, 8),
                    'positions_count': np.random.randint(3, 15)
                })

            return sorted(history, key=lambda x: x['date'])

        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []

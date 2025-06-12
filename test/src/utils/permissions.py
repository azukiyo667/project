# Gestionnaire des permissions et abonnements

import discord
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import os

class PermissionManager:
    def __init__(self, db_manager):
        """Initialisation du gestionnaire de permissions"""
        self.db_manager = db_manager

        # Configuration des rôles Discord
        self.role_ids = {
            'premium': int(os.getenv('PREMIUM_ROLE_ID', 0)),
            'vip': int(os.getenv('VIP_ROLE_ID', 0)),
            'admin': int(os.getenv('ADMIN_ROLE_ID', 0))
        }

        # Configuration des limites par tier
        self.tier_limits = {
            'free': {
                'signals_per_day': 10,
                'watchlist_size': 3,
                'alerts_per_user': 2,
                'timeframes': ['1h', '4h'],
                'features': ['basic_signals', 'market_overview']
            },
            'premium': {
                'signals_per_day': 100,
                'watchlist_size': 20,
                'alerts_per_user': 10,
                'timeframes': ['1h', '4h', '1d'],
                'features': ['basic_signals', 'market_overview', 'portfolio', 'watchlist', 'alerts', 'analysis']
            },
            'vip': {
                'signals_per_day': -1,  # Illimité
                'watchlist_size': -1,   # Illimité
                'alerts_per_user': -1,  # Illimité
                'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
                'features': ['all']
            }
        }

        # Cache des permissions pour éviter les requêtes répétées
        self.permission_cache = {}
        self.cache_expiry = {}

    def get_user_tier(self, user_id: int, guild: discord.Guild = None) -> str:
        """Détermine le niveau d'abonnement d'un utilisateur"""
        try:
            # Vérification du cache
            if user_id in self.permission_cache:
                if datetime.utcnow() < self.cache_expiry.get(user_id, datetime.utcnow()):
                    return self.permission_cache[user_id]

            # Vérification en base de données
            user_data = self.db_manager.get_user(user_id)

            if user_data:
                subscription_end = user_data.get('subscription_end')
                subscription_tier = user_data.get('subscription_tier', 'free')

                # Vérification de l'expiration
                if subscription_end:
                    try:
                        if isinstance(subscription_end, str):
                            end_date = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
                        else:
                            end_date = subscription_end

                        if datetime.utcnow() > end_date:
                            # Abonnement expiré, retour au niveau gratuit
                            self.db_manager.update_subscription(user_id, 'free', 0)
                            subscription_tier = 'free'
                    except:
                        subscription_tier = 'free'

                # Vérification des rôles Discord si disponible
                if guild:
                    member = guild.get_member(user_id)
                    if member:
                        role_tier = self._check_discord_roles(member)
                        if role_tier and role_tier != subscription_tier:
                            subscription_tier = role_tier
            else:
                subscription_tier = 'free'

            # Mise en cache
            self.permission_cache[user_id] = subscription_tier
            self.cache_expiry[user_id] = datetime.utcnow() + timedelta(minutes=5)

            return subscription_tier

        except Exception as e:
            logging.error(f"Erreur lors de la récupération du tier pour {user_id}: {e}")
            return 'free'

    def _check_discord_roles(self, member: discord.Member) -> Optional[str]:
        """Vérifie les rôles Discord pour déterminer le tier"""
        try:
            user_role_ids = [role.id for role in member.roles]

            if self.role_ids['admin'] in user_role_ids:
                return 'vip'  # Admin = VIP
            elif self.role_ids['vip'] in user_role_ids:
                return 'vip'
            elif self.role_ids['premium'] in user_role_ids:
                return 'premium'

            return None

        except Exception as e:
            logging.error(f"Erreur lors de la vérification des rôles: {e}")
            return None

    def has_permission(self, user_id: int, feature: str, guild: discord.Guild = None) -> bool:
        """Vérifie si un utilisateur a accès à une fonctionnalité"""
        try:
            user_tier = self.get_user_tier(user_id, guild)

            if user_tier == 'vip':
                return True  # VIP a accès à tout

            tier_features = self.tier_limits.get(user_tier, {}).get('features', [])

            return feature in tier_features or 'all' in tier_features

        except Exception as e:
            logging.error(f"Erreur lors de la vérification des permissions: {e}")
            return False

    def check_usage_limit(self, user_id: int, usage_type: str, guild: discord.Guild = None) -> Dict[str, any]:
        """Vérifie les limites d'utilisation"""
        try:
            user_tier = self.get_user_tier(user_id, guild)
            limits = self.tier_limits.get(user_tier, {})

            limit = limits.get(usage_type, 0)

            if limit == -1:  # Illimité
                return {
                    'allowed': True,
                    'limit': -1,
                    'used': 0,
                    'remaining': -1
                }

            # Récupération de l'utilisation actuelle (à implémenter selon le type)
            current_usage = self._get_current_usage(user_id, usage_type)

            return {
                'allowed': current_usage < limit,
                'limit': limit,
                'used': current_usage,
                'remaining': max(0, limit - current_usage)
            }

        except Exception as e:
            logging.error(f"Erreur lors de la vérification des limites: {e}")
            return {'allowed': False, 'limit': 0, 'used': 0, 'remaining': 0}

    def _get_current_usage(self, user_id: int, usage_type: str) -> int:
        """Récupère l'utilisation actuelle d'un utilisateur"""
        try:
            # Implémentation simplifiée - dans un vrai système, récupérer depuis la DB
            today = datetime.utcnow().date()

            if usage_type == 'signals_per_day':
                # Compter les signaux demandés aujourd'hui
                return 0  # À implémenter avec la DB
            elif usage_type == 'watchlist_size':
                # Compter les éléments dans la watchlist
                alerts = self.db_manager.get_active_alerts()
                user_alerts = [a for a in alerts if a['user_id'] == user_id and a['alert_type'] == 'watchlist']
                return len(user_alerts)
            elif usage_type == 'alerts_per_user':
                # Compter les alertes actives
                alerts = self.db_manager.get_active_alerts()
                user_alerts = [a for a in alerts if a['user_id'] == user_id]
                return len(user_alerts)

            return 0

        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'utilisation: {e}")
            return 0

    def get_available_timeframes(self, user_id: int, guild: discord.Guild = None) -> List[str]:
        """Récupère les timeframes disponibles pour un utilisateur"""
        try:
            user_tier = self.get_user_tier(user_id, guild)
            return self.tier_limits.get(user_tier, {}).get('timeframes', ['1h'])
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des timeframes: {e}")
            return ['1h']

    def create_upgrade_embed(self, current_tier: str = 'free') -> discord.Embed:
        """Crée un embed pour encourager la mise à niveau"""
        embed = discord.Embed(
            title="🚀 Mise à Niveau Premium",
            description="Débloquez tout le potentiel du Trading Bot!",
            color=discord.Color.gold()
        )

        # Plan gratuit
        embed.add_field(
            name="🆓 Plan Gratuit (Actuel)" if current_tier == 'free' else "🆓 Plan Gratuit",
            value="• 10 signaux/jour\n• Timeframes 1h, 4h\n• Vue marché basique\n• 3 alertes max",
            inline=True
        )

        # Plan Premium
        premium_price = os.getenv('PREMIUM_PRICE', '29.99')
        embed.add_field(
            name="💎 Plan Premium" + (" (Actuel)" if current_tier == 'premium' else ""),
            value=f"**${premium_price}/mois**\n• 100 signaux/jour\n• Analyses complètes\n• Portfolio tracking\n• 20 cryptos watchlist\n• Support prioritaire",
            inline=True
        )

        # Plan VIP
        vip_price = os.getenv('VIP_PRICE', '79.99')
        embed.add_field(
            name="👑 Plan VIP" + (" (Actuel)" if current_tier == 'vip' else ""),
            value=f"**${vip_price}/mois**\n• Signaux illimités\n• Tous timeframes\n• Alertes personnalisées\n• Support 24/7\n• Accès bêta\n• Backtesting avancé",
            inline=True
        )

        embed.add_field(
            name="💳 Méthodes de Paiement",
            value="• PayPal\n• Stripe (CB)\n• Crypto (BTC, ETH, USDT)\n• Virement bancaire",
            inline=False
        )

        embed.add_field(
            name="🎁 Offre Spéciale",
            value="**Code LAUNCH50** - 50% de réduction sur le premier mois!",
            inline=False
        )

        embed.set_footer(text="Satisfait ou remboursé sous 7 jours!")

        return embed

    def create_feature_locked_embed(self, feature_name: str, required_tier: str) -> discord.Embed:
        """Crée un embed pour une fonctionnalité verrouillée"""
        embed = discord.Embed(
            title=f"🔒 {feature_name} - Fonctionnalité {required_tier.title()}",
            description=f"Cette fonctionnalité nécessite un abonnement {required_tier.title()}.",
            color=discord.Color.gold()
        )

        if required_tier == 'premium':
            benefits = [
                "📊 Analyses techniques avancées",
                "📈 Graphiques détaillés",
                "🎯 Niveaux de support/résistance",
                "📱 Alertes personnalisées",
                "💼 Suivi de portfolio"
            ]
        else:  # vip
            benefits = [
                "🚀 Tous les avantages Premium",
                "⚡ Signaux en temps réel",
                "🔍 Backtesting avancé",
                "👨‍💼 Support dédié 24/7",
                "🎯 Analyses multi-timeframes",
                "🤖 Bot trading automatisé"
            ]

        embed.add_field(
            name=f"🎁 Avantages {required_tier.title()}",
            value="\n".join(benefits),
            inline=False
        )

        embed.add_field(
            name="🚀 Mise à niveau",
            value="Utilisez `/upgrade` pour voir nos offres!",
            inline=False
        )

        return embed

    def log_permission_check(self, user_id: int, feature: str, granted: bool):
        """Log les vérifications de permissions pour analytics"""
        try:
            self.db_manager.log_activity(
                user_id,
                'permission_check',
                f"Feature: {feature}, Granted: {granted}"
            )
        except Exception as e:
            logging.error(f"Erreur lors du log de permission: {e}")

    def invalidate_cache(self, user_id: int = None):
        """Invalide le cache des permissions"""
        try:
            if user_id:
                self.permission_cache.pop(user_id, None)
                self.cache_expiry.pop(user_id, None)
            else:
                self.permission_cache.clear()
                self.cache_expiry.clear()

            logging.info(f"Cache invalidé pour {'utilisateur ' + str(user_id) if user_id else 'tous les utilisateurs'}")

        except Exception as e:
            logging.error(f"Erreur lors de l'invalidation du cache: {e}")

    def get_user_stats(self, user_id: int) -> Dict:
        """Récupère les statistiques d'utilisation d'un utilisateur"""
        try:
            user_tier = self.get_user_tier(user_id)

            stats = {
                'tier': user_tier,
                'signals_today': self._get_current_usage(user_id, 'signals_per_day'),
                'watchlist_size': self._get_current_usage(user_id, 'watchlist_size'),
                'active_alerts': self._get_current_usage(user_id, 'alerts_per_user'),
                'available_features': self.tier_limits.get(user_tier, {}).get('features', []),
                'available_timeframes': self.tier_limits.get(user_tier, {}).get('timeframes', [])
            }

            # Ajout des limites
            limits = self.tier_limits.get(user_tier, {})
            stats['limits'] = {
                'signals_per_day': limits.get('signals_per_day', 0),
                'watchlist_size': limits.get('watchlist_size', 0),
                'alerts_per_user': limits.get('alerts_per_user', 0)
            }

            return stats

        except Exception as e:
            logging.error(f"Erreur lors de la récupération des stats pour {user_id}: {e}")
            return {}

    async def upgrade_user(self, user_id: int, new_tier: str, duration_days: int = 30) -> bool:
        """Met à niveau un utilisateur"""
        try:
            # Validation du tier
            if new_tier not in ['free', 'premium', 'vip']:
                return False

            # Mise à jour en base
            success = self.db_manager.update_subscription(user_id, new_tier, duration_days)

            if success:
                # Invalidation du cache
                self.invalidate_cache(user_id)

                # Log de l'activité
                self.db_manager.log_activity(
                    user_id,
                    'subscription_upgrade',
                    f"Upgrade vers {new_tier} pour {duration_days} jours"
                )

                logging.info(f"Utilisateur {user_id} upgradé vers {new_tier}")
                return True

            return False

        except Exception as e:
            logging.error(f"Erreur lors de l'upgrade de {user_id}: {e}")
            return False

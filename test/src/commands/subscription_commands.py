# Commandes d'abonnement et de paiement

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Optional
import hashlib
import secrets

class SubscriptionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Configuration des prix
        self.prices = {
            'premium': {
                'monthly': 29.99,
                'quarterly': 79.99,  # 3 mois
                'yearly': 299.99     # 12 mois (2 mois gratuits)
            },
            'vip': {
                'monthly': 79.99,
                'quarterly': 219.99,  # 3 mois
                'yearly': 799.99      # 12 mois (2 mois gratuits)
            }
        }

        # Codes promo actifs
        self.promo_codes = {
            'LAUNCH50': {'discount': 0.5, 'expires': datetime(2025, 12, 31)},
            'WELCOME25': {'discount': 0.25, 'expires': datetime(2025, 8, 31)},
            'STUDENT': {'discount': 0.3, 'expires': datetime(2025, 12, 31)},
            'CRYPTO2025': {'discount': 0.4, 'expires': datetime(2025, 7, 15)}
        }

    @app_commands.command(name="upgrade", description="Voir les plans d'abonnement et upgrader")
    async def upgrade_plan(self, interaction: discord.Interaction):
        """Affiche les options d'upgrade"""
        await interaction.response.defer(ephemeral=True)

        try:
            current_tier = self.bot.permission_manager.get_user_tier(interaction.user.id, interaction.guild)

            embed = discord.Embed(
                title="🚀 Plans d'Abonnement Trading Bot Premium",
                description="Choisissez le plan qui vous convient le mieux!",
                color=discord.Color.gold()
            )

            # Plan actuel
            tier_emojis = {'free': '🆓', 'premium': '💎', 'vip': '👑'}
            tier_names = {'free': 'Gratuit', 'premium': 'Premium', 'vip': 'VIP'}

            embed.add_field(
                name=f"{tier_emojis.get(current_tier, '❓')} Plan Actuel",
                value=f"**{tier_names.get(current_tier, 'Inconnu')}**",
                inline=False
            )

            # Plan Premium
            embed.add_field(
                name="💎 Plan Premium",
                value=f"**${self.prices['premium']['monthly']}/mois**\n"
                      f"• 100 signaux par jour\n"
                      f"• Analyses techniques complètes\n"
                      f"• Portfolio tracking\n"
                      f"• 20 cryptos en watchlist\n"
                      f"• Alertes personnalisées\n"
                      f"• Support prioritaire",
                inline=True
            )

            # Plan VIP
            embed.add_field(
                name="👑 Plan VIP",
                value=f"**${self.prices['vip']['monthly']}/mois**\n"
                      f"• Signaux illimités\n"
                      f"• Tous les timeframes\n"
                      f"• Bot trading automatisé\n"
                      f"• Backtesting avancé\n"
                      f"• Support 24/7 dédié\n"
                      f"• Accès fonctionnalités bêta\n"
                      f"• Analyses prédictives IA",
                inline=True
            )

            # Offres spéciales
            embed.add_field(
                name="🎁 Offres Spéciales",
                value="**LAUNCH50** - 50% de réduction\n"
                      "**WELCOME25** - 25% pour nouveaux users\n"
                      "**STUDENT** - 30% tarif étudiant\n"
                      "**CRYPTO2025** - 40% offre limitée",
                inline=False
            )

            # Boutons d'action
            view = UpgradeView(self.bot, current_tier)

            embed.set_footer(text="💳 Paiement sécurisé | 🔄 Annulation à tout moment | 💯 Satisfait ou remboursé 7j")

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans upgrade_plan: {e}")
            await interaction.followup.send("❌ Erreur lors de l'affichage des plans.", ephemeral=True)

    @app_commands.command(name="subscription", description="Voir votre abonnement actuel")
    async def view_subscription(self, interaction: discord.Interaction):
        """Affiche les détails de l'abonnement"""
        await interaction.response.defer(ephemeral=True)

        try:
            user_data = self.bot.db_manager.get_user(interaction.user.id)

            if not user_data:
                # Créer l'utilisateur s'il n'existe pas
                self.bot.db_manager.add_user(interaction.user.id, str(interaction.user), 'free')
                user_data = {'subscription_tier': 'free', 'subscription_end': None}

            tier = user_data.get('subscription_tier', 'free')
            end_date = user_data.get('subscription_end')
            total_spent = user_data.get('total_spent', 0)

            tier_colors = {
                'free': discord.Color.blue(),
                'premium': discord.Color.purple(),
                'vip': discord.Color.gold()
            }

            tier_names = {
                'free': '🆓 Gratuit',
                'premium': '💎 Premium',
                'vip': '👑 VIP'
            }

            embed = discord.Embed(
                title="📋 Votre Abonnement",
                color=tier_colors.get(tier, discord.Color.blue())
            )

            embed.add_field(
                name="🎯 Plan Actuel",
                value=tier_names.get(tier, 'Inconnu'),
                inline=True
            )

            if end_date and tier != 'free':
                try:
                    if isinstance(end_date, str):
                        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                    days_remaining = (end_date - datetime.utcnow()).days

                    if days_remaining > 0:
                        embed.add_field(
                            name="📅 Expire le",
                            value=f"{end_date.strftime('%d/%m/%Y')}\n({days_remaining} jours restants)",
                            inline=True
                        )

                        # Alerte si expiration proche
                        if days_remaining <= 7:
                            embed.add_field(
                                name="⚠️ Expiration Proche",
                                value="Votre abonnement expire bientôt!\nRenouvelez avec `/upgrade`",
                                inline=False
                            )
                    else:
                        embed.add_field(
                            name="❌ Statut",
                            value="Abonnement expiré",
                            inline=True
                        )
                except:
                    pass

            # Statistiques d'utilisation
            stats = self.bot.permission_manager.get_user_stats(interaction.user.id)

            embed.add_field(
                name="📊 Utilisation Aujourd'hui",
                value=f"Signaux: {stats.get('signals_today', 0)}\n"
                      f"Watchlist: {stats.get('watchlist_size', 0)}\n"
                      f"Alertes: {stats.get('active_alerts', 0)}",
                inline=True
            )

            if total_spent > 0:
                embed.add_field(
                    name="💰 Total Dépensé",
                    value=f"${total_spent:.2f}",
                    inline=True
                )

            # Boutons d'action
            view = SubscriptionManageView(self.bot, tier)

            embed.set_footer(text="Merci de votre confiance! 🙏")

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans view_subscription: {e}")
            await interaction.followup.send("❌ Erreur lors de l'affichage de l'abonnement.", ephemeral=True)

    @app_commands.command(name="promo", description="Utiliser un code promo")
    @app_commands.describe(code="Code promo à utiliser")
    async def use_promo_code(self, interaction: discord.Interaction, code: str):
        """Utilise un code promo"""
        await interaction.response.defer(ephemeral=True)

        try:
            code = code.upper().strip()

            if code not in self.promo_codes:
                await interaction.followup.send("❌ Code promo invalide ou expiré.", ephemeral=True)
                return

            promo = self.promo_codes[code]

            # Vérification de l'expiration
            if datetime.utcnow() > promo['expires']:
                await interaction.followup.send("❌ Ce code promo a expiré.", ephemeral=True)
                return

            discount_pct = int(promo['discount'] * 100)

            embed = discord.Embed(
                title="🎉 Code Promo Valide!",
                description=f"Code **{code}** accepté!",
                color=discord.Color.green()
            )

            embed.add_field(
                name="💰 Réduction",
                value=f"{discount_pct}% de réduction",
                inline=True
            )

            embed.add_field(
                name="⏰ Valide jusqu'au",
                value=promo['expires'].strftime('%d/%m/%Y'),
                inline=True
            )

            # Calcul des prix avec réduction
            premium_price = self.prices['premium']['monthly'] * (1 - promo['discount'])
            vip_price = self.prices['vip']['monthly'] * (1 - promo['discount'])

            embed.add_field(
                name="💎 Premium avec réduction",
                value=f"${premium_price:.2f}/mois (au lieu de ${self.prices['premium']['monthly']})",
                inline=False
            )

            embed.add_field(
                name="👑 VIP avec réduction",
                value=f"${vip_price:.2f}/mois (au lieu de ${self.prices['vip']['monthly']})",
                inline=False
            )

            # Bouton pour upgrader avec le code
            view = PromoUpgradeView(self.bot, code, promo['discount'])

            embed.set_footer(text="Offre limitée - Profitez-en maintenant!")

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans use_promo_code: {e}")
            await interaction.followup.send("❌ Erreur lors de l'utilisation du code promo.", ephemeral=True)

class UpgradeView(discord.ui.View):
    def __init__(self, bot, current_tier):
        super().__init__(timeout=300)
        self.bot = bot
        self.current_tier = current_tier

    @discord.ui.button(label="💎 Upgrade Premium", style=discord.ButtonStyle.primary)
    async def upgrade_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_upgrade(interaction, 'premium')

    @discord.ui.button(label="👑 Upgrade VIP", style=discord.ButtonStyle.success)
    async def upgrade_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_upgrade(interaction, 'vip')

    @discord.ui.button(label="💳 Moyens de Paiement", style=discord.ButtonStyle.secondary)
    async def payment_methods(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💳 Moyens de Paiement Acceptés",
            description="Choisissez votre méthode de paiement préférée",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🏦 Cartes Bancaires",
            value="• Visa, Mastercard, Amex\n• Paiement sécurisé Stripe\n• Prélèvement automatique",
            inline=True
        )

        embed.add_field(
            name="💰 Cryptomonnaies",
            value="• Bitcoin (BTC)\n• Ethereum (ETH)\n• USDT, USDC\n• Binance Coin (BNB)",
            inline=True
        )

        embed.add_field(
            name="🌐 Autres Méthodes",
            value="• PayPal\n• Virement SEPA\n• Apple Pay\n• Google Pay",
            inline=True
        )

        embed.set_footer(text="Tous les paiements sont sécurisés et chiffrés")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _handle_upgrade(self, interaction, tier):
        await interaction.response.defer(ephemeral=True)

        try:
            if self.current_tier == tier:
                await interaction.followup.send(f"✅ Vous avez déjà un abonnement {tier.title()}!", ephemeral=True)
                return

            # Génération d'un lien de paiement sécurisé
            payment_id = self._generate_payment_id(interaction.user.id, tier)

            embed = discord.Embed(
                title=f"💳 Paiement {tier.title()}",
                description=f"Procédure de paiement pour l'abonnement {tier.title()}",
                color=discord.Color.green()
            )

            embed.add_field(
                name="💰 Montant",
                value=f"${self.bot.get_cog('SubscriptionCommands').prices[tier]['monthly']:.2f}/mois",
                inline=True
            )

            embed.add_field(
                name="🔒 ID de Transaction",
                value=f"`{payment_id}`",
                inline=True
            )

            embed.add_field(
                name="📋 Étapes Suivantes",
                value="1. **Contactez notre équipe** sur Discord\n"
                      "2. **Fournissez votre ID de transaction**\n"
                      "3. **Choisissez votre méthode de paiement**\n"
                      "4. **Activation instantanée** après paiement",
                inline=False
            )

            embed.add_field(
                name="📞 Support",
                value="**Discord:** @TradingBotSupport\n"
                      "**Email:** support@tradingbot.com\n"
                      "**Telegram:** @TradingBotHelp",
                inline=False
            )

            embed.set_footer(text="⚡ Activation en moins de 5 minutes!")

            await interaction.followup.send(embed=embed, ephemeral=True)

            # Log de la demande de paiement
            self.bot.db_manager.log_activity(
                interaction.user.id,
                'payment_request',
                f"Demande upgrade {tier} - ID: {payment_id}"
            )

        except Exception as e:
            logging.error(f"Erreur lors de l'upgrade: {e}")
            await interaction.followup.send("❌ Erreur lors du processus de paiement.", ephemeral=True)

    def _generate_payment_id(self, user_id, tier):
        """Génère un ID de paiement unique"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        data = f"{user_id}_{tier}_{timestamp}_{secrets.token_hex(8)}"
        return hashlib.md5(data.encode()).hexdigest()[:12].upper()

class SubscriptionManageView(discord.ui.View):
    def __init__(self, bot, current_tier):
        super().__init__(timeout=300)
        self.bot = bot
        self.current_tier = current_tier

        # Masquer le bouton upgrade si déjà VIP
        if current_tier != 'vip':
            self.add_item(discord.ui.Button(
                label="🚀 Upgrade",
                style=discord.ButtonStyle.primary,
                custom_id="upgrade_btn"
            ))

    @discord.ui.button(label="📊 Statistiques", style=discord.ButtonStyle.secondary)
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats = self.bot.permission_manager.get_user_stats(interaction.user.id)

        embed = discord.Embed(
            title="📊 Vos Statistiques d'Utilisation",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🎯 Signaux Demandés",
            value=f"Aujourd'hui: {stats.get('signals_today', 0)}\nLimite: {stats.get('limits', {}).get('signals_per_day', 'Illimité')}",
            inline=True
        )

        embed.add_field(
            name="👀 Watchlist",
            value=f"Cryptos suivies: {stats.get('watchlist_size', 0)}\nLimite: {stats.get('limits', {}).get('watchlist_size', 'Illimité')}",
            inline=True
        )

        embed.add_field(
            name="🔔 Alertes Actives",
            value=f"Alertes: {stats.get('active_alerts', 0)}\nLimite: {stats.get('limits', {}).get('alerts_per_user', 'Illimité')}",
            inline=True
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class PromoUpgradeView(discord.ui.View):
    def __init__(self, bot, promo_code, discount):
        super().__init__(timeout=300)
        self.bot = bot
        self.promo_code = promo_code
        self.discount = discount

    @discord.ui.button(label="💎 Premium avec Promo", style=discord.ButtonStyle.primary)
    async def upgrade_premium_promo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_promo_upgrade(interaction, 'premium')

    @discord.ui.button(label="👑 VIP avec Promo", style=discord.ButtonStyle.success)
    async def upgrade_vip_promo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_promo_upgrade(interaction, 'vip')

    async def _handle_promo_upgrade(self, interaction, tier):
        await interaction.response.defer(ephemeral=True)

        try:
            # Calcul du prix avec réduction
            original_price = self.bot.get_cog('SubscriptionCommands').prices[tier]['monthly']
            discounted_price = original_price * (1 - self.discount)
            savings = original_price - discounted_price

            embed = discord.Embed(
                title=f"🎉 Upgrade {tier.title()} avec Code Promo",
                description=f"Profitez de votre réduction avec le code **{self.promo_code}**!",
                color=discord.Color.green()
            )

            embed.add_field(
                name="💰 Prix Original",
                value=f"~~${original_price:.2f}~~",
                inline=True
            )

            embed.add_field(
                name="🎁 Prix avec Promo",
                value=f"**${discounted_price:.2f}**",
                inline=True
            )

            embed.add_field(
                name="💸 Économies",
                value=f"${savings:.2f}",
                inline=True
            )

            embed.add_field(
                name="📞 Finaliser la Commande",
                value="Contactez notre support avec ce code promo pour finaliser votre abonnement à prix réduit!",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur lors de l'upgrade promo: {e}")
            await interaction.followup.send("❌ Erreur lors du processus de paiement.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SubscriptionCommands(bot))

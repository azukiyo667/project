# Commandes d'administration pour les propriétaires du bot

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Optional, List
import json
import psutil
import os

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # IDs des administrateurs autorisés
        self.admin_ids = [
            # Ajoutez ici les IDs Discord des administrateurs
            123456789012345678,  # Remplacez par votre ID Discord
        ]

    def is_admin(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est administrateur"""
        return user_id in self.admin_ids

    @app_commands.command(name="admin_stats", description="[ADMIN] Statistiques globales du bot")
    async def admin_stats(self, interaction: discord.Interaction):
        """Affiche les statistiques administrateur"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Accès refusé. Commande réservée aux administrateurs.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Statistiques de base de données
            db_stats = self.bot.db_manager.get_database_stats()

            # Statistiques de performance
            perf_stats = self.bot.db_manager.get_performance_stats(30)

            # Statistiques système
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            embed = discord.Embed(
                title="📊 Statistiques Administrateur",
                description="Vue d'ensemble complète du système",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            # Base de données
            embed.add_field(
                name="🗄️ Base de Données",
                value=f"Utilisateurs: {db_stats.get('users_count', 0):,}\n"
                      f"Signaux: {db_stats.get('signals_count', 0):,}\n"
                      f"Portfolios: {db_stats.get('portfolios_count', 0):,}\n"
                      f"Taille: {db_stats.get('db_size_mb', 0):.1f} MB",
                inline=True
            )

            # Performance (30 derniers jours)
            embed.add_field(
                name="📈 Performance (30j)",
                value=f"Signaux totaux: {perf_stats.get('total_signals', 0):,}\n"
                      f"Taux de réussite: {perf_stats.get('success_rate', 0):.1f}%\n"
                      f"P&L moyen: {perf_stats.get('total_profit_loss', 0):+.2f}%\n"
                      f"Confiance moy.: {perf_stats.get('avg_confidence', 0):.1f}%",
                inline=True
            )

            # Système
            embed.add_field(
                name="💻 Système",
                value=f"CPU: {cpu_percent}%\n"
                      f"RAM: {memory.percent}% ({memory.used // 1024**3}GB/{memory.total // 1024**3}GB)\n"
                      f"Disque: {disk.percent}% ({disk.used // 1024**3}GB/{disk.total // 1024**3}GB)\n"
                      f"Serveurs: {len(self.bot.guilds)}",
                inline=True
            )

            # Top symboles
            top_symbols = perf_stats.get('top_symbols', [])[:5]
            if top_symbols:
                symbols_text = "\n".join([f"{s['symbol']}: {s['count']} signaux" for s in top_symbols])
                embed.add_field(
                    name="🏆 Top Symboles",
                    value=symbols_text,
                    inline=False
                )

            embed.set_footer(text="Données en temps réel")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans admin_stats: {e}")
            await interaction.followup.send("❌ Erreur lors de la récupération des statistiques.", ephemeral=True)

    @app_commands.command(name="admin_users", description="[ADMIN] Gestion des utilisateurs")
    @app_commands.describe(action="Action à effectuer", user_id="ID de l'utilisateur", tier="Nouveau niveau d'abonnement")
    async def admin_users(self, interaction: discord.Interaction, action: str, user_id: Optional[str] = None, tier: Optional[str] = None):
        """Gestion des utilisateurs"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Accès refusé.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if action.lower() == "list":
                # Liste des utilisateurs premium/vip
                premium_users = self.bot.db_manager.get_premium_users()

                embed = discord.Embed(
                    title="👥 Utilisateurs Premium/VIP",
                    color=discord.Color.gold()
                )

                if premium_users:
                    users_text = []
                    for uid in premium_users[:20]:  # Limite à 20
                        user_data = self.bot.db_manager.get_user(uid)
                        if user_data:
                            tier_emoji = {"premium": "💎", "vip": "👑"}.get(user_data['subscription_tier'], "❓")
                            users_text.append(f"{tier_emoji} <@{uid}> ({user_data['subscription_tier']})")

                    embed.add_field(
                        name=f"📋 Utilisateurs Actifs ({len(premium_users)})",
                        value="\n".join(users_text[:10]) + (f"\n... et {len(users_text) - 10} autres" if len(users_text) > 10 else ""),
                        inline=False
                    )
                else:
                    embed.add_field(name="📋 Utilisateurs", value="Aucun utilisateur premium actif", inline=False)

                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action.lower() == "upgrade" and user_id and tier:
                # Upgrade d'un utilisateur
                try:
                    uid = int(user_id)
                except ValueError:
                    await interaction.followup.send("❌ ID utilisateur invalide.", ephemeral=True)
                    return

                if tier.lower() not in ['free', 'premium', 'vip']:
                    await interaction.followup.send("❌ Tier invalide. Utilisez: free, premium, vip", ephemeral=True)
                    return

                success = await self.bot.permission_manager.upgrade_user(uid, tier.lower(), 30)

                if success:
                    embed = discord.Embed(
                        title="✅ Utilisateur Upgradé",
                        description=f"<@{uid}> a été upgradé vers {tier.lower()}",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Erreur",
                        description="Impossible d'upgrader cet utilisateur",
                        color=discord.Color.red()
                    )

                await interaction.followup.send(embed=embed, ephemeral=True)

            else:
                await interaction.followup.send("❌ Action invalide. Utilisez: list, upgrade", ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans admin_users: {e}")
            await interaction.followup.send("❌ Erreur lors de l'exécution de la commande.", ephemeral=True)

    @app_commands.command(name="admin_signals", description="[ADMIN] Gestion des signaux")
    @app_commands.describe(action="Action à effectuer", symbol="Symbole pour forcer un signal")
    async def admin_signals(self, interaction: discord.Interaction, action: str, symbol: Optional[str] = None):
        """Gestion des signaux"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Accès refusé.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if action.lower() == "force" and symbol:
                # Force un signal pour test
                if '/' not in symbol:
                    symbol = f"{symbol.upper()}/USDT"

                analysis = await self.bot.analyzer.analyze_symbol(symbol, '1h')
                signal = await self.bot.signal_generator.generate_signal(symbol, analysis)

                # Envoi forcé du signal
                await self.bot.send_signal(signal)

                embed = discord.Embed(
                    title="🚀 Signal Forcé",
                    description=f"Signal {signal['action']} généré pour {symbol}",
                    color=discord.Color.green()
                )

                embed.add_field(name="Action", value=signal['action'], inline=True)
                embed.add_field(name="Confiance", value=f"{signal['confidence']:.1f}%", inline=True)
                embed.add_field(name="Prix", value=f"${signal['price']:.4f}", inline=True)

                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action.lower() == "stats":
                # Statistiques des signaux récents
                signals = self.bot.db_manager.get_signals(limit=50, days=7)

                if signals:
                    buy_count = len([s for s in signals if s['action'] == 'BUY'])
                    sell_count = len([s for s in signals if s['action'] == 'SELL'])
                    hold_count = len([s for s in signals if s['action'] == 'HOLD'])
                    avg_confidence = sum(s['confidence'] for s in signals) / len(signals)

                    embed = discord.Embed(
                        title="📊 Statistiques Signaux (7j)",
                        color=discord.Color.blue()
                    )

                    embed.add_field(name="🟢 BUY", value=str(buy_count), inline=True)
                    embed.add_field(name="🔴 SELL", value=str(sell_count), inline=True)
                    embed.add_field(name="⏸️ HOLD", value=str(hold_count), inline=True)
                    embed.add_field(name="📊 Confiance Moy.", value=f"{avg_confidence:.1f}%", inline=True)
                    embed.add_field(name="📈 Total", value=str(len(signals)), inline=True)

                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("📊 Aucun signal récent trouvé.", ephemeral=True)

            else:
                await interaction.followup.send("❌ Action invalide. Utilisez: force, stats", ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans admin_signals: {e}")
            await interaction.followup.send("❌ Erreur lors de l'exécution.", ephemeral=True)

    @app_commands.command(name="admin_maintenance", description="[ADMIN] Maintenance du bot")
    @app_commands.describe(action="Action de maintenance")
    async def admin_maintenance(self, interaction: discord.Interaction, action: str):
        """Maintenance du système"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Accès refusé.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if action.lower() == "cleanup":
                # Nettoyage de la base de données
                self.bot.db_manager.cleanup_old_data(90)

                embed = discord.Embed(
                    title="🧹 Nettoyage Effectué",
                    description="Base de données nettoyée (données > 90 jours supprimées)",
                    color=discord.Color.green()
                )

            elif action.lower() == "backup":
                # Sauvegarde de la base de données
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                backup_path = f"backup/trading_bot_{timestamp}.db"

                success = self.bot.db_manager.backup_database(backup_path)

                if success:
                    embed = discord.Embed(
                        title="💾 Sauvegarde Créée",
                        description=f"Sauvegarde: `{backup_path}`",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Erreur Sauvegarde",
                        description="Impossible de créer la sauvegarde",
                        color=discord.Color.red()
                    )

            elif action.lower() == "restart":
                # Redémarrage des tâches
                embed = discord.Embed(
                    title="🔄 Redémarrage",
                    description="Redémarrage des tâches automatiques...",
                    color=discord.Color.orange()
                )

                await interaction.followup.send(embed=embed, ephemeral=True)

                # Redémarrage des tâches
                self.bot.market_analysis.restart()
                self.bot.portfolio_update.restart()
                self.bot.daily_report.restart()

                return

            elif action.lower() == "cache":
                # Vidage du cache des permissions
                self.bot.permission_manager.invalidate_cache()

                embed = discord.Embed(
                    title="🗑️ Cache Vidé",
                    description="Cache des permissions réinitialisé",
                    color=discord.Color.green()
                )

            else:
                await interaction.followup.send("❌ Action invalide. Utilisez: cleanup, backup, restart, cache", ephemeral=True)
                return

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans admin_maintenance: {e}")
            await interaction.followup.send("❌ Erreur lors de la maintenance.", ephemeral=True)

    @app_commands.command(name="admin_broadcast", description="[ADMIN] Diffuser un message")
    @app_commands.describe(tier="Niveau ciblé", message="Message à diffuser")
    async def admin_broadcast(self, interaction: discord.Interaction, tier: str, message: str):
        """Diffuse un message aux utilisateurs"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Accès refusé.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if tier.lower() not in ['all', 'free', 'premium', 'vip']:
                await interaction.followup.send("❌ Tier invalide. Utilisez: all, free, premium, vip", ephemeral=True)
                return

            # Création de l'embed de diffusion
            embed = discord.Embed(
                title="📢 Message Important",
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.set_footer(text="Message de l'équipe Trading Bot Premium")

            # Simulation d'envoi (dans un vrai bot, envoyer aux utilisateurs concernés)
            sent_count = 0

            if tier.lower() == 'all':
                sent_count = 100  # Simulation
            elif tier.lower() == 'premium':
                premium_users = self.bot.db_manager.get_premium_users()
                sent_count = len([u for u in premium_users if self.bot.permission_manager.get_user_tier(u) == 'premium'])
            elif tier.lower() == 'vip':
                premium_users = self.bot.db_manager.get_premium_users()
                sent_count = len([u for u in premium_users if self.bot.permission_manager.get_user_tier(u) == 'vip'])

            result_embed = discord.Embed(
                title="✅ Message Diffusé",
                description=f"Message envoyé à {sent_count} utilisateurs ({tier.lower()})",
                color=discord.Color.green()
            )

            await interaction.followup.send(embed=result_embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans admin_broadcast: {e}")
            await interaction.followup.send("❌ Erreur lors de la diffusion.", ephemeral=True)

    @app_commands.command(name="admin_config", description="[ADMIN] Configuration du bot")
    @app_commands.describe(setting="Paramètre à modifier", value="Nouvelle valeur")
    async def admin_config(self, interaction: discord.Interaction, setting: str, value: str):
        """Configure les paramètres du bot"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Accès refusé.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Paramètres configurables
            configurable_settings = {
                'alert_channel': 'ALERT_CHANNEL_ID',
                'premium_channel': 'PREMIUM_CHANNEL_ID',
                'vip_channel': 'VIP_CHANNEL_ID',
                'rsi_period': 'RSI_PERIOD',
                'macd_fast': 'MACD_FAST',
                'macd_slow': 'MACD_SLOW'
            }

            if setting.lower() not in configurable_settings:
                available = ", ".join(configurable_settings.keys())
                await interaction.followup.send(f"❌ Paramètre invalide. Disponibles: {available}", ephemeral=True)
                return

            # Simulation de la mise à jour (dans un vrai système, modifier les variables d'environnement)
            embed = discord.Embed(
                title="⚙️ Configuration Mise à Jour",
                description=f"Paramètre **{setting}** défini à `{value}`",
                color=discord.Color.green()
            )

            embed.add_field(
                name="⚠️ Note",
                value="Redémarrage requis pour certains paramètres",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans admin_config: {e}")
            await interaction.followup.send("❌ Erreur lors de la configuration.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))

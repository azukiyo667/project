# Commandes de gestion de portfolio

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Optional
import matplotlib.pyplot as plt
import io
import base64

class PortfolioCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_position", description="Ajouter une position à votre portfolio")
    @app_commands.describe(
        symbol="Symbole de la cryptomonnaie (ex: BTC, ETH)",
        quantity="Quantité possédée",
        entry_price="Prix d'entrée moyen"
    )
    async def add_position(self, interaction: discord.Interaction, symbol: str, quantity: float, entry_price: float):
        """Ajoute une position au portfolio"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Vérification des permissions
            if not self.bot.permission_manager.has_permission(interaction.user.id, 'portfolio', interaction.guild):
                embed = self.bot.permission_manager.create_feature_locked_embed("Portfolio Tracking", "premium")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Validation des données
            if quantity <= 0 or entry_price <= 0:
                await interaction.followup.send("❌ La quantité et le prix doivent être positifs.", ephemeral=True)
                return

            # Formatage du symbole
            if '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"

            # Ajout de la position
            success = await self.bot.portfolio_manager.add_position(
                interaction.user.id,
                symbol,
                quantity,
                entry_price
            )

            if success:
                position_value = quantity * entry_price

                embed = discord.Embed(
                    title="✅ Position Ajoutée",
                    description=f"Position {symbol} ajoutée à votre portfolio!",
                    color=discord.Color.green()
                )

                embed.add_field(name="📊 Symbole", value=symbol, inline=True)
                embed.add_field(name="📈 Quantité", value=f"{quantity:.6f}", inline=True)
                embed.add_field(name="💰 Prix d'Entrée", value=f"${entry_price:.4f}", inline=True)
                embed.add_field(name="💎 Valeur Initiale", value=f"${position_value:.2f}", inline=True)

                embed.set_footer(text="Position ajoutée avec succès! Utilisez /portfolio pour voir votre portfolio complet.")

            else:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="Impossible d'ajouter cette position. Veuillez réessayer.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans add_position: {e}")
            await interaction.followup.send("❌ Erreur lors de l'ajout de la position.", ephemeral=True)

    @app_commands.command(name="portfolio_summary", description="Résumé détaillé de votre portfolio")
    async def portfolio_summary(self, interaction: discord.Interaction):
        """Affiche un résumé détaillé du portfolio"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Vérification des permissions
            if not self.bot.permission_manager.has_permission(interaction.user.id, 'portfolio', interaction.guild):
                embed = self.bot.permission_manager.create_feature_locked_embed("Portfolio Tracking", "premium")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Mise à jour et récupération du portfolio
            portfolio_data = await self.bot.portfolio_manager.update_portfolio(interaction.user.id)

            if portfolio_data.get('error'):
                await interaction.followup.send(f"❌ Erreur: {portfolio_data['error']}", ephemeral=True)
                return

            if not portfolio_data['positions']:
                embed = discord.Embed(
                    title="📊 Portfolio Vide",
                    description="Votre portfolio est vide. Utilisez `/add_position` pour ajouter des positions!",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Création de l'embed détaillé
            embed = await self._create_detailed_portfolio_embed(portfolio_data)

            # Boutons d'action
            view = PortfolioActionView(self.bot)

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans portfolio_summary: {e}")
            await interaction.followup.send("❌ Erreur lors de l'affichage du portfolio.", ephemeral=True)

    @app_commands.command(name="portfolio_alerts", description="Configurer des alertes pour votre portfolio")
    @app_commands.describe(
        alert_type="Type d'alerte (profit, loss, price)",
        threshold="Seuil de déclenchement (%)",
        symbol="Symbole spécifique (optionnel)"
    )
    async def setup_portfolio_alerts(self, interaction: discord.Interaction, alert_type: str, threshold: float, symbol: Optional[str] = None):
        """Configure des alertes de portfolio"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Vérification des permissions
            if not self.bot.permission_manager.has_permission(interaction.user.id, 'alerts', interaction.guild):
                embed = self.bot.permission_manager.create_feature_locked_embed("Alertes Portfolio", "premium")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Validation du type d'alerte
            valid_types = ['profit', 'loss', 'price']
            if alert_type.lower() not in valid_types:
                await interaction.followup.send(f"❌ Type d'alerte invalide. Utilisez: {', '.join(valid_types)}", ephemeral=True)
                return

            # Formatage du symbole si fourni
            if symbol and '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"

            # Ajout de l'alerte
            success = self.bot.db_manager.add_user_alert(
                interaction.user.id,
                symbol or 'ALL',
                f'portfolio_{alert_type.lower()}',
                threshold,
                'above' if alert_type in ['profit', 'price'] else 'below'
            )

            if success:
                embed = discord.Embed(
                    title="🔔 Alerte Configurée",
                    description="Votre alerte de portfolio a été configurée!",
                    color=discord.Color.green()
                )

                embed.add_field(name="🎯 Type", value=alert_type.title(), inline=True)
                embed.add_field(name="📊 Seuil", value=f"{threshold}%", inline=True)
                embed.add_field(name="💎 Symbole", value=symbol or "Tout le portfolio", inline=True)

                embed.set_footer(text="Vous recevrez une notification quand cette condition sera remplie.")

            else:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="Impossible de configurer cette alerte.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans setup_portfolio_alerts: {e}")
            await interaction.followup.send("❌ Erreur lors de la configuration de l'alerte.", ephemeral=True)

    @app_commands.command(name="portfolio_report", description="Rapport de performance détaillé")
    @app_commands.describe(period="Période du rapport (7d, 30d, 90d)")
    async def portfolio_report(self, interaction: discord.Interaction, period: Optional[str] = "30d"):
        """Génère un rapport de performance détaillé"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Vérification des permissions VIP
            user_tier = self.bot.permission_manager.get_user_tier(interaction.user.id, interaction.guild)
            if user_tier != 'vip':
                embed = self.bot.permission_manager.create_feature_locked_embed("Rapports Avancés", "vip")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Validation de la période
            valid_periods = {'7d': 7, '30d': 30, '90d': 90}
            if period not in valid_periods:
                period = "30d"

            days = valid_periods[period]

            # Récupération des données
            portfolio_data = await self.bot.portfolio_manager.update_portfolio(interaction.user.id)
            history = await self.bot.portfolio_manager.get_portfolio_history(interaction.user.id, days)

            if not portfolio_data['positions']:
                await interaction.followup.send("📊 Aucune donnée de portfolio disponible.", ephemeral=True)
                return

            # Génération du rapport
            report = self.bot.portfolio_manager.generate_portfolio_report(interaction.user.id, portfolio_data)

            # Création de l'embed de rapport
            embed = await self._create_report_embed(report, period)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans portfolio_report: {e}")
            await interaction.followup.send("❌ Erreur lors de la génération du rapport.", ephemeral=True)

    async def _create_detailed_portfolio_embed(self, portfolio_data: dict) -> discord.Embed:
        """Crée un embed détaillé du portfolio"""
        embed = discord.Embed(
            title="📊 Portfolio Détaillé",
            description="Analyse complète de votre portfolio crypto",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        # Résumé financier
        total_value = portfolio_data['total_value']
        total_invested = portfolio_data['total_invested']
        total_pnl = portfolio_data['total_pnl_percentage']

        pnl_color = "🟢" if total_pnl >= 0 else "🔴"

        embed.add_field(
            name="💰 Valeur Totale",
            value=f"${total_value:,.2f}",
            inline=True
        )

        embed.add_field(
            name="📈 Investissement Initial",
            value=f"${total_invested:,.2f}",
            inline=True
        )

        embed.add_field(
            name=f"{pnl_color} P&L Global",
            value=f"{total_pnl:+.2f}%\n(${portfolio_data['total_pnl_absolute']:+,.2f})",
            inline=True
        )

        # Top positions (5 premières)
        positions = sorted(portfolio_data['positions'], key=lambda x: x['position_value'], reverse=True)[:5]

        position_text = ""
        for i, pos in enumerate(positions, 1):
            pnl_emoji = "🟢" if pos['pnl_percentage'] >= 0 else "🔴"
            position_text += f"{i}. **{pos['symbol']}**: {pnl_emoji} {pos['pnl_percentage']:+.1f}% (${pos['position_value']:.0f})\n"

        if position_text:
            embed.add_field(
                name="🏆 Top Positions",
                value=position_text,
                inline=False
            )

        # Métriques de risque
        risk_metrics = portfolio_data.get('risk_metrics', {})
        risk_level = risk_metrics.get('risk_level', 'unknown')
        risk_emojis = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}

        embed.add_field(
            name=f"{risk_emojis.get(risk_level, '❓')} Niveau de Risque",
            value=f"{risk_level.title()}\nVaR 95%: {risk_metrics.get('var_95', 0):.1f}%",
            inline=True
        )

        # Diversification
        diversification = portfolio_data.get('diversification', {})
        concentration_risk = diversification.get('concentration_risk', 'unknown')

        embed.add_field(
            name="🎯 Diversification",
            value=f"Score: {diversification.get('score', 0):.1f}/100\nRisque: {concentration_risk.title()}",
            inline=True
        )

        # Performance
        performance = portfolio_data.get('performance', {})
        win_rate = performance.get('win_rate', 0)

        embed.add_field(
            name="📊 Performance",
            value=f"Taux de réussite: {win_rate:.1f}%\nPositions gagnantes: {performance.get('winning_positions', 0)}",
            inline=True
        )

        # Alertes actives
        alerts = portfolio_data.get('alerts', [])
        if alerts:
            alert_text = "\n".join([alert['message'][:50] + "..." if len(alert['message']) > 50 else alert['message'] for alert in alerts[:3]])
            embed.add_field(
                name="🚨 Alertes Récentes",
                value=alert_text,
                inline=False
            )

        embed.set_footer(text="Portfolio mis à jour en temps réel")

        return embed

    async def _create_report_embed(self, report: dict, period: str) -> discord.Embed:
        """Crée un embed de rapport de performance"""
        embed = discord.Embed(
            title=f"📈 Rapport de Performance ({period})",
            description="Analyse détaillée de votre performance de trading",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )

        summary = report.get('summary', {})
        performance = report.get('performance', {})

        # Résumé exécutif
        embed.add_field(
            name="💼 Résumé Exécutif",
            value=f"Valeur: ${summary.get('total_value', 0):,.2f}\n"
                  f"P&L: {summary.get('total_pnl', 0):+.2f}%\n"
                  f"Positions: {summary.get('positions_count', 0)}\n"
                  f"Risque: {summary.get('risk_level', 'N/A').title()}",
            inline=True
        )

        # Métriques clés
        embed.add_field(
            name="🎯 Métriques Clés",
            value=f"Taux de réussite: {performance.get('win_rate', 0):.1f}%\n"
                  f"Profit moyen: {performance.get('avg_win', 0):.2f}%\n"
                  f"Perte moyenne: {performance.get('avg_loss', 0):.2f}%\n"
                  f"Ratio P/L: {performance.get('profit_loss_ratio', 'N/A')}",
            inline=True
        )

        # Recommandations
        recommendations = report.get('recommendations', [])
        if recommendations:
            rec_text = "\n".join([f"• {rec}" for rec in recommendations[:5]])
            embed.add_field(
                name="💡 Recommandations",
                value=rec_text,
                inline=False
            )

        embed.set_footer(text="Rapport généré par l'IA de Trading Bot Premium")

        return embed

class PortfolioActionView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.button(label="📊 Graphique", style=discord.ButtonStyle.primary)
    async def show_chart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📊 Génération du graphique en cours... (Fonctionnalité Premium)", ephemeral=True)

    @discord.ui.button(label="🔄 Actualiser", style=discord.ButtonStyle.secondary)
    async def refresh_portfolio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        try:
            portfolio_data = await self.bot.portfolio_manager.update_portfolio(interaction.user.id)

            if portfolio_data.get('error'):
                await interaction.followup.send(f"❌ Erreur: {portfolio_data['error']}", ephemeral=True)
                return

            embed = discord.Embed(
                title="🔄 Portfolio Actualisé",
                description=f"Dernière mise à jour: {datetime.utcnow().strftime('%H:%M:%S')}",
                color=discord.Color.green()
            )

            embed.add_field(
                name="💰 Valeur Totale",
                value=f"${portfolio_data['total_value']:,.2f}",
                inline=True
            )

            embed.add_field(
                name="📈 P&L Global",
                value=f"{portfolio_data['total_pnl_percentage']:+.2f}%",
                inline=True
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur refresh_portfolio: {e}")
            await interaction.followup.send("❌ Erreur lors de l'actualisation.", ephemeral=True)

    @discord.ui.button(label="🔔 Alertes", style=discord.ButtonStyle.success)
    async def manage_alerts(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔔 Gestion des Alertes",
            description="Configurez vos alertes de portfolio",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="💡 Types d'Alertes Disponibles",
            value="• **Profit Target** - Objectif de gain atteint\n"
                  "• **Stop Loss** - Seuil de perte dépassé\n"
                  "• **Price Alert** - Prix cible atteint\n"
                  "• **Volume Spike** - Pic de volume détecté",
            inline=False
        )

        embed.add_field(
            name="⚙️ Configuration",
            value="Utilisez `/portfolio_alerts` pour configurer vos alertes personnalisées.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(PortfolioCommands(bot))

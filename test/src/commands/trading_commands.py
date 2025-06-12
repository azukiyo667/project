# Commandes de trading pour le bot Discord

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

class TradingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="signal", description="Obtenir un signal de trading pour une crypto")
    @app_commands.describe(
        symbol="Symbole de la cryptomonnaie (ex: BTC, ETH, BNB)",
        timeframe="Timeframe d'analyse (1h, 4h, 1d)"
    )
    async def get_signal(self, interaction: discord.Interaction, symbol: str, timeframe: Optional[str] = "1h"):
        """Commande pour obtenir un signal de trading"""
        await interaction.response.defer()

        try:
            # Vérification des permissions
            user_tier = self.bot.permission_manager.get_user_tier(interaction.user.id)

            if user_tier == 'free' and timeframe not in ['1h', '4h']:
                await interaction.followup.send(
                    "❌ Les timeframes avancés sont réservés aux abonnés Premium!\n"
                    "Utilisez `!upgrade` pour découvrir nos offres.",
                    ephemeral=True
                )
                return

            # Formatage du symbole
            if '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"

            # Génération du signal
            analysis = await self.bot.analyzer.analyze_symbol(symbol, timeframe)

            if analysis.get('error'):
                await interaction.followup.send(f"❌ Erreur lors de l'analyse de {symbol}: {analysis.get('error_message', 'Erreur inconnue')}")
                return

            signal = await self.bot.signal_generator.generate_signal(symbol, analysis)

            # Création de l'embed selon le niveau d'abonnement
            embed = await self._create_signal_embed(signal, user_tier)

            await interaction.followup.send(embed=embed)

            # Log de l'activité
            self.bot.db_manager.log_activity(
                interaction.user.id,
                'signal_request',
                f"Signal demandé pour {symbol} ({timeframe})"
            )

        except Exception as e:
            logging.error(f"Erreur dans la commande signal: {e}")
            await interaction.followup.send("❌ Une erreur est survenue lors de l'analyse. Veuillez réessayer plus tard.")

    @app_commands.command(name="analyze", description="Analyse technique complète d'une crypto")
    @app_commands.describe(symbol="Symbole de la cryptomonnaie à analyser")
    async def analyze_crypto(self, interaction: discord.Interaction, symbol: str):
        """Analyse technique complète - Premium uniquement"""
        await interaction.response.defer()

        try:
            user_tier = self.bot.permission_manager.get_user_tier(interaction.user.id)

            if user_tier == 'free':
                embed = discord.Embed(
                    title="🔒 Fonctionnalité Premium",
                    description="L'analyse technique complète est réservée aux abonnés Premium et VIP!",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="🚀 Avantages Premium",
                    value="• Analyses techniques détaillées\n• Graphiques personnalisés\n• Indicateurs avancés\n• Support et résistance\n• Patterns de trading",
                    inline=False
                )
                embed.add_field(
                    name="💎 Mise à niveau",
                    value="Utilisez `/upgrade` pour voir nos offres!",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return

            # Formatage du symbole
            if '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"

            # Analyse complète
            analysis = await self.bot.analyzer.analyze_symbol(symbol, '1h')
            analysis_4h = await self.bot.analyzer.analyze_symbol(symbol, '4h')
            analysis_1d = await self.bot.analyzer.analyze_symbol(symbol, '1d')

            # Création de l'embed d'analyse complète
            embed = await self._create_analysis_embed(symbol, analysis, analysis_4h, analysis_1d, user_tier)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.error(f"Erreur dans la commande analyze: {e}")
            await interaction.followup.send("❌ Une erreur est survenue lors de l'analyse complète.")

    @app_commands.command(name="watchlist", description="Ajouter une crypto à votre watchlist")
    @app_commands.describe(
        symbol="Symbole de la cryptomonnaie",
        price_alert="Prix d'alerte (optionnel)"
    )
    async def add_to_watchlist(self, interaction: discord.Interaction, symbol: str, price_alert: Optional[float] = None):
        """Ajouter une crypto à la watchlist personnelle"""
        await interaction.response.defer(ephemeral=True)

        try:
            user_tier = self.bot.permission_manager.get_user_tier(interaction.user.id)

            if user_tier == 'free':
                await interaction.followup.send(
                    "❌ La watchlist personnalisée est réservée aux abonnés Premium!\n"
                    "Utilisez `/upgrade` pour accéder à cette fonctionnalité.",
                    ephemeral=True
                )
                return

            # Formatage du symbole
            if '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"

            # Ajout à la base de données
            success = self.bot.db_manager.add_user_alert(
                interaction.user.id,
                symbol,
                'watchlist',
                price_alert,
                'above' if price_alert else None
            )

            if success:
                embed = discord.Embed(
                    title="✅ Ajouté à la Watchlist",
                    description=f"{symbol} a été ajouté à votre watchlist personnelle!",
                    color=discord.Color.green()
                )

                if price_alert:
                    embed.add_field(
                        name="🔔 Alerte Prix",
                        value=f"Alert configurée à ${price_alert:,.2f}",
                        inline=False
                    )

                embed.add_field(
                    name="📱 Notifications",
                    value="Vous recevrez des notifications pour cette crypto!",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="Impossible d'ajouter cette crypto à votre watchlist.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans add_to_watchlist: {e}")
            await interaction.followup.send("❌ Erreur lors de l'ajout à la watchlist.", ephemeral=True)

    @app_commands.command(name="portfolio", description="Voir votre portfolio de trading")
    async def view_portfolio(self, interaction: discord.Interaction):
        """Affichage du portfolio personnel"""
        await interaction.response.defer(ephemeral=True)

        try:
            user_tier = self.bot.permission_manager.get_user_tier(interaction.user.id)

            if user_tier == 'free':
                embed = discord.Embed(
                    title="🔒 Portfolio Premium",
                    description="Le suivi de portfolio est une fonctionnalité Premium!",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="🎯 Fonctionnalités Portfolio",
                    value="• Suivi en temps réel\n• Calcul automatique des P&L\n• Alertes de performance\n• Analyse de risque\n• Historique détaillé",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Récupération du portfolio
            portfolio = self.bot.db_manager.get_user_portfolio(interaction.user.id)

            if not portfolio:
                embed = discord.Embed(
                    title="📊 Portfolio Vide",
                    description="Votre portfolio est vide. Ajoutez des positions avec `/add_position`!",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Création de l'embed portfolio
            embed = await self._create_portfolio_embed(portfolio, user_tier)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Erreur dans view_portfolio: {e}")
            await interaction.followup.send("❌ Erreur lors de l'affichage du portfolio.", ephemeral=True)

    @app_commands.command(name="market", description="Vue d'ensemble du marché crypto")
    async def market_overview(self, interaction: discord.Interaction):
        """Vue d'ensemble du marché"""
        await interaction.response.defer()

        try:
            # Génération du rapport de marché
            report = await self.bot.analyzer.generate_daily_report()

            embed = discord.Embed(
                title="📈 Vue d'Ensemble du Marché",
                description="Analyse du marché crypto en temps réel",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            # Sentiment général
            sentiment_color = {
                'Bullish': '🟢',
                'Bearish': '🔴',
                'Neutral': '🟡'
            }

            sentiment = report.get('market_sentiment', 'Neutral')
            embed.add_field(
                name=f"{sentiment_color.get(sentiment, '🟡')} Sentiment Général",
                value=sentiment,
                inline=True
            )

            embed.add_field(
                name="📊 Signaux Actifs",
                value=f"🟢 Achat: {report.get('buy_signals', 0)}\n🔴 Vente: {report.get('sell_signals', 0)}\n⏸️ Attente: {report.get('hold_signals', 0)}",
                inline=True
            )

            embed.add_field(
                name="🎯 Performance",
                value=f"{report.get('global_performance', 0):+.2f}%",
                inline=True
            )

            # Top performer
            if 'top_performer' in report:
                embed.add_field(
                    name="🏆 Top Performer",
                    value=f"{report['top_performer']['symbol']}: {report['top_performer']['gain']:+.2f}%",
                    inline=False
                )

            embed.set_footer(text="Données mises à jour en temps réel")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.error(f"Erreur dans market_overview: {e}")
            await interaction.followup.send("❌ Erreur lors de la récupération de la vue marché.")

    @app_commands.command(name="help_trading", description="Guide d'utilisation des commandes de trading")
    async def trading_help(self, interaction: discord.Interaction):
        """Guide d'aide pour les commandes de trading"""
        embed = discord.Embed(
            title="🤖 Guide des Commandes Trading",
            description="Découvrez toutes les fonctionnalités de trading disponibles",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🆓 Commandes Gratuites",
            value="`/signal` - Signal de base (1h, 4h)\n`/market` - Vue d'ensemble du marché\n`/help_trading` - Ce guide",
            inline=False
        )

        embed.add_field(
            name="💎 Commandes Premium",
            value="`/analyze` - Analyse technique complète\n`/watchlist` - Watchlist personnalisée\n`/portfolio` - Suivi de portfolio\n`/alerts` - Alertes personnalisées",
            inline=False
        )

        embed.add_field(
            name="👑 Commandes VIP",
            value="• Analyses multi-timeframes\n• Signaux prioritaires\n• Support 24/7\n• Backtesting avancé",
            inline=False
        )

        embed.add_field(
            name="📊 Utilisation des Signaux",
            value="🟢 **BUY** - Signal d'achat détecté\n🔴 **SELL** - Signal de vente détecté\n⏸️ **HOLD** - Attendre une meilleure opportunité",
            inline=False
        )

        embed.add_field(
            name="⚠️ Avertissement",
            value="Les signaux sont informatifs uniquement. Tradez toujours de manière responsable!",
            inline=False
        )

        embed.set_footer(text="Pour passer Premium: /upgrade")

        await interaction.response.send_message(embed=embed)

    async def _create_signal_embed(self, signal: dict, user_tier: str) -> discord.Embed:
        """Création de l'embed pour un signal"""
        action = signal['action']
        color_map = {
            'BUY': discord.Color.green(),
            'SELL': discord.Color.red(),
            'HOLD': discord.Color.yellow()
        }

        action_emoji = {
            'BUY': '🚀',
            'SELL': '📉',
            'HOLD': '⏸️'
        }

        embed = discord.Embed(
            title=f"{action_emoji.get(action, '📊')} Signal {action} - {signal['symbol']}",
            color=color_map.get(action, discord.Color.blue()),
            timestamp=datetime.utcnow()
        )

        # Informations de base (tous niveaux)
        embed.add_field(name="💰 Prix Actuel", value=f"${signal['price']:.4f}", inline=True)
        embed.add_field(name="📊 Confiance", value=f"{signal['confidence']:.1f}%", inline=True)
        embed.add_field(name="⏰ Timeframe", value=signal['timeframe'], inline=True)

        # Informations Premium
        if user_tier in ['premium', 'vip'] and action != 'HOLD':
            if signal.get('take_profit'):
                embed.add_field(name="🎯 Take Profit", value=f"${signal['take_profit']:.4f}", inline=True)
            if signal.get('stop_loss'):
                embed.add_field(name="🛑 Stop Loss", value=f"${signal['stop_loss']:.4f}", inline=True)
            if signal.get('risk_reward'):
                embed.add_field(name="💎 Risk/Reward", value=f"1:{signal['risk_reward']:.2f}", inline=True)

        # Informations VIP
        if user_tier == 'vip':
            indicators = signal.get('indicators', {})
            if indicators.get('rsi'):
                embed.add_field(name="📈 RSI", value=f"{indicators['rsi']:.1f}", inline=True)
            if indicators.get('macd'):
                macd_signal = "🟢" if indicators['macd'] > indicators.get('macd_signal', 0) else "🔴"
                embed.add_field(name="📉 MACD", value=macd_signal, inline=True)

        # Recommandations
        recommendations = signal.get('recommendations', [])[:3]  # Limite à 3
        if recommendations:
            embed.add_field(
                name="💡 Recommandations",
                value='\n'.join(recommendations),
                inline=False
            )

        # Footer selon le niveau
        tier_footer = {
            'free': "Niveau Gratuit - Upgrade pour plus de détails!",
            'premium': "Niveau Premium - Analyses avancées incluses",
            'vip': "Niveau VIP - Accès complet aux analyses"
        }

        embed.set_footer(text=f"Trading Bot Premium © 2025 | {tier_footer.get(user_tier, '')}")

        return embed

    async def _create_analysis_embed(self, symbol: str, analysis_1h: dict, analysis_4h: dict, analysis_1d: dict, user_tier: str) -> discord.Embed:
        """Création de l'embed pour l'analyse complète"""
        embed = discord.Embed(
            title=f"📊 Analyse Technique Complète - {symbol}",
            description="Analyse multi-timeframes détaillée",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        # Analyse par timeframe
        timeframes = [
            ("1H", analysis_1h),
            ("4H", analysis_4h),
            ("1D", analysis_1d)
        ]

        for tf_name, analysis in timeframes:
            if not analysis.get('error'):
                signal = analysis['signal']
                confidence = analysis['confidence']

                signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}

                embed.add_field(
                    name=f"⏰ {tf_name}",
                    value=f"{signal_emoji.get(signal, '🟡')} {signal}\n{confidence:.1f}% confiance",
                    inline=True
                )

        # Indicateurs techniques (VIP uniquement)
        if user_tier == 'vip' and not analysis_1h.get('error'):
            indicators = analysis_1h.get('indicators', {})

            embed.add_field(
                name="📈 Indicateurs Techniques",
                value=f"RSI: {indicators.get('rsi', 0):.1f}\n"
                      f"MACD: {'🟢' if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else '🔴'}\n"
                      f"BB Position: {indicators.get('bb_position', 0.5):.2f}",
                inline=True
            )

        # Patterns détectés
        if not analysis_1h.get('error'):
            patterns = analysis_1h.get('patterns', {})
            bullish = len(patterns.get('bullish_patterns', []))
            bearish = len(patterns.get('bearish_patterns', []))

            pattern_text = f"🟢 Haussiers: {bullish}\n🔴 Baissiers: {bearish}"

            embed.add_field(
                name="🔍 Patterns Détectés",
                value=pattern_text,
                inline=True
            )

        embed.set_footer(text="Analyse Premium - Ne constitue pas un conseil financier")

        return embed

    async def _create_portfolio_embed(self, portfolio: list, user_tier: str) -> discord.Embed:
        """Création de l'embed pour le portfolio"""
        embed = discord.Embed(
            title="📊 Votre Portfolio",
            description="Suivi de vos positions de trading",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        total_value = 0
        total_pnl = 0

        for position in portfolio[:10]:  # Limite à 10 positions
            symbol = position['symbol']
            quantity = position['quantity']
            entry_price = position['entry_price']
            current_price = position['current_price'] or entry_price

            position_value = quantity * current_price
            pnl = (current_price - entry_price) / entry_price * 100
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"

            total_value += position_value
            total_pnl += pnl

            embed.add_field(
                name=f"{symbol}",
                value=f"Qty: {quantity:.4f}\n"
                      f"P&L: {pnl_emoji} {pnl:+.2f}%\n"
                      f"Valeur: ${position_value:.2f}",
                inline=True
            )

        # Résumé global
        avg_pnl = total_pnl / len(portfolio) if portfolio else 0
        pnl_color = "🟢" if avg_pnl >= 0 else "🔴"

        embed.add_field(
            name="💼 Résumé Global",
            value=f"Valeur Totale: ${total_value:.2f}\n"
                  f"P&L Moyen: {pnl_color} {avg_pnl:+.2f}%\n"
                  f"Positions: {len(portfolio)}",
            inline=False
        )

        embed.set_footer(text="Portfolio Premium - Mis à jour en temps réel")

        return embed

async def setup(bot):
    await bot.add_cog(TradingCommands(bot))

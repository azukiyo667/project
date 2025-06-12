import discord
from discord.ext import commands, tasks
import asyncio
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import sqlite3
from src.trading.analyzer import TradingAnalyzer
from src.trading.signal_generator import SignalGenerator
from src.database.db_manager import DatabaseManager
from src.utils.permissions import PermissionManager
from src.trading.portfolio import PortfolioManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()

class TradingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Bot de Trading Crypto Premium - Signaux automatisés et analyses avancées"
        )

        # Initialisation des composants
        self.db_manager = DatabaseManager()
        self.analyzer = TradingAnalyzer()
        self.signal_generator = SignalGenerator()
        self.permission_manager = PermissionManager()
        self.portfolio_manager = PortfolioManager()

        # Configuration des canaux
        self.alert_channel_id = int(os.getenv('ALERT_CHANNEL_ID', 0))
        self.premium_channel_id = int(os.getenv('PREMIUM_CHANNEL_ID', 0))
        self.vip_channel_id = int(os.getenv('VIP_CHANNEL_ID', 0))

    async def on_ready(self):
        logging.info(f'{self.user} est connecté!')
        logging.info(f'Bot connecté à {len(self.guilds)} serveurs')

        # Démarrage des tâches automatiques
        if not self.market_analysis.is_running():
            self.market_analysis.start()
        if not self.portfolio_update.is_running():
            self.portfolio_update.start()
        if not self.daily_report.is_running():
            self.daily_report.start()

        # Synchronisation des commandes slash
        try:
            synced = await self.tree.sync()
            logging.info(f"Synchronisé {len(synced)} commandes slash")
        except Exception as e:
            logging.error(f"Erreur lors de la synchronisation: {e}")

    @tasks.loop(minutes=5)
    async def market_analysis(self):
        """Analyse du marché toutes les 5 minutes"""
        try:
            # Analyse des principales cryptomonnaies
            symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']

            for symbol in symbols:
                analysis = await self.analyzer.analyze_symbol(symbol)

                if analysis['signal'] != 'HOLD':
                    signal = await self.signal_generator.generate_signal(symbol, analysis)
                    await self.send_signal(signal)

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse du marché: {e}")

    @tasks.loop(hours=1)
    async def portfolio_update(self):
        """Mise à jour des portfolios des utilisateurs premium"""
        try:
            premium_users = self.db_manager.get_premium_users()

            for user_id in premium_users:
                portfolio = await self.portfolio_manager.update_portfolio(user_id)
                if portfolio['alerts']:
                    await self.send_portfolio_alert(user_id, portfolio)

        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour des portfolios: {e}")

    @tasks.loop(hours=24)
    async def daily_report(self):
        """Rapport quotidien de performance"""
        try:
            report = await self.analyzer.generate_daily_report()

            # Envoi aux différents niveaux d'abonnement
            await self.send_daily_report(report)

        except Exception as e:
            logging.error(f"Erreur lors de la génération du rapport: {e}")

    async def send_signal(self, signal):
        """Envoi des signaux selon le niveau d'abonnement"""
        try:
            # Signal gratuit (limité)
            if signal['confidence'] >= 85:
                channel = self.get_channel(self.alert_channel_id)
                if channel:
                    embed = self.create_signal_embed(signal, 'basic')
                    await channel.send(embed=embed)

            # Signal premium
            if signal['confidence'] >= 75:
                channel = self.get_channel(self.premium_channel_id)
                if channel:
                    embed = self.create_signal_embed(signal, 'premium')
                    await channel.send(embed=embed)

            # Signal VIP (tous les signaux)
            channel = self.get_channel(self.vip_channel_id)
            if channel:
                embed = self.create_signal_embed(signal, 'vip')
                await channel.send(embed=embed)

        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du signal: {e}")

    def create_signal_embed(self, signal, tier):
        """Création des embeds pour les signaux"""
        color_map = {
            'BUY': discord.Color.green(),
            'SELL': discord.Color.red(),
            'HOLD': discord.Color.yellow()
        }

        embed = discord.Embed(
            title=f"🚀 Signal {signal['action']} - {signal['symbol']}",
            color=color_map.get(signal['action'], discord.Color.blue()),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="💰 Prix", value=f"${signal['price']:.4f}", inline=True)
        embed.add_field(name="📊 Confiance", value=f"{signal['confidence']:.1f}%", inline=True)
        embed.add_field(name="⏰ Timeframe", value=signal['timeframe'], inline=True)

        if tier in ['premium', 'vip']:
            embed.add_field(name="🎯 Take Profit", value=f"${signal['take_profit']:.4f}", inline=True)
            embed.add_field(name="🛑 Stop Loss", value=f"${signal['stop_loss']:.4f}", inline=True)
            embed.add_field(name="💎 Risk/Reward", value=f"1:{signal['risk_reward']:.2f}", inline=True)

        if tier == 'vip':
            embed.add_field(name="📈 RSI", value=f"{signal['indicators']['rsi']:.1f}", inline=True)
            embed.add_field(name="📉 MACD", value=signal['indicators']['macd_signal'], inline=True)
            embed.add_field(name="🔔 Volume", value=f"{signal['volume_change']:+.1f}%", inline=True)

        embed.set_footer(text=f"Trading Bot Premium © 2025 | Tier: {tier.upper()}")

        return embed

    async def send_daily_report(self, report):
        """Envoi du rapport quotidien"""
        try:
            embed = discord.Embed(
                title="📊 Rapport Quotidien de Trading",
                description="Résumé des performances et opportunités du marché",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(name="💹 Performance Globale", value=f"{report['global_performance']:+.2f}%", inline=True)
            embed.add_field(name="🎯 Signaux Envoyés", value=str(report['signals_sent']), inline=True)
            embed.add_field(name="✅ Taux de Réussite", value=f"{report['success_rate']:.1f}%", inline=True)

            embed.add_field(name="🏆 Top Performer", value=f"{report['top_performer']['symbol']}: {report['top_performer']['gain']:+.2f}%", inline=False)

            # Envoi aux canaux appropriés
            for channel_id in [self.alert_channel_id, self.premium_channel_id, self.vip_channel_id]:
                channel = self.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du rapport: {e}")

if __name__ == "__main__":
    bot = TradingBot()

    # Chargement des cogs (extensions)
    async def load_extensions():
        extensions = [
            'src.commands.trading_commands',
            'src.commands.portfolio_commands',
            'src.commands.subscription_commands',
            'src.commands.admin_commands'
        ]

        for extension in extensions:
            try:
                await bot.load_extension(extension)
                logging.info(f"Extension {extension} chargée")
            except Exception as e:
                logging.error(f"Erreur lors du chargement de {extension}: {e}")

    # Démarrage du bot
    async def main():
        async with bot:
            await load_extensions()
            await bot.start(os.getenv('DISCORD_TOKEN'))

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Arrêt du bot...")
    except Exception as e:
        logging.error(f"Erreur critique: {e}")

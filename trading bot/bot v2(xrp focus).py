import ccxt
import pandas as pd
import matplotlib.pyplot as plt

from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# Config de départ
symbol = 'XRP/USDT'
timeframe = '1h'
initial_balance_usdt = 10000
buy_threshold = -0.03  # -3% pour acheter
sell_threshold = 0.05  # +5% pour vendre
trading_fee = 0.001  # 0.1% de frais de trading
stop_loss_percentage = 0.05  # Stop loss à 5%

# Récupère les données de prix depuis Binance
exchange = ccxt.binance()
since = exchange.parse8601('2025-01-01T00:00:00Z')  # Début à 1er janvier 2025
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# MAINTENANT calculer les indicateurs techniques (après avoir créé df)
# Moyennes mobiles
df['sma20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
df['sma50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()

# RSI
df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()

# MACD
macd = MACD(close=df['close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_hist'] = macd.macd_diff()

# Bandes de Bollinger
bollinger = BollingerBands(close=df['close'], window=20)
df['bollinger_upper'] = bollinger.bollinger_hband()
df['bollinger_lower'] = bollinger.bollinger_lband()

# Simule le trading
# Réinitialiser les variables
usdt = initial_balance_usdt
coin = 0
last_buy_price = None
buy_signals = []
sell_signals = []

# Paramètres de la stratégie
rsi_oversold = 30      # Niveau de survente du RSI
rsi_overbought = 70    # Niveau de surachat du RSI
trailing_stop = 0.05   # Stop suiveur (2%)

for i, row in df.iterrows():
    if i < 50:  # Ignorer les premières lignes car les indicateurs ne sont pas calculés
        continue
        
    price = row['close']
    
    # LOGIQUE D'ACHAT
    if usdt > 0:  # Si on a de l'USDT disponible pour acheter
        # Signal de croisement de moyennes mobiles haussier
        golden_cross = df['sma20'].iloc[i-1] <= df['sma50'].iloc[i-1] and df['sma20'].iloc[i] > df['sma50'].iloc[i]
        # RSI en zone de survente
        rsi_buy_signal = row['rsi'] < rsi_oversold
        # Prix touche la bande de Bollinger inférieure
        bollinger_buy = price <= row['bollinger_lower']
        
        # Acheter si au moins deux conditions sont remplies
        if (golden_cross and rsi_buy_signal) or (golden_cross and bollinger_buy) or (rsi_buy_signal and bollinger_buy):
            coin = (usdt * (1 - trading_fee)) / price
            usdt = 0
            last_buy_price = price
            buy_signals.append((row['timestamp'], price))
            print(f"Achat à {price:.2f} USDT - RSI: {row['rsi']:.1f}")
    
    # LOGIQUE DE VENTE
    elif coin > 0:  # Si on a des crypto à vendre
        # Signal de croisement de moyennes mobiles baissier
        death_cross = df['sma20'].iloc[i-1] >= df['sma50'].iloc[i-1] and df['sma20'].iloc[i] < df['sma50'].iloc[i]
        # RSI en zone de surachat
        rsi_sell_signal = row['rsi'] > rsi_overbought
        # Prix touche la bande de Bollinger supérieure
        bollinger_sell = price >= row['bollinger_upper']
        # Stop loss
        stop_loss_triggered = price < last_buy_price * (1 - stop_loss_percentage)
        # Trailing stop
        trailing_stop_price = last_buy_price * (1 + sell_threshold)  # Prix cible initial
        trailing_stop_triggered = price < trailing_stop_price * (1 - trailing_stop) and price > last_buy_price
        
        # Vendre si conditions de vente remplies ou stop loss déclenché
        if (death_cross and rsi_sell_signal) or bollinger_sell or stop_loss_triggered or trailing_stop_triggered:
            usdt = (coin * price) * (1 - trading_fee)
            coin = 0
            sell_signals.append((row['timestamp'], price))
            
            reason = "Conditions techniques"
            if stop_loss_triggered:
                reason = "Stop-loss"
            elif trailing_stop_triggered:
                reason = "Trailing stop"
                
            print(f"Vente à {price:.2f} USDT - Raison: {reason}")

portfolio_value = usdt

# Résultat final
profit = portfolio_value - initial_balance_usdt
profit_percentage = (profit / initial_balance_usdt) * 100

print(f"Balance finale: {portfolio_value:.2f} USDT")
print(f"Profit/Perte: {profit:.2f} USDT ({profit_percentage:.2f}%)")
print(f"Nombre d'opérations: {len(buy_signals)}")

# Calculer les drawdowns
total_value = []
for i, row in df.iterrows():
    if i < 50:
        continue
    if len(buy_signals) > 0 and len(sell_signals) > 0:
        current_value = usdt if coin == 0 else coin * row['close']
        total_value.append(current_value)

if total_value:
    max_drawdown = ((pd.Series(total_value).cummax() - pd.Series(total_value)) / pd.Series(total_value).cummax()).max() * 100
    print(f"Drawdown maximum: {max_drawdown:.2f}%")

# Affiche le graphique
# Améliorer le graphique
plt.figure(figsize=(12, 6))

# Courbe du prix
plt.plot(df['timestamp'], df['close'], label='Prix XRP/USDT', color='blue')

# Indicateurs techniques principaux (facultatif)
plt.plot(df['timestamp'], df['sma20'], label='SMA 20', alpha=0.7, color='orange')
plt.plot(df['timestamp'], df['sma50'], label='SMA 50', alpha=0.7, color='purple')

# Signaux d'achat et de vente
for ts, p in buy_signals:
    plt.plot(ts, p, marker='^', color='green', markersize=10)
for ts, p in sell_signals:
    plt.plot(ts, p, marker='v', color='red', markersize=10)
    
plt.title(f"Stratégie de trading XRP/USDT")
plt.xlabel("Date")
plt.ylabel("Prix (USDT)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# Configuration
symbol = 'XLM/USDT'
timeframe = '1h'
initial_balance_usdt = 10000
buy_threshold = -0.02
sell_threshold = 0.05
trading_fee = 0.001
stop_loss_percentage = 0.05

# Récupération des données historiques
exchange = ccxt.binance()
start_date = exchange.parse8601('2025-01-01T00:00:00Z')
end_date = exchange.parse8601('2025-05-16T00:00:00Z')
all_ohlcv = []
limit = 1000

current_since = start_date
while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=limit)
    if len(ohlcv) == 0:
        break
    all_ohlcv.extend(ohlcv)
    
    current_since = ohlcv[-1][0] + 1
    
    if current_since > end_date or len(all_ohlcv) > 5000:
        break
        
df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Indicateurs techniques
df['sma20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
df['sma50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()

macd = MACD(close=df['close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_hist'] = macd.macd_diff()

bollinger = BollingerBands(close=df['close'], window=20)
df['bollinger_upper'] = bollinger.bollinger_hband()
df['bollinger_lower'] = bollinger.bollinger_lband()

df['price_change_pct'] = df['close'].pct_change().abs() * 100
df['volatility'] = df['price_change_pct'].rolling(14).mean()

# Variables pour la simulation
usdt = initial_balance_usdt
coin = 0
last_buy_price = None
buy_signals = []
sell_signals = []
highest_price_since_buy = 0
portfolio_values = []

# Paramètres stratégiques
rsi_oversold = 29
rsi_overbought = 25
min_profit_for_trailing = 0.03

max_price_missed = []

for i, row in df.iterrows():
    if i < 50:
        continue
        
    price = row['close']
    current_value = usdt + (coin * price)
    portfolio_values.append(current_value)
    
    # Achat
    if usdt > 0:
        golden_cross = df['sma20'].iloc[i-1] <= df['sma50'].iloc[i-1] and df['sma20'].iloc[i] > df['sma50'].iloc[i]
        rsi_buy_signal = row['rsi'] < rsi_oversold
        bollinger_buy = price <= row['bollinger_lower']
        
        if (golden_cross and rsi_buy_signal) or (golden_cross and bollinger_buy) or (rsi_buy_signal and bollinger_buy):
            coin = (usdt * (1 - trading_fee)) / price
            usdt = 0
            last_buy_price = price
            highest_price_since_buy = price
            buy_signals.append((row['timestamp'], price))
            print(f"Achat à {price:.2f} USDT - RSI: {row['rsi']:.1f}")
    
    # Vente
    elif coin > 0:
        if price > highest_price_since_buy:
            highest_price_since_buy = price
            
        death_cross = df['sma20'].iloc[i-1] >= df['sma50'].iloc[i-1] and df['sma20'].iloc[i] < df['sma50'].iloc[i]
        rsi_sell_signal = row['rsi'] > rsi_overbought
        bollinger_sell = price >= row['bollinger_upper']
        stop_loss_triggered = price < last_buy_price * (1 - stop_loss_percentage)
        
        current_profit = (price / last_buy_price) - 1
        
        if current_profit > 0.15:
            trailing_stop = 0.07
        elif current_profit > 0.10:
            trailing_stop = 0.05
        elif current_profit > 0.05:
            trailing_stop = 0.03
        else:
            trailing_stop = 0.03
        
        trailing_stop_triggered = False
        if current_profit > min_profit_for_trailing:
            trailing_stop_triggered = price < highest_price_since_buy * (1 - trailing_stop)
        
        if (death_cross and rsi_sell_signal) or bollinger_sell or stop_loss_triggered or trailing_stop_triggered:
            usdt = (coin * price) * (1 - trading_fee)
            
            max_missed_pct = ((highest_price_since_buy - price) / price) * 100
            max_price_missed.append(max_missed_pct)
            
            coin = 0
            sell_signals.append((row['timestamp'], price))
            
            reason = "Conditions techniques"
            if stop_loss_triggered:
                reason = "Stop-loss"
            elif trailing_stop_triggered:
                reason = "Trailing stop"
            
            profit_pct = ((price - last_buy_price) / last_buy_price) * 100
            highest_pct = ((highest_price_since_buy - last_buy_price) / last_buy_price) * 100
            print(f"Vente à {price:.2f} USDT - Raison: {reason} - Profit: {profit_pct:.1f}% (Max: {highest_pct:.1f}%)")
            
            highest_price_since_buy = 0

# Vente des coins restants à la fin
if coin > 0:
    last_price = df['close'].iloc[-1]
    usdt = (coin * last_price) * (1 - trading_fee)
    
    profit_pct = ((last_price - last_buy_price) / last_buy_price) * 100
    highest_pct = ((highest_price_since_buy - last_buy_price) / last_buy_price) * 100
    
    sell_signals.append((df['timestamp'].iloc[-1], last_price))
    print(f"Vente de fin de simulation à {last_price:.2f} USDT - Profit: {profit_pct:.1f}% (Max: {highest_pct:.1f}%)")

portfolio_value = usdt

# Résultat
profit = portfolio_value - initial_balance_usdt
profit_percentage = (profit / initial_balance_usdt) * 100

print(f"Balance finale: {portfolio_value:.2f} USDT")
print(f"Profit/Perte: {profit:.2f} USDT ({profit_percentage:.2f}%)")
print(f"Nombre d'opérations: {len(buy_signals)}")

if max_price_missed:
    avg_missed = np.mean(max_price_missed)
    print(f"Pourcentage moyen de prix max manqué: {avg_missed:.2f}%")

portfolio_series = pd.Series(portfolio_values)
drawdown = ((portfolio_series.cummax() - portfolio_series) / portfolio_series.cummax()).max() * 100
print(f"Drawdown maximum: {drawdown:.2f}%")

if total_value:
    max_drawdown = ((pd.Series(total_value).cummax() - pd.Series(total_value)) / pd.Series(total_value).cummax()).max() * 100
    print(f"Drawdown maximum: {max_drawdown:.2f}%")

# Graphique
plt.figure(figsize=(14, 8))

plt.plot(df['timestamp'], df['close'], label=f'{symbol}', color='blue', alpha=0.7)
plt.plot(df['timestamp'], df['sma20'], label='SMA 20', alpha=0.7, color='orange')
plt.plot(df['timestamp'], df['sma50'], label='SMA 50', alpha=0.7, color='purple')
plt.plot(df['timestamp'], df['bollinger_upper'], 'r--', alpha=0.3)
plt.plot(df['timestamp'], df['bollinger_lower'], 'g--', alpha=0.3)

for ts, p in buy_signals:
    plt.plot(ts, p, marker='^', color='green', markersize=12)
for ts, p in sell_signals:
    plt.plot(ts, p, marker='v', color='red', markersize=12)
    
plt.title(f"Stratégie de trading optimisée - {symbol}")
plt.xlabel("Date")
plt.ylabel("Prix (USDT)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
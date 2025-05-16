import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

# Config de départ
symbol = 'XRP/USDT'
timeframe = '1h'
initial_balance_usdt = 1000
buy_threshold = -0.03  # -3% pour acheter
sell_threshold = 0.05  # +5% pour vendre
trading_fee = 0.001  # 0.1% de frais de trading
stop_loss_percentage = 0.07  # Stop loss à 5%
max_positions = 3  # NOUVEAU: Nombre maximal de positions simultanées

# Récupère les données de prix depuis Binance
exchange = ccxt.binance()
start_date = exchange.parse8601('2024-01-01T00:00:00Z')
end_date = exchange.parse8601('2025-01-16T00:00:00Z')  # Aujourd'hui
all_ohlcv = []
limit = 1000  # Nombre maximum de bougies par requête

current_since = start_date
while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=limit)
    if len(ohlcv) == 0:
        break
    all_ohlcv.extend(ohlcv)
    
    # Prépare la prochaine itération
    current_since = ohlcv[-1][0] + 1  # Timestamp de la dernière bougie + 1ms
    
    # Si on a atteint la date finale ou suffisamment de données
    if current_since > end_date or len(all_ohlcv) > 5000:
        break
        
df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Calcul des indicateurs techniques
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

atr_indicator = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
df['atr'] = atr_indicator.average_true_range()
df['atr_percent'] = (df['atr'] / df['close']) * 100

# Détection du type de marché
df['price_change_20d'] = df['close'].pct_change(periods=20) * 100
df['market_trend'] = np.where(abs(df['price_change_20d']) > 10, 'trending', 'sideways')

# Indicateur de force du volume
df['volume_sma20'] = df['volume'].rolling(window=20).mean()
df['volume_ratio'] = df['volume'] / df['volume_sma20']

# NOUVELLE STRUCTURE pour gérer plusieurs positions
usdt = initial_balance_usdt
positions = []  # Liste des positions ouvertes
buy_signals = []
sell_signals = []
positions_sizes = []  # Pour le graphique

# Paramètres de la stratégie
rsi_oversold_base = 30
rsi_overbought = 70
trailing_stop_base = 0.07

# Pour suivre le prix maximum atteint pour chaque position
highest_prices = {}

for i, row in df.iterrows():
    if i < 50:  # Ignorer les premières lignes car les indicateurs ne sont pas calculés
        continue
        
    price = row['close']
    
    # D'abord, vérifier si on doit vendre des positions existantes
    for pos_idx in range(len(positions)-1, -1, -1):  # Parcourir de la fin vers le début
        pos = positions[pos_idx]
        
        # Signal de croisement de moyennes mobiles baissier
        death_cross = df['sma20'].iloc[i-1] >= df['sma50'].iloc[i-1] and df['sma20'].iloc[i] < df['sma50'].iloc[i]
        # RSI en zone de surachat
        rsi_sell_signal = row['rsi'] > rsi_overbought
        # Prix touche la bande de Bollinger supérieure
        bollinger_sell = price >= row['bollinger_upper']
        
        # Stop loss dynamique
        atr_stop = pos['buy_price'] - (row['atr'] * 2.0)
        fixed_stop = pos['buy_price'] * (1 - stop_loss_percentage)
        stop_price = max(atr_stop, fixed_stop)
        stop_loss_triggered = price < stop_price
        
        # Trailing stop adaptatif
        if str(row['market_trend']) == 'trending':
            trailing_stop = 0.08
            if price > pos['buy_price'] * 1.05:
                trailing_stop = 0.05
            elif price > pos['buy_price'] * 1.10:
                trailing_stop = 0.03
        else:  # Marché latéral
            trailing_stop = 0.05
            if price > pos['buy_price'] * 1.03:
                trailing_stop = 0.03
            elif price > pos['buy_price'] * 1.05:
                trailing_stop = 0.02
                
        # Mise à jour du prix le plus haut
        pos_id = pos['id']
        if pos_id not in highest_prices:
            highest_prices[pos_id] = pos['buy_price']
        elif price > highest_prices[pos_id]:
            highest_prices[pos_id] = price
            
        # Trailing stop uniquement si profit minimal
        trailing_stop_triggered = False
        min_profit_for_trailing = 0.03 if str(row['market_trend']) == 'trending' else 0.02
        
        if price > pos['buy_price'] * (1 + min_profit_for_trailing):
            trailing_stop_triggered = price < (highest_prices[pos_id] * (1 - trailing_stop))
            
        # Vendre si conditions remplies
        if (death_cross and rsi_sell_signal) or bollinger_sell or stop_loss_triggered or trailing_stop_triggered:
            profit = (price - pos['buy_price']) / pos['buy_price'] * 100
            usdt += (pos['amount'] * price) * (1 - trading_fee)
            
            reason = "Conditions techniques"
            if stop_loss_triggered:
                reason = "Stop-loss"
            elif trailing_stop_triggered:
                reason = "Trailing stop"
                
            sell_signals.append((row['timestamp'], price))
            print(f"Vente à {price:.2f} USDT - Raison: {reason} - Profit: {profit:.2f}%")
            
            # Supprimer la position vendue
            del positions[pos_idx]
    
    # Ensuite, vérifier si on peut acheter de nouvelles positions
    if usdt > 0 and len(positions) < max_positions:  # Vérifier nombre max de positions
        # Adapter le RSI selon le marché
        current_rsi_oversold = rsi_oversold_base
        if str(row['market_trend']) == 'sideways':
            current_rsi_oversold = 25
        
        # Signal de croisement de moyennes mobiles haussier
        golden_cross = df['sma20'].iloc[i-1] <= df['sma50'].iloc[i-1] and df['sma20'].iloc[i] > df['sma50'].iloc[i]
        # RSI en zone de survente
        rsi_buy_signal = row['rsi'] < current_rsi_oversold
        # Prix touche la bande de Bollinger inférieure
        bollinger_buy = price <= row['bollinger_lower']
        
        # NOUVEAUX FILTRES
        volume_filter = row['volume_ratio'] > 1.2
        macd_improving = row['macd_hist'] > df['macd_hist'].iloc[i-1]
        volatility_ok = row['atr_percent'] > 1.0
        
        # Acheter si conditions remplies
        main_conditions = (golden_cross and rsi_buy_signal) or (golden_cross and bollinger_buy) or (rsi_buy_signal and bollinger_buy)
        filter_conditions = volume_filter or macd_improving or volatility_ok
        
        if main_conditions and filter_conditions:
            # Déterminer taille de position selon contexte
            position_size = 0.3  # Position de base réduite à 30% pour permettre plusieurs positions
            
            # Augmenter sur signal fort
            if row['rsi'] < 20:
                position_size = min(position_size + 0.1, 0.5)  # Max 50% par position
                
            # Ajuster selon marché
            if str(row['market_trend']) == 'sideways':
                position_size *= 0.5
            
            # Montant à investir et tokens achetés
            amount_to_invest = min(usdt * position_size, usdt)  # Ne pas dépasser le solde
            coin_amount = (amount_to_invest * (1 - trading_fee)) / price
            
            # Créer la position
            new_position = {
                'id': len(buy_signals),  # Identifiant unique
                'buy_price': price,
                'amount': coin_amount,
                'timestamp': row['timestamp'],
                'buy_index': i
            }
            
            positions.append(new_position)
            usdt -= amount_to_invest
            buy_signals.append((row['timestamp'], price))
            positions_sizes.append(position_size * 100)
            
            print(f"Achat à {price:.2f} USDT - RSI: {row['rsi']:.1f} - Position: {position_size*100:.0f}%")

# Vendre les positions restantes à la fin de la simulation
for pos in positions:
    last_price = df['close'].iloc[-1]
    usdt += (pos['amount'] * last_price) * (1 - trading_fee)
    sell_signals.append((df['timestamp'].iloc[-1], last_price))
    print(f"Vente de fin de simulation à {last_price:.2f} USDT")

# Résultats finaux
profit = usdt - initial_balance_usdt
profit_percentage = (profit / initial_balance_usdt) * 100

# Calcul des métriques avancées
if len(buy_signals) > 0 and len(sell_signals) > 0:
    win_trades = 0
    gains = []
    losses = []
    
    for i in range(min(len(buy_signals), len(sell_signals))):
        buy_price = buy_signals[i][1]
        sell_price = sell_signals[i][1]
        trade_return = (sell_price - buy_price) / buy_price
        
        if sell_price > buy_price:
            win_trades += 1
            gains.append(trade_return)
        else:
            losses.append(abs(trade_return))
    
    win_rate = (win_trades / len(buy_signals)) * 100 if len(buy_signals) > 0 else 0
    
    # Profit factor et expectancy
    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
    profit_factor = (avg_gain * win_trades) / (avg_loss * (len(buy_signals) - win_trades)) if avg_loss > 0 and len(buy_signals) > win_trades else 0
    expectancy = (win_rate/100 * avg_gain) - ((100-win_rate)/100 * avg_loss)

print(f"Balance finale: {usdt:.2f} USDT")
print(f"Profit/Perte: {profit:.2f} USDT ({profit_percentage:.2f}%)")
print(f"Nombre d'opérations: {len(buy_signals)}")

if len(buy_signals) > 0:
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Profit factor: {profit_factor:.2f}")
    print(f"Expectancy: {expectancy*100:.2f}%")

# Affichage simplifié: un seul graphique
plt.figure(figsize=(14, 7))
plt.plot(df['timestamp'], df['close'], label=symbol, color='blue')
plt.plot(df['timestamp'], df['sma20'], label='SMA 20', alpha=0.7, color='orange')
plt.plot(df['timestamp'], df['sma50'], label='SMA 50', alpha=0.7, color='purple')
plt.plot(df['timestamp'], df['bollinger_upper'], 'r--', alpha=0.3)
plt.plot(df['timestamp'], df['bollinger_lower'], 'r--', alpha=0.3)

# Signaux d'achat et de vente
for i, (ts, p) in enumerate(buy_signals):
    if i < len(positions_sizes):
        size = positions_sizes[i]/20 + 6  # Taille du marker selon la position
        plt.plot(ts, p, marker='^', color='green', markersize=size)
    else:
        plt.plot(ts, p, marker='^', color='green', markersize=10)
        
for ts, p in sell_signals:
    plt.plot(ts, p, marker='v', color='red', markersize=10)

plt.title(f"Stratégie de trading - {symbol}")
plt.ylabel("Prix (USDT)")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
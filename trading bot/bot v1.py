import ccxt
import pandas as pd
import matplotlib.pyplot as plt

# Config de départ
symbol = 'XRP/USDT'
timeframe = '1h'
initial_balance_usdt = 10000
buy_threshold = -0.03  # -1% pour acheter
sell_threshold = 0.05  # +1% pour vendre

# Récupère les données de prix depuis Binance
exchange = ccxt.binance()
since = exchange.parse8601('2025-01-01T00:00:00Z')  # Début à 1er janvier 2024
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Simule le trading
usdt = initial_balance_usdt
btc = 0
last_price = df['close'][0]
last_buy_price = None

trading_fee = 0.001
stop_loss_percentage = 0.05

buy_signals = []
sell_signals = []

for i, row in df.iterrows():
	price = row['close']
	change = (price - last_price) / last_price

	if btc == 0 and change <= buy_threshold:
		# Achat
		btc = (usdt * (1 - trading_fee)) / price
		usdt = 0
		last_buy_price = price
		buy_signals.append((row['timestamp'], price))
		print(f"Achat à {price:.2f} USDT")

	elif btc > 0 and (price - last_buy_price) / last_buy_price >= sell_threshold:
		# Vente
		usdt = (btc * price) * (1 - trading_fee)
		btc = 0
		sell_signals.append((row['timestamp'], price))
		print(f"Vente à {price:.2f} USDT")

	if btc > 0 and (last_buy_price - price) / last_buy_price >= stop_loss_percentage:
		# Vente (stop-loss)
		usdt = (btc * price) * (1 - trading_fee)
		btc = 0
		sell_signals.append((row['timestamp'], price))
		print(f"Stop-loss déclenché: Vente à {price:.2f} USDT")

	last_price = price

# Résultat final
portfolio_value = usdt if btc == 0 else btc * df['close'].iloc[-1]
print(f"\nBalance finale : {portfolio_value:.2f} USDT")

# Affiche le graphique
plt.figure(figsize=(14, 6))
plt.plot(df['timestamp'], df['close'], label='Prix BTC')

for ts, p in buy_signals:
	plt.plot(ts, p, marker='^', color='green', markersize=10)
for ts, p in sell_signals:
	plt.plot(ts, p, marker='v', color='red', markersize=10)

plt.title("Stratégie simple BTC/USDT")
plt.xlabel("Date")
plt.ylabel("Prix (USDT)")
plt.legend()
plt.grid()
plt.show()

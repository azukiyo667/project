import ccxt
import pandas as pd
from trading_env import TradingEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import matplotlib.pyplot as plt
import csv
import ta
import time
import datetime

def fetch_all_ohlcv(exchange, symbol, timeframe, since=None, until=None, total_limit=5000):
    all_ohlcv = []
    left = total_limit
    current_since = since
    while left > 0:
        limit = min(1000, left)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=current_since, limit=limit)
        if not ohlcv:
            break
        # Si until est défini, on ne garde que les bougies avant until
        if until is not None:
            ohlcv = [row for row in ohlcv if row[0] < until]
            if not ohlcv:
                break
        all_ohlcv += ohlcv
        left -= len(ohlcv)
        if len(ohlcv) < limit:
            break
        current_since = ohlcv[-1][0] + 1  # +1ms pour éviter doublon
        time.sleep(0.2)
    return all_ohlcv

# Exemple : récupérer du 1er janvier 2024 au 1er avril 2024
start_date = "2025-01-01"
end_date = "2025-04-01"
since = int(pd.Timestamp(start_date).timestamp() * 1000)
until = int(pd.Timestamp(end_date).timestamp() * 1000)

# 📡 Récupérer les données de Binance
exchange = ccxt.binance()
ohlcv = fetch_all_ohlcv(exchange, 'XRP/USDT', '1h', since=since, until=until, total_limit=5000)

df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Date'] = pd.to_datetime(df['Timestamp'], unit='ms')
df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
df['SMA_10'] = df['Close'].rolling(10).mean()
df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
df['EMA_20'] = df['Close'].ewm(span=20).mean()
df['MACD'] = ta.trend.MACD(df['Close']).macd()
df['BB_UPPER'] = ta.volatility.BollingerBands(df['Close']).bollinger_hband()
df['BB_LOWER'] = ta.volatility.BollingerBands(df['Close']).bollinger_lband()
df['VOLUME_NORM'] = df['Volume'] / df['Volume'].rolling(20).mean()  # volume normalisé
df['RETURNS'] = df['Close'].pct_change().fillna(0)  # returns instantanés
df['VOLATILITY'] = df['Close'].rolling(20).std() / df['Close'].rolling(20).mean()  # volatilité relative
df['DIST_HIGH'] = (df['Close'] - df['High'].rolling(20).max()) / df['High'].rolling(20).max()
df['DIST_LOW'] = (df['Close'] - df['Low'].rolling(20).min()) / df['Low'].rolling(20).min()
df = df.dropna().reset_index(drop=True)

split_idx = int(len(df) * 0.8)
df_train = df.iloc[:split_idx].reset_index(drop=True)
df_test = df.iloc[split_idx:].reset_index(drop=True)

# 🧱 Environnement
env = DummyVecEnv([lambda: TradingEnv(df_test)])

# 📦 Charger le modèle
model = PPO.load("ppo_trading_bot", device="cpu")

# 🔁 Tester le bot et collecter les données
obs = env.reset()
done = False

dates = []
prices = []
balances = []
actions = []
rewards = []
prev_position = 0
total_reward = 0
buy_signals = []
sell_signals = []

while not done:
    action, _ = model.predict(obs)
    obs, reward, done, info = env.step(action)
    total_reward += reward
    state = env.envs[0]
    idx = state.current_step
    dates.append(df['Date'].iloc[idx-1])
    prices.append(df['Close'].iloc[idx-1])
    balances.append(state.balance)
    actions.append(action[0])
    rewards.append(reward)

    if prev_position == 0 and state.position == 1:
        buy_signals.append(len(dates)-1)
    if prev_position == 1 and state.position == 0:
        sell_signals.append(len(dates)-1)
    prev_position = state.position

print(f"Total Reward: {total_reward}")

with open("resultats_bot.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Date", "Prix", "Balance", "Action", "Reward"])
    for i in range(len(dates)):
        writer.writerow([
            dates[i],
            prices[i],
            balances[i],
            actions[i],
            rewards[i]
        ])

# Affichage graphique
plt.figure(figsize=(14, 10))

# 1. Prix + signaux
plt.subplot(4, 1, 1)
plt.plot(dates, prices, label='Prix')
# plt.plot(dates, [df['SMA_10'].iloc[i] for i in range(len(dates))], label='SMA 10', linestyle='--')
# plt.plot(dates, [df['EMA_20'].iloc[i] for i in range(len(dates))], label='EMA 20', linestyle='-.')
# plt.plot(dates, [df['BB_UPPER'].iloc[i] for i in range(len(dates))], label='Bollinger Upper', color='grey', alpha=0.5)
# plt.plot(dates, [df['BB_LOWER'].iloc[i] for i in range(len(dates))], label='Bollinger Lower', color='grey', alpha=0.5)
plt.scatter([dates[i] for i in buy_signals], [prices[i] for i in buy_signals], marker='^', color='g', label='Achat', s=80)
plt.scatter([dates[i] for i in sell_signals], [prices[i] for i in sell_signals], marker='v', color='r', label='Vente', s=80)
plt.legend()
plt.title('Prix XRP/USDT et indicateurs')

# 2. Balance
plt.subplot(3, 1, 2)
plt.plot(dates, balances, label='Balance', color='orange')
plt.legend()
plt.title('Évolution du solde')

# 3. Rewards
plt.subplot(3, 1, 3)
plt.plot(dates, rewards, label='Reward', color='purple')
plt.axhline(y=0, color='grey', linestyle='--', alpha=0.5)
plt.legend()
plt.title('Récompense à chaque étape')

plt.tight_layout()
plt.show()
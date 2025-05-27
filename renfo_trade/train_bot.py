import ccxt
import pandas as pd
from trading_env import TradingEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
import ta
import time

N_ENVS = 11  # Choisis selon ton CPU

# 🔌 Connecter à Binance et préparer les données AVANT make_env
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
end_date = "2025-05-27"
since = int(pd.Timestamp(start_date).timestamp() * 1000)
until = int(pd.Timestamp(end_date).timestamp() * 1000)

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
df['VOLUME_NORM'] = df['Volume'] / df['Volume'].rolling(20).mean()
df['RETURNS'] = df['Close'].pct_change().fillna(0)
df['VOLATILITY'] = df['Close'].rolling(20).std() / df['Close'].rolling(20).mean()
df['DIST_HIGH'] = (df['Close'] - df['High'].rolling(20).max()) / df['High'].rolling(20).max()
df['DIST_LOW'] = (df['Close'] - df['Low'].rolling(20).min()) / df['Low'].rolling(20).min()
df = df.dropna().reset_index(drop=True)

split_idx = int(len(df) * 0.8)
df_train = df.iloc[:split_idx].reset_index(drop=True)
df_test = df.iloc[split_idx:].reset_index(drop=True)

def make_env():
    return TradingEnv(df_train)

if __name__ == "__main__":

    env = SubprocVecEnv([make_env for _ in range(N_ENVS)])

    model = PPO("MlpPolicy", env, verbose=1, device="cpu", n_steps=2048)
    model.learn(total_timesteps=600000)
    model.save("ppo_trading_bot")
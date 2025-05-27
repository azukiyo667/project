import ccxt
import pandas as pd
from trading_env import TradingEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
import ta

N_ENVS = 6  # Choisis selon ton CPU

# 🔌 Connecter à Binance et préparer les données AVANT make_env
exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('XRP/USDT', timeframe='1h', limit=1000)
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

def make_env():
    return TradingEnv(df)

if __name__ == "__main__":

    env = SubprocVecEnv([make_env for _ in range(N_ENVS)])

    model = PPO("MlpPolicy", env, verbose=1, device="cpu")
    model.learn(total_timesteps=500000)
    model.save("ppo_trading_bot")
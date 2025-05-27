# trading_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class TradingEnv(gym.Env):
    def __init__(self, df, window_size=50, initial_balance=1000):
        super(TradingEnv, self).__init__()

        self.df = df.reset_index()
        self.window_size = window_size
        self.initial_balance = initial_balance
        self.action_space = spaces.Discrete(3)
        self.hold_steps = 0

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(window_size * 12 + 2,), dtype=np.float32)

    def _get_observation(self):
        window = self.df.iloc[self.current_step - self.window_size:self.current_step]
        obs = np.concatenate([
            (window['Close'] / window['Close'].iloc[0] - 1).values,
            window['SMA_10'].values / window['Close'].values,
            window['RSI'].values / 100,
            window['EMA_20'].values / window['Close'].values,
            window['MACD'].values / window['Close'].values,
            window['BB_UPPER'].values / window['Close'].values,
            window['BB_LOWER'].values / window['Close'].values,
            window['VOLUME_NORM'].values,
            window['RETURNS'].values,
            window['VOLATILITY'].values,
            window['DIST_HIGH'].values,
            window['DIST_LOW'].values,
            [self.position],
            [self.balance / self.initial_balance - 1]
        ])
        return obs.astype(np.float32)

    def reset(self, *, seed=None, options=None):
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        self.current_step = self.window_size
        self.max_balance = self.initial_balance
        self.hold_steps = 0
        return self._get_observation(), {}

    def step(self, action):
        done = False
        reward = 0
        truncated = False
        info = {}
        old_balance = self.balance
        fee = 0.001
        price = self.df['Close'].iloc[self.current_step]

        if self.position == 1:
            self.hold_steps += 1
        else:
            self.hold_steps = 0

        if action == 1:  # Buy
            if self.position == 0:
                self.position = 1
                self.entry_price = price
                self.qty = self.balance / price
            else:
                reward = -0.1

        elif action == 2:  # Sell
            if self.position == 1:
                raw_reward = (price - self.entry_price) * self.qty - price * fee * self.qty
                reward = raw_reward / (self.entry_price * self.qty) * 100
                reward += 0.01 * self.hold_steps
                self.balance += raw_reward
                self.position = 0
                self.qty = 0
            else:
                reward = -0.1

        reward = (self.balance - old_balance) / self.initial_balance

        if action in [1, 2]:
            reward -= 0.005

        if self.balance > self.max_balance:
            reward += 0.1
            self.max_balance = self.balance

        self.current_step += 1
        if self.current_step >= len(self.df):
            done = True

        obs = self._get_observation()
        return obs, reward, done, truncated, info


    def render(self, mode='human'):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Position: {self.position}")

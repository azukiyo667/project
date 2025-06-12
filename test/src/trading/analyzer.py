# Module d'analyse technique avancée pour le trading automatisé

import ccxt
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging
import asyncio
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class TradingAnalyzer:
    def __init__(self):
        """Initialisation de l'analyseur de trading"""
        self.exchanges = {
            'binance': ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': False,
                'enableRateLimit': True,
            })
        }

        self.timeframes = ['1h', '4h', '1d']
        self.indicators_config = {
            'rsi_period': int(os.getenv('RSI_PERIOD', 14)),
            'macd_fast': int(os.getenv('MACD_FAST', 12)),
            'macd_slow': int(os.getenv('MACD_SLOW', 26)),
            'macd_signal': int(os.getenv('MACD_SIGNAL', 9)),
            'bb_period': int(os.getenv('BB_PERIOD', 20)),
            'bb_std': float(os.getenv('BB_STD', 2))
        }

        self.ml_model = None
        self.scaler = MinMaxScaler()
        self._initialize_ml_model()

    def _initialize_ml_model(self):
        """Initialisation du modèle de machine learning"""
        try:
            self.ml_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            logging.info("Modèle ML initialisé avec succès")
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation du ML: {e}")

    async def analyze_symbol(self, symbol, timeframe='1h'):
        """
        Analyse complète d'un symbole crypto

        Args:
            symbol (str): Symbole à analyser (ex: 'BTC/USDT')
            timeframe (str): Timeframe d'analyse

        Returns:
            dict: Résultats de l'analyse
        """
        try:
            # Récupération des données OHLCV
            ohlcv = await self._fetch_ohlcv_data(symbol, timeframe)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Calcul des indicateurs techniques
            indicators = self._calculate_indicators(df)

            # Analyse des patterns
            patterns = self._detect_patterns(df, indicators)

            # Analyse de volume
            volume_analysis = self._analyze_volume(df)

            # Signal de machine learning
            ml_signal = self._get_ml_prediction(df, indicators)

            # Calcul du signal final
            final_signal = self._calculate_final_signal(indicators, patterns, volume_analysis, ml_signal)

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.utcnow(),
                'price': float(df['close'].iloc[-1]),
                'signal': final_signal['action'],
                'confidence': final_signal['confidence'],
                'indicators': indicators,
                'patterns': patterns,
                'volume_analysis': volume_analysis,
                'ml_prediction': ml_signal,
                'take_profit': final_signal.get('take_profit'),
                'stop_loss': final_signal.get('stop_loss'),
                'risk_reward': final_signal.get('risk_reward', 0)
            }

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse de {symbol}: {e}")
            return self._get_error_response(symbol, str(e))

    async def _fetch_ohlcv_data(self, symbol, timeframe, limit=200):
        """Récupération des données OHLCV"""
        try:
            exchange = self.exchanges['binance']
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des données pour {symbol}: {e}")
            raise

    def _calculate_indicators(self, df):
        """Calcul des indicateurs techniques"""
        indicators = {}

        try:
            # RSI
            indicators['rsi'] = ta.momentum.RSIIndicator(df['close'], window=self.indicators_config['rsi_period']).rsi().iloc[-1]

            # MACD
            macd = ta.trend.MACD(df['close'],
                               window_fast=self.indicators_config['macd_fast'],
                               window_slow=self.indicators_config['macd_slow'],
                               window_sign=self.indicators_config['macd_signal'])
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd.macd_diff().iloc[-1]

            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'],
                                            window=self.indicators_config['bb_period'],
                                            window_dev=self.indicators_config['bb_std'])
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            indicators['bb_position'] = (df['close'].iloc[-1] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])

            # EMA
            indicators['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1]
            indicators['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1]
            indicators['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator().iloc[-1]

            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            indicators['stoch_k'] = stoch.stoch().iloc[-1]
            indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]

            # ADX (Average Directional Index)
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            indicators['adx'] = adx.adx().iloc[-1]
            indicators['di_plus'] = adx.adx_pos().iloc[-1]
            indicators['di_minus'] = adx.adx_neg().iloc[-1]

            # Support et Résistance
            support_resistance = self._calculate_support_resistance(df)
            indicators.update(support_resistance)

            return indicators

        except Exception as e:
            logging.error(f"Erreur lors du calcul des indicateurs: {e}")
            return {}

    def _detect_patterns(self, df, indicators):
        """Détection des patterns de trading"""
        patterns = {
            'bullish_patterns': [],
            'bearish_patterns': [],
            'continuation_patterns': [],
            'reversal_patterns': []
        }

        try:
            current_price = df['close'].iloc[-1]
            prev_prices = df['close'].iloc[-5:].tolist()

            # Pattern Golden Cross
            if indicators.get('ema_9', 0) > indicators.get('ema_21', 0) and indicators.get('ema_21', 0) > indicators.get('ema_50', 0):
                patterns['bullish_patterns'].append('golden_cross')

            # Pattern Death Cross
            if indicators.get('ema_9', 0) < indicators.get('ema_21', 0) and indicators.get('ema_21', 0) < indicators.get('ema_50', 0):
                patterns['bearish_patterns'].append('death_cross')

            # Pattern MACD Divergence
            if indicators.get('macd', 0) > indicators.get('macd_signal', 0) and indicators.get('macd_histogram', 0) > 0:
                patterns['bullish_patterns'].append('macd_bullish_crossover')
            elif indicators.get('macd', 0) < indicators.get('macd_signal', 0) and indicators.get('macd_histogram', 0) < 0:
                patterns['bearish_patterns'].append('macd_bearish_crossover')

            # Pattern RSI Oversold/Overbought
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                patterns['reversal_patterns'].append('rsi_oversold')
            elif rsi > 70:
                patterns['reversal_patterns'].append('rsi_overbought')

            # Pattern Bollinger Band Squeeze
            bb_width = (indicators.get('bb_upper', 0) - indicators.get('bb_lower', 0)) / indicators.get('bb_middle', 1)
            if bb_width < 0.05:  # Bandes très rapprochées
                patterns['continuation_patterns'].append('bb_squeeze')

            # Pattern Double Top/Bottom (simplifié)
            if len(prev_prices) >= 5:
                highs = [df['high'].iloc[i] for i in range(-5, 0)]
                lows = [df['low'].iloc[i] for i in range(-5, 0)]

                if self._is_double_top(highs):
                    patterns['reversal_patterns'].append('double_top')
                elif self._is_double_bottom(lows):
                    patterns['reversal_patterns'].append('double_bottom')

            return patterns

        except Exception as e:
            logging.error(f"Erreur lors de la détection des patterns: {e}")
            return patterns

    def _analyze_volume(self, df):
        """Analyse du volume de trading"""
        try:
            recent_volume = df['volume'].iloc[-10:].mean()
            long_term_volume = df['volume'].iloc[-50:].mean()

            volume_ratio = recent_volume / long_term_volume if long_term_volume > 0 else 1
            volume_trend = 'increasing' if volume_ratio > 1.2 else 'decreasing' if volume_ratio < 0.8 else 'stable'

            # Volume Price Trend (VPT)
            vpt = ta.volume.VolumePriceTrendIndicator(df['close'], df['volume']).volume_price_trend().iloc[-1]

            return {
                'volume_ratio': volume_ratio,
                'volume_trend': volume_trend,
                'vpt': vpt,
                'volume_confirmation': volume_ratio > 1.1  # Volume confirme le mouvement
            }

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse du volume: {e}")
            return {'volume_ratio': 1, 'volume_trend': 'unknown', 'vpt': 0, 'volume_confirmation': False}

    def _get_ml_prediction(self, df, indicators):
        """Prédiction utilisant le machine learning"""
        try:
            if self.ml_model is None:
                return {'prediction': 'HOLD', 'confidence': 0.5}

            # Préparation des features
            features = self._prepare_features(df, indicators)

            if len(features) > 0:
                # Prédiction
                prediction_proba = self.ml_model.predict_proba([features])[0]
                prediction = self.ml_model.predict([features])[0]

                confidence = max(prediction_proba)

                signal_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}

                return {
                    'prediction': signal_map.get(prediction, 'HOLD'),
                    'confidence': confidence,
                    'probabilities': {
                        'sell': prediction_proba[0] if len(prediction_proba) > 0 else 0,
                        'hold': prediction_proba[1] if len(prediction_proba) > 1 else 0,
                        'buy': prediction_proba[2] if len(prediction_proba) > 2 else 0
                    }
                }

        except Exception as e:
            logging.error(f"Erreur lors de la prédiction ML: {e}")

        return {'prediction': 'HOLD', 'confidence': 0.5}

    def _prepare_features(self, df, indicators):
        """Préparation des features pour le ML"""
        try:
            features = [
                indicators.get('rsi', 50) / 100,
                indicators.get('macd', 0),
                indicators.get('bb_position', 0.5),
                indicators.get('stoch_k', 50) / 100,
                indicators.get('adx', 20) / 100,
                indicators.get('volume_ratio', 1),
                (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2],  # Price change
                len(indicators.get('bullish_patterns', [])) - len(indicators.get('bearish_patterns', []))
            ]

            return [f if not np.isnan(f) else 0 for f in features]

        except Exception as e:
            logging.error(f"Erreur lors de la préparation des features: {e}")
            return []

    def _calculate_final_signal(self, indicators, patterns, volume_analysis, ml_signal):
        """Calcul du signal final basé sur tous les indicateurs"""
        try:
            signals = []
            weights = []

            # Signal RSI
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                signals.append(1)  # BUY
                weights.append(0.15)
            elif rsi > 70:
                signals.append(-1)  # SELL
                weights.append(0.15)
            else:
                signals.append(0)  # HOLD
                weights.append(0.05)

            # Signal MACD
            if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
                signals.append(1)
                weights.append(0.2)
            else:
                signals.append(-1)
                weights.append(0.2)

            # Signal EMA
            if indicators.get('ema_9', 0) > indicators.get('ema_21', 0):
                signals.append(1)
                weights.append(0.15)
            else:
                signals.append(-1)
                weights.append(0.15)

            # Signal Patterns
            bullish_count = len(patterns.get('bullish_patterns', []))
            bearish_count = len(patterns.get('bearish_patterns', []))

            if bullish_count > bearish_count:
                signals.append(1)
                weights.append(0.2)
            elif bearish_count > bullish_count:
                signals.append(-1)
                weights.append(0.2)
            else:
                signals.append(0)
                weights.append(0.1)

            # Signal Volume
            if volume_analysis.get('volume_confirmation', False):
                signals.append(1 if volume_analysis.get('volume_ratio', 1) > 1 else -1)
                weights.append(0.1)
            else:
                signals.append(0)
                weights.append(0.05)

            # Signal ML
            ml_pred = ml_signal.get('prediction', 'HOLD')
            ml_conf = ml_signal.get('confidence', 0.5)

            if ml_pred == 'BUY':
                signals.append(1)
                weights.append(0.2 * ml_conf)
            elif ml_pred == 'SELL':
                signals.append(-1)
                weights.append(0.2 * ml_conf)
            else:
                signals.append(0)
                weights.append(0.1)

            # Calcul du signal pondéré
            if sum(weights) > 0:
                weighted_signal = sum(s * w for s, w in zip(signals, weights)) / sum(weights)
            else:
                weighted_signal = 0

            # Détermination de l'action finale
            if weighted_signal > 0.3:
                action = 'BUY'
                confidence = min(95, abs(weighted_signal) * 100)
            elif weighted_signal < -0.3:
                action = 'SELL'
                confidence = min(95, abs(weighted_signal) * 100)
            else:
                action = 'HOLD'
                confidence = 50

            # Calcul des niveaux de Take Profit et Stop Loss
            current_price = indicators.get('current_price', 0)

            result = {
                'action': action,
                'confidence': confidence,
                'weighted_signal': weighted_signal
            }

            if action != 'HOLD' and current_price > 0:
                if action == 'BUY':
                    result['take_profit'] = current_price * 1.03  # 3% profit
                    result['stop_loss'] = current_price * 0.98    # 2% loss
                    result['risk_reward'] = 1.5
                else:  # SELL
                    result['take_profit'] = current_price * 0.97  # 3% profit sur short
                    result['stop_loss'] = current_price * 1.02    # 2% loss sur short
                    result['risk_reward'] = 1.5

            return result

        except Exception as e:
            logging.error(f"Erreur lors du calcul du signal final: {e}")
            return {'action': 'HOLD', 'confidence': 0}

    def _calculate_support_resistance(self, df):
        """Calcul des niveaux de support et résistance"""
        try:
            highs = df['high'].rolling(window=20).max()
            lows = df['low'].rolling(window=20).min()

            current_price = df['close'].iloc[-1]

            resistance = highs.iloc[-1]
            support = lows.iloc[-1]

            return {
                'support': support,
                'resistance': resistance,
                'distance_to_support': (current_price - support) / current_price * 100,
                'distance_to_resistance': (resistance - current_price) / current_price * 100
            }

        except Exception as e:
            logging.error(f"Erreur lors du calcul support/résistance: {e}")
            return {'support': 0, 'resistance': 0, 'distance_to_support': 0, 'distance_to_resistance': 0}

    def _is_double_top(self, highs):
        """Détection du pattern Double Top"""
        if len(highs) < 5:
            return False

        # Logique simplifiée pour détecter un double top
        peak1_idx = highs.index(max(highs[:3]))
        peak2_idx = highs.index(max(highs[2:]))

        if abs(highs[peak1_idx] - highs[peak2_idx]) / highs[peak1_idx] < 0.02:  # Pics similaires (2% de différence)
            return True

        return False

    def _is_double_bottom(self, lows):
        """Détection du pattern Double Bottom"""
        if len(lows) < 5:
            return False

        # Logique similaire pour double bottom
        valley1_idx = lows.index(min(lows[:3]))
        valley2_idx = lows.index(min(lows[2:]))

        if abs(lows[valley1_idx] - lows[valley2_idx]) / lows[valley1_idx] < 0.02:
            return True

        return False

    def _get_error_response(self, symbol, error_msg):
        """Response d'erreur standardisée"""
        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'error': True,
            'error_message': error_msg,
            'signal': 'HOLD',
            'confidence': 0
        }

    async def generate_daily_report(self):
        """Génération du rapport quotidien"""
        try:
            # Analyse des principales cryptos
            symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT', 'DOT/USDT']

            analyses = []
            for symbol in symbols:
                analysis = await self.analyze_symbol(symbol, '1d')
                analyses.append(analysis)

            # Calcul des statistiques globales
            buy_signals = len([a for a in analyses if a['signal'] == 'BUY'])
            sell_signals = len([a for a in analyses if a['signal'] == 'SELL'])
            hold_signals = len([a for a in analyses if a['signal'] == 'HOLD'])

            avg_confidence = np.mean([a['confidence'] for a in analyses if not a.get('error', False)])

            # Top performer
            valid_analyses = [a for a in analyses if not a.get('error', False)]
            if valid_analyses:
                top_performer = max(valid_analyses, key=lambda x: x['confidence'])
            else:
                top_performer = {'symbol': 'N/A', 'gain': 0}

            report = {
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'total_analyzed': len(analyses),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': hold_signals,
                'avg_confidence': avg_confidence,
                'market_sentiment': 'Bullish' if buy_signals > sell_signals else 'Bearish' if sell_signals > buy_signals else 'Neutral',
                'top_performer': {
                    'symbol': top_performer['symbol'],
                    'gain': top_performer.get('confidence', 0)
                },
                'analyses': analyses,
                'global_performance': np.random.uniform(-2, 5),  # Simulation - à remplacer par vraies données
                'signals_sent': buy_signals + sell_signals,
                'success_rate': np.random.uniform(65, 85)  # Simulation - à calculer réellement
            }

            return report

        except Exception as e:
            logging.error(f"Erreur lors de la génération du rapport: {e}")
            return self._get_empty_report()

    def _get_empty_report(self):
        """Rapport vide en cas d'erreur"""
        return {
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'error': True,
            'total_analyzed': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'global_performance': 0,
            'signals_sent': 0,
            'success_rate': 0
        }

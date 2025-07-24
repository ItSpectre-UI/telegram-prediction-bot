import ccxt
import pandas as pd
import pandas_ta as ta
import time
from telegram import Bot

# --- CONFIGURATION ---
BOT_TOKEN = "8236277562:AAGhfN49ngLT1kJBk5x0hlnGQroEs75E_QU"
CHAT_ID = "100513147"
SYMBOL = "BTC/USDT"
EXCHANGE = ccxt.mexc()
bot = Bot(token=BOT_TOKEN)

# --- STRATEGY SETTINGS ---
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14
ADX_THRESHOLD = 25
VOLUME_LOOKBACK = 5

def fetch_ohlcv(symbol, timeframe, limit=100):
    data = EXCHANGE.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['time','open','high','low','close','volume'])
    return df

def analyze_market():
    df_1h = fetch_ohlcv(SYMBOL, '1h')
    df_5m = fetch_ohlcv(SYMBOL, '5m')

    df_1h['ema_fast'] = ta.ema(df_1h['close'], EMA_FAST)
    df_1h['ema_slow'] = ta.ema(df_1h['close'], EMA_SLOW)
    trend = "UP" if df_1h['ema_fast'].iloc[-1] > df_1h['ema_slow'].iloc[-1] else "DOWN"

    df_5m['ema_fast'] = ta.ema(df_5m['close'], EMA_FAST)
    df_5m['ema_slow'] = ta.ema(df_5m['close'], EMA_SLOW)
    df_5m['rsi'] = ta.rsi(df_5m['close'], RSI_PERIOD)
    macd = ta.macd(df_5m['close'])
    df_5m['macd_hist'] = macd['MACDh_12_26_9']
    adx = ta.adx(df_5m['high'], df_5m['low'], df_5m['close'])
    df_5m['adx'] = adx['ADX_14']
    df_5m['volume_avg'] = df_5m['volume'].rolling(VOLUME_LOOKBACK).mean()

    latest = df_5m.iloc[-1]

    if trend == "UP":
        conditions = [
            latest['ema_fast'] > latest['ema_slow'],
            55 <= latest['rsi'] <= 70,
            latest['macd_hist'] > 0,
            latest['adx'] > ADX_THRESHOLD,
            latest['volume'] > latest['volume_avg'],
            latest['close'] > latest['open'],
            latest['rsi'] < 75
        ]
        if all(conditions):
            return "📈 Long Signal (UP Trend) for BTC/USDT"
    elif trend == "DOWN":
        conditions = [
            latest['ema_fast'] < latest['ema_slow'],
            30 <= latest['rsi'] <= 45,
            latest['macd_hist'] < 0,
            latest['adx'] > ADX_THRESHOLD,
            latest['volume'] > latest['volume_avg'],
            latest['close'] < latest['open'],
            latest['rsi'] > 25
        ]
        if all(conditions):
            return "📉 Short Signal (DOWN Trend) for BTC/USDT"
    return None

def main_loop():
    sent_signals = {"last": ""}
    while True:
        try:
            signal = analyze_market()
            if signal and signal != sent_signals["last"]:
                bot.send_message(chat_id=CHAT_ID, text=signal)
                sent_signals["last"] = signal
                print(f"✅ Signal sent: {signal}")
            else:
                print("No signal right now.")
            time.sleep(60)
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    main_loop()

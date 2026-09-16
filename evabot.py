#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 DARK X HYBRID V3 - 1 MIN WINGO TELEGRAM BOT
🧠 Priority: Alternating → Trend → Markov → Loss Breaker
📊 WIN/LOSS/JACKPOT Tracking
🤖 Telegram Bot
"""

import asyncio
import time
import requests
import os
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

try:
    from telegram import Bot
    from telegram.error import TelegramError, TimedOut, NetworkError
except ImportError:
    print("❌ python-telegram-bot not installed! Run: pip install python-telegram-bot")
    exit(1)

# ==================== কনফিগ ====================
BOT_TOKEN = "8792594779:AAEwfVCtDlD3PuSuuTthf2wtpxwHjRmM2Po"
CHAT_ID = "5833642063"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# ==================== ওয়েব সার্ভার ====================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DARK X HYBRID V3 BOT is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

def keep_alive():
    while True:
        try:
            time.sleep(600)
            port = int(os.environ.get("PORT", 8080))
            requests.get(f"http://localhost:{port}/", timeout=5)
        except:
            pass

threading.Thread(target=keep_alive, daemon=True).start()

# ==================== বট ====================
bot = Bot(token=BOT_TOKEN)

# ==================== ডেটা ====================
total_wins = 0
total_losses = 0
total_jackpots = 0
total_rounds = 0
current_streak = 0
best_win_streak = 0
worst_loss_streak = 0
current_level = 1
consecutive_losses = 0

hourly_wins = 0
hourly_losses = 0
hourly_rounds = 0
hourly_best_win_streak = 0
hourly_worst_loss_streak = 0

last_predicted_period = None
last_predicted_signal = None
last_predicted_num = None
prediction_sent_for_period = {}
last_result_sent = False

# ============================================================
# 🧠 ENGINE 1: ALTERNATING PATTERN
# ============================================================
def alternating_engine(types):
    if len(types) < 4:
        return None
    last4 = types[:4]
    if last4 == ["BIG", "SMALL", "BIG", "SMALL"]:
        return {"prediction": "BIG", "confidence": 88, "reason": "ALTERNATING (B-S-B-S)"}
    elif last4 == ["SMALL", "BIG", "SMALL", "BIG"]:
        return {"prediction": "SMALL", "confidence": 88, "reason": "ALTERNATING (S-B-S-B)"}
    return None

# ============================================================
# 🧠 ENGINE 2: TREND FOLLOW (5/0, 4/1)
# ============================================================
def trend_engine(types):
    if len(types) < 5:
        return None
    recent5 = types[:5]
    big_count = recent5.count("BIG")
    small_count = recent5.count("SMALL")
    if big_count >= 4:
        return {"prediction": "BIG", "confidence": 85 if big_count == 5 else 80,
                "reason": f"TREND FOLLOW ({big_count}B-{small_count}S)"}
    elif small_count >= 4:
        return {"prediction": "SMALL", "confidence": 85 if small_count == 5 else 80,
                "reason": f"TREND FOLLOW ({big_count}B-{small_count}S)"}
    return None

# ============================================================
# 🧠 ENGINE 3: MARKOV CHAIN (DARK X)
# ============================================================
def markov_engine(data, level):
    if len(data) < 3:
        return {"prediction": "BIG", "confidence": 50, "reason": "MARKOV (Fallback)"}
    types = [d['side'] for d in data[:10]]
    last1 = types[0] if len(types) > 0 else "BIG"
    last2 = types[1] if len(types) > 1 else "BIG"
    if last1 == "SMALL":
        pred, conf = "BIG", 75
    else:
        pred, conf = "SMALL", 60
    if last1 == "BIG" and last2 == "BIG":
        pred, conf = "SMALL", 90
    elif last1 == "SMALL" and last2 == "SMALL":
        pred, conf = "BIG", 95
    elif last1 == "SMALL" and last2 == "BIG":
        pred, conf = "BIG", 70
    elif last1 == "BIG" and last2 == "SMALL":
        pred, conf = "BIG", 85
    if level >= 3 and len(data) > 0:
        latest_num = data[0]['number']
        pred = "SMALL" if latest_num >= 5 else "BIG"
        conf = 99
    return {"prediction": pred, "confidence": conf, "reason": "MARKOV CHAIN"}

# ============================================================
# 🧠 ENGINE 4: SMART LOSS BREAKER
# ============================================================
def loss_breaker_engine(data, level, consec_losses):
    if consec_losses < 3:
        return None
    markov = markov_engine(data, level)
    if consec_losses % 2 == 1:
        pred = "SMALL" if markov['prediction'] == "BIG" else "BIG"
        reason = f"LOSS BREAKER (উল্টো, {consec_losses}টি টানা লস)"
    else:
        pred = markov['prediction']
        reason = f"LOSS BREAKER (একই দিক, {consec_losses}টি টানা লস)"
    return {"prediction": pred, "confidence": min(99, markov['confidence'] + 5), "reason": reason}

# ============================================================
# 🔥 MASTER HYBRID V3 ENGINE
# ============================================================
def hybrid_v3_engine(data, level, consec_losses):
    if len(data) < 3:
        return {"prediction": "BIG", "confidence": 50, "number": 7, "reason": "INSUFFICIENT DATA"}
    types = [d['side'] for d in data]
    
    # Step 1: Alternating
    alt = alternating_engine(types)
    if alt:
        num = random.randint(5, 9) if alt['prediction'] == "BIG" else random.randint(0, 4)
        return {"prediction": alt['prediction'], "confidence": alt['confidence'],
                "number": num, "reason": alt['reason']}
    
    # Step 2: Trend Follow
    trend = trend_engine(types)
    if trend:
        num = random.randint(5, 9) if trend['prediction'] == "BIG" else random.randint(0, 4)
        return {"prediction": trend['prediction'], "confidence": trend['confidence'],
                "number": num, "reason": trend['reason']}
    
    # Step 4: Loss Breaker
    if consec_losses >= 3:
        lb = loss_breaker_engine(data, level, consec_losses)
        if lb:
            num = random.randint(5, 9) if lb['prediction'] == "BIG" else random.randint(0, 4)
            return {"prediction": lb['prediction'], "confidence": lb['confidence'],
                    "number": num, "reason": lb['reason']}
    
    # Step 3: Markov (Fallback)
    markov = markov_engine(data, level)
    num = random.randint(5, 9) if markov['prediction'] == "BIG" else random.randint(0, 4)
    return {"prediction": markov['prediction'], "confidence": markov['confidence'],
            "number": num, "reason": markov['reason']}

# ==================== API ====================
def fetch_api_data():
    try:
        url = API_URL + "?t=" + str(int(time.time() * 1000))
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"API Error: {e}")
    return []

# ==================== Telegram সেন্ড ====================
async def send_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False

# ==================== হাওয়ারলি রিপোর্ট ====================
async def send_hourly_report():
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global total_wins, total_losses, total_rounds, total_jackpots
    global best_win_streak, worst_loss_streak
    
    if hourly_rounds == 0:
        return
    
    hourly_win_rate = (hourly_wins / hourly_rounds * 100) if hourly_rounds > 0 else 0
    total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
    
    report_msg = (
        f"📊 *HOURLY REPORT - HYBRID V3*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *TIME:* {datetime.now().strftime('%I:%M %p')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 *HOURLY ROUNDS:* `{hourly_rounds}`\n"
        f"✅ *HOURLY WINS:* `{hourly_wins}`\n"
        f"❌ *HOURLY LOSSES:* `{hourly_losses}`\n"
        f"📈 *HOURLY WIN RATE:* `{hourly_win_rate:.1f}%`\n"
        f"🔥 *BEST WIN STREAK:* `{hourly_best_win_streak}x`\n"
        f"📉 *WORST LOSS STREAK:* `{hourly_worst_loss_streak}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *TOTAL ROUNDS:* `{total_rounds}`\n"
        f"✅ *TOTAL WINS:* `{total_wins}`\n"
        f"❌ *TOTAL LOSSES:* `{total_losses}`\n"
        f"💎 *JACKPOTS:* `{total_jackpots}`\n"
        f"📈 *TOTAL WIN RATE:* `{total_win_rate:.1f}%`\n"
        f"🔥 *BEST WIN STREAK:* `{best_win_streak}x`\n"
        f"📉 *WORST LOSS STREAK:* `{worst_loss_streak}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ DARK X HYBRID V3 BOT"
    )
    
    await send_message(report_msg)
    
    hourly_wins = 0
    hourly_losses = 0
    hourly_rounds = 0
    hourly_best_win_streak = 0
    hourly_worst_loss_streak = 0

# ==================== মেইন লুপ ====================
async def prediction_bot():
    global total_wins, total_losses, total_jackpots, total_rounds
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global current_streak, best_win_streak, worst_loss_streak
    global current_level, consecutive_losses
    global last_predicted_period, last_predicted_signal, last_predicted_num
    global prediction_sent_for_period, last_result_sent

    print("🔥 DARK X HYBRID V3 BOT STARTED...")
    print("🧠 1. Alternating | 2. Trend | 3. Markov | 4. Loss Breaker")
    print("📡 MODE: 1 MIN WINGO")

    await send_message(
        "🔥 *DARK X HYBRID V3 BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🧠 *PRIORITY ORDER:*\n"
        "1️⃣ Alternating Pattern\n"
        "2️⃣ Trend Follow (4+/5)\n"
        "3️⃣ Markov Chain (DARK X)\n"
        "4️⃣ Loss Breaker (3+ losses)\n"
        "📡 *MODE:* 1 MIN WINGO\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ WAITING FOR FIRST SIGNAL..."
    )

    last_hour_time = time.time()

    while True:
        try:
            current_sec = int(time.time()) % 60
            sleep_time = 60 - current_sec + 3
            await asyncio.sleep(sleep_time)

            raw_list = fetch_api_data()
            if not raw_list:
                print("⚠️ API ডেটা নেই")
                continue

            history_data = []
            for h in raw_list[:20]:
                num = int(h['number'])
                history_data.append({
                    'issueNumber': str(h['issueNumber']),
                    'number': num,
                    'side': "BIG" if num >= 5 else "SMALL"
                })

            latest = history_data[0]
            latest_issue = latest['issueNumber']
            actual_num = latest['number']
            actual_type = "BIG" if actual_num >= 5 else "SMALL"

            print(f"📡 PERIOD: {latest_issue}, NUMBER: {actual_num}")

            # ==================== RESULT CHECK ====================
            if last_predicted_period == latest_issue and last_predicted_signal is not None and not last_result_sent:
                is_win = (last_predicted_signal == actual_type)
                is_jackpot = (last_predicted_num == actual_num)
                
                if is_jackpot:
                    total_jackpots += 1
                    total_wins += 1
                    hourly_wins += 1
                    consecutive_losses = 0
                    current_level = 1
                    status = "💎 JACKPOT"
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                elif is_win:
                    total_wins += 1
                    hourly_wins += 1
                    consecutive_losses = 0
                    current_level = 1
                    status = "✅ WIN"
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                else:
                    total_losses += 1
                    hourly_losses += 1
                    consecutive_losses += 1
                    current_level = min(3, current_level + 1)
                    status = "❌ LOSS"
                    if current_streak <= 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                
                if current_streak > best_win_streak:
                    best_win_streak = current_streak
                if current_streak > hourly_best_win_streak:
                    hourly_best_win_streak = current_streak
                if abs(current_streak) > worst_loss_streak and current_streak < 0:
                    worst_loss_streak = abs(current_streak)
                if abs(current_streak) > hourly_worst_loss_streak and current_streak < 0:
                    hourly_worst_loss_streak = abs(current_streak)
                
                total_rounds += 1
                hourly_rounds += 1
                
                total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
                streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                level_emoji = "🟢" if current_level == 1 else ("🟡" if current_level == 2 else "🔴")
                
                result_msg = (
                    f"🎯 *RESULT UPDATE*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 PERIOD: `#{latest_issue[-5:]}`\n"
                    f"🎯 PREDICTED: `{last_predicted_signal}` → `{last_predicted_num}`\n"
                    f"🎰 ACTUAL: `{actual_num}` (`{actual_type}`)\n"
                    f"📌 RESULT: `{status}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 WIN RATE: `{total_win_rate:.1f}%` ({total_wins}W/{total_losses}L)\n"
                    f"💎 JACKPOTS: `{total_jackpots}`\n"
                    f"{streak_emoji} STREAK: `{current_streak:+d}`\n"
                    f"{level_emoji} LEVEL: `{current_level}` ({current_level}x)\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ DARK X HYBRID V3 BOT"
                )
                
                await send_message(result_msg)
                last_result_sent = True
                print(f"📊 Result sent: {status}")
                
                last_predicted_period = None
                last_predicted_signal = None
                last_predicted_num = None
                
                if time.time() - last_hour_time >= 3600:
                    await send_hourly_report()
                    last_hour_time = time.time()

            # ==================== NEW PREDICTION ====================
            next_period = str(int(latest_issue) + 1)
            
            if not prediction_sent_for_period.get(next_period, False):
                pred = hybrid_v3_engine(history_data, current_level, consecutive_losses)
                
                streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                level_emoji = "🟢" if current_level == 1 else ("🟡" if current_level == 2 else "🔴")
                
                if pred['confidence'] >= 85:
                    rec = "🔥 HIGH CONFIDENCE - Normal Bet"
                elif pred['confidence'] >= 70:
                    rec = "⚡ MEDIUM CONFIDENCE - Safe Bet"
                else:
                    rec = "⚠️ LOW CONFIDENCE - Small Bet"
                
                prediction_msg = (
                    f"🔥 *DARK X HYBRID V3 - 1M WINGO* 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 PERIOD: `#{next_period[-5:]}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 PREDICTION: `{pred['prediction']}`\n"
                    f"🔢 TARGET NUMBER: `{pred['number']}`\n"
                    f"⚡ CONFIDENCE: `{pred['confidence']}%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🧠 ENGINE: {pred['reason']}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 RECOMMENDATION:\n"
                    f"• {rec}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{level_emoji} LEVEL: `{current_level}` ({current_level}x)\n"
                    f"{streak_emoji} STREAK: `{current_streak:+d}`\n"
                    f"❌ CONSECUTIVE LOSSES: `{consecutive_losses}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏳ RESULT AWAITING...\n"
                    f"⚡ DARK X HYBRID V3 BOT"
                )
                
                last_predicted_period = next_period
                last_predicted_signal = pred['prediction']
                last_predicted_num = pred['number']
                prediction_sent_for_period[next_period] = True
                last_result_sent = False
                
                await send_message(prediction_msg)
                print(f"✅ Prediction: {next_period} → {pred['prediction']} ({pred['number']}) [{pred['reason']}]")
                
                if len(prediction_sent_for_period) > 10:
                    oldest = min(prediction_sent_for_period.keys())
                    del prediction_sent_for_period[oldest]

        except Exception as e:
            print(f"❌ Loop Error: {e}")
            await asyncio.sleep(5)

# ==================== স্টার্ট ====================
if __name__ == '__main__':
    print("🔥 DARK X HYBRID V3 - 1M WINGO")
    print("━━━━━━━━━━━━━━━━━━━━")
    print("🧠 1. Alternating Pattern")
    print("🧠 2. Trend Follow (4+/5)")
    print("🧠 3. Markov Chain (DARK X)")
    print("🧠 4. Loss Breaker (3+ losses)")
    print("📡 MODE: 1 MIN WINGO")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    try:
        asyncio.run(prediction_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
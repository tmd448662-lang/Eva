#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 SHIKAARI BOSS - 5 MIN WINGO TELEGRAM BOT
🧠 Algorithm: Last-1 (Normal) + 11-Last (Repeat)
📊 WIN/LOSS/JACKPOT Tracking
🤖 Telegram Bot
"""

import asyncio
import time
import requests
import os
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

# ✅ 5 MIN WINGO API
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json"

# ==================== ওয়েব সার্ভার ====================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SHIKAARI BOSS BOT is running!")

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
# 🧠 SHIKAARI BOSS অ্যালগরিদম
# ============================================================

def shikaari_boss_algorithm(history_numbers):
    """
    NORMAL RULE: Last Number − 1
    REPEAT RULE: যদি শেষ ২টি একই হয় → 11 − Last Number
    """
    if len(history_numbers) < 2:
        return None
    
    last = history_numbers[0]
    prev = history_numbers[1]
    
    # REPEAT RULE
    if last == prev:
        result = 11 - last
        if result > 9:
            result = result - 10
        rule = "REPEAT RULE"
    else:
        # NORMAL RULE
        result = last - 1
        if result < 0:
            result = 9
        rule = "NORMAL RULE"
    
    return {
        "prediction": "BIG" if result >= 5 else "SMALL",
        "number": result,
        "rule": rule,
        "last": last,
        "prev": prev
    }

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
        f"📊 *HOURLY REPORT - SHIKAARI BOSS (5M)*\n"
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
        f"⚡ SHIKAARI BOSS BOT"
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
    global last_predicted_period, last_predicted_signal, last_predicted_num
    global prediction_sent_for_period, last_result_sent

    print("🔥 SHIKAARI BOSS BOT STARTED...")
    print("🧠 Algorithm: Last-1 + 11-Last")
    print("📡 MODE: 5 MIN WINGO")

    await send_message(
        "🔥 *SHIKAARI BOSS BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🧠 *ALGORITHM:* SHIKAARI BOSS\n"
        "📌 *NORMAL:* Last − 1\n"
        "📌 *REPEAT:* 11 − Last\n"
        "📡 *MODE:* 5 MIN WINGO\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ WAITING FOR FIRST SIGNAL..."
    )

    last_hour_time = time.time()

    while True:
        try:
            # ✅ 5 MIN = 300 সেকেন্ড অপেক্ষা
            current_sec = int(time.time()) % 300
            sleep_time = 300 - current_sec + 5
            print(f"⏳ অপেক্ষা {sleep_time} সেকেন্ড...")
            await asyncio.sleep(sleep_time)

            raw_list = fetch_api_data()
            if not raw_list:
                print("⚠️ API ডেটা নেই")
                continue

            history_data = []
            history_numbers = []
            for h in raw_list[:20]:
                num = int(h['number'])
                history_data.append({
                    'issueNumber': str(h['issueNumber']),
                    'number': num,
                    'side': "BIG" if num >= 5 else "SMALL"
                })
                history_numbers.append(num)

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
                    status = "💎 JACKPOT"
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                elif is_win:
                    total_wins += 1
                    hourly_wins += 1
                    status = "✅ WIN"
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                else:
                    total_losses += 1
                    hourly_losses += 1
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
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ SHIKAARI BOSS BOT"
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
                pred = shikaari_boss_algorithm(history_numbers)
                
                if pred:
                    streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                    
                    prediction_msg = (
                        f"🔥 *SHIKAARI BOSS PREDICTION* 🔥\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 PERIOD: `#{next_period[-5:]}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 PREDICTION: `{pred['prediction']}`\n"
                        f"🔢 TARGET NUMBER: `{pred['number']}`\n"
                        f"📌 RULE: `{pred['rule']}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 LAST: `{pred['last']}` | PREV: `{pred['prev']}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"{streak_emoji} STREAK: `{current_streak:+d}`\n"
                        f"📈 WIN RATE: `{(total_wins/total_rounds*100) if total_rounds > 0 else 0:.1f}%`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ RESULT AWAITING...\n"
                        f"⚡ SHIKAARI BOSS BOT"
                    )
                    
                    last_predicted_period = next_period
                    last_predicted_signal = pred['prediction']
                    last_predicted_num = pred['number']
                    prediction_sent_for_period[next_period] = True
                    last_result_sent = False
                    
                    await send_message(prediction_msg)
                    print(f"✅ Prediction: {next_period} → {pred['prediction']} ({pred['number']}) [{pred['rule']}]")
                    
                    if len(prediction_sent_for_period) > 10:
                        oldest = min(prediction_sent_for_period.keys())
                        del prediction_sent_for_period[oldest]

        except Exception as e:
            print(f"❌ Loop Error: {e}")
            await asyncio.sleep(5)

# ==================== স্টার্ট ====================
if __name__ == '__main__':
    print("🔥 SHIKAARI BOSS BOT")
    print("━━━━━━━━━━━━━━━━━━━━")
    print("🧠 NORMAL: Last - 1")
    print("🧠 REPEAT: 11 - Last")
    print("📡 MODE: 5 MIN WINGO")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    try:
        asyncio.run(prediction_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Fatal Error: {e}") 
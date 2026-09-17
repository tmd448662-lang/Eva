#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 SHIKAARI BOSS + ADAPTIVE RECOVERY - 5 MIN WINGO
🧠 SHIKAARI: Last-1 (Normal) + 11-Last (Repeat)
🎯 ADAPTIVE RECOVERY:
   Level 1 (0-2 Loss): SHIKAARI Normal
   Level 2 (3 Loss): REVERSE ENGINE 🔄
   Level 3 (4+ Loss): TRIPLE ENGINE 🔥
✅ WIN → Level 1 Reset
❌ Skip ছাড়াই কাজ করে!
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
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json"

# ==================== ওয়েব সার্ভার ====================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SHIKAARI ADAPTIVE BOT is running!")

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

# 🎯 ADAPTIVE LEVEL
current_level = 1
consecutive_losses = 0
max_loss_streak_ever = 0
level_history = {1: 0, 2: 0, 3: 0}

# Recovery Stats
recovery_wins = 0
recovery_losses = 0

# Hourly Stats
hourly_wins = 0
hourly_losses = 0
hourly_rounds = 0
hourly_best_win_streak = 0
hourly_worst_loss_streak = 0
hourly_current_streak = 0
hourly_current_streak_type = "WIN"
hourly_jackpots = 0
hourly_recovery_wins = 0

last_predicted_period = None
last_predicted_signal = None
last_predicted_num = None
prediction_sent_for_period = {}
last_result_sent = False
last_hour_report_time = time.time()

# ============================================================
# 🧠 SHIKAARI BOSS BASE ENGINE
# ============================================================
def shikaari_base(history_numbers):
    """SHIKAARI BOSS Basic Logic"""
    if len(history_numbers) < 2:
        return None
    
    last = history_numbers[0]
    prev = history_numbers[1]
    
    if last == prev:
        result = 11 - last
        if result > 9:
            result = result - 10
        rule = "REPEAT (11-L)"
    else:
        result = last - 1
        if result < 0:
            result = 9
        rule = "NORMAL (L-1)"
    
    return {
        "prediction": "BIG" if result >= 5 else "SMALL",
        "number": result,
        "rule": rule,
        "last": last,
        "prev": prev
    }

# ============================================================
# 🔄 REVERSE ENGINE (3 Loss Recovery)
# ============================================================
def reverse_engine(history_numbers):
    """
    3 Loss হলে: উল্টা প্রেডিকশন
    SHIKAARI যা বলে তার উল্টো
    """
    base = shikaari_base(history_numbers)
    if not base:
        return None
    
    # উল্টা প্রেডিকশন
    reverse_pred = "SMALL" if base['prediction'] == "BIG" else "BIG"
    
    # উল্টা নাম্বার
    if reverse_pred == "BIG":
        reverse_num = 5 + (base['number'] % 5)
    else:
        reverse_num = base['number'] % 5
    
    return {
        "prediction": reverse_pred,
        "number": reverse_num,
        "rule": f"REVERSE ({base['rule']})",
        "last": base['last'],
        "prev": base['prev']
    }

# ============================================================
# 🔥 TRIPLE ENGINE (4+ Loss Recovery)
# ============================================================
def trend_follow_engine(history_numbers):
    """শেষ ৫টি দেখে ট্রেন্ড ফলো"""
    if len(history_numbers) < 5:
        return None
    
    last5 = history_numbers[:5]
    big_count = sum(1 for n in last5 if n >= 5)
    small_count = 5 - big_count
    
    if big_count >= 3:
        pred = "BIG"
        num = 5 + (history_numbers[0] % 5)
    else:
        pred = "SMALL"
        num = history_numbers[0] % 5
    
    return {
        "prediction": pred,
        "number": num,
        "rule": f"TREND ({big_count}B-{small_count}S)"
    }

def markov_engine(history_numbers):
    """Markov Chain - শেষ ২টি দেখে"""
    if len(history_numbers) < 2:
        return None
    
    last = history_numbers[0]
    prev = history_numbers[1]
    
    # Markov Pattern
    if last >= 5 and prev >= 5:
        pred = "SMALL"
        conf = "High"
    elif last < 5 and prev < 5:
        pred = "BIG"
        conf = "High"
    elif last < 5 and prev >= 5:
        pred = "BIG"
        conf = "Medium"
    else:  # last >= 5 and prev < 5
        pred = "SMALL"
        conf = "Medium"
    
    num = 5 + (last % 5) if pred == "BIG" else last % 5
    
    return {
        "prediction": pred,
        "number": num,
        "rule": f"MARKOV ({conf})"
    }

def triple_engine(history_numbers):
    """
    Triple Engine: TREND + MARKOV + REVERSE
    Majority Vote দিয়ে সিদ্ধান্ত
    """
    trend = trend_follow_engine(history_numbers)
    markov = markov_engine(history_numbers)
    reverse = reverse_engine(history_numbers)
    
    if not all([trend, markov, reverse]):
        return None
    
    # Vote
    votes = {"BIG": 0, "SMALL": 0}
    votes[trend['prediction']] += 1
    votes[markov['prediction']] += 1
    votes[reverse['prediction']] += 1
    
    # Majority
    if votes["BIG"] >= 2:
        final_pred = "BIG"
    else:
        final_pred = "SMALL"
    
    # Number Selection
    if final_pred == trend['prediction']:
        final_num = trend['number']
    elif final_pred == markov['prediction']:
        final_num = markov['number']
    else:
        final_num = reverse['number']
    
    return {
        "prediction": final_pred,
        "number": final_num,
        "rule": f"TRIPLE (T:{trend['prediction']} M:{markov['prediction']} R:{reverse['prediction']})",
        "votes": votes
    }

# ============================================================
# 🎯 ADAPTIVE SHIKAARI ENGINE
# ============================================================
def adaptive_shikaari_engine(history_numbers, level, consec_losses):
    """
    Level 1 (0-2 Loss): SHIKAARI Normal
    Level 2 (3 Loss): REVERSE Engine
    Level 3 (4+ Loss): TRIPLE Engine
    """
    if level == 1:
        # Normal SHIKAARI
        return shikaari_base(history_numbers)
    
    elif level == 2:
        # REVERSE Engine (3 Loss)
        return reverse_engine(history_numbers)
    
    elif level >= 3:
        # TRIPLE Engine (4+ Loss)
        triple = triple_engine(history_numbers)
        if triple:
            return triple
        # Fallback
        return reverse_engine(history_numbers)
    
    return shikaari_base(history_numbers)

# ============================================================
# 🎯 LEVEL MANAGEMENT
# ============================================================
def get_level_emoji(level):
    emojis = {1: "🟢", 2: "🔄", 3: "🔥"}
    return emojis.get(level, "⚪")

def get_level_multiplier(level):
    multipliers = {1: 1, 2: 2, 3: 3}
    return multipliers.get(level, 1)

def get_level_recommendation(level):
    recommendations = {
        1: "🟢 NORMAL BET (1x)",
        2: "🔄 REVERSE ENGINE (2x)",
        3: "🔥 TRIPLE ENGINE (3x)"
    }
    return recommendations.get(level, "⚪ UNKNOWN")

def update_level_on_result(is_win, is_jackpot):
    """
    WIN → Level 1 Reset
    LOSS → Level UP (1 → 2 → 3)
    3+ Loss এও Level 3 এ থাকে (Skip নেই)
    """
    global current_level, consecutive_losses, max_loss_streak_ever
    global level_history, recovery_wins, hourly_recovery_wins
    
    if is_win or is_jackpot:
        # WIN → Level 1
        if current_level > 1:
            recovery_wins += 1
            hourly_recovery_wins += 1
        current_level = 1
        consecutive_losses = 0
    else:
        consecutive_losses += 1
        
        if consecutive_losses > max_loss_streak_ever:
            max_loss_streak_ever = consecutive_losses
        
        # Level UP (max 3)
        if consecutive_losses >= 4:
            current_level = 3
        elif consecutive_losses >= 3:
            current_level = 2
        else:
            current_level = 1
    
    if current_level in level_history:
        level_history[current_level] += 1

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
    global hourly_current_streak, hourly_current_streak_type, hourly_jackpots
    global hourly_recovery_wins
    global total_wins, total_losses, total_rounds, total_jackpots
    global best_win_streak, worst_loss_streak, max_loss_streak_ever
    global level_history, recovery_wins, last_hour_report_time

    if hourly_rounds == 0:
        return

    hourly_win_rate = (hourly_wins / hourly_rounds * 100) if hourly_rounds > 0 else 0
    total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0

    report_msg = (
        f"📊 *HOURLY REPORT - ADAPTIVE SHIKAARI (5M)*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *TIME:* {datetime.now().strftime('%I:%M %p')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 *HOURLY ROUNDS:* `{hourly_rounds}`\n"
        f"✅ *HOURLY WINS:* `{hourly_wins}`\n"
        f"❌ *HOURLY LOSSES:* `{hourly_losses}`\n"
        f"📈 *HOURLY WIN RATE:* `{hourly_win_rate:.1f}%`\n"
        f"🔄 *RECOVERY WINS:* `{hourly_recovery_wins}`\n"
        f"🔥 *BEST WIN STREAK:* `{hourly_best_win_streak}x`\n"
        f"📉 *WORST LOSS STREAK:* `{hourly_worst_loss_streak}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *TOTAL ROUNDS:* `{total_rounds}`\n"
        f"✅ *TOTAL WINS:* `{total_wins}`\n"
        f"❌ *TOTAL LOSSES:* `{total_losses}`\n"
        f"💎 *JACKPOTS:* `{total_jackpots}`\n"
        f"🔄 *RECOVERY WINS:* `{recovery_wins}`\n"
        f"📈 *TOTAL WIN RATE:* `{total_win_rate:.1f}%`\n"
        f"🔥 *BEST WIN STREAK:* `{best_win_streak}x`\n"
        f"📉 *WORST LOSS STREAK:* `{worst_loss_streak}x`\n"
        f"🛡️ *MAX LOSS STREAK:* `{max_loss_streak_ever}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *LEVEL DISTRIBUTION:*\n"
        f"🟢 Level 1: `{level_history.get(1, 0)}`\n"
        f"🔄 Level 2: `{level_history.get(2, 0)}`\n"
        f"🔥 Level 3: `{level_history.get(3, 0)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ ADAPTIVE SHIKAARI BOT"
    )

    await send_message(report_msg)

    hourly_wins = 0
    hourly_losses = 0
    hourly_rounds = 0
    hourly_best_win_streak = 0
    hourly_worst_loss_streak = 0
    hourly_current_streak = 0
    hourly_current_streak_type = "WIN"
    hourly_jackpots = 0
    hourly_recovery_wins = 0
    last_hour_report_time = time.time()

# ==================== মেইন লুপ ====================
async def prediction_bot():
    global total_wins, total_losses, total_jackpots, total_rounds
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global hourly_current_streak, hourly_current_streak_type, hourly_jackpots
    global hourly_recovery_wins
    global current_streak, best_win_streak, worst_loss_streak
    global current_level, consecutive_losses, max_loss_streak_ever, level_history
    global recovery_wins
    global last_predicted_period, last_predicted_signal, last_predicted_num
    global prediction_sent_for_period, last_result_sent
    global last_hour_report_time

    print("🔥 ADAPTIVE SHIKAARI BOT STARTED...")
    print("🧠 Level 1: SHIKAARI Normal")
    print("🔄 Level 2: REVERSE Engine (3 Loss)")
    print("🔥 Level 3: TRIPLE Engine (4+ Loss)")
    print("📡 MODE: 5 MIN WINGO")

    await send_message(
        "🔥 *ADAPTIVE SHIKAARI BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🧠 *ADAPTIVE LEVELS:*\n"
        "🟢 Level 1: SHIKAARI Normal\n"
        "🔄 Level 2: REVERSE Engine\n"
        "🔥 Level 3: TRIPLE Engine\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *HOW IT WORKS:*\n"
        "• 0-2 Loss → Normal SHIKAARI\n"
        "• 3 Loss → Reverse Prediction\n"
        "• 4+ Loss → Triple Engine Vote\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ WIN → Level 1 Reset\n"
        "❌ Skip ছাড়াই কাজ করে\n"
        "📡 *MODE:* 5 MIN WINGO\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ WAITING FOR FIRST SIGNAL..."
    )

    while True:
        try:
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
                old_level = current_level
                
                if is_jackpot:
                    total_jackpots += 1
                    total_wins += 1
                    hourly_wins += 1
                    hourly_jackpots += 1
                    status = "💎 JACKPOT"
                    is_win = True
                elif is_win:
                    total_wins += 1
                    hourly_wins += 1
                    status = "✅ WIN"
                else:
                    total_losses += 1
                    hourly_losses += 1
                    status = "❌ LOSS"
                
                # Level Update
                update_level_on_result(is_win, is_jackpot)
                
                # Streak
                if is_win:
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                else:
                    if current_streak <= 0:
                        current_streak -= 1
                    else:
                        current_streak = -1

                if current_streak > best_win_streak:
                    best_win_streak = current_streak
                if abs(current_streak) > worst_loss_streak and current_streak < 0:
                    worst_loss_streak = abs(current_streak)

                # Hourly Streak
                if is_win:
                    if hourly_current_streak_type == "WIN":
                        hourly_current_streak += 1
                    else:
                        hourly_current_streak = 1
                        hourly_current_streak_type = "WIN"
                    if hourly_current_streak > hourly_best_win_streak:
                        hourly_best_win_streak = hourly_current_streak
                else:
                    if hourly_current_streak_type == "LOSS":
                        hourly_current_streak += 1
                    else:
                        hourly_current_streak = 1
                        hourly_current_streak_type = "LOSS"
                    if hourly_current_streak > hourly_worst_loss_streak:
                        hourly_worst_loss_streak = hourly_current_streak

                total_rounds += 1
                hourly_rounds += 1

                total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
                streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                level_emoji = get_level_emoji(current_level)

                # Level Change Indicator
                level_change = ""
                if old_level != current_level:
                    if current_level == 1 and is_win:
                        level_change = "🔄 Level Reset (WIN) ✅"
                    elif current_level == 2:
                        level_change = "🔄 REVERSE ENGINE ACTIVATED"
                    elif current_level == 3:
                        level_change = "🔥 TRIPLE ENGINE ACTIVATED"
                elif current_level == 2:
                    level_change = "🔄 REVERSE Engine Active"
                elif current_level == 3:
                    level_change = "🔥 TRIPLE Engine Active"

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
                    f"{level_emoji} *LEVEL: {current_level}*\n"
                    f"❌ CONSECUTIVE LOSSES: `{consecutive_losses}`\n"
                    f"{level_change}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ ADAPTIVE SHIKAARI"
                )

                await send_message(result_msg)
                print(f"📊 {status} | Level: {current_level} | Consec Loss: {consecutive_losses}")

                last_result_sent = True
                last_predicted_period = None
                last_predicted_signal = None
                last_predicted_num = None

                if time.time() - last_hour_report_time >= 3600:
                    await send_hourly_report()

            # ==================== NEW PREDICTION ====================
            next_period = str(int(latest_issue) + 1)

            if not prediction_sent_for_period.get(next_period, False):
                pred = adaptive_shikaari_engine(history_numbers, current_level, consecutive_losses)

                if pred:
                    streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                    level_emoji = get_level_emoji(current_level)
                    multiplier = get_level_multiplier(current_level)
                    recommendation = get_level_recommendation(current_level)

                    prediction_msg = (
                        f"🔥 *ADAPTIVE SHIKAARI PREDICTION* 🔥\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 PERIOD: `#{next_period[-5:]}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 PREDICTION: `{pred['prediction']}`\n"
                        f"🔢 TARGET NUMBER: `{pred['number']}`\n"
                        f"📌 RULE: `{pred['rule']}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 LAST: `{pred['last']}` | PREV: `{pred['prev']}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"{level_emoji} *LEVEL: {current_level}* ({multiplier}x)\n"
                        f"💡 {recommendation}\n"
                        f"❌ CONSECUTIVE LOSSES: `{consecutive_losses}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"{streak_emoji} STREAK: `{current_streak:+d}`\n"
                        f"📈 WIN RATE: `{(total_wins/total_rounds*100) if total_rounds > 0 else 0:.1f}%`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ RESULT AWAITING...\n"
                        f"⚡ ADAPTIVE SHIKAARI"
                    )

                    last_predicted_period = next_period
                    last_predicted_signal = pred['prediction']
                    last_predicted_num = pred['number']
                    prediction_sent_for_period[next_period] = True
                    last_result_sent = False

                    await send_message(prediction_msg)
                    print(f"✅ Prediction: {next_period} → {pred['prediction']} ({pred['number']}) [L{current_level}]")

                    if len(prediction_sent_for_period) > 10:
                        oldest = min(prediction_sent_for_period.keys())
                        del prediction_sent_for_period[oldest]

        except Exception as e:
            print(f"❌ Loop Error: {e}")
            await asyncio.sleep(5)

# ==================== স্টার্ট ====================
if __name__ == '__main__':
    print("🔥 ADAPTIVE SHIKAARI BOT")
    print("━━━━━━━━━━━━━━━━━━━━")
    print("🟢 Level 1: SHIKAARI Normal")
    print("🔄 Level 2: REVERSE Engine")
    print("🔥 Level 3: TRIPLE Engine")
    print("━━━━━━━━━━━━━━━━━━━━")
    print("📡 MODE: 5 MIN WINGO")
    print("━━━━━━━━━━━━━━━━━━━━")
    print(f"🤖 BOT: @Eva267o")
    print(f"📡 CHAT ID: {CHAT_ID}")

    try:
        asyncio.run(prediction_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
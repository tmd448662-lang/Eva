#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 PATTERN MATCHER - 5/6/7 Digit - 1 MIN WINGO
📊 PDF 1 Based Bot (No Pattern = Majority)
🤖 @Eva267o
"""

import asyncio
import time
import requests
import os
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from telegram import Bot
    from telegram.error import TelegramError, TimedOut, NetworkError
except ImportError:
    print("❌ python-telegram-bot ইনস্টল নেই!")
    exit(1)

# ==================== 📌 কনফিগারেশন ====================
BOT_TOKEN = "8792594779:AAEwfVCtDlD3PuSuuTthf2wtpxwHjRmM2Po"
CHAT_ID = "5833642063"

# ✅ 1 MIN WINGO API
API_URLS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    "https://api.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
]

# ==================== 🌐 ওয়েব সার্ভার ====================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"PATTERN MATCHER BOT is running!")

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

# ==================== 📊 বট ইনিশিয়ালাইজ ====================
try:
    bot = Bot(token=BOT_TOKEN)
    logger.info("✅ বট ইনিশিয়ালাইজেশন সফল!")
    logger.info("🤖 বট: @Eva267o")
except Exception as e:
    logger.error(f"❌ বট ইনিশিয়ালাইজেশন ব্যর্থ: {e}")
    exit(1)

# ==================== গ্লোবাল ভেরিয়েবল ====================
total_wins = 0
total_losses = 0
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
last_pattern_matched = None
prediction_sent_for_period = {}
last_result_sent = False

# ============================================================
#  📚 PATTERN DATABASE (PDF 1 থেকে)
# ============================================================

# 5-Digit Patterns
PATTERNS_5 = {
    "SSBSS": "S", "BBSBS": "S", "SBBBS": "B", "BSBBB": "S",
    "BBBBS": "B", "BBBSB": "B", "SSBSB": "B",
    "SBSBS": "B", "SBSBB": "B", "SSSBB": "B", "BSSBS": "S",
    "SBBSB": "S", "BSBSB": "S", "SBSSB": "S",
    "BSSSB": "S", "BBSBB": "B", "SBBBB": "B",
    "SBSSBB": "B", "BBSSSB": "B", "BSSBSB": "S",
}

# 6-Digit Patterns
PATTERNS_6 = {
    "BSBBSS": "S", "BSBSSS": "S", "SSSBBB": "B", "SSSBBS": "B",
    "SSBBBS": "B", "BSBSSB": "S", "BSSSBS": "B", "SSSSSS": "B",
    "SSSSSB": "B", "BBSBSB": "S", "BBBBSB": "S", "SBBBBB": "S",
    "SBBBBS": "S", "BBSBBB": "S", "BSBSBB": "S", "SSSSBS": "B",
    "SSBBSB": "B", "SBSSSB": "B", "BSBBBS": "S", "SSSBSB": "B",
}

# 7-Digit Patterns
PATTERNS_7 = {
    "SSBBBS": "B", "BSSSSB": "S", "BSSSBB": "S", "SBBBBS": "S",
    "SSSBBB": "B", "BSSBBB": "S", "SSSSBB": "B", "SSSSSSB": "B",
    "SSSSSB": "B", "BSBSBSB": "S", "BSSBSBS": "S",
    "SBSBSB": "B", "BSBSBSS": "B", "SSSBSB": "B", "BBSBSB": "S",
    "BBSBSBS": "B", "SBSBSBS": "S", "BSSBSBS": "B", "SSSSSSS": "B",
    "BBBBBBS": "S", "SBBBBBB": "S", "BSBBBSB": "S",
    "SSSBBSB": "B", "BBSBBBS": "S",
}

ALL_PATTERNS = {}
ALL_PATTERNS.update(PATTERNS_5)
ALL_PATTERNS.update(PATTERNS_6)
ALL_PATTERNS.update(PATTERNS_7)

# ============================================================
#  🧠 PATTERN MATCHER ENGINE (No Pattern = Majority)
# ============================================================
def pattern_matcher(data):
    if len(data) < 5:
        return {
            "prediction": "BIG", "confidence": 50,
            "reason": "INSUFFICIENT DATA",
            "pattern": None, "pattern_type": "NONE"
        }
    
    sides = [d['side'][0] for d in data]
    
    # 7-digit চেক
    if len(sides) >= 7:
        pattern_7 = ''.join(sides[:7])
        if pattern_7 in PATTERNS_7:
            pred_letter = PATTERNS_7[pattern_7]
            pred = "BIG" if pred_letter == "B" else "SMALL"
            return {
                "prediction": pred, "confidence": 80,
                "reason": f"7-DIGIT MATCH ({pattern_7})",
                "pattern": pattern_7, "pattern_type": "7-DIGIT"
            }
    
    # 6-digit চেক
    if len(sides) >= 6:
        pattern_6 = ''.join(sides[:6])
        if pattern_6 in PATTERNS_6:
            pred_letter = PATTERNS_6[pattern_6]
            pred = "BIG" if pred_letter == "B" else "SMALL"
            return {
                "prediction": pred, "confidence": 75,
                "reason": f"6-DIGIT MATCH ({pattern_6})",
                "pattern": pattern_6, "pattern_type": "6-DIGIT"
            }
    
    # 5-digit চেক
    if len(sides) >= 5:
        pattern_5 = ''.join(sides[:5])
        if pattern_5 in PATTERNS_5:
            pred_letter = PATTERNS_5[pattern_5]
            pred = "BIG" if pred_letter == "B" else "SMALL"
            return {
                "prediction": pred, "confidence": 70,
                "reason": f"5-DIGIT MATCH ({pattern_5})",
                "pattern": pattern_5, "pattern_type": "5-DIGIT"
            }
    
    # ✅ No Pattern → Majority Vote
    recent5 = sides[:5]
    big_count = recent5.count("B")
    small_count = recent5.count("S")
    pred = "BIG" if big_count >= small_count else "SMALL"
    
    return {
        "prediction": pred,
        "confidence": 55,
        "reason": f"MAJORITY ({big_count}B-{small_count}S)",
        "pattern": None,
        "pattern_type": "MAJORITY"
    }

# ==================== 📡 API ফেচ ====================
def fetch_api_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    
    for api_url in API_URLS:
        try:
            url = api_url + "?t=" + str(int(time.time() * 1000))
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                list_data = data.get("data", {}).get("list", [])
                if list_data and len(list_data) > 0:
                    return list_data
            else:
                logger.warning(f"⚠️ {api_url} → HTTP {res.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ {api_url} → এরর: {e}")
    
    return []

# ==================== 📤 মেসেজ সেন্ড ====================
async def send_message(text, parse_mode="Markdown", retry_count=3):
    for attempt in range(retry_count):
        try:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode=parse_mode)
            return True
        except (TimedOut, NetworkError):
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"❌ টেলিগ্রাম এরর: {e}")
            break
    return False

# ==================== 📊 হাওয়ারলি রিপোর্ট ====================
async def send_hourly_report():
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global total_wins, total_losses, total_rounds
    global best_win_streak, worst_loss_streak
    
    if hourly_rounds == 0:
        return
    
    hourly_win_rate = (hourly_wins / hourly_rounds * 100) if hourly_rounds > 0 else 0
    total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
    
    report_msg = (
        f"📊 *আওয়ারলি রিপোর্ট - 1M PATTERN MATCHER*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *সময়:* {datetime.now().strftime('%I:%M %p')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 *এই ঘন্টায় রাউন্ড:* `{hourly_rounds}`\n"
        f"✅ *এই ঘন্টায় জয়:* `{hourly_wins}`\n"
        f"❌ *এই ঘন্টায় হার:* `{hourly_losses}`\n"
        f"📈 *এই ঘন্টায় হার:* `{hourly_win_rate:.1f}%`\n"
        f"🔥 *সেরা জয় স্ট্রিক:* `{hourly_best_win_streak}x`\n"
        f"📉 *সেরা হার স্ট্রিক:* `{hourly_worst_loss_streak}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *মোট রাউন্ড:* `{total_rounds}`\n"
        f"✅ *মোট জয়:* `{total_wins}`\n"
        f"❌ *মোট হার:* `{total_losses}`\n"
        f"📈 *মোট জয়ের হার:* `{total_win_rate:.1f}%`\n"
        f"🔥 *সেরা জয় স্ট্রিক:* `{best_win_streak}x`\n"
        f"📉 *সেরা হার স্ট্রিক:* `{worst_loss_streak}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 @Eva267o"
    )
    
    await send_message(report_msg)
    
    hourly_wins = 0
    hourly_losses = 0
    hourly_rounds = 0
    hourly_best_win_streak = 0
    hourly_worst_loss_streak = 0

# ==================== 🚀 মেইন লুপ ====================
async def prediction_bot():
    global total_wins, total_losses, total_rounds
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global current_streak, best_win_streak, worst_loss_streak
    global last_predicted_period, last_predicted_signal
    global last_pattern_matched, prediction_sent_for_period
    global last_result_sent

    logger.info("🔥 PATTERN MATCHER - 1M WINGO স্টার্ট...")
    logger.info(f"📚 5-Digit: {len(PATTERNS_5)} | 6-Digit: {len(PATTERNS_6)} | 7-Digit: {len(PATTERNS_7)}")
    logger.info(f"📊 মোট প্যাটার্ন: {len(ALL_PATTERNS)}")
    logger.info("✅ No Pattern = Majority Vote")

    await send_message(
        "🔥 *PATTERN MATCHER - 1M WINGO* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📚 *Pattern Database:*\n"
        f"• 5-Digit: `{len(PATTERNS_5)}` patterns\n"
        f"• 6-Digit: `{len(PATTERNS_6)}` patterns\n"
        f"• 7-Digit: `{len(PATTERNS_7)}` patterns\n"
        f"• মোট: `{len(ALL_PATTERNS)}` patterns\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *No Pattern = Majority Vote*\n"
        "📡 *মোড:* 1 MIN WINGO\n"
        "🤖 *বট:* @Eva267o\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ প্রথম সিগন্যালের জন্য অপেক্ষা..."
    )

    last_hour_time = time.time()

    while True:
        try:
            # ✅ 1 MIN (60 সেকেন্ড) অপেক্ষা
            current_sec = int(time.time()) % 60
            sleep_time = 60 - current_sec + 3
            logger.info(f"⏳ অপেক্ষা {sleep_time} সেকেন্ড...")
            await asyncio.sleep(sleep_time)

            raw_list = fetch_api_data()
            if not raw_list:
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

            logger.info(f"📡 পিরিয়ড: {latest_issue}, নাম্বার: {actual_num} ({actual_type})")

            # ===== রেজাল্ট চেক =====
            if last_predicted_period == latest_issue and last_predicted_signal is not None and not last_result_sent:
                is_win = (last_predicted_signal == actual_type)
                
                if is_win:
                    total_wins += 1
                    hourly_wins += 1
                    
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                    
                    if current_streak > best_win_streak:
                        best_win_streak = current_streak
                    if current_streak > hourly_best_win_streak:
                        hourly_best_win_streak = current_streak
                    
                    status = "✅ জয় 🎉"
                else:
                    total_losses += 1
                    hourly_losses += 1
                    
                    if current_streak <= 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                    
                    if abs(current_streak) > worst_loss_streak:
                        worst_loss_streak = abs(current_streak)
                    if abs(current_streak) > hourly_worst_loss_streak:
                        hourly_worst_loss_streak = abs(current_streak)
                    
                    status = "❌ হার"

                total_rounds += 1
                hourly_rounds += 1
                
                total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
                streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"

                result_msg = (
                    f"🎯 *রেজাল্ট আপডেট*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 পিরিয়ড: `#{latest_issue[-5:]}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔮 প্রেডিকশন: `{last_predicted_signal}`\n"
                    f"🎰 একচুয়াল: `{actual_num}` → `{actual_type}`\n"
                    f"📌 রেজাল্ট: `{status}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 জয়ের হার: `{total_win_rate:.1f}%` ({total_wins}W/{total_losses}L)\n"
                    f"{streak_emoji} স্ট্রিক: `{current_streak:+d}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 @Eva267o"
                )

                await send_message(result_msg)
                last_result_sent = True

                if time.time() - last_hour_time >= 3600:
                    await send_hourly_report()
                    last_hour_time = time.time()

            # ===== নতুন প্রেডিকশন =====
            next_period = str(int(latest_issue) + 1)
            
            if not prediction_sent_for_period.get(next_period, False):
                
                pred = pattern_matcher(history_data)
                last_pattern_matched = pred.get('pattern')
                
                streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                
                if pred['confidence'] >= 80:
                    rec = "🔥 হাই কনফিডেন্স"
                elif pred['confidence'] >= 70:
                    rec = "⚡ মিডিয়াম কনফিডেন্স"
                elif pred['confidence'] >= 60:
                    rec = "⚠️ লো কনফিডেন্স"
                else:
                    rec = "🟡 Majority Vote (No Pattern)"

                prediction_msg = (
                    f"🔥 *PATTERN MATCHER - 1M WINGO* 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 পিরিয়ড: `#{next_period[-5:]}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 প্রেডিকশন: `{pred['prediction']}`\n"
                    f"⚡ কনফিডেন্স: `{pred['confidence']}%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🧠 ইঞ্জিন: {pred['reason']}\n"
                    f"📊 প্যাটার্ন টাইপ: `{pred['pattern_type']}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 রেকমেন্ডেশন:\n"
                    f"• {rec}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{streak_emoji} স্ট্রিক: `{current_streak:+d}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏳ রেজাল্টের জন্য অপেক্ষা...\n"
                    f"🤖 @Eva267o"
                )

                last_predicted_period = next_period
                last_predicted_signal = pred['prediction']
                prediction_sent_for_period[next_period] = True
                last_result_sent = False

                await send_message(prediction_msg)
                logger.info(f"✅ প্রেডিকশন: {next_period} → {pred['prediction']} ({pred['reason']})")

                if len(prediction_sent_for_period) > 10:
                    oldest = min(prediction_sent_for_period.keys())
                    del prediction_sent_for_period[oldest]

        except Exception as e:
            logger.error(f"❌ Loop Error: {e}")
            await asyncio.sleep(5)

# ==================== 🚀 স্টার্ট ====================
if __name__ == '__main__':
    print("🔥 PATTERN MATCHER - 1M WINGO")
    print("━━━━━━━━━━━━━━━━━━━━")
    print(f"📚 5-Digit Patterns: {len(PATTERNS_5)}")
    print(f"📚 6-Digit Patterns: {len(PATTERNS_6)}")
    print(f"📚 7-Digit Patterns: {len(PATTERNS_7)}")
    print(f"📊 Total: {len(ALL_PATTERNS)}")
    print("✅ No Pattern = Majority Vote")
    print("📡 MODE: 1 MIN WINGO")
    print("🤖 BOT: @Eva267o")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    try:
        asyncio.run(prediction_bot())
    except KeyboardInterrupt:
        print("\n👋 বট বন্ধ করা হয়েছে")
    except Exception as e:
        print(f"❌ ফাটাল এরর: {e}")

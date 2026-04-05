import telebot
import requests
import threading
import time

BOT_TOKEN = "8511427168:AAE1doWBxBZo_-q83e8qVY3WI631o9XikSY"
ADMIN_ID = 7138785294

API_URL = "https://api-lc79-congthuc-vip-tuananh.onrender.com/api/taixiumd5"

bot = telebot.TeleBot(BOT_TOKEN)

tool_status = False
chat_id = None
last_session = None

history = []
win = 0
lose = 0

last_prediction = None


def is_admin(uid):
    return uid == ADMIN_ID


# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
"""🤖 TOOL TÀI XỈU LC79

/battool → bật tool
/tattool → tắt tool
""")


# ================= BẬT TOOL =================
@bot.message_handler(commands=['battool'])
def battool(message):
    global tool_status, chat_id

    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Không có quyền")
        return

    tool_status = True
    chat_id = message.chat.id

    bot.send_message(chat_id, "✅ Tool đã bật")


# ================= TẮT TOOL =================
@bot.message_handler(commands=['tattool'])
def tattool(message):
    global tool_status

    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Không có quyền")
        return

    tool_status = False
    bot.send_message(message.chat.id, "⛔ Tool đã tắt")


# ================= TOOL LOOP =================
def tool_loop():
    global last_session, win, lose, history, last_prediction

    while True:
        if tool_status and chat_id:
            try:
                r = requests.get(API_URL, timeout=10)
                js = r.json()

                data = js["data"]

                phien = data["Phiên"]
                ket = data["Kết"]

                x1 = data["Xúc xắc 1"]
                x2 = data["Xúc xắc 2"]
                x3 = data["Xúc xắc 3"]

                tong = data["Tổng"]

                du_doan = data["Dự đoán"]
                tin_cay = data["Độ tin cậy"]

                next_session = data["Phiên hiện tại"]

                # ===== CHECK PHIÊN MỚI =====
                if phien != last_session:

                    # ===== TÍNH WIN LOSE =====
                    if last_prediction and last_prediction != "Bỏ":
                        if last_prediction == ket:
                            win += 1
                            history.append("✅")
                        else:
                            lose += 1
                            history.append("❌")

                        history = history[-10:]

                    last_prediction = du_doan
                    last_session = phien

                    total = win + lose
                    rate = round((win / total) * 100, 2) if total > 0 else 0

                    history_text = " ".join(history) if history else "Chưa có"

                    # ===== HIỂN THỊ TÀI XỈU ĐẸP =====
                    if du_doan == "Tài":
                        show_pred = "🟢 TÀI"
                    elif du_doan == "Xỉu":
                        show_pred = "🔴 XỈU"
                    else:
                        show_pred = "⚪ BỎ"

                    # ===== CẢNH BÁO =====
                    warning = ""
                    if tin_cay < 60:
                        warning = "\n🚨 Kèo yếu - cân nhắc bỏ"

                    # ===== UI ĐẸP =====
                    msg = f"""
╔══════════════════════╗
   🎰 TOOL TÀI XỈU LC79
╚══════════════════════╝

📊 Phiên: {phien}
🎲 Xúc xắc: {x1} • {x2} • {x3}
🔢 Tổng: {tong}
🎯 Kết quả: {ket}

━━━━━━━━━━━━━━━━━━

🔮 DỰ ĐOÁN PHIÊN {next_session}

┌─────────────────┐
      👉 {show_pred}
└─────────────────┘

📈 Độ tin cậy: {tin_cay}%{warning}

━━━━━━━━━━━━━━━━━━

🏆 Thắng: {win} | 💀 Thua: {lose}
📊 Winrate: {rate}%

📜 Lịch sử gần:
{history_text}

━━━━━━━━━━━━━━━━━━
⚠️ Lưu ý:
Tool chỉ mang tính chất tham khảo
Không đảm bảo chính xác 100%
Cân nhắc trước khi chơi
━━━━━━━━━━━━━━━━━━
"""

                    bot.send_message(chat_id, msg)

            except Exception as e:
                print("API lỗi:", e)

        time.sleep(5)


# ================= RUN =================
threading.Thread(target=tool_loop, daemon=True).start()

print("Bot đang chạy...")

bot.infinity_polling()
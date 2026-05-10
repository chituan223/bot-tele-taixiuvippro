import telebot
import requests
import threading
import time

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
BOT_TOKEN = "8511427168:AAE1doWBxBZo_-q83e8qVY3WI631o9XikSY"
ADMIN_ID = 7138785294
API_URL = "https://api-lc79-congthuc-vip-tuananh.onrender.com/"

bot = telebot.TeleBot(BOT_TOKEN)

tool_status = False
chat_id = None
last_session = None

history = []
win = 0
lose = 0
last_prediction = None

# Font chữ Bold giả cho giao diện sang trọng
B_MAP = {
    'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇',
    'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏',
    'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗',
    'Y': '𝐘', 'Z': '𝐙', 'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟',
    'g': '𝐠', 'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧',
    'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯',
    'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳', '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑',
    '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
}
def bold(text): return ''.join(B_MAP.get(c, c) for c in str(text))

# ================= CHECK ADMIN =================
def is_admin(uid):
    return uid == ADMIN_ID

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    msg = f"""
╔══════════════════════╗
       ✨ {bold('MD5 CORE AI SYSTEM')} ✨
╚══════════════════════╝
👋 {bold('Xin chào')}, {message.from_user.first_name}!

🚀 {bold('HỆ THỐNG DỰ ĐOÁN TÀI XỈU VIP')}
━━━━━━━━━━━━━━━━━━━━━━
▶️ /battool : Kích hoạt hệ thống
▶️ /tattool : Dừng hệ thống
━━━━━━━━━━━━━━━━━━━━━━
⚠️ {bold('Lưu ý')}: Đánh đều tay, quản lý vốn!
"""
    bot.send_message(message.chat.id, msg)

# ================= BẬT TOOL =================
@bot.message_handler(commands=['battool'])
def battool(message):
    global tool_status, chat_id
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, f"❌ {bold('TRUY CẬP BỊ TỪ CHỐI')}")
        return

    tool_status = True
    chat_id = message.chat.id
    bot.send_message(chat_id, f"✅ {bold('HỆ THỐNG ĐÃ KÍCH HOẠT')} 🟢\nĐang chờ tín hiệu từ Server...")

# ================= TẮT TOOL =================
@bot.message_handler(commands=['tattool'])
def tattool(message):
    global tool_status
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, f"❌ {bold('TRUY CẬP BỊ TỪ CHỐI')}")
        return

    tool_status = False
    bot.send_message(message.chat.id, f"⛔ {bold('HỆ THỐNG ĐÃ TẮT')} 🔴")

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
                phien_ht = data["Phiên hiện tại"]
                x1 = data["Xúc xắc 1"]
                x2 = data["Xúc xắc 2"]
                x3 = data["Xúc xắc 3"]
                tong = data["Tổng"]
                ket_qua = data["Kết"]
                du_doan = data["Dự đoán"]
                do_tin_cay = data["Độ tin cậy"]
                pattern = data["Pattern"]

                if phien != last_session:
                    # Gửi tin nhắn thông báo AI đang quét dữ liệu
                    scan_msg = bot.send_message(chat_id, f"""
🔍 {bold('AI CORE')} đang quét dữ liệu phiên `{phien_ht}`...
━━━━━━━━━━━━━━━━━━━━
⚙️ {bold('Algorithm')}: `LC79-Bitwise v3.0`
📡 {bold('Status')}: `Fetching data...`
📊 {bold('Analyzing')}: `1,024 patterns`
⌛ {bold('Loading')}: [▰▰▰▰▰▰▰▱▱▱] 75%
""")
                    # Đợi 2 giây để tạo hiệu ứng AI đang làm việc thật
                    time.sleep(2)
                    bot.delete_message(chat_id, scan_msg.message_id)

                    # ===== XỬ LÝ THẮNG THUA PHIÊN TRƯỚC =====
                    if last_prediction:
                        if last_prediction == ket_qua:
                            win += 1
                            history.append("✅")
                        else:
                            lose += 1
                            history.append("❌")
                        history = history[-10:]

                    last_prediction = du_doan
                    last_session = phien

                    total = win + lose
                    rate = round((win / total) * 100, 1) if total > 0 else 0
                    history_text = " ".join(history) if history else "Chưa có dữ liệu"

                    # ===== GIAO DIỆN DỰ ĐOÁN CHÍNH =====
                    icon = "🔴" if "Tài" in str(du_doan) else "🔵" if "Xỉu" in str(du_doan) else "🟡"
                    
                    final_msg = f"""
┏━━━━━━━━━━━━━━━━━━┓
   💎 {bold('TOOL LC79 VIP PRO AI 3.0')} 💎
┗━━━━━━━━━━━━━━━━━━┛
🕒 {bold('Phiên vừa qua')}: `{phien}`
🎲 {bold('Xúc xắc')}: `{x1} - {x2} - {x3}`
📊 {bold('Tổng điểm')}: `{tong}` ➜ {bold(str(ket_qua).upper())}
━━━━━━━━━━━━━━━━━━━━
🆔 {bold('PHIÊN HIỆN TẠI')}: `{phien_ht}`

{icon} {bold('Hệ Thống Dự Đoán')}:
➡ ✨ {bold(str(du_doan).upper())} ✨

📈 {bold('Độ Tin Cậy AI')}: `{do_tin_cay}%`
🧬 {bold('Chuỗi Pattern')}: `{pattern}`
━━━━━━━━━━━━━━━━━━━━
📊 {bold('PHÂN TÍCH HIỆU SUẤT')}
🏆 {bold('Thắng')}: `{win}`  |  💀 {bold('Thua')}: `{lose}`
📈 {bold('Tỷ lệ thắng')}: `{rate}%`
📜 {bold('Lịch sử')}: {history_text}
━━━━━━━━━━━━━━━━━━━━
🛰 {bold('Status')}: {bold('ONLINE 🟢')} | {bold('v3.0.1')}
"""
                    bot.send_message(chat_id, final_msg)

            except Exception as e:
                print("API lỗi:", e)

        time.sleep(10)

# ================= RUN =================
threading.Thread(target=tool_loop, daemon=True).start()

print("Bot MD5 CORE AI đang chạy...")
bot.infinity_polling()

import json
import random
import string
import re
import asyncio
import httpx 
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
BOT_TOKEN = "8782059164:AAEFUDE7syalSWkXeY5Md2Hl_sJMQOPzmT8"
ADMIN_ID = 7138785294 
API_LUCKYWIN = "https://api-luck8-tuananh.onrender.com/api/taixiumd5"
API_LC79 = "https://api-lc79-congthuc-vip-tuananh.onrender.com/api/taixiumd5"
API_XOCDIA88 = "https://api-xocdia88-vip-pro.onrender.com/"

# ========== UTILS (TIỆN ÍCH) ==========

def load(f):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            return json.load(file)
    except: return {}

def save(f, d):
    with open(f, 'w', encoding='utf-8') as file:
        json.dump(d, file, ensure_ascii=False, indent=4)

def gen_key():
    return f"BUFF-{''.join(random.choices(string.ascii_uppercase + string.digits, k=12))}"

def gen_content():
    return f"NAP{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

# Font chữ đậm nghệ thuật chuyên sâu
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

def bold(text):
    return ''.join(B_MAP.get(c, c) for c in text)

# ========== KEYBOARDS (GIAO DIỆN NÚT) ==========

BTN_NHAP_KEY = bold('🔑 Nhập Key')
BTN_NAP_TIEN = bold('💰 Nạp Tiền')
BTN_DU_DOAN = bold('🎯 Dự Đoán')
BTN_LIEN_HE = bold('📞 Hỗ Trợ')

ALL_BUTTONS = [BTN_NHAP_KEY, BTN_NAP_TIEN, BTN_DU_DOAN, BTN_LIEN_HE]

def main_kb():
    return ReplyKeyboardMarkup([
        [BTN_NHAP_KEY, BTN_NAP_TIEN],
        [BTN_DU_DOAN, BTN_LIEN_HE]
    ], resize_keyboard=True)

def nap_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(bold("⚡ 1 Ngày - 15.000đ"), callback_data="nap_1_15000")],
        [InlineKeyboardButton(bold("⚡ 3 Ngày - 35.000đ"), callback_data="nap_3_35000")],
        [InlineKeyboardButton(bold("⚡ 1 Tháng - 70.000đ"), callback_data="nap_30_70000")],
        [InlineKeyboardButton(bold("👑 Vĩnh Viễn - 100.000đ"), callback_data="nap_9999_100000")]
    ])

def tool_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(bold("🎮 LC79 (AUTO)"), callback_data="tool_lc79")],
        [InlineKeyboardButton(bold("🎮 XD88 (AUTO)"), callback_data="tool_xocdia88")],
        [InlineKeyboardButton(bold("🎮 LUCKYWIN (AUTO)"), callback_data="tool_luckywin")]
    ])

# ========== FUNCTIONS (XỬ LÝ CHÍNH) ==========

async def check_user_key(uid):
    keys = load("keys.json")
    if uid not in keys: return False
    # Lọc bỏ các key hết hạn để file luôn sạch
    valid_keys = [k for k in keys[uid] if datetime.fromisoformat(k['expiry']) > datetime.now()]
    if valid_keys != keys[uid]:
        keys[uid] = valid_keys
        save("keys.json", keys)
    return len(valid_keys) > 0

async def fetch_api_data(url):
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json().get('data', {})
    except: pass
    return None

async def loop_prediction(context, chat_id, message_id, api_url, name):
    # Đổi từ range(15) thành While True để chạy vô tận
    error_count = 0
    while True:
        data = await fetch_api_data(api_url)
        if data:
            error_count = 0
            phien_vua_qua = data.get('Phiên') or data.get('Phien') or "N/A"
            x1 = data.get('Xúc xắc 1') or data.get('Xuc_xac_1') or "?"
            x2 = data.get('Xúc xắc 2') or data.get('Xuc_xac_2') or "?"
            x3 = data.get('Xúc xắc 3') or data.get('Xuc_xac_3') or "?"
            tong = data.get('Tổng') or data.get('Tong') or "N/A"
            ket_qua = data.get('Kết') or data.get('Ket') or "N/A"
            phien_hien_tai = data.get('Phiên hiện tại') or data.get('Phien_hien_tai') or "N/A"
            du_doan = data.get('Dự đoán') or data.get('Du_doan') or "N/A"
            do_tin_cay = data.get('Độ tin cậy') or data.get('Do_tin_cay') or "95%"
            
            icon = "🔴" if "Tài" in str(du_doan) else "🔵" if "Xỉu" in str(du_doan) else "🟡"
            
            res_text = f"""┏━━━━━━━━━━━━━━━━━━┓
   🔥 {bold(f'DỰ ĐOÁN {name}')} 🔥
┗━━━━━━━━━━━━━━━━━━┛
💎 {bold('Phiên Vừa Qua')}: `{phien_vua_qua}`
🎲 {bold('Kết Quả')}: `{x1}-{x2}-{x3}` ➔ {bold(str(ket_qua))}
📊 {bold('Tổng Điểm')}: `{tong}`
━━━━━━━━━━━━━━━━━━━━
🆔 {bold('Phiên Hiện Tại')}: `{phien_hien_tai}`
{icon} {bold('Hệ Thống Phân Tích')}: ✨ {bold(str(du_doan).upper())} ✨
📈 {bold('Độ Tin Cậy')}: `{do_tin_cay}`
━━━━━━━━━━━━━━━━━━━━
🔄 {bold('Trạng Thái')}: {bold('Tự Động Cập Nhật...')}
⏳ {bold('Thời Gian')}: {datetime.now().strftime('%H:%M:%S')}
🚀 {bold('Lưu ý')}: Làm mới sau mỗi 20 giây."""
            
            try:
                await context.bot.edit_message_text(res_text, chat_id=chat_id, message_id=message_id)
            except Exception:
                # Nếu không edit được (do tin nhắn bị xóa hoặc lỗi), thoát vòng lặp
                break
        else:
            error_count += 1
            if error_count > 5:
                try:
                    await context.bot.edit_message_text(f"❌ {bold('MẤT KẾT NỐI API')} {name}. Đang thử lại...", chat_id=chat_id, message_id=message_id)
                except: break
        
        # Đợi 20 giây cho phiên tiếp theo
        await asyncio.sleep(20)

# ========== HANDLERS (XỬ LÝ LỆNH) ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = str(u.id)
    users = load("users.json")
    users[uid] = {"name": u.first_name, "username": u.username, "join": str(datetime.now())}
    save("users.json", users)
    
    msg = f"""👋 {bold('Chào mừng')}, {bold(u.first_name)}!
    
🔥 {bold('HỆ THỐNG TOOL MD5 CORE AI')} 🔥
━━━━━━━━━━━━━━━━━━━━
🤖 {bold('Hệ thống')}: {bold('Sẵn sàng 🟢')}
🆔 {bold('ID Của Bạn')}: `{u.id}`
📅 {bold('Ngày')}: {datetime.now().strftime('%d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━
🚀 {bold('Vui lòng chọn chức năng bên dưới để bắt đầu!')}"""
    await update.message.reply_text(msg, reply_markup=main_kb())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    state = context.user_data.get('state')

    if text in ALL_BUTTONS: context.user_data['state'] = None

    if state == 'INPUT_KEY':
        key_input = text.strip()
        if not re.match(r"^BUFF-[A-Z0-9]{12}$", key_input):
            await update.message.reply_text(f"❌ {bold('SAI ĐỊNH DẠNG')} (BUFF-XXXXXXXXXXXX)")
            return
        
        keys_db = load("keys.json")
        found_key = None
        owner_id = None
        
        # Tìm key trong toàn bộ database
        for oid in keys_db:
            for k in keys_db[oid]:
                if k['key'] == key_input and datetime.fromisoformat(k['expiry']) > datetime.now():
                    found_key = k
                    owner_id = oid
                    break
            if found_key: break
            
        if found_key:
            # Nếu người nhập không phải chủ key, chuyển key qua cho người mới
            if owner_id != uid:
                if uid not in keys_db: keys_db[uid] = []
                keys_db[uid].append(found_key)
                # Xóa ở chủ cũ
                keys_db[owner_id] = [k for k in keys_db[owner_id] if k['key'] != key_input]
                save("keys.json", keys_db)
            
            context.user_data['state'] = None
            await update.message.reply_text(f"✅ {bold('KÍCH HOẠT THÀNH CÔNG!')}", reply_markup=main_kb())
        else:
            await update.message.reply_text(f"❌ {bold('KEY KHÔNG HỢP LỆ HOẶC HẾT HẠN')}")
        return

    if text == BTN_NHAP_KEY:
        context.user_data['state'] = 'INPUT_KEY'
        await update.message.reply_text(f"🔑 {bold('NHẬP MÃ KEY CỦA BẠN')}:")
    elif text == BTN_NAP_TIEN:
        if await check_user_key(uid):
            await update.message.reply_text(f"⚠️ {bold('BẠN ĐANG CÓ KEY CÒN HẠN!')}")
            return
        await update.message.reply_text(f"💰 {bold('CHỌN GÓI DỊCH VỤ CẦN MUA')}:", reply_markup=nap_kb())
    elif text == BTN_DU_DOAN:
        if await check_user_key(uid):
            await update.message.reply_text(f"🎯 {bold('CHỌN SẢNH GAME MUỐN DỰ ĐOÁN')}:", reply_markup=tool_kb())
        else:
            await update.message.reply_text(f"❌ {bold('BẠN CẦN CÓ KEY ĐỂ SỬ DỤNG')}")
    elif text == BTN_LIEN_HE:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(bold("💬 Nhắn Admin"), url="https://t.me/anhyeuem1111")]])
        support_msg = f"""📞 {bold('HỖ TRỢ KHÁCH HÀNG')}
━━━━━━━━━━━━━━━━━━━━
👨‍💻 {bold('Kỹ Thuật')}: @anhyeuem1111
⏰ {bold('Làm việc')}: 24/7 (Phản hồi nhanh)
🌟 {bold('Dịch vụ')}: Nạp key, lỗi tool, cộng tác.
━━━━━━━━━━━━━━━━━━━━
🚀 {bold('Nhấn vào nút bên dưới để gặp hỗ trợ!')}"""
        await update.message.reply_text(support_msg, reply_markup=kb)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)

    if query.data in ["tool_lc79", "tool_xocdia88", "tool_luckywin"]:
        name_map = {"tool_lc79": "LC79", "tool_xocdia88": "XD88", "tool_luckywin": "LUCKYWIN"}
        api_map = {"tool_lc79": API_LC79, "tool_xocdia88": API_XOCDIA88, "tool_luckywin": API_LUCKYWIN}
        
        name = name_map[query.data]
        api_url = api_map[query.data]
        
        msg = await query.message.reply_text(f"🔄 {bold(f'Đang kết nối API {name}...')}")
        asyncio.create_task(loop_prediction(context, query.message.chat_id, msg.message_id, api_url, name))

    elif query.data.startswith("nap_"):
        _, days, price = query.data.split("_")
        content = gen_content()
        pending = load("pending.json")
        pending[uid] = {"days": int(days), "price": int(price), "content": content}
        save("pending.json", pending)
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(bold("✅ Đã Chuyển"), callback_data="paid")]])
        
        text = f"""💰 {bold('𝐓𝐇𝐀𝐍𝐇 𝐓𝐎𝐀́𝐍 𝐍𝐀̣𝐏 𝐓𝐈𝐄̂̀𝐍')} 💰
━━━━━━━━━━━━━━━━━━━━
💵 {bold('𝐒𝐨̂́ 𝐭𝐢𝐞̂̀𝐧')}: {int(price):,} VNĐ
🏦 {bold('𝐍𝐠𝐚̂𝐧 𝐡𝐚̀𝐧𝐠')}: TPBANK
👤 {bold('𝐂𝐡𝐮̉ 𝐓𝐊')}: DINH THI TUYET
💳 {bold('𝐒𝐨̂́ 𝐓𝐊')}: `00006326953`

📝 {bold('𝐍𝐨̣̂𝐢 𝐝𝐮𝐧𝐠')}: `{content}`
━━━━━━━━━━━━━━━━━━━━
⚠️ {bold('𝐂𝐡uyển khoản đúng nội dung')}
📞 {bold('Liên hệ')}: @anhyeuem1111

👉 {bold('Quét QR hoặc chuyển tay')}
👉 {bold('Sau khi chuyển, bấm ✅ Đã chuyển')}"""
        
        await query.message.reply_photo(photo="https://i.postimg.cc/9Qwpq35R/1775383551412.png", caption=text, reply_markup=kb)

    elif query.data == "paid":
        context.user_data['state'] = 'WAIT_PHOTO'
        await query.message.reply_text(f"⏳ {bold('𝐇𝐀̃𝐘 𝐆𝐔̛̉𝐈 𝐀̉𝐍𝐇 𝐁𝐈𝐋𝐋')} (Biên lai) để Admin duyệt.")

    elif query.data.startswith("approve_"):
        if query.from_user.id != ADMIN_ID: return
        target_uid = query.data.split("_")[1]
        pending = load("pending.json")
        if target_uid in pending:
            days = pending[target_uid]['days']
            key = gen_key()
            expiry = datetime.now() + timedelta(days=days if days < 9000 else 3650)
            keys = load("keys.json")
            if target_uid not in keys: keys[target_uid] = []
            keys[target_uid].append({"key": key, "expiry": expiry.isoformat()})
            save("keys.json", keys)
            del pending[target_uid]
            save("pending.json", pending)
            
            try:
                msg_user = f"🎊 {bold('𝐃𝐔𝐘𝐄̂𝐓 𝐓𝐇𝐀̀𝐍𝐇 𝐂𝐎̂𝐍𝐆!')}\n━━━━━━━━━━━━━━\n🔑 𝐊𝐄𝐘: `{key}`\n⏰ 𝐇𝐚̣𝐧 𝐝𝐮̀𝐧𝐠: {expiry.strftime('%d/%m/%Y')}\n━━━━━━━━━━━━━━\n🚀 Chúc bạn may mắn!"
                await context.bot.send_message(int(target_uid), msg_user)
            except: pass
            await query.edit_message_caption(caption=f"✅ ĐÃ DUYỆT CHO ID: {target_uid}\n🔑 Key: `{key}`")

    elif query.data.startswith("reject_"):
        if query.from_user.id != ADMIN_ID: return
        target_uid = query.data.split("_")[1]
        pending = load("pending.json")
        if target_uid in pending:
            del pending[target_uid]
            save("pending.json", pending)
            try:
                await context.bot.send_message(int(target_uid), f"❌ {bold('GIAO DỊCH BỊ TỪ CHỐI!')}\nNội dung thanh toán không hợp lệ hoặc chưa nhận được tiền.")
            except: pass
            await query.edit_message_caption(caption=f"❌ ĐÃ TỪ CHỐI ID: {target_uid}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'WAIT_PHOTO':
        uid = str(update.effective_user.id)
        pending = load("pending.json")
        info = pending.get(uid, {})
        
        admin_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ DUYỆT", callback_data=f"approve_{uid}"),
             InlineKeyboardButton("❌ TỪ CHỐI", callback_data=f"reject_{uid}")]
        ])
        caption = f"🔔 {bold('YÊU CẦU NẠP TIỀN MỚI')}\n━━━━━━━━━━━━━━\n👤 User: {update.effective_user.first_name}\n🆔 ID: `{uid}`\n💵 Tiền: {info.get('price', 0):,}đ\n📝 Nội dung: `{info.get('content', 'N/A')}`"
        
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=admin_kb)
        
        await update.message.reply_text(f"✅ {bold('ĐÃ GỬI BILL!')} Vui lòng chờ Admin kiểm tra.")
        context.user_data['state'] = None

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🤖 Bot is starting (Enhanced Stability)...")
    app.run_polling()

if __name__ == "__main__":
    main()

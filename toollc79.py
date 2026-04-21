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
BOT_TOKEN = "8511427168:AAE1doWBxBZo_-q83e8qVY3WI631o9XikSY"
ADMIN_ID = 7138785294 
API_LUCKYWIN = "https://api-luck8-tuananh.onrender.com/api/taixiumd5"
API_LC79 = "https://api-lc79-congthuc-vip-tuananh.onrender.com/api/taixiumd5"
API_XOCDIA88 = "https://api-xocdia88-vip-pro.onrender.com/api/taixiumd5"

# --- CẤU HÌNH FIREBASE (DÙNG REST API) ---
FIREBASE_URL = "https://tuanchimto-37c66-default-rtdb.firebaseio.com"

# ========== FIREBASE ENGINE (KHÔNG DÙNG JSON FILE) ==========

async def fb_get(path):
    """Lấy dữ liệu từ Firebase"""
    url = f"{FIREBASE_URL}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else {}
            return {}
    except: return {}

async def fb_set(path, data):
    """Ghi đè dữ liệu vào Firebase"""
    url = f"{FIREBASE_URL}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.put(url, json=data)
    except: pass

async def fb_update(path, data):
    """Cập nhật dữ liệu vào Firebase"""
    url = f"{FIREBASE_URL}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.patch(url, json=data)
    except: pass

async def fb_delete(path):
    """Xóa dữ liệu trên Firebase"""
    url = f"{FIREBASE_URL}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.delete(url)
    except: pass

# ========== UTILS (TIỆN ÍCH) ==========

def gen_key():
    return f"BUFF-{''.join(random.choices(string.ascii_uppercase + string.digits, k=12))}"

def gen_content():
    return f"NAP{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

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
def bold(text): return ''.join(B_MAP.get(c, c) for c in text)

# ========== KEYBOARDS (GIAO DIỆN NÚT) ==========

BTN_NHAP_KEY = bold('🔑 Nhập Key')
BTN_NAP_TIEN = bold('💰 Nạp Tiền')
BTN_DU_DOAN = bold('🎯 Dự Đoán')
BTN_LIEN_HE = bold('📞 Hỗ Trợ')
ALL_BUTTONS = [BTN_NHAP_KEY, BTN_NAP_TIEN, BTN_DU_DOAN, BTN_LIEN_HE]

def main_kb():
    return ReplyKeyboardMarkup([[BTN_NHAP_KEY, BTN_NAP_TIEN], [BTN_DU_DOAN, BTN_LIEN_HE]], resize_keyboard=True)

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
    # Luôn lấy dữ liệu mới nhất từ Firebase để kiểm tra
    user_keys = await fb_get(f"keys/{uid}")
    if not user_keys or not isinstance(user_keys, list): return False
    now = datetime.now()
    valid_keys = [k for k in user_keys if datetime.fromisoformat(k['expiry']) > now]
    # Cập nhật lại nếu có key hết hạn để làm sạch DB
    if len(valid_keys) != len(user_keys):
        await fb_set(f"keys/{uid}", valid_keys)
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
            do_tin_cay = data.get('Độ tin cậy') or data.get('Do_tin_cay') or "N/A"
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
            except: break
        else:
            error_count += 1
            if error_count > 5:
                try: await context.bot.edit_message_text(f"❌ {bold('MẤT KẾT NỐI API')} {name}.", chat_id=chat_id, message_id=message_id)
                except: break
        await asyncio.sleep(20)

# ========== HANDLERS (XỬ LÝ LỆNH) ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = str(u.id)
    await fb_update(f"users/{uid}", {"name": u.first_name, "username": u.username, "join": str(datetime.now())})
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
        
        all_keys_db = await fb_get("keys")
        found_key, owner_id = None, None
        
        if all_keys_db:
            for oid, k_list in all_keys_db.items():
                if not isinstance(k_list, list): continue
                for k in k_list:
                    if k['key'] == key_input and datetime.fromisoformat(k['expiry']) > datetime.now():
                        found_key, owner_id = k, oid
                        break
                if found_key: break
            
        if found_key:
            if owner_id != uid:
                # Chuyển quyền sở hữu key sang người nhập mới
                user_keys = await fb_get(f"keys/{uid}")
                if not isinstance(user_keys, list): user_keys = []
                user_keys.append(found_key)
                await fb_set(f"keys/{uid}", user_keys)
                
                # Xóa key ở người cũ
                old_owner_keys = [k for k in all_keys_db[owner_id] if k['key'] != key_input]
                await fb_set(f"keys/{owner_id}", old_owner_keys)
            
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
        msg = await query.message.reply_text(f"🔄 {bold(f'Đang kết nối API {name_map[query.data]}...')}")
        asyncio.create_task(loop_prediction(context, query.message.chat_id, msg.message_id, api_map[query.data], name_map[query.data]))

    elif query.data.startswith("nap_"):
        _, days, price = query.data.split("_")
        content = gen_content()
        await fb_set(f"pending/{uid}", {"days": int(days), "price": int(price), "content": content})
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(bold("✅ Đã Chuyển"), callback_data="paid")]])
        
        text = f"""💰 {bold('𝐓𝐇𝐀𝐍𝐇 𝐓𝐎𝐀́𝐍 𝐍𝐀̣𝐏 𝐓𝐈𝐄̂̀𝐍')} 💰
━━━━━━━━━━━━━━━━━━━━
💵 {bold('𝐒𝐨̂́ 𝐭𝐢𝐞̂̀𝐧')}: {int(price):,} VNĐ
🏦 {bold('𝐍𝐠𝐚̂𝐧 𝐡𝐚̀ n 𝐠')}: TPBANK
👤 {bold('𝐂𝐡𝐮̉ 𝐓𝐊')}: DINH THI TUYET
💳 {bold('𝐒𝐨̂́ 𝐓𝐊')}: `00006326953`

📝 {bold('𝐍𝐨̣̂i 𝐝𝐮n𝐠')}: `{content}`
━━━━━━━━━━━━━━━━━━━━
⚠️ {bold('𝐂𝐡uy𝐞̂̉ n 𝐤𝐡𝐨𝐚̉n đ𝐮́n𝐠 𝐧𝐨̣̂i 𝐝𝐮n𝐠')}
📞 {bold('𝐋𝐢𝐞̂ n 𝐡𝐞̣̂')}: @anhyeuem1111"""

        await query.message.reply_photo(
            photo="https://i.postimg.cc/9Qwpq35R/1775383551412.png", 
            caption=text, 
            reply_markup=kb
        )

    elif query.data == "paid":
        context.user_data['state'] = 'WAIT_PHOTO'
        await query.message.reply_text(f"⏳ {bold('𝐇𝐀̃𝐘 𝐆𝐔̛̉𝐈 𝐀̉𝐍𝐇 𝐁𝐈𝐋𝐋')} để Admin duyệt.")

    elif query.data.startswith("approve_"):
        if query.from_user.id != ADMIN_ID: return
        target_uid = query.data.split("_")[1]
        p_info = await fb_get(f"pending/{target_uid}")
        if p_info:
            new_key_code = gen_key()
            days_to_add = int(p_info['days'])
            expiry_date = datetime.now() + timedelta(days=days_to_add if days_to_add < 9000 else 3650)
            
            # Lấy list key hiện tại của user
            current_keys = await fb_get(f"keys/{target_uid}")
            if not isinstance(current_keys, list):
                current_keys = []
            
            current_keys.append({
                "key": new_key_code, 
                "expiry": expiry_date.isoformat(),
                "created_at": datetime.now().isoformat()
            })
            
            # Cập nhật lên Firebase
            await fb_set(f"keys/{target_uid}", current_keys)
            await fb_delete(f"pending/{target_uid}")
            
            try:
                msg_to_user = f"""🎊 {bold('𝐃𝐔𝐘𝐄̂𝐓 𝐓𝐇𝐀̀𝐍𝐇 𝐂𝐎̂𝐍𝐆!')}
━━━━━━━━━━━━━━━━━━━━
🔑 𝐊𝐄𝐘: `{new_key_code}`
⏳ 𝐇𝐚̣ hạn dùng: {expiry_date.strftime('%d/%m/%Y %H:%M')}
🚀 𝐇𝐚̃𝐲 𝐧𝐡𝐚̣̂𝐩 𝐤𝐞𝐲 đ𝐞̂̉ 𝐬𝐮̛̉ 𝐝𝐮̣𝐧𝐠!"""
                await context.bot.send_message(int(target_uid), msg_to_user)
            except: pass
            
            await query.edit_message_caption(caption=f"✅ ĐÃ DUYỆT CHO ID: {target_uid}\n🔑 Key: `{new_key_code}`\n📅 Hạn: {expiry_date.strftime('%d/%m/%Y')}")

    elif query.data.startswith("reject_"):
        if query.from_user.id != ADMIN_ID: return
        target_uid = query.data.split("_")[1]
        await fb_delete(f"pending/{target_uid}")
        try: await context.bot.send_message(int(target_uid), f"❌ {bold('GIAO DỊCH BỊ TỪ CHỐI!')}")
        except: pass
        await query.edit_message_caption(caption=f"❌ ĐÃ TỪ CHỐI ID: {target_uid}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'WAIT_PHOTO':
        uid = str(update.effective_user.id)
        info = await fb_get(f"pending/{uid}")
        if not info:
            await update.message.reply_text("❌ Lỗi: Không tìm thấy yêu cầu nạp. Vui lòng bấm Nạp Tiền lại.")
            return
            
        admin_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ DUYỆT", callback_data=f"approve_{uid}"), 
             InlineKeyboardButton("❌ TỪ CHỐI", callback_data=f"reject_{uid}")]
        ])
        
        caption = f"🔔 {bold('YÊU CẦU MỚI')}\n👤 User: {update.effective_user.first_name}\n🆔 ID: `{uid}`\n💵 Tiền: {info.get('price', 0):,}đ\n📝 Nội dung: `{info.get('content', 'N/A')}`"
        
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=admin_kb)
        await update.message.reply_text(f"✅ {bold('ĐÃ GỬI BILL!')} Vui lòng chờ Admin.")
        context.user_data['state'] = None

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot Firebase Cloud is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()

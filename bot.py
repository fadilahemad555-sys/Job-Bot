import os
import json
from telegram import Bot

# الكلمات اللي عايز تبحث عنها
KEYWORDS = ["احتاج محرر فيديو", "مطلوب مونتير", "video editor needed"]
OFFSET_FILE = "offset.json"

# دالة لقرآة آخر تحديث
def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            return json.load(f).get('offset', 0)
    return 0

# دالة لحفظ آخر تحديث
def save_offset(offset):
    with open(OFFSET_FILE, 'w') as f:
        json.dump({'offset': offset}, f)

# تشغيل البوت
token = os.getenv("BOT_TOKEN")
admin = os.getenv("CHAT_ID")
if not token or not admin:
    exit()

bot = Bot(token)
offset = load_offset()
updates = bot.get_updates(offset=offset)

for upd in updates:
    if upd.message and upd.message.text:
        if any(kw.lower() in upd.message.text.lower() for kw in KEYWORDS):
            bot.send_message(chat_id=admin, text=f"🔔 لقينا: {upd.message.text}")

if updates:
    save_offset(updates[-1].update_id + 1)
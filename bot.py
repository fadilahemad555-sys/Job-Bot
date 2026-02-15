import os
import json
import logging
from telegram import Bot

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الكلمات المفتاحية
KEYWORDS = [
    "احتاج محرر فيديو",
    "مطلوب مونتير",
    "video editor needed",
    "need video editor"
]

OFFSET_FILE = "offset.json"

def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, 'r') as f:
            data = json.load(f)
            return data.get('offset', 0)
    return 0

def save_offset(offset):
    with open(OFFSET_FILE, 'w') as f:
        json.dump({'offset': offset}, f)

def contains_keyword(text):
    if not text:
        return False
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False

def main():
    token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("CHAT_ID")

    if not token or not admin_id:
        logger.error("تأكد من تعيين BOT_TOKEN و CHAT_ID في Secrets")
        return

    bot = Bot(token)
    offset = load_offset()
    logger.info(f"بدء التشغيل بالـ offset: {offset}")

    try:
        updates = bot.get_updates(offset=offset, timeout=10, allowed_updates=['message'])
        if not updates:
            logger.info("لا توجد رسائل جديدة")
            return

        for update in updates:
            if update.message and update.message.text:
                msg = update.message
                text = msg.text
                if contains_keyword(text):
                    alert = (
                        f"🔔 تم العثور على كلمة مفتاحية!\n"
                        f"من: {msg.from_user.first_name} (@{msg.from_user.username})\n"
                        f"النص: {text}\n"
                        f"الدردشة: {msg.chat_id}"
                    )
                    logger.info(alert)
                    bot.send_message(chat_id=admin_id, text=alert)

        # تحديث offset
        last_id = updates[-1].update_id
        save_offset(last_id + 1)
        logger.info(f"تم حفظ offset الجديد: {last_id + 1}")

    except Exception as e:
        logger.exception(f"خطأ: {e}")

if __name__ == "__main__":
    main()
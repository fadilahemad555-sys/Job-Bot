import os
import requests
import time

# الكلمات المفتاحية بعدة لغات وصيغ (عدل أو أضف كما تريد)
KEYWORDS = [
    # العربية
    "أبحث عن محرر فيديو",
    "أحتاج محرر فيديو",
    "مطلوب مونتير",
    "أبحث عن مونتير",
    "احتاج مونتير",
    "بدي مونتير",
    "ابحث عن شخص يعدل فيديو",
    # الإنجليزية
    "looking for a video editor",
    "need a video editor",
    "hiring video editor",
    "video editor needed",
    "seeking video editor",
    "want a video editor",
    "need someone to edit video"
]

# إعدادات تليجرام من الأسرار
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    """إرسال رسالة إلى تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        r = requests.post(url, json=payload)
        return r.status_code == 200
    except:
        return False

def search_reddit():
    """البحث في Reddit عن الكلمات المفتاحية"""
    found_links = []  # لتجنب التكرار
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for kw in KEYWORDS:
        try:
            # البحث في Reddit (آخر 10 نتائج)
            url = f"https://www.reddit.com/search.json?q={kw}&sort=new&limit=10"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                posts = data.get('data', {}).get('children', [])
                for post in posts:
                    p = post['data']
                    title = p['title']
                    permalink = p['permalink']
                    full_url = f"https://reddit.com{permalink}"
                    if full_url not in found_links:
                        found_links.append(full_url)
                        # إرسال التنبيه
                        msg = f"🔔 <b>{kw}</b>\n\n{title}\n\n🔗 {full_url}"
                        send_telegram(msg)
                        time.sleep(1)  # مهلة بين الرسائل
        except Exception as e:
            print(f"خطأ: {e}")
            continue

# يمكنك إضافة دوال بحث لمواقع أخرى هنا (مثل تويتر، لينكد إن...) لاحقاً

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("تأكد من تعيين BOT_TOKEN و CHAT_ID في الأسرار")
        exit()
    send_telegram("🚀 بدء البحث عن فرص تحرير الفيديو...")
    search_reddit()
    send_telegram("✅ انتهى البحث.")
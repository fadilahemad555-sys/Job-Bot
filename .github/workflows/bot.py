import os
import requests
import time
import json

# إعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_FILE = "sent_links.json"

# الكلمات المفتاحية العامة (أضف ما تريد)
KEYWORDS = [
    "video editor", "edit video", "video editing", "looking for editor",
    "need video editor", "hiring video editor", "video production",
    "محرر فيديو", "مونتير", "مونتاج", "فيديو"
]

# قائمة المصادر (يمكنك إضافة المزيد)
SOURCES = {
    "reddit": {
        "subreddits": ["forhire", "jobs", "freelance", "videoediting", "videography"],
        "url": "https://www.reddit.com/r/{sub}/search.json?q={kw}&restrict_sr=on&sort=new&limit=5"
    },
    # يمكنك إضافة تويتر أو غيره هنا لاحقاً
}

def load_sent():
    """تحميل الروابط المرسلة سابقاً"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_sent(sent_set):
    """حفظ الروابط المرسلة"""
    with open(SENT_FILE, 'w') as f:
        json.dump(list(sent_set), f)

def send_telegram(message):
    """إرسال رسالة إلى تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("فشل الإرسال:", e)

def search_reddit(sent_links):
    """البحث في ريديت"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    new_found = False
    for sub in SOURCES["reddit"]["subreddits"]:
        for kw in KEYWORDS:
            try:
                url = SOURCES["reddit"]["url"].format(sub=sub, kw=kw)
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    posts = data.get('data', {}).get('children', [])
                    for post in posts:
                        p = post['data']
                        title = p['title']
                        permalink = p['permalink']
                        full_url = f"https://reddit.com{permalink}"
                        if full_url not in sent_links:
                            sent_links.add(full_url)
                            msg = f"🔔 <b>r/{sub}</b> - {kw}\n\n{title}\n\n🔗 {full_url}"
                            send_telegram(msg)
                            new_found = True
                            time.sleep(1)
            except Exception as e:
                print(f"خطأ في {sub}/{kw}: {e}")
                continue
    return new_found

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("تأكد من تعيين BOT_TOKEN و CHAT_ID")
        exit()

    sent_links = load_sent()
    send_telegram("🚀 بدء البحث المتقدم...")
    found = search_reddit(sent_links)
    if found:
        save_sent(sent_links)
        send_telegram(f"✅ تم العثور على {len(sent_links)} رابط جديد.")
    else:
        send_telegram("✅ لم يتم العثور على نتائج جديدة هذه المرة.")

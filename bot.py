import os
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

# ========== الإعدادات الأساسية ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_FILE = "sent_links.json"

# ========== كلمات مفتاحية متقدمة (كما في Google Alerts) ==========
KEYWORDS_QUERY = '''
("looking for" OR "need" OR "wanted" OR "seeking" OR "searching for" OR 
"مرحبا أحتاج محرر فيديو" OR "أحتاج محرر فيديو" OR "لدي بعض الفيديوهات أريد تعديلها") 
("video editor" OR "reels editor" OR "short form editor" OR "create video from text" OR 
"محرر فيديو" OR "محرر ريلز") 
("DM me" OR "contact me" OR "send DM" OR "shoot me a DM" OR "راسلني" OR "الخاص" OR "تواصل معي") 
(site:twitter.com OR site:facebook.com OR site:instagram.com OR site:youtube.com OR site:tiktok.com) 
-"job" -"hiring" -"career" -"vacancy" -"apply" -"recruitment" -"linkedin" -"indeed" -"fiverr" -"upwork" -"freelancer" -"guru" -"glassdoor" -"bayt"
'''

# استخراج الكلمات المفتاحية من الاستعلام (تقريباً)
KEYWORDS = [
    "looking for video editor",
    "need video editor",
    "wanted video editor",
    "seeking video editor",
    "searching for video editor",
    "مرحبا أحتاج محرر فيديو",
    "أحتاج محرر فيديو",
    "لدي بعض الفيديوهات أريد تعديلها",
    "video editor",
    "reels editor",
    "short form editor",
    "create video from text",
    "محرر فيديو",
    "محرر ريلز"
]

# كلمات الاستبعاد
EXCLUDE_WORDS = ["job", "hiring", "career", "vacancy", "apply", "recruitment", 
                 "linkedin", "indeed", "fiverr", "upwork", "freelancer", "guru", 
                 "glassdoor", "bayt"]

# المواقع المستهدفة
SITES = ["twitter.com", "facebook.com", "instagram.com", "youtube.com", "tiktok.com"]

# ========== دوال مساعدة ==========
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_sent(sent_set):
    with open(SENT_FILE, 'w') as f:
        json.dump(list(sent_set), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("فشل الإرسال:", e)

def is_excluded(text):
    text_lower = text.lower()
    for word in EXCLUDE_WORDS:
        if word in text_lower:
            return True
    return False

# ========== البحث في ريديت (مصدر إضافي) ==========
def search_reddit(sent_links):
    headers = {'User-Agent': 'Mozilla/5.0'}
    subreddits = ["forhire", "jobs", "freelance", "videoediting", "videography"]
    found = False
    for sub in subreddits:
        for kw in KEYWORDS:
            try:
                url = f"https://www.reddit.com/r/{sub}/search.json?q={kw}&restrict_sr=on&sort=new&limit=5"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    posts = data.get('data', {}).get('children', [])
                    for post in posts:
                        p = post['data']
                        title = p['title']
                        permalink = p['permalink']
                        full_url = f"https://reddit.com{permalink}"
                        if full_url not in sent_links and not is_excluded(title):
                            sent_links.add(full_url)
                            msg = f"🔴 <b>Reddit r/{sub}</b>\n\n{title}\n\n🔗 {full_url}"
                            send_telegram(msg)
                            found = True
                            time.sleep(1)
            except:
                continue
    return found

# ========== البحث في تويتر عبر Nitter ==========
def search_twitter(sent_links):
    headers = {'User-Agent': 'Mozilla/5.0'}
    found = False
    for kw in KEYWORDS:
        try:
            url = f"https://nitter.net/search?q={kw}&f=tweets"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                tweets = soup.find_all('div', class_='tweet-content')[:10]
                for tweet in tweets:
                    text = tweet.get_text(strip=True)
                    link_tag = tweet.find_parent('a', href=True)
                    if link_tag:
                        link = "https://nitter.net" + link_tag['href']
                        if link not in sent_links and not is_excluded(text):
                            sent_links.add(link)
                            msg = f"🐦 <b>تويتر</b>\n\n{text[:200]}...\n\n🔗 {link}"
                            send_telegram(msg)
                            found = True
                            time.sleep(1)
        except:
            continue
    return found

# ========== البحث في مواقع أخرى عبر بحث جوجل (محاكاة بسيطة) ==========
def search_google(sent_links):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    found = False
    for site in SITES:
        # بناء استعلام بحث: كلمات مفتاحية + site: + استبعاد كلمات
        query = f'({" OR ".join(KEYWORDS[:5])}) site:{site} -{" -".join(EXCLUDE_WORDS)}'
        url = f"https://www.google.com/search?q={quote(query)}&tbs=qdr:d"  # آخر يوم
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                # استخراج النتائج (قد يتغير بناء جوجل)
                results = soup.find_all('div', class_='g')[:5]
                for r in results:
                    link_tag = r.find('a', href=True)
                    if link_tag:
                        link = link_tag['href']
                        if link.startswith('/url?q='):
                            link = link.split('/url?q=')[1].split('&')[0]
                        if link not in sent_links and not is_excluded(r.get_text()):
                            sent_links.add(link)
                            title = r.find('h3')
                            title_text = title.get_text() if title else "نتيجة بحث"
                            msg = f"🌐 <b>{site}</b>\n\n{title_text}\n\n🔗 {link}"
                            send_telegram(msg)
                            found = True
                            time.sleep(2)
        except:
            continue
    return found

# ========== التشغيل الرئيسي ==========
if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ تأكد من تعيين BOT_TOKEN و CHAT_ID في الأسرار")
        exit()

    sent_links = load_sent()
    send_telegram("🚀 بدء البحث المتقدم (ريديت + تويتر + جوجل)...")

    found_reddit = search_reddit(sent_links)
    found_twitter = search_twitter(sent_links)
    found_google = search_google(sent_links)

    if found_reddit or found_twitter or found_google:
        save_sent(sent_links)
        send_telegram("✅ تم العثور على نتائج جديدة!")
    else:
        send_telegram("ℹ️ لا توجد نتائج جديدة حالياً.")
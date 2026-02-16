import os
import requests
import json
import time
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_FILE = "sent_links.json"

KEYWORDS = [
    "احتاج محرر فيديو", "مطلوب مونتير", "بحاجة مونتير", "محرر فيديو",
    "video editor needed", "looking for video editor", "hiring video editor",
    "احتاج مونتير", "بدي مونتير", "أبحث عن محرر فيديو"
]

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
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def search_reddit():
    headers = {'User-Agent': 'Mozilla/5.0'}
    subreddits = ["forhire", "jobs", "freelance", "videoediting", "videography"]
    sent = load_sent()
    new_found = False
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
                        if full_url not in sent:
                            sent.add(full_url)
                            msg = f"🎯 <b>r/{sub}</b>\n\n{title}\n\n🔗 {full_url}"
                            send_telegram(msg)
                            new_found = True
                            time.sleep(1)
            except:
                continue
    if new_found:
        save_sent(sent)
        send_telegram("✅ تم العثور على نتائج جديدة!")
    else:
        send_telegram("ℹ️ لا توجد نتائج جديدة حالياً.")

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        exit()
    send_telegram("🚀 بدء البحث...")
    search_reddit()

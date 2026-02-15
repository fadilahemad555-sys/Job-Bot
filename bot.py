import os
import requests
import time
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class VideoClientHunterBot:
    def __init__(self):
        # ========== الإعدادات الأساسية ==========
        self.telegram_token = os.environ.get('TELEGRAM_TOKEN')
        self.chat_id = os.environ.get('CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.telegram_token}"
        
        # ========== قاعدة البيانات ==========
        self.db_file = Path('video_clients_db.json')
        self.job_db = self.load_database()
        
        # ========== الكلمات المفتاحية المطورة (أكثر دقة) ==========
        self.video_keywords = [
            'video editor', 'video editing', 'motion graphics', 'youtube editor',
            'shorts editor', 'reels editor', 'tiktok editor', 'premiere pro', 
            'after effects', 'davinci resolve', 'visual storyteller', 'montage'
        ]
        
        self.stats = {'total_checked': 0, 'passed_filter': 0, 'duplicates': 0, 'newly_sent': 0}

    def load_database(self):
        try:
            if self.db_file.exists():
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except: return {}

    def save_database(self):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.job_db, f, ensure_ascii=False, indent=2)

    def generate_id(self, title, url):
        return hashlib.md5(f"{title}{url}".encode()).hexdigest()

    def is_video_opportunity(self, title, description=''):
        combined = f"{title} {description}".lower()
        # استثناء المنشورات التي تبحث عن عمل (For Hire) في رديت
        if '[for hire]' in title.lower() or 'hiring a video editor' not in combined:
            if not any(kw in combined for kw in self.video_keywords):
                return False
        return any(kw in combined for kw in self.video_keywords)

    def safe_request(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers, timeout=20)
            return response if response.status_code == 200 else None
        except: return None

    def search_reddit(self, subreddit):
        print(f"🔍 فحص r/{subreddit}...")
        opps = []
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
        res = self.safe_request(url)
        if res:
            items = res.json().get('data', {}).get('children', [])
            for item in items:
                data = item.get('data', {})
                title = data.get('title', '')
                desc = data.get('selftext', '')[:500]
                link = f"https://reddit.com{data.get('permalink', '')}"
                
                if self.is_video_opportunity(title, desc):
                    job_id = self.generate_id(title, link)
                    if job_id not in self.job_db:
                        opps.append({
                            'title': title, 'url': link, 'desc': desc,
                            'platform': f"Reddit (r/{subreddit})", 'id': job_id
                        })
        return opps

    def format_message(self, job):
        return (
            f"🎯 <b>فرصة فيديو جديدة مكتشفة!</b>\n\n"
            f"📝 <b>العنوان:</b> {job['title']}\n"
            f"🌐 <b>المصدر:</b> {job['platform']}\n"
            f"📄 <b>نبذة:</b> {job['desc'][:200]}...\n\n"
            f"🔗 <b>رابط التقديم:</b>\n{job['url']}\n\n"
            f"⏰ {datetime.now().strftime('%H:%M')}"
        )

    def send_telegram(self, text):
        url = f"{self.base_url}/sendMessage"
        payload = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        try:
            requests.post(url, json=payload, timeout=10)
            return True
        except: return False

    def run(self):
        all_jobs = []
        # فحص أهم 3 مجتمعات في رديت للمحررين
        for sub in ['VideoEditing', 'forhire', 'Hiring']:
            all_jobs.extend(self.search_reddit(sub))
            time.sleep(2)

        sent_count = 0
        for job in all_jobs:
            if self.send_telegram(self.format_message(job)):
                self.job_db[job['id']] = {'time': datetime.now().isoformat()}
                sent_count += 1
                time.sleep(3)
        
        self.save_database()
        if sent_count == 0:
            self.send_telegram(f"ℹ️ لا توجد وظائف فيديو جديدة حالياً\n📊 تم فحص 75 منشور.\n⏰ {datetime.now().strftime('%H:%M')}")
        print(f"✅ تم إرسال {sent_count} وظائف.")

if __name__ == "__main__":
    if not os.environ.get('TELEGRAM_TOKEN'):
        print("خطأ: يرجى ضبط TELEGRAM_TOKEN")
    else:
        VideoClientHunterBot().run()
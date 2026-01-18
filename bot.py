import os
import requests
import time
import json
import re
from datetime import datetime, timedelta

class VideoJobHunter:
    def __init__(self):
        # ⚠️ الأمان: التوكنات من Environment فقط
        self.telegram_token = os.environ.get('TELEGRAM_TOKEN')
        self.chat_id = os.environ.get('CHAT_ID', '8497315428')
        self.base_url = f"https://api.telegram.org/bot{self.telegram_token}"
        
        # ✅ مصادر متنوعة (لتجنب الاعتماد على مصدر واحد)
        self.platforms = {
            'remoteok': 'https://remoteok.io/api?tag=video',
            'weworkremotely': 'https://weworkremotely.com/categories/remote-design-jobs.json',
            'flexjobs': 'https://www.flexjobs.com/search?search=video+editing',
            'dribbble': 'https://dribbble.com/jobs?q=video+editor',
            'github': 'https://jobs.github.com/positions.json?description=video',
            'indeed': 'https://www.indeed.com/jobs?q=video+editor&l=remote'
        }
        
        # ✅ كلمات بحث متنوعة
        self.keywords = [
            # مصطلحات دولية
            'video editor', 'video editing', 'motion graphics',
            'after effects', 'premiere pro', 'final cut pro',
            'video production', 'video post-production',
            'ai video', 'text to video', 'video ai',
            'background removal', 'product video',
            
            # مصطلحات عربية
            'مونتاج', 'محرر فيديو', 'تصميم فيديو',
            'موشن جرافيك', 'انيميشن', 'مصمم فيديو'
        ]
        
        # ⏱️ إضافة تأخيرات عشوائية لتجنب الحظر
        self.delays = [2, 3, 4, 5, 6]
        
    def safe_request(self, url, platform_name):
        """طلب آمن مع تأخيرات عشوائية"""
        try:
            # تأخير عشوائي
            time.sleep(self.delays[platform_name.__hash__() % len(self.delays)])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            # ⚠️ التحقق من حالة الاستجابة
            if response.status_code == 429:  # Too Many Requests
                print(f"⚠️ حظر مؤقت من {platform_name}، انتظر 60 ثانية")
                time.sleep(60)
                return None
                
            return response
        except Exception as e:
            print(f"❌ خطأ في {platform_name}: {e}")
            return None
    
    def search_remoteok(self):
        """بحث في RemoteOK"""
        jobs = []
        try:
            url = self.platforms['remoteok']
            response = self.safe_request(url, 'remoteok')
            
            if response and response.status_code == 200:
                data = response.json()
                for job in data[1:]:  # تخطي العنصر الأول
                    title = job.get('position', '').lower()
                    
                    # ✅ فلترة ذكية
                    if any(keyword in title for keyword in self.keywords):
                        job_info = {
                            'platform': 'RemoteOK',
                            'title': job.get('position', ''),
                            'company': job.get('company', ''),
                            'url': job.get('url', ''),
                            'description': job.get('description', '')[:200] + '...',
                            'salary': job.get('salary', 'غير محدد'),
                            'tags': job.get('tags', [])
                        }
                        jobs.append(job_info)
        except Exception as e:
            print(f"Error RemoteOK: {e}")
        
        return jobs
    
    def search_github_jobs(self):
        """بحث في GitHub Jobs"""
        jobs = []
        try:
            url = self.platforms['github']
            response = self.safe_request(url, 'github')
            
            if response and response.status_code == 200:
                data = response.json()
                for job in data:
                    title = job.get('title', '').lower()
                    desc = job.get('description', '').lower()
                    
                    if any(keyword in title or keyword in desc for keyword in self.keywords):
                        job_info = {
                            'platform': 'GitHub Jobs',
                            'title': job.get('title', ''),
                            'company': job.get('company', ''),
                            'url': job.get('url', ''),
                            'location': job.get('location', 'Remote'),
                            'type': job.get('type', 'Full-time')
                        }
                        jobs.append(job_info)
        except Exception as e:
            print(f"Error GitHub Jobs: {e}")
        
        return jobs
    
    def search_flexjobs(self):
        """بحث في FlexJobs (مثال للويب سكرابينج الآمن)"""
        jobs = []
        try:
            url = self.platforms['flexjobs']
            response = self.safe_request(url, 'flexjobs')
            
            if response and response.status_code == 200:
                # استخدام regex للبحث عن وظائف فيديو
                content = response.text.lower()
                
                # البحث عن أنماط
                video_patterns = [
                    r'video editor.*?\$(\d+)',
                    r'motion graphic.*?remote',
                    r'video production.*?contract',
                    r'video.*?edit.*?remote'
                ]
                
                for pattern in video_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    if matches:
                        job_info = {
                            'platform': 'FlexJobs',
                            'title': 'Video Editor Position',
                            'url': url,
                            'found_pattern': pattern
                        }
                        jobs.append(job_info)
        except Exception as e:
            print(f"Error FlexJobs: {e}")
        
        return jobs
    
    def search_custom_sources(self):
        """بحث في مصادر مخصصة آمنة"""
        jobs = []
        
        # ⚠️ مصادر بديلة آمنة
        custom_sources = [
            {
                'name': 'Video Editing Subreddits',
                'url': 'https://www.reddit.com/r/videoediting/hot.json?limit=5',
                'type': 'json'
            },
            {
                'name': 'Creative Market',
                'url': 'https://creativemarket.com/jobs?category=video',
                'type': 'html'
            },
            {
                'name': '99designs',
                'url': 'https://99designs.com/jobs?skills=video-editing',
                'type': 'html'
            }
        ]
        
        for source in custom_sources:
            try:
                response = self.safe_request(source['url'], source['name'])
                if response and response.status_code == 200:
                    # هنا يمكنك إضافة معالجة خاصة لكل مصدر
                    job_info = {
                        'platform': source['name'],
                        'title': f'Video Jobs on {source["name"]}',
                        'url': source['url'],
                        'status': 'Active'
                    }
                    jobs.append(job_info)
            except Exception as e:
                print(f"Error {source['name']}: {e}")
        
        return jobs
    
    def format_job_message(self, job):
        """تنسيق رسالة الوظيفة"""
        message = f"""
🎬 <b>وظيفة فيديو جديدة!</b>

📌 <b>المنصة:</b> {job['platform']}
🏷️ <b>المسمى:</b> {job.get('title', 'Video Editor')}
🏢 <b>الشركة:</b> {job.get('company', 'غير محدد')}
💰 <b>الراتب:</b> {job.get('salary', 'متفاوض عليه')}
📍 <b>المكان:</b> {job.get('location', 'عن بعد')}

📝 <b>الوصف:</b>
{job.get('description', 'تفاصيل الوظيفة متاحة على الرابط')}

🔗 <b>رابط التقديم:</b>
{job.get('url', 'https://example.com')}

⏰ <b>وقت الاكتشاف:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message
    
    def send_to_telegram(self, message):
        """إرسال إلى تليجرام"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            # ⚠️ التحقق من حظر تليجرام
            if response.status_code == 429:
                retry_after = response.json().get('parameters', {}).get('retry_after', 30)
                print(f"⏳ تليجرام يطلب الانتظار: {retry_after} ثانية")
                time.sleep(retry_after + 5)
                return False
                
            return response.status_code == 200
        except Exception as e:
            print(f"❌ خطأ تليجرام: {e}")
            return False
    
    def run_search_cycle(self):
        """دورة بحث كاملة"""
        all_jobs = []
        
        print("🚀 بدء البحث عن وظائف الفيديو...")
        
        # 🔍 البحث في كل المنصات
        search_methods = [
            self.search_remoteok,
            self.search_github_jobs,
            self.search_flexjobs,
            self.search_custom_sources
        ]
        
        for method in search_methods:
            try:
                print(f"🔍 البحث في: {method.__name__}")
                jobs = method()
                all_jobs.extend(jobs)
                
                # تأخير بين المنصات
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ خطأ في {method.__name__}: {e}")
                continue
        
        # 📤 إرسال النتائج
        if all_jobs:
            print(f"✅ تم العثور على {len(all_jobs)} وظيفة")
            
            # إرسال رسالة تجميعية أولى
            self.send_to_telegram(f"🎯 <b>تم العثور على {len(all_jobs)} وظيفة فيديو جديدة!</b>")
            time.sleep(2)
            
            # إرسال كل وظيفة
            for i, job in enumerate(all_jobs[:10]):  # الحد: 10 وظائف لكل دورة
                message = self.format_job_message(job)
                self.send_to_telegram(message)
                
                # تأخير بين الرسائل
                if i < len(all_jobs) - 1:
                    time.sleep(3)
        else:
            print("⚠️ لم يتم العثور على وظائف هذه الدورة")
            self.send_to_telegram("⚠️ <b>لم يتم العثور على وظائف فيديو جديدة هذه الدورة</b>")
        
        return len(all_jobs)

def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("🤖 بوت البحث عن وظائف الفيديو - الإصدار الآمن")
    print("=" * 50)
    
    # التحقق من التوكنات
    if not os.environ.get('TELEGRAM_TOKEN'):
        print("❌ خطأ: TELEGRAM_TOKEN غير موجود")
        return
    
    # إنشاء وتشغيل البوت
    bot = VideoJobHunter()
    
    # تشغيل دورة البحث
    jobs_found = bot.run_search_cycle()
    
    print(f"\n{'='*50}")
    print(f"✅ اكتملت الدورة. الوظائف الموجودة: {jobs_found}")
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

if __name__ == "__main__":
    main()

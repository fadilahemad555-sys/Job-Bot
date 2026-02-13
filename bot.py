import os
import requests
import time
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class SmartVideoJobBot:
    def __init__(self):
        # ========== الإعدادات الأساسية ==========
        self.telegram_token = os.environ.get('TELEGRAM_TOKEN')
        self.chat_id = os.environ.get('CHAT_ID', '8497315428')
        self.base_url = f"https://api.telegram.org/bot{self.telegram_token}"
        
        # ========== ملف التتبع (مهم جداً!) ==========
        self.db_file = Path('job_database.json')
        self.job_db = self.load_database()
        
        # ========== المنصات الموثوقة فقط ==========
        self.api_sources = {
            'remoteok': {
                'url': 'https://remoteok.io/api',
                'active': True
            }
        }
        
        # ========== كلمات مفتاحية دقيقة جداً ==========
        self.required_keywords = [
            'video editor',
            'video editing',
            'motion graphics',
            'motion designer',
            'video producer',
            'video production',
            'post production',
            'post-production'
        ]
        
        # كلمات داعمة (لزيادة الدقة)
        self.support_keywords = [
            'premiere',
            'after effects',
            'final cut',
            'davinci',
            'resolve',
            'avid',
            'video content',
            'video specialist'
        ]
        
        # ========== كلمات استبعاد قوية ==========
        self.exclude_keywords = [
            # وظائف برمجة
            'software engineer', 'developer', 'programmer', 'backend', 'frontend',
            'full stack', 'devops', 'ios', 'android', 'react', 'python', 'java',
            'data scientist', 'machine learning', 'ai engineer', 'ml engineer',
            
            # وظائف إدارة
            'product manager', 'project manager', 'account manager', 'sales manager',
            'marketing manager', 'business development', 'customer success',
            
            # وظائف أخرى
            'recruiter', 'hr manager', 'accountant', 'financial analyst',
            'content writer', 'copywriter', 'seo specialist'
        ]
        
        # ========== إحصائيات ==========
        self.stats = {
            'total_checked': 0,
            'passed_filter': 0,
            'already_sent': 0,
            'newly_sent': 0
        }
    
    # ==================== إدارة قاعدة البيانات ====================
    
    def load_database(self):
        """تحميل قاعدة بيانات الوظائف المرسلة"""
        try:
            if self.db_file.exists():
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # تنظيف تلقائي: حذف الوظائف الأقدم من 10 أيام
                cutoff = (datetime.now() - timedelta(days=10)).isoformat()
                cleaned_data = {
                    k: v for k, v in data.items() 
                    if not k.startswith('_') and v.get('sent_at', '') > cutoff
                }
                
                # الاحتفاظ بالإعدادات الخاصة (مثل _last_no_jobs_alert)
                for key in data:
                    if key.startswith('_'):
                        cleaned_data[key] = data[key]
                
                # حفظ البيانات المنظفة
                if len(cleaned_data) < len(data):
                    self.save_database(cleaned_data)
                    print(f"🧹 تنظيف قاعدة البيانات: {len(data)} → {len(cleaned_data)} وظيفة")
                
                return cleaned_data
            
            return {}
        except Exception as e:
            print(f"⚠️ خطأ في تحميل قاعدة البيانات: {e}")
            return {}
    
    def save_database(self, data=None):
        """حفظ قاعدة البيانات"""
        try:
            if data is None:
                data = self.job_db
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ خطأ في حفظ قاعدة البيانات: {e}")
    
    def generate_unique_id(self, title, company, url):
        """إنشاء معرّف فريد للوظيفة"""
        # استخدام URL كمعرف أساسي (الأكثر موثوقية)
        if url:
            return hashlib.md5(url.encode()).hexdigest()
        
        # بديل: استخدام العنوان + الشركة
        unique_str = f"{title.lower().strip()}{company.lower().strip()}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def is_job_already_sent(self, job_id):
        """فحص إذا تم إرسال الوظيفة مسبقاً"""
        return job_id in self.job_db
    
    def mark_job_as_sent(self, job_id, job_info):
        """تسجيل الوظيفة كمرسلة"""
        self.job_db[job_id] = {
            'title': job_info.get('title', ''),
            'company': job_info.get('company', ''),
            'url': job_info.get('url', ''),
            'sent_at': datetime.now().isoformat(),
            'platform': job_info.get('platform', '')
        }
        self.save_database()
    
    # ==================== الفلترة الذكية ====================
    
    def is_valid_video_job(self, title, description=''):
        """فحص صارم: هل هذه وظيفة فيديو حقيقية؟"""
        title_lower = title.lower().strip()
        desc_lower = description.lower()[:500]  # فحص أول 500 حرف فقط
        combined = f"{title_lower} {desc_lower}"
        
        # ========== خطوة 1: استبعاد الوظائف غير المناسبة ==========
        for exclude_word in self.exclude_keywords:
            if exclude_word in combined:
                print(f"   ❌ استبعاد: يحتوي على '{exclude_word}'")
                return False
        
        # ========== خطوة 2: يجب وجود كلمة مفتاحية أساسية ==========
        has_required = False
        for keyword in self.required_keywords:
            if keyword in title_lower:
                has_required = True
                print(f"   ✅ كلمة مطلوبة: '{keyword}'")
                break
        
        if not has_required:
            # فحص في الوصف أيضاً
            for keyword in self.required_keywords:
                if keyword in desc_lower:
                    has_required = True
                    print(f"   ✅ كلمة مطلوبة في الوصف: '{keyword}'")
                    break
        
        if not has_required:
            print(f"   ❌ رفض: لا تحتوي على كلمات مفتاحية مطلوبة")
            return False
        
        # ========== خطوة 3 (اختيارية): التحقق من الكلمات الداعمة ==========
        # هذا يزيد من الثقة ولكن ليس إلزامياً
        has_support = any(word in combined for word in self.support_keywords)
        if has_support:
            print(f"   ⭐ وظيفة قوية: تحتوي على كلمات داعمة")
        
        return True
    
    # ==================== البحث في المنصات ====================
    
    def safe_api_call(self, url, platform_name, max_retries=2):
        """طلب API آمن مع إعادة المحاولة"""
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                
                # معالجة حظر API
                if response.status_code == 429:
                    wait_time = 60 * (attempt + 1)
                    print(f"   ⏳ Rate limit من {platform_name}، انتظار {wait_time}ث...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code == 200:
                    return response
                else:
                    print(f"   ⚠️ استجابة غير متوقعة: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️ انتهى الوقت في المحاولة {attempt + 1}")
            except Exception as e:
                print(f"   ❌ خطأ في المحاولة {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(5)
        
        return None
    
    def search_remoteok(self):
        """البحث في RemoteOK"""
        platform_name = "RemoteOK"
        jobs = []
        
        try:
            print(f"\n🔍 البحث في {platform_name}...")
            
            source = self.api_sources['remoteok']
            response = self.safe_api_call(source['url'], platform_name)
            
            if not response:
                print(f"❌ فشل الاتصال بـ {platform_name}")
                return []
            
            data = response.json()
            print(f"   📊 إجمالي الوظائف: {len(data)}")
            
            # تخطي العنصر الأول (metadata)
            for job in data[1:]:
                try:
                    self.stats['total_checked'] += 1
                    
                    # ========== استخراج البيانات ==========
                    title = job.get('position', '')
                    company = job.get('company', 'غير محدد')
                    description = job.get('description', '')
                    url_link = job.get('url', '')
                    
                    if not title or not url_link:
                        continue
                    
                    print(f"\n🔎 فحص: {title[:60]}...")
                    
                    # ========== فحص الصلاحية ==========
                    if not self.is_valid_video_job(title, description):
                        continue
                    
                    self.stats['passed_filter'] += 1
                    
                    # ========== فحص التكرار ==========
                    job_id = self.generate_unique_id(title, company, url_link)
                    
                    if self.is_job_already_sent(job_id):
                        print(f"   ⏭️ تم إرسالها مسبقاً")
                        self.stats['already_sent'] += 1
                        continue
                    
                    # ========== وظيفة جديدة وصالحة! ==========
                    job_info = {
                        'id': job_id,
                        'platform': platform_name,
                        'title': title,
                        'company': company,
                        'url': url_link,
                        'description': description[:400] + '...' if len(description) > 400 else description,
                        'salary': job.get('salary_max', job.get('salary', 'غير محدد')),
                        'tags': ', '.join(job.get('tags', [])[:5]),
                        'location': job.get('location', 'Remote'),
                        'posted_date': job.get('date', 'غير محدد')
                    }
                    
                    jobs.append(job_info)
                    print(f"   ✅ وظيفة صالحة وجديدة!")
                    
                except Exception as e:
                    print(f"   ⚠️ خطأ في معالجة وظيفة: {e}")
                    continue
            
            print(f"\n✅ {platform_name}: وجدنا {len(jobs)} وظيفة جديدة صالحة")
            
        except Exception as e:
            print(f"❌ خطأ عام في {platform_name}: {e}")
        
        return jobs
    
    # ==================== إرسال تليجرام ====================
    
    def format_message(self, job):
        """تنسيق رسالة احترافية"""
        message = f"""
🎬 <b>وظيفة فيديو جديدة!</b>

📌 <b>المنصة:</b> {job['platform']}
🏷️ <b>المسمى الوظيفي:</b> {job['title']}
🏢 <b>الشركة:</b> {job['company']}
💰 <b>الراتب:</b> {job.get('salary', 'غير محدد')}
📍 <b>الموقع:</b> {job.get('location', 'Remote')}
🏷️ <b>المهارات:</b> {job.get('tags', 'غير محدد')}

📝 <b>نبذة:</b>
{job['description']}

🔗 <b>رابط التقديم:</b>
{job['url']}

⏰ <b>تاريخ الاكتشاف:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

<i>🤖 تم اكتشافها تلقائياً بواسطة Video Job Bot</i>
"""
        return message.strip()
    
    def send_telegram(self, message, retry=True):
        """إرسال رسالة تليجرام مع معالجة الأخطاء"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            # معالجة Rate Limit
            if response.status_code == 429:
                if retry:
                    retry_after = response.json().get('parameters', {}).get('retry_after', 30)
                    print(f"   ⏳ Telegram rate limit: انتظار {retry_after}ث")
                    time.sleep(retry_after + 2)
                    return self.send_telegram(message, retry=False)
                return False
            
            if response.status_code != 200:
                print(f"   ⚠️ Telegram error: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ خطأ إرسال Telegram: {e}")
            return False
    
    # ==================== التشغيل الرئيسي ====================
    
    def run(self):
        """تشغيل البوت"""
        print("\n" + "="*70)
        print("🤖 Video Job Hunter Bot - النسخة المحسنة v3.1")
        print("="*70)
        print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💾 قاعدة البيانات: {len([k for k in self.job_db.keys() if not k.startswith('_')])} وظيفة محفوظة")
        print("="*70)
        
        # ========== البحث في المنصات ==========
        all_jobs = []
        
        # يمكنك إضافة منصات أخرى هنا
        search_functions = [
            self.search_remoteok,
            # self.search_other_platform,  # أضف منصات أخرى
        ]
        
        for search_func in search_functions:
            try:
                jobs = search_func()
                all_jobs.extend(jobs)
                time.sleep(5)  # تأخير بين المنصات
            except Exception as e:
                print(f"❌ خطأ في {search_func.__name__}: {e}")
        
        # ========== عرض الإحصائيات ==========
        print("\n" + "="*70)
        print("📊 إحصائيات البحث:")
        print(f"   🔍 إجمالي الوظائف المفحوصة: {self.stats['total_checked']}")
        print(f"   ✅ نجحت في الفلترة: {self.stats['passed_filter']}")
        print(f"   ⏭️ مرسلة مسبقاً: {self.stats['already_sent']}")
        print(f"   🆕 وظائف جديدة: {len(all_jobs)}")
        print("="*70)
        
        # ========== إرسال الوظائف - الحل النهائي المضمون 100% ==========
        if len(all_jobs) > 0:
            print(f"\n📋 محاولة إرسال {len(all_jobs)} وظيفة...")
            
            # ✅ إرسال كل وظيفة أولاً
            successfully_sent = 0
            for i, job in enumerate(all_jobs[:10], 1):  # حد أقصى 10 وظائف
                print(f"\n📤 إرسال الوظيفة {i}/{len(all_jobs)}: {job['title'][:40]}...")
                
                message = self.format_message(job)
                
                if self.send_telegram(message):
                    self.mark_job_as_sent(job['id'], job)
                    self.stats['newly_sent'] += 1
                    successfully_sent += 1
                    print(f"   ✅ تم الإرسال بنجاح")
                    time.sleep(3)  # تأخير بين الرسائل
                else:
                    print(f"   ❌ فشل الإرسال")
            
            # ✅ إرسال الملخص فقط إذا تم إرسال وظيفة واحدة على الأقل فعلياً
            if successfully_sent > 0:
                summary = f"🎯 <b>تم إرسال {successfully_sent} وظيفة فيديو جديدة بنجاح!</b>\n\n"
                summary += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                self.send_telegram(summary)
                print(f"\n✅ تم إرسال {successfully_sent} وظيفة بنجاح")
            else:
                print(f"\n⚠️ فشل إرسال جميع الوظائف ({len(all_jobs)} وظيفة)")
        
        else:
            # ✅ التحسين: لا ترسل شيء إلا إذا مر 12 ساعة
            print("\nℹ️ لا توجد وظائف جديدة في هذه الدورة")
            
            # إرسال تنبيه فقط مرة كل ساعتين
            last_alert = self.job_db.get('_last_no_jobs_alert', {})
            last_alert_time = last_alert.get('time', '')
            
            should_send_alert = False
            if not last_alert_time:
                should_send_alert = True
            else:
                try:
                    time_diff = (datetime.now() - datetime.fromisoformat(last_alert_time)).total_seconds()
                    if time_diff > 7200:  # ساعتين (2 * 60 * 60 = 7200 ثانية)
                        should_send_alert = True
                except:
                    should_send_alert = True
            
            if should_send_alert:
                alert_msg = "ℹ️ <b>لا توجد وظائف فيديو جديدة حالياً</b>\n\n"
                alert_msg += f"⏰ آخر فحص: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                alert_msg += f"📊 إجمالي الوظائف المفحوصة: {self.stats['total_checked']}\n"
                alert_msg += f"💾 قاعدة البيانات: {len([k for k in self.job_db.keys() if not k.startswith('_')])} وظيفة\n\n"
                alert_msg += "<i>سيتم البحث مجدداً في الدورة القادمة</i>"
                
                self.send_telegram(alert_msg)
                self.job_db['_last_no_jobs_alert'] = {'time': datetime.now().isoformat()}
                self.save_database()
                print("📨 تم إرسال تنبيه عدم وجود وظائف جديدة")
            else:
                print("⏭️ تخطي إرسال التنبيه (لم يمر ساعتين بعد)")
        
        # ========== النتيجة النهائية ==========
        print("\n" + "="*70)
        print(f"✅ اكتملت الدورة بنجاح")
        print(f"📊 النتائج:")
        print(f"   • وظائف جديدة تم إرسالها: {self.stats['newly_sent']}")
        print(f"   • إجمالي قاعدة البيانات: {len([k for k in self.job_db.keys() if not k.startswith('_')])} وظيفة")
        print("="*70 + "\n")
        
        return self.stats['newly_sent']


# ==================== التشغيل ====================

def main():
    """الدالة الرئيسية"""
    
    # التحقق من التوكن
    if not os.environ.get('TELEGRAM_TOKEN'):
        print("\n" + "❌"*30)
        print("خطأ فادح: TELEGRAM_TOKEN غير موجود!")
        print("\nالحل:")
        print("  export TELEGRAM_TOKEN='your_bot_token_here'")
        print("  export CHAT_ID='your_chat_id'")
        print("❌"*30 + "\n")
        return
    
    # تشغيل البوت
    try:
        bot = SmartVideoJobBot()
        jobs_sent = bot.run()
        
        print(f"✅ النتيجة النهائية: تم إرسال {jobs_sent} وظيفة جديدة")
        
    except KeyboardInterrupt:
        print("\n⚠️ تم إيقاف البوت يدوياً (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

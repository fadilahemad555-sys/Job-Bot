import os
import requests
import time
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class VideoClientHunterBot:
    """
    بوت ذكي للبحث عن فرص عمل في تحرير الفيديو
    يجلب: وظائف دائمة + مشاريع Freelance + طلبات مباشرة
    """
    
    def __init__(self):
        # ========== الإعدادات الأساسية ==========
        self.telegram_token = os.environ.get('TELEGRAM_TOKEN')
        self.chat_id = os.environ.get('CHAT_ID', '8497315428')
        self.base_url = f"https://api.telegram.org/bot{self.telegram_token}"
        
        # ========== قاعدة البيانات ==========
        self.db_file = Path('video_clients_db.json')
        self.job_db = self.load_database()
        
        # ========== الكلمات المفتاحية الذكية ==========
        self.video_keywords = [
            'video editor',
            'video editing',
            'video producer',
            'video production',
            'motion graphics',
            'motion designer',
            'video content creator',
            'youtube editor',
            'video specialist',
            'post production',
            'montage',
            'premiere pro',
            'after effects',
            'final cut pro',
            'davinci resolve'
        ]
        
        # ========== كلمات الاستبعاد (فقط الصارمة) ==========
        self.exclude_titles = [
            'software engineer',
            'data scientist',
            'backend developer',
            'frontend developer',
            'mobile developer',
            'recruiter',
            'accountant'
        ]
        
        # ========== الإحصائيات ==========
        self.stats = {
            'total_checked': 0,
            'passed_filter': 0,
            'duplicates': 0,
            'newly_sent': 0
        }
    
    # ==================== إدارة قاعدة البيانات ====================
    
    def load_database(self):
        """تحميل قاعدة البيانات"""
        try:
            if self.db_file.exists():
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # تنظيف: حذف الوظائف الأقدم من 15 يوم
                cutoff = (datetime.now() - timedelta(days=15)).isoformat()
                cleaned = {
                    k: v for k, v in data.items()
                    if not k.startswith('_') and v.get('sent_at', '') > cutoff
                }
                
                # الاحتفاظ بالإعدادات
                for key in data:
                    if key.startswith('_'):
                        cleaned[key] = data[key]
                
                if len(cleaned) < len(data):
                    self.save_database(cleaned)
                    print(f"🧹 تنظيف: {len(data)} → {len(cleaned)} فرصة")
                
                return cleaned
            return {}
        except Exception as e:
            print(f"⚠️ خطأ تحميل DB: {e}")
            return {}
    
    def save_database(self, data=None):
        """حفظ قاعدة البيانات"""
        try:
            if data is None:
                data = self.job_db
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ خطأ حفظ DB: {e}")
    
    def generate_id(self, title, company, url):
        """إنشاء معرف فريد"""
        if url:
            return hashlib.md5(url.encode()).hexdigest()
        unique = f"{title.lower().strip()}{company.lower().strip()}"
        return hashlib.md5(unique.encode()).hexdigest()
    
    def is_duplicate(self, job_id):
        """فحص التكرار"""
        return job_id in self.job_db
    
    def mark_as_sent(self, job_id, job_info):
        """تسجيل كمرسل"""
        self.job_db[job_id] = {
            'title': job_info.get('title', ''),
            'company': job_info.get('company', ''),
            'url': job_info.get('url', ''),
            'sent_at': datetime.now().isoformat(),
            'type': job_info.get('type', 'job')
        }
        self.save_database()
    
    # ==================== الفلتر الذكي ====================
    
    def is_video_opportunity(self, title, description=''):
        """فحص ذكي: هل هذه فرصة فيديو؟"""
        title_lower = title.lower().strip()
        desc_lower = description.lower()[:800]
        
        # ========== خطوة 1: هل تحتوي على كلمة فيديو؟ ==========
        has_video_keyword = False
        for keyword in self.video_keywords:
            if keyword in title_lower or keyword in desc_lower:
                has_video_keyword = True
                print(f"   ✅ وجدت: '{keyword}'")
                break
        
        if not has_video_keyword:
            print(f"   ❌ لا توجد كلمات فيديو")
            return False
        
        # ========== خطوة 2: استبعاد ذكي ==========
        # فقط أول 4 كلمات من العنوان
        first_words = ' '.join(title_lower.split()[:4])
        
        for exclude in self.exclude_titles:
            if exclude in first_words:
                print(f"   ❌ استبعاد: '{exclude}' في العنوان")
                return False
        
        print(f"   ✅ فرصة صالحة!")
        return True
    
    # ==================== البحث في المنصات ====================
    
    def safe_request(self, url, headers=None, timeout=30):
        """طلب آمن"""
        try:
            if headers is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response
            print(f"   ⚠️ Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
        return None
    
    def search_remoteok(self):
        """البحث في RemoteOK"""
        print(f"\n🔍 البحث في RemoteOK...")
        opportunities = []
        
        try:
            response = self.safe_request('https://remoteok.io/api')
            if not response:
                return []
            
            data = response.json()
            print(f"   📊 الوظائف: {len(data)}")
            
            for job in data[1:]:  # تخطي metadata
                try:
                    self.stats['total_checked'] += 1
                    
                    title = job.get('position', '')
                    company = job.get('company', 'غير محدد')
                    desc = job.get('description', '')
                    url = job.get('url', '')
                    
                    if not title or not url:
                        continue
                    
                    print(f"\n🔎 {title[:50]}...")
                    
                    if not self.is_video_opportunity(title, desc):
                        continue
                    
                    self.stats['passed_filter'] += 1
                    
                    # فحص التكرار
                    job_id = self.generate_id(title, company, url)
                    if self.is_duplicate(job_id):
                        print(f"   ⏭️ مكررة")
                        self.stats['duplicates'] += 1
                        continue
                    
                    # فرصة جديدة!
                    opp = {
                        'id': job_id,
                        'type': 'وظيفة دائمة',
                        'platform': 'RemoteOK',
                        'title': title,
                        'company': company,
                        'url': url,
                        'description': desc[:500],
                        'salary': job.get('salary_max') or job.get('salary', 'غير محدد'),
                        'location': job.get('location', 'Remote'),
                        'tags': ', '.join(job.get('tags', [])[:5])
                    }
                    
                    opportunities.append(opp)
                    print(f"   ✅ فرصة جديدة!")
                    
                except Exception as e:
                    print(f"   ⚠️ خطأ معالجة: {e}")
            
            print(f"\n✅ RemoteOK: {len(opportunities)} فرصة جديدة")
            
        except Exception as e:
            print(f"❌ خطأ RemoteOK: {e}")
        
        return opportunities
    
    def search_wwr(self):
        """البحث في We Work Remotely"""
        print(f"\n🔍 البحث في We Work Remotely...")
        opportunities = []
        
        try:
            # WWR لديهم RSS feed
            response = self.safe_request('https://weworkremotely.com/categories/remote-video-editing-jobs.rss')
            if not response:
                return []
            
            # معالجة RSS بسيطة
            content = response.text
            
            # استخراج الوظائف من RSS (بسيط)
            import re
            items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
            
            print(f"   📊 الوظائف: {len(items)}")
            
            for item in items[:20]:  # أول 20
                try:
                    self.stats['total_checked'] += 1
                    
                    title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item)
                    
                    if not title_match or not link_match:
                        continue
                    
                    title = title_match.group(1).strip()
                    url = link_match.group(1).strip()
                    desc = desc_match.group(1).strip() if desc_match else ''
                    
                    # استخراج الشركة من العنوان
                    # عادة: "Job Title: Company Name"
                    company = 'غير محدد'
                    if ':' in title:
                        parts = title.split(':')
                        if len(parts) >= 2:
                            company = parts[1].strip()
                            title = parts[0].strip()
                    
                    print(f"\n🔎 {title[:50]}...")
                    
                    if not self.is_video_opportunity(title, desc):
                        continue
                    
                    self.stats['passed_filter'] += 1
                    
                    job_id = self.generate_id(title, company, url)
                    if self.is_duplicate(job_id):
                        print(f"   ⏭️ مكررة")
                        self.stats['duplicates'] += 1
                        continue
                    
                    opp = {
                        'id': job_id,
                        'type': 'وظيفة دائمة',
                        'platform': 'We Work Remotely',
                        'title': title,
                        'company': company,
                        'url': url,
                        'description': desc[:500],
                        'salary': 'غير محدد',
                        'location': 'Remote',
                        'tags': ''
                    }
                    
                    opportunities.append(opp)
                    print(f"   ✅ فرصة جديدة!")
                    
                except Exception as e:
                    print(f"   ⚠️ خطأ: {e}")
            
            print(f"\n✅ WWR: {len(opportunities)} فرصة جديدة")
            
        except Exception as e:
            print(f"❌ خطأ WWR: {e}")
        
        return opportunities
    
    # ==================== إرسال تليجرام ====================
    
    def format_message(self, opp):
        """تنسيق رسالة احترافية"""
        emoji = "💼" if opp['type'] == 'وظيفة دائمة' else "🎬"
        
        message = f"""
{emoji} <b>{opp['type']} جديدة!</b>

🏷️ <b>المسمى:</b> {opp['title']}
🏢 <b>الشركة:</b> {opp['company']}
🌐 <b>المنصة:</b> {opp['platform']}
💰 <b>الراتب:</b> {opp.get('salary', 'غير محدد')}
📍 <b>الموقع:</b> {opp.get('location', 'Remote')}
"""
        
        if opp.get('tags'):
            message += f"🏷️ <b>المهارات:</b> {opp['tags']}\n"
        
        message += f"""
📝 <b>الوصف:</b>
{opp['description']}

🔗 <b>التقديم:</b>
{opp['url']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return message.strip()
    
    def send_telegram(self, message):
        """إرسال رسالة"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 429:
                wait = response.json().get('parameters', {}).get('retry_after', 30)
                print(f"   ⏳ انتظار {wait}ث")
                time.sleep(wait + 2)
                return self.send_telegram(message)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"   ❌ خطأ Telegram: {e}")
            return False
    
    # ==================== التشغيل الرئيسي ====================
    
    def run(self):
        """تشغيل البوت"""
        print("\n" + "="*70)
        print("🎬 Video Client Hunter Bot - صياد الفرص v1.0")
        print("="*70)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💾 قاعدة البيانات: {len([k for k in self.job_db if not k.startswith('_')])} فرصة")
        print("="*70)
        
        # البحث في جميع المنصات
        all_opportunities = []
        
        platforms = [
            self.search_remoteok,
            self.search_wwr,
        ]
        
        for platform_func in platforms:
            try:
                opps = platform_func()
                all_opportunities.extend(opps)
                time.sleep(5)  # راحة بين المنصات
            except Exception as e:
                print(f"❌ خطأ في {platform_func.__name__}: {e}")
        
        # الإحصائيات
        print("\n" + "="*70)
        print("📊 الإحصائيات:")
        print(f"   🔍 المفحوصة: {self.stats['total_checked']}")
        print(f"   ✅ نجحت في الفلتر: {self.stats['passed_filter']}")
        print(f"   ⏭️ مكررة: {self.stats['duplicates']}")
        print(f"   🆕 فرص جديدة: {len(all_opportunities)}")
        print("="*70)
        
        # الإرسال
        if len(all_opportunities) > 0:
            successfully_sent = 0
            
            for i, opp in enumerate(all_opportunities[:15], 1):
                print(f"\n📤 إرسال {i}/{len(all_opportunities)}: {opp['title'][:40]}...")
                
                message = self.format_message(opp)
                
                if self.send_telegram(message):
                    self.mark_as_sent(opp['id'], opp)
                    successfully_sent += 1
                    print(f"   ✅ تم الإرسال")
                    time.sleep(3)
                else:
                    print(f"   ❌ فشل")
            
            # ملخص نهائي
            if successfully_sent > 0:
                summary = f"🎯 <b>تم إرسال {successfully_sent} فرصة عمل جديدة!</b>\n\n"
                summary += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                self.send_telegram(summary)
                print(f"\n✅ نجح إرسال {successfully_sent} فرصة")
        
        else:
            print("\nℹ️ لا توجد فرص جديدة")
            
            # تشخيص
            print(f"\n📊 تشخيص:")
            print(f"   🔍 المفحوصة: {self.stats['total_checked']}")
            print(f"   ✅ الفلتر: {self.stats['passed_filter']}")
            print(f"   ⏭️ مكررة: {self.stats['duplicates']}")
            
            # تنبيه كل 30 دقيقة
            last_alert = self.job_db.get('_last_alert', {})
            last_time = last_alert.get('time', '')
            
            should_alert = False
            if not last_time:
                should_alert = True
            else:
                try:
                    diff = (datetime.now() - datetime.fromisoformat(last_time)).total_seconds()
                    if diff > 1800:  # 30 دقيقة
                        should_alert = True
                except:
                    should_alert = True
            
            if should_alert:
                reason = ""
                if self.stats['total_checked'] == 0:
                    reason = "لا يوجد اتصال بالمنصات"
                elif self.stats['passed_filter'] == 0:
                    reason = f"تم فحص {self.stats['total_checked']} فرصة لكن لا شيء يطابق"
                elif self.stats['duplicates'] > 0:
                    reason = f"وجدنا {self.stats['duplicates']} فرصة لكنها مكررة"
                
                alert = f"ℹ️ <b>لا توجد فرص جديدة حالياً</b>\n\n"
                alert += f"⏰ آخر فحص: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                alert += f"📊 المفحوصة: {self.stats['total_checked']}\n"
                alert += f"🔍 السبب: {reason}\n\n"
                alert += "<i>⏰ التنبيه التالي بعد 30 دقيقة</i>"
                
                self.send_telegram(alert)
                self.job_db['_last_alert'] = {'time': datetime.now().isoformat()}
                self.save_database()
        
        print("\n" + "="*70)
        print(f"✅ انتهت الدورة")
        print(f"📊 تم إرسال: {self.stats['newly_sent']} فرصة")
        print("="*70 + "\n")
        
        return self.stats['newly_sent']


def main():
    """الدالة الرئيسية"""
    
    if not os.environ.get('TELEGRAM_TOKEN'):
        print("\n❌ خطأ: TELEGRAM_TOKEN غير موجود!")
        print("\nالحل:")
        print("  export TELEGRAM_TOKEN='your_token'")
        print("  export CHAT_ID='your_chat_id'\n")
        return
    
    try:
        bot = VideoClientHunterBot()
        sent = bot.run()
        print(f"✅ تم إرسال {sent} فرصة جديدة")
        
    except KeyboardInterrupt:
        print("\n⚠️ تم الإيقاف (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

import os, requests, time

def send_telegram(text):
    # نتحقق أولاً أن النص ليس فارغاً
    if not text or len(text.strip()) < 5:
        print("⚠️ رسالة فارغة أو قصيرة جداً، تم الغاء الارسال")
        return
        
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # نرسل كنص عادي (Plain Text) لتجنب مشاكل الرموز
    payload = {'chat_id': chat_id, 'text': text}
    res = requests.post(url, json=payload)
    
    if res.status_code == 200:
        print("✅ تم الإرسال بنجاح")
    else:
        print(f"❌ خطأ في الإرسال: {res.text}")

def start():
    print("🚀 بدء فحص رديت...")
    
    # كلمات بحث محددة
    queries = ['hiring video editor', 'looking for video editor']
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for q in queries:
        try:
            # طلب البيانات من رديت
            response = requests.get(f"https://www.reddit.com/search.json?q={q}&sort=new&limit=5", headers=headers)
            if response.status_code == 200:
                posts = response.json().get('data', {}).get('children', [])
                
                for p in posts:
                    data = p['data']
                    title = data.get('title', 'بدون عنوان')
                    link = f"https://reddit.com{data.get('permalink', '')}"
                    
                    # نجهز الرسالة بشكل بسيط جداً
                    clean_msg = f"🎯 وظيفة فيديو جديدة:\n\n📌 العنوان: {title}\n\n🔗 الرابط: {link}"
                    
                    send_telegram(clean_msg)
                    time.sleep(3) # راحة بين كل رسالة
            else:
                print(f"⚠️ فشل رديت: {response.status_code}")
        except Exception as e:
            print(f"❌ خطأ تقني: {e}")

if __name__ == "__main__":
    # نرسل رسالة تجريبية أولاً لنرى هل تصل "فارغة" أم لا
    send_telegram("📡 البوت بدأ العمل بنجاح.. جاري فحص الوظائف حالياً.")
    start()

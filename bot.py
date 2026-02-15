import os, requests, time

# بياناتك المباشرة
TOKEN = "7699373105:AAEu8IHqroR_QcPhWz142cQywaf881xPDE0"
CHAT_ID = "8497315428"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text}
    try:
        res = requests.post(url, json=payload)
        return res.status_code == 200
    except:
        return False

def start_hunting():
    # رسالة تأكيد التشغيل
    send_telegram("🚀 تم تفعيل البوت الجديد بنجاح! جاري البحث عن وظائف...")
    
    queries = ['hiring video editor', 'looking for video editor', 'youtube editor']
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for q in queries:
        try:
            url = f"https://www.reddit.com/search.json?q={q}&sort=new&limit=5"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                posts = res.json().get('data', {}).get('children', [])
                for p in posts:
                    data = p['data']
                    msg = f"🎯 فرصة فيديو:\n{data['title']}\n\n🔗 https://reddit.com{data['permalink']}"
                    send_telegram(msg)
                    time.sleep(2)
        except:
            continue
    send_telegram("✅ انتهى الفحص الدوري.")

if __name__ == "__main__":
    start_hunting()
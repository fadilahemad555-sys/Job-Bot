# ============================================================
# منصة بريكولات - الملف الرئيسي (نسخة مبسطة)
# ✅ زر Google واحد فقط للزوار غير المسجلين
# ✅ إكمال ملف مبسط (الاسم، التخصص، المدينة)
# ✅ جلسة دائمة
# ============================================================

import os
import re
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message as MailMessage
from authlib.integrations.flask_client import OAuth

# ================== إعدادات التطبيق ==================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bricolets-super-secret-key')
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['SESSION_PERMANENT'] = True

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///bricolets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ================== إعدادات البريد ==================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hichamcasawi709@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = 'hichamcasawi709@gmail.com'
mail = Mail(app)

# ================== إعدادات Google OAuth ==================
oauth = OAuth(app)
GOOGLE_CLIENT_ID = '72444910931-8jqc98ph36rs703c4c4sp3jkqku6lvt0.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = 'https://bricoletsapp.pythonanywhere.com/callback/google'

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'},
    redirect_uri=GOOGLE_REDIRECT_URI
)

# ================== إعدادات التخزين ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'ogg', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# ================== نماذج قاعدة البيانات ==================
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_google'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    user_type = db.Column(db.String(20), nullable=False, default='client')
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    profile_image = db.Column(db.String(200), nullable=True)
    specialty = db.Column(db.String(50), nullable=True)
    video_work = db.Column(db.String(200), nullable=True)
    portfolio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    experience_years = db.Column(db.Integer, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def profile_completed(self):
        return bool(self.full_name and self.district and self.specialty)

class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    specialty = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    images = db.Column(db.Text, nullable=True)
    voice = db.Column(db.String(200), nullable=True)
    video = db.Column(db.String(200), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    offers_count = db.Column(db.Integer, default=0)
    client = db.relationship('User', backref='requests')

class Offer(db.Model):
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, nullable=True)
    voice = db.Column(db.String(200), nullable=True)
    video = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, nullable=True)
    voice = db.Column(db.String(200), nullable=True)
    video = db.Column(db.String(200), nullable=True)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=True)
    score = db.Column(db.Float, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# إنشاء الجداول والمستخدمين التجريبيين
with app.app_context():
    db.create_all()
    # إضافة المستخدمين (نفس الكود السابق مختصر)
    try:
        if not User.query.filter_by(email='hichamcasawi709@gmail.com').first():
            u = User(username='hicham', email='hichamcasawi709@gmail.com', password=generate_password_hash('hi555657585959'), full_name='هشام', district='مراكش', is_admin=True, specialty='مطور')
            db.session.add(u)
        db.session.commit()
    except: pass

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== دوال مساعدة ==================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_to_local(file, subfolder=''):
    if not file or not file.filename: return None
    if not allowed_file(file.filename):
        flash('نوع الملف غير مسموح به', 'danger')
        return None
    try:
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        new_filename = f"{name}_{timestamp}{ext}"
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder_path, exist_ok=True)
        file.save(os.path.join(folder_path, new_filename))
        return f'/uploads/{subfolder}/{new_filename}'
    except Exception as e:
        print(e)
        return None

def save_multiple_files(files, subfolder=''):
    urls = []
    for f in files:
        if f and f.filename:
            url = save_file_to_local(f, subfolder)
            if url: urls.append(url)
    return ','.join(urls)

def delete_file(file_url):
    if not file_url or not file_url.startswith('/uploads/'): return
    try:
        full = os.path.join(app.config['UPLOAD_FOLDER'], file_url.replace('/uploads/', '', 1))
        if os.path.exists(full): os.remove(full)
    except: pass

def contains_blocked_patterns(text):
    if not text: return False
    return bool(re.search(r'(\+212|0)[5-7]\d{8}', text) or re.search(r'(facebook|whatsapp|instagram|tiktok|telegram|wa\.me|fb\.com)', text, re.I))

def time_ago(dt):
    if not dt: return "منذ فترة"
    diff = datetime.utcnow() - dt
    if diff.days: return f"منذ {diff.days} يوم"
    if diff.seconds//3600: return f"منذ {diff.seconds//3600} ساعة"
    if diff.seconds//60: return f"منذ {diff.seconds//60} دقيقة"
    return "منذ لحظات"

def get_unread_messages_count(user_id):
    chats = Chat.query.filter((Chat.client_id==user_id)|(Chat.artisan_id==user_id)).all()
    return sum(Message.query.filter_by(chat_id=c.id, is_read=False).filter(Message.sender_id!=user_id).count() for c in chats)

def get_artisan_rating(artisan_id):
    ratings = Rating.query.filter_by(rated_id=artisan_id).all()
    if not ratings: return 0,0
    avg = sum(r.score for r in ratings if r.score)/len(ratings)
    return round(avg,1), len(ratings)

def normalize_city(city):
    return ' '.join(city.strip().split()) if city else city

def is_admin_user(user):
    return user and hasattr(user, 'is_admin') and user.is_admin

def admin_required(f):
    @wraps(f)
    def dec(*a,**k):
        if not current_user.is_authenticated or not is_admin_user(current_user):
            flash('غير مصرح')
            return redirect(url_for('index'))
        return f(*a,**k)
    return dec

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

app.jinja_env.globals.update(time_ago=time_ago, get_unread_messages_count=get_unread_messages_count)

# ================== بيانات المدن والتخصصات ==================
MOROCCAN_CITIES = ['الدار البيضاء','مراكش','فاس','طنجة','أكادير','الرباط','مكناس','وجدة','سلا','القنيطرة']
SPECIALTIES = ['بلومبي','نجار','سباك','كهربائي','رسام','حدائق','جباص','المنيوم','جلايجي','كباص']

# ================== مسارات Google OAuth ==================
@app.route('/login-google')
def login_google():
    return google.authorize_redirect(url_for('google_callback', _external=True))

@app.route('/callback/google')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    email = user_info.get('email')
    google_id = user_info.get('id')
    name = user_info.get('name')
    if not email:
        flash('فشل البريد')
        return redirect(url_for('login_google'))
    user = User.query.filter((User.email==email)|(User.google_id==google_id)).first()
    if user:
        if not user.google_id: user.google_id = google_id
        db.session.commit()
        login_user(user, remember=True)
        if not user.profile_completed:
            return redirect(url_for('complete_profile'))
        return redirect(url_for('index'))
    else:
        username = email.split('@')[0]
        base = username
        cnt=1
        while User.query.filter_by(username=username).first():
            username = f"{base}{cnt}"
            cnt+=1
        user = User(username=username, email=email, password=generate_password_hash(os.urandom(16).hex()), google_id=google_id, full_name=name, user_type='client', is_admin=(email=='hichamcasawi709@gmail.com'))
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash('تم التسجيل. أكمل بياناتك')
        return redirect(url_for('complete_profile'))

# ================== إكمال الملف الشخصي المبسط ==================
@app.route('/complete-profile', methods=['GET','POST'])
@login_required
def complete_profile():
    if current_user.profile_completed:
        return redirect(url_for('index'))
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        district = request.form.get('district','').strip()
        specialty = request.form.get('specialty','').strip()
        if specialty == 'other':
            specialty = request.form.get('other_specialty','').strip()
        if not full_name or not district or not specialty:
            flash('جميع الحقول مطلوبة', 'danger')
            return redirect(url_for('complete_profile'))
        current_user.full_name = full_name
        current_user.district = normalize_city(district)
        current_user.specialty = specialty
        db.session.commit()
        flash('تم إكمال الملف الشخصي بنجاح', 'success')
        return redirect(url_for('index'))
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>إكمال الملف</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container" style="max-width:500px;margin-top:50px"><h2 class="text-center">أكمل ملفك الشخصي</h2>
    <form method="POST"><div class="mb-3"><label>الاسم الكامل</label><input type="text" name="full_name" class="form-control" required></div>
    <div class="mb-3"><label>المدينة</label><input list="cities" name="district" class="form-control" required><datalist id="cities">{% for city in MOROCCAN_CITIES %}<option value="{{ city }}">{% endfor %}</datalist></div>
    <div class="mb-3"><label>التخصص</label><select name="specialty" id="spec" class="form-select" onchange="if(this.value=='other') document.getElementById('other_spec').style.display='block'; else document.getElementById('other_spec').style.display='none';"><option value="">اختر</option>{% for s in SPECIALTIES %}<option value="{{ s }}">{{ s }}</option>{% endfor %}<option value="other">تخصص آخر</option></select>
    <input type="text" name="other_specialty" id="other_spec" class="form-control mt-2" style="display:none;" placeholder="اكتب تخصصك"></div>
    <button type="submit" class="btn btn-primary w-100">تم</button></form></div></body></html>
    ''', MOROCCAN_CITIES=MOROCCAN_CITIES, SPECIALTIES=SPECIALTIES)# ================== الصفحة الرئيسية ==================
@app.route('/')
def index():
    # 1. زائر غير مسجل: يرى فقط زر Google
    if not current_user.is_authenticated:
        total_clients = User.query.filter_by(user_type='client').count()
        total_artisans = User.query.filter_by(user_type='artisan').count()
        return render_template_string('''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>بريكولات - تسجيل الدخول</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; }
                .card { max-width: 400px; border-radius: 20px; text-align: center; padding: 30px; }
                .btn-google { background: #4285f4; color: white; padding: 12px 20px; border-radius: 40px; text-decoration: none; display: inline-block; font-weight: bold; }
                .btn-google:hover { background: #357ae8; color: white; }
            </style>
        </head>
        <body>
            <div class="card shadow">
                <h2 class="mb-3">🔨 بريكولات</h2>
                <p class="mb-4">منصة الحرفيين في المغرب</p>
                <a href="{{ url_for('login_google') }}" class="btn-google">📱 تسجيل الدخول عبر Google</a>
                <small class="d-block mt-3 text-muted">👥 {{ total_clients }} زبون | 🔨 {{ total_artisans }} حرفي</small>
            </div>
        </body>
        </html>
        ''', total_clients=total_clients, total_artisans=total_artisans)

    # 2. مستخدم مسجل لكن لم يكمل الملف الشخصي
    if not current_user.profile_completed:
        return redirect(url_for('complete_profile'))

    # 3. مستخدم مسجل وكامل الملف: الصفحة الكاملة
    total_clients = User.query.filter_by(user_type='client').count()
    total_artisans = User.query.filter_by(user_type='artisan').count()
    all_requests = Request.query.filter_by(status='open').order_by(Request.created_at.desc()).all()
    my_requests = Request.query.filter_by(client_id=current_user.id).order_by(Request.created_at.desc()).all()
    unread = get_unread_messages_count(current_user.id)

    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>بريكولات - الرئيسية</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}
            .cover-image{width:100%;max-height:300px;object-fit:cover;border-radius:10px;margin-bottom:20px;cursor:pointer;}
            .action-btn-group{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0;}
            .action-btn{flex:1 1 auto;min-width:200px;padding:15px;border-radius:10px;text-align:center;text-decoration:none;color:white;font-weight:bold;transition:0.3s;}
            .action-btn.primary{background-color:#007bff;}
            .action-btn.success{background-color:#28a745;}
            .action-btn.warning{background-color:#ffc107;color:black;}
            .action-btn.info{background-color:#17a2b8;}
            .request-card{margin-bottom:20px;border:1px solid #ddd;border-radius:10px;padding:15px;background:#f9f9f9;}
            .apk-button{position:fixed;top:20px;right:20px;background-color:#ff9800;color:white;padding:8px 12px;border-radius:30px;font-size:14px;text-decoration:none;z-index:1000;}
        </style>
    </head>
    <body>
        <a href="https://apk.e-droid.net/apk/app3935653-hz92wj.apk?v=1" class="apk-button" target="_blank">📱 تحميل التطبيق</a>
        <div class="stats-mini">👥 {{ total_clients }} | 🔨 {{ total_artisans }}</div>
        <div class="container mt-4">
            <img src="{{ url_for('static', filename='cover.jpg') }}?v={{ range(1, 1000) | random }}" class="cover-image" onclick="openModal(this.src)" onerror="this.src='https://images.unsplash.com/photo-1565008447742-97f6f38c985c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80';">
            {% if current_user.is_admin %}
            <div class="mb-3"><form method="POST" action="{{ url_for('upload_cover_image') }}" enctype="multipart/form-data" class="d-flex"><input type="file" name="cover_image" class="form-control form-control-sm w-50" required><button type="submit" class="btn btn-sm btn-success">رفع غلاف</button></form></div>
            {% endif %}
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>مرحباً {{ current_user.full_name or current_user.username }}</h2>
                <div>
                    <a href="/profile" class="btn btn-outline-primary">الملف الشخصي</a>
                    <a href="/messages" class="btn btn-outline-info position-relative">الرسائل{% if unread > 0 %}<span class="badge bg-danger">{{ unread }}</span>{% endif %}</a>
                    <a href="/logout" class="btn btn-danger">تسجيل خروج</a>
                </div>
            </div>
            <div class="action-btn-group">
                <a href="{{ url_for('post_request') }}" class="action-btn primary">أنا صاحب منزل أحتاج معلم</a>
                <a href="{{ url_for('post_request') }}" class="action-btn success">أنا صاحب شركة أحتاج مقاول</a>
                <a href="{{ url_for('post_request') }}" class="action-btn warning">أنا مقاول أحتاج معلم</a>
                <a href="{{ url_for('post_request') }}" class="action-btn info">أنا معلم أحتاج مساعد أو خدام</a>
            </div>
            <div class="action-btn-group">
                <a href="/search" class="action-btn primary">جميع الطلبات في المغرب</a>
                <a href="/search?district={{ current_user.district }}&specialty={{ current_user.specialty }}" class="action-btn success">طلبات في مدينتي وتخصصي</a>
            </div>
            <hr>
            <h3>طلباتي</h3>
            <div class="row">
                {% for req in my_requests %}
                <div class="col-md-6"><div class="request-card"><h5>{{ req.title }}</h5><p>{{ req.description[:100] }}...</p><p><strong>التخصص:</strong> {{ req.specialty }}</p><p><strong>الحي:</strong> {{ req.district }}</p><p><strong>عروض:</strong> {{ req.offers_count }}/30</p><a href="/view-offers/{{ req.id }}" class="btn btn-sm btn-primary">عرض العروض</a> <a href="/delete-request/{{ req.id }}" class="btn btn-sm btn-danger">حذف</a></div></div>
                {% else %}<p class="text-muted">لا توجد طلبات لك. انشر طلبك الآن!</p>{% endfor %}
            </div>
            <hr>
            <h3>الطلبات المفتوحة</h3>
            <div class="row">
                {% for req in all_requests %}
                <div class="col-md-6"><div class="request-card"><h5>{{ req.title }}</h5><p>{{ req.description[:100] }}...</p><p><strong>التخصص:</strong> {{ req.specialty }}</p><p><strong>الحي:</strong> {{ req.district }}</p><p><strong>عروض:</strong> {{ req.offers_count }}/30</p><a href="/view-offers/{{ req.id }}" class="btn btn-sm btn-primary">عرض التفاصيل</a> {% if req.status == 'open' and req.offers_count < 30 %}<a href="/send-offer/{{ req.id }}" class="btn btn-sm btn-success">تقديم عرض</a>{% endif %}</div></div>
                {% else %}<p class="text-muted">لا توجد طلبات مفتوحة حالياً.</p>{% endfor %}
            </div>
        </div>
        <div class="modal fade" id="imageModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-body"><img src="" id="modalImage" style="width:100%;"></div></div></div></div>
        <script>function openModal(src){ document.getElementById('modalImage').src=src; new bootstrap.Modal(document.getElementById('imageModal')).show(); }</script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body></html>
    ''', total_clients=total_clients, total_artisans=total_artisans, all_requests=all_requests, my_requests=my_requests, unread=unread)


# ================== مسارات إضافية ==================
@app.route('/messages')
@login_required
def messages_list():
    if current_user.user_type == 'client':
        chats = Chat.query.filter_by(client_id=current_user.id).order_by(Chat.created_at.desc()).all()
    else:
        chats = Chat.query.filter_by(artisan_id=current_user.id).order_by(Chat.created_at.desc()).all()
    data = []
    for c in chats:
        other = User.query.get(c.artisan_id if current_user.id==c.client_id else c.client_id)
        last = Message.query.filter_by(chat_id=c.id).order_by(Message.created_at.desc()).first()
        unread = Message.query.filter_by(chat_id=c.id, is_read=False).filter(Message.sender_id != current_user.id).count()
        data.append({'chat':c, 'other':other, 'last':last, 'unread':unread})
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>الرسائل</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><h1>الرسائل</h1><a href="/" class="btn btn-secondary mb-3">العودة</a>
    <div class="list-group">{% for item in data %}<a href="/chat/{{ item.chat.id }}" class="list-group-item list-group-item-action d-flex justify-content-between"><div><img src="{{ item.other.profile_image or '/uploads/placeholder.jpg' }}" style="width:40px;height:40px;border-radius:50%;object-fit:cover; margin-left:10px;"><strong>{{ item.other.full_name or item.other.username }}</strong><br><small>{% if item.last %}{{ item.last.content[:50] }}{% else %}لا توجد رسائل{% endif %}</small></div>{% if item.unread >0 %}<span class="badge bg-danger">{{ item.unread }}</span>{% endif %}</a>{% else %}<p>لا توجد محادثات</p>{% endfor %}</div></div></body></html>''', data=data)

@app.route('/chat/<int:chat_id>', methods=['GET','POST'])
@login_required
def view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if current_user.id not in [chat.client_id, chat.artisan_id] and not is_admin_user(current_user):
        return redirect(url_for('index'))
    other = User.query.get(chat.artisan_id if current_user.id==chat.client_id else chat.client_id)
    if request.method == 'POST':
        content = request.form.get('message', '')
        if contains_blocked_patterns(content):
            flash('الرسالة تحتوي على رقم هاتف أو رابط ممنوع')
            return redirect(url_for('view_chat', chat_id=chat_id))
        images = voice = video = ''
        if 'images' in request.files:
            files = request.files.getlist('images')
            if files and files[0].filename:
                images = save_multiple_files(files, subfolder=f"chats/{chat_id}")
        if 'voice' in request.files:
            f = request.files['voice']
            if f and f.filename:
                voice = save_file_to_local(f, subfolder=f"chats/{chat_id}")
        if 'video' in request.files:
            f = request.files['video']
            if f and f.filename:
                video = save_file_to_local(f, subfolder=f"chats/{chat_id}")
        msg = Message(chat_id=chat_id, sender_id=current_user.id, content=content, images=images, voice=voice, video=video)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('view_chat', chat_id=chat_id))
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    for m in messages:
        if m.sender_id != current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>محادثة</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.message-container{height:400px;overflow-y:scroll;border:1px solid #ddd;padding:10px;background:#f9f9f9;margin-bottom:10px;}.my-message{background:#007bff;color:white;margin-left:auto;padding:8px;border-radius:15px;max-width:70%;clear:both;float:right;}.other-message{background:#e9ecef;padding:8px;border-radius:15px;max-width:70%;clear:both;float:left;}</style></head>
    <body><div class="container mt-5"><div class="d-flex"><img src="{{ other.profile_image or '/uploads/placeholder.jpg' }}" style="width:50px;height:50px;border-radius:50%;"><h4 class="mx-2">{{ other.full_name or other.username }}</h4></div>
    <div class="message-container" id="messageContainer">{% for m in messages %}<div class="{% if m.sender_id==current_user.id %}my-message{% else %}other-message{% endif %}">{{ m.content }}{% if m.images %}<br><a href="{{ m.images }}" target="_blank">📷 عرض الصور</a>{% endif %}</div>{% endfor %}</div>
    <form method="POST" enctype="multipart/form-data"><textarea name="message" class="form-control" rows="2" placeholder="اكتب رسالتك..."></textarea><div class="mt-2"><button type="submit" class="btn btn-primary">إرسال</button><input type="file" name="images" accept="image/*" multiple style="display:none;" id="imgInput"><label for="imgInput" class="btn btn-secondary">➕ صور</label></div></form></div>
    <script>var c=document.getElementById('messageContainer');c.scrollTop=c.scrollHeight;</script></body></html>''', messages=messages, other=other)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج', 'success')
    return redirect(url_for('index'))

@app.route('/artisans')
def artisans_list():
    artisans = User.query.filter_by(user_type='artisan').all()
    data = []
    for a in artisans:
        avg, num = get_artisan_rating(a.id)
        data.append({'artisan':a, 'avg':avg, 'num':num})
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>الحرفيون</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><h1>الحرفيون</h1><div class="row">{% for item in data %}<div class="col-md-4 mb-3"><div class="card"><img src="{{ item.artisan.profile_image or '/uploads/placeholder.jpg' }}" class="card-img-top" style="height:200px;object-fit:cover;"><div class="card-body"><h5><a href="/user/{{ item.artisan.id }}">{{ item.artisan.full_name }}</a></h5><p>{{ item.artisan.specialty }} - {{ item.artisan.district }}</p>{% if item.num>0 %}<p>⭐ {{ item.avg }} ({{ item.num }})</p>{% endif %}</div></div></div>{% endfor %}</div><a href="/" class="btn btn-secondary">العودة</a></div></body></html>''', data=data)

@app.route('/user/<int:user_id>')
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    portfolio_list = user.portfolio.split(',') if user.portfolio else []
    avg, num = get_artisan_rating(user.id) if user.user_type=='artisan' else (0,0)
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>{{ user.full_name }}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><div class="text-center"><img src="{{ user.profile_image or '/uploads/placeholder.jpg' }}" style="width:150px;height:150px;border-radius:50%;"><h2>{{ user.full_name }}</h2><p>{{ user.district }} - {{ user.specialty }}</p>{% if user.user_type=='artisan' and portfolio_list %}<h3>أعماله</h3><div class="row">{% for img in portfolio_list %}<div class="col-md-3"><img src="{{ img }}" class="img-fluid mb-2"></div>{% endfor %}</div>{% endif %}</div><a href="/" class="btn btn-secondary">رجوع</a></div></body></html>''', user=user, portfolio_list=portfolio_list, avg=avg, num=num)

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.district = request.form['district']
        current_user.phone = request.form.get('phone','')
        current_user.specialty = request.form['specialty']
        exp = request.form.get('experience_years','')
        if exp.isdigit():
            current_user.experience_years = int(exp)
        if 'profile_image' in request.files:
            f = request.files['profile_image']
            if f and f.filename:
                if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
                    delete_file(current_user.profile_image)
                url = save_file_to_local(f, subfolder=f"users/{current_user.id}")
                if url:
                    current_user.profile_image = url
        if 'video_work' in request.files:
            f = request.files['video_work']
            if f and f.filename:
                url = save_file_to_local(f, subfolder=f"artisans/{current_user.id}")
                if url:
                    current_user.video_work = url
        if 'new_portfolio' in request.files:
            files = request.files.getlist('new_portfolio')
            if files and files[0].filename:
                urls = save_multiple_files(files, subfolder=f"artisans/{current_user.id}/portfolio")
                if urls:
                    old = current_user.portfolio.split(',') if current_user.portfolio else []
                    current_user.portfolio = ','.join(old + urls.split(','))
        db.session.commit()
        flash('تم تحديث الملف الشخصي', 'success')
        return redirect(url_for('profile'))
    portfolio_list = current_user.portfolio.split(',') if current_user.portfolio else []
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>ملفي</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><h2>الملف الشخصي</h2><form method="POST" enctype="multipart/form-data"><div class="mb-3"><label>الاسم</label><input type="text" name="full_name" value="{{ current_user.full_name }}" class="form-control"></div>
    <div class="mb-3"><label>رقم الهاتف</label><input type="text" name="phone" value="{{ current_user.phone }}" class="form-control"></div>
    <div class="mb-3"><label>المدينة</label><input type="text" name="district" value="{{ current_user.district }}" class="form-control"></div>
    <div class="mb-3"><label>التخصص</label><select name="specialty" class="form-select">{% for s in SPECIALTIES %}<option value="{{ s }}" {% if current_user.specialty==s %}selected{% endif %}>{{ s }}</option>{% endfor %}</select></div>
    <div class="mb-3"><label>سنوات الخبرة</label><input type="number" name="experience_years" value="{{ current_user.experience_years }}" class="form-control"></div>
    <div class="mb-3"><label>الصورة الشخصية</label><input type="file" name="profile_image" class="form-control"></div>
    <div class="mb-3"><label>فيديو العمل</label><input type="file" name="video_work" class="form-control"></div>
    <div class="mb-3"><label>صور أعمال جديدة</label><input type="file" name="new_portfolio" class="form-control" multiple accept="image/*"></div>
    <button type="submit" class="btn btn-primary">حفظ</button></form>
    {% if portfolio_list %}<h3 class="mt-4">أعمالي الحالية</h3><div class="row">{% for img in portfolio_list %}<div class="col-md-3"><img src="{{ img }}" class="img-fluid mb-2"></div>{% endfor %}</div>{% endif %}
    <a href="/" class="btn btn-secondary mt-3">رجوع</a></div></body></html>''', current_user=current_user, SPECIALTIES=SPECIALTIES, portfolio_list=portfolio_list)

@app.route('/search')
def search():
    specialty = request.args.get('specialty','')
    district = request.args.get('district','')
    q = Request.query.filter_by(status='open')
    if specialty: q = q.filter_by(specialty=specialty)
    if district: q = q.filter_by(district=district)
    requests = q.order_by(Request.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>بحث</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><h1>الطلبات المفتوحة</h1><a href="/" class="btn btn-secondary mb-3">العودة</a><div class="row">{% for req in requests %}<div class="col-md-6"><div class="card mb-3"><div class="card-body"><h5>{{ req.title }}</h5><p>{{ req.description[:100] }}</p><p>{{ req.specialty }} - {{ req.district }}</p><a href="/view-offers/{{ req.id }}" class="btn btn-sm btn-primary">عرض</a></div></div></div>{% endfor %}</div></div></body></html>''', requests=requests)

@app.route('/post-request', methods=['GET','POST'])
@login_required
def post_request():
    if request.method == 'POST':
        title = request.form.get('title','طلب خدمة')
        desc = request.form['description']
        specialty = request.form['specialty']
        if specialty == 'other':
            specialty = request.form.get('other_specialty','')
        district = request.form['district']
        images = ''
        if 'images' in request.files:
            files = request.files.getlist('images')
            images = save_multiple_files(files, subfolder='requests')
        req = Request(title=title, description=desc, specialty=specialty, district=district, images=images, client_id=current_user.id)
        db.session.add(req)
        db.session.commit()
        flash('تم نشر الطلب', 'success')
        return redirect(url_for('index'))
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>نشر طلب</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container" style="max-width:600px;margin-top:50px"><h2>طلب جديد</h2><form method="POST" enctype="multipart/form-data"><div class="mb-3"><label>العنوان</label><input type="text" name="title" class="form-control" value="طلب خدمة"></div>
    <div class="mb-3"><label>الوصف</label><textarea name="description" class="form-control" rows="4" required></textarea></div>
    <div class="mb-3"><label>التخصص</label><select name="specialty" class="form-select" onchange="if(this.value=='other')document.getElementById('other_spec').style.display='block';else document.getElementById('other_spec').style.display='none';">{% for s in SPECIALTIES %}<option value="{{ s }}">{{ s }}</option>{% endfor %}<option value="other">تخصص آخر</option></select><input type="text" name="other_specialty" id="other_spec" class="form-control mt-2" style="display:none;"></div>
    <div class="mb-3"><label>المدينة</label><input list="cities" name="district" class="form-control" required><datalist id="cities">{% for city in MOROCCAN_CITIES %}<option>{{ city }}</option>{% endfor %}</datalist></div>
    <div class="mb-3"><label>صور</label><input type="file" name="images" class="form-control" multiple accept="image/*"></div>
    <button type="submit" class="btn btn-primary">نشر</button></form></div></body></html>''', SPECIALTIES=SPECIALTIES, MOROCCAN_CITIES=MOROCCAN_CITIES)

@app.route('/send-offer/<int:request_id>', methods=['GET','POST'])
@login_required
def send_offer(request_id):
    req = Request.query.get_or_404(request_id)
    if req.status != 'open' or req.offers_count >= 30:
        flash('الطلب مغلق', 'danger')
        return redirect(url_for('index'))
    if Offer.query.filter_by(request_id=request_id, artisan_id=current_user.id).first():
        flash('سبق أن قدمت عرضاً', 'warning')
        return redirect(url_for('index'))
    if request.method == 'POST':
        message = request.form['message']
        images = ''
        if 'images' in request.files:
            files = request.files.getlist('images')
            if files and files[0].filename:
                images = save_multiple_files(files, subfolder=f"offers/{request_id}")
        offer = Offer(request_id=request_id, artisan_id=current_user.id, message=message, images=images)
        db.session.add(offer)
        req.offers_count += 1
        if req.offers_count >= 30:
            req.status = 'cancelled'
        db.session.commit()
        chat = Chat.query.filter_by(request_id=request_id, client_id=req.client_id, artisan_id=current_user.id).first()
        if not chat:
            chat = Chat(request_id=request_id, client_id=req.client_id, artisan_id=current_user.id)
            db.session.add(chat)
            db.session.commit()
        msg = Message(chat_id=chat.id, sender_id=current_user.id, content=f"عرض: {message}", images=images)
        db.session.add(msg)
        db.session.commit()
        flash('تم إرسال العرض', 'success')
        return redirect(url_for('index'))
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>تقديم عرض</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container" style="max-width:600px;margin-top:50px"><h2>تقديم عرض للطلب: {{ req.title }}</h2><form method="POST" enctype="multipart/form-data"><textarea name="message" class="form-control" rows="4" required placeholder="رسالتك..."></textarea><div class="mt-3"><label>صور (اختياري)</label><input type="file" name="images" class="form-control" multiple accept="image/*"></div><button type="submit" class="btn btn-primary mt-3">إرسال العرض</button></form></div></body></html>''', req=req)

@app.route('/view-offers/<int:request_id>')
@login_required
def view_offers(request_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id != current_user.id and not is_admin_user(current_user):
        return redirect(url_for('index'))
    offers = Offer.query.filter_by(request_id=request_id).all()
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>العروض</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><h1>عروض الطلب: {{ req.title }}</h1><div class="row">{% for o in offers %}<div class="col-md-4 mb-3"><div class="card"><div class="card-body"><h5>{{ o.artisan.full_name }}</h5><p>{{ o.message }}</p>{% if o.images %}<a href="{{ o.images }}" target="_blank">صور</a>{% endif %}</div></div></div>{% endfor %}</div><a href="/" class="btn btn-secondary">رجوع</a></div></body></html>''', req=req, offers=offers)

@app.route('/delete-request/<int:request_id>')
@login_required
def delete_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id != current_user.id and not is_admin_user(current_user):
        flash('غير مصرح', 'danger')
        return redirect(url_for('index'))
    db.session.delete(req)
    db.session.commit()
    flash('تم حذف الطلب', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    requests = Request.query.all()
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>لوحة الإدارة</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body><div class="container mt-5"><h1>لوحة الإدارة</h1><h3>المستخدمون</h3><table class="table"><tr><th>ID</th><th>الاسم</th><th>البريد</th><th>النوع</th></tr>{% for u in users %}<tr><td>{{ u.id }}</td><td>{{ u.full_name }}</td><td>{{ u.email }}</td><td>{{ u.user_type }}</td></tr>{% endfor %}</table>
    <h3>الطلبات</h3><table class="table"><tr><th>ID</th><th>العنوان</th><th>العميل</th><th>الحالة</th></tr>{% for r in requests %}<tr><td>{{ r.id }}</td><td>{{ r.title }}</td><td>{{ r.client.full_name }}</td><td>{{ r.status }}</td></tr>{% endfor %}</table>
    <a href="/" class="btn btn-secondary">الرئيسية</a></div></body></html>''', users=users, requests=requests)

@app.route('/upload-instruction-image', methods=['POST'])
@login_required
@admin_required
def upload_instruction_image():
    file = request.files.get('instruction_image')
    if file and allowed_file(file.filename):
        filename = 'instruction.jpg'
        filepath = os.path.join(STATIC_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        file.save(filepath)
        flash('تم رفع الصورة التعليمية', 'success')
    else:
        flash('فشل الرفع', 'danger')
    return redirect(request.referrer or url_for('index'))

@app.route('/test-email')
@login_required
@admin_required
def test_email():
    try:
        msg = MailMessage(subject="اختبار", recipients=['hichamcasawi709@gmail.com'], html="<h1>نجاح</h1>")
        mail.send(msg)
        return "✅ تم إرسال البريد"
    except Exception as e:
        return f"❌ فشل: {e}"

@app.route('/list-users-email')
@login_required
@admin_required
def list_users_email():
    users = User.query.filter(User.email != None, User.email != '').all()
    result = "<h2>المستخدمون ذوو بريد</h2><ul>"
    for u in users:
        result += f"<li>{u.id}: {u.email} - {u.full_name}</li>"
    result += f"<p>العدد: {len(users)}</p></ul>"
    return result

@app.route('/client-dashboard')
@login_required
def client_dashboard():
    return redirect(url_for('index'))

@app.route('/artisan-dashboard')
@login_required
def artisan_dashboard():
    return redirect(url_for('index'))

@app.route('/upload-cover-image', methods=['POST'])
@login_required
@admin_required
def upload_cover_image():
    file = request.files.get('cover_image')
    if file and allowed_file(file.filename):
        filepath = os.path.join(STATIC_FOLDER, 'cover.jpg')
        if os.path.exists(filepath):
            os.remove(filepath)
        file.save(filepath)
        flash('تم رفع صورة الغلاف', 'success')
    else:
        flash('فشل الرفع', 'danger')
    return redirect(request.referrer or url_for('index'))

# ================== تشغيل التطبيق ==================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

print("✅ تم تحميل الملف بالكامل مع التعديلات المطلوبة.")


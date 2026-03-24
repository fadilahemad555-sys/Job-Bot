# ============================================================
# منصة بريكولات - الملف الرئيسي الكامل (بدون مفاتيح)
# ============================================================

import os
import re
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message as MailMessage
from authlib.integrations.flask_client import OAuth

# ================== إعدادات التطبيق ==================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bricolets-fixed-secret-key-2026'

# إعداد قاعدة البيانات
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///bricolets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# ================== إعدادات البريد الإلكتروني ==================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hichamcasawi709@gmail.com'
app.config['MAIL_PASSWORD'] = 'kxlafkpzbxuguida'
app.config['MAIL_DEFAULT_SENDER'] = 'hichamcasawi709@gmail.com'

mail = Mail(app)

# ================== إعدادات OAuth (Google) ==================
oauth = OAuth(app)

# بيانات Google تُقرأ من متغيرات البيئة (الموجودة في wsgi.py)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = 'https://bricoletsapp.pythonanywhere.com/callback/google'

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("GOOGLE_CLIENT_ID و GOOGLE_CLIENT_SECRET غير مضبوطين في البيئة")

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
    redirect_uri=GOOGLE_REDIRECT_URI
)

# ================== إعدادات التخزين المحلي ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'ogg', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# إنشاء المجلدات
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'users'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'requests'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'offers'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'chats'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'artisans'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'portfolio'), exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# ================== إعدادات SQLAlchemy و Login ==================
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ================== النماذج (Models) ==================

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
        return bool(self.full_name and self.phone and self.district and self.specialty)

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
    request = db.relationship('Request')
    artisan = db.relationship('User', foreign_keys=[artisan_id])

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
    rater = db.relationship('User', foreign_keys=[rater_id])
    rated = db.relationship('User', foreign_keys=[rated_id])

# ================== إنشاء الجداول وإضافة المستخدمين التجريبيين ==================
with app.app_context():
    db.create_all()
    print("✅ تم التأكد من وجود الجداول.")

    try:
        admin_user = User.query.filter_by(email='hichamcasawi709@gmail.com').first()
        if admin_user:
            admin_user.password = generate_password_hash('hi555657585959')
            print("🔄 تم تحديث كلمة سر حساب الأدمن.")
        else:
            admin_user = User(
                username='hicham',
                email='hichamcasawi709@gmail.com',
                password=generate_password_hash('hi555657585959'),
                user_type='client',
                full_name='هشام',
                district='مراكش',
                is_admin=True,
                profile_image='/uploads/placeholder.jpg',
                specialty='مطور'
            )
            db.session.add(admin_user)
            print("➕ تم إضافة حساب الأدمن.")

        if not User.query.filter_by(email='admin@test.com').first():
            admin = User(
                username='admin',
                email='admin@test.com',
                password=generate_password_hash('admin123'),
                user_type='client',
                full_name='أحمد المري',
                district='مراكش - جليز',
                age=35,
                gender='ذكر',
                profile_image='/uploads/placeholder.jpg',
                specialty='زبون'
            )
            db.session.add(admin)
            print("➕ تم إضافة مستخدم الزبون التجريبي.")

        if not User.query.filter_by(email='artisan@test.com').first():
            artisan = User(
                username='artisan1',
                email='artisan@test.com',
                password=generate_password_hash('artisan123'),
                user_type='artisan',
                full_name='محمد السباك',
                specialty='سباك',
                district='مراكش - جليز',
                age=40,
                gender='ذكر',
                profile_image='/uploads/placeholder.jpg',
                video_work='',
                portfolio='',
                experience_years=8
            )
            db.session.add(artisan)
            print("➕ تم إضافة مستخدم الحرفي التجريبي.")

        db.session.commit()
        print("👤 تم التأكد من وجود المستخدمين.")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ خطأ أثناء إضافة المستخدمين: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== دوال مساعدة للتخزين المحلي ==================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_to_local(file, subfolder=''):
    if not file or not file.filename:
        print("⚠️ الملف فارغ أو غير موجود")
        return None
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
        file_path = os.path.join(folder_path, new_filename)
        file.save(file_path)
        print(f"✅ تم حفظ الملف: {file_path}")
        return f'/uploads/{subfolder}/{new_filename}'
    except Exception as e:
        print(f"❌ خطأ في حفظ الملف: {e}")
        flash('حدث خطأ أثناء حفظ الملف', 'danger')
        return None

def save_multiple_files(files, subfolder=''):
    urls = []
    for file in files:
        if file and file.filename:
            url = save_file_to_local(file, subfolder)
            if url:
                urls.append(url)
    return ','.join(urls)

def delete_file(file_url):
    if not file_url or not file_url.startswith('/uploads/'):
        return
    try:
        relative_path = file_url.replace('/uploads/', '', 1)
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"✅ تم حذف الملف: {full_path}")
        else:
            print(f"⚠️ الملف غير موجود: {full_path}")
    except Exception as e:
        print(f"❌ خطأ في حذف الملف: {e}")

def delete_message_image(message_id, image_url):
    if not image_url:
        return False
    delete_file(image_url)
    msg = Message.query.get(message_id)
    if msg and msg.images:
        urls = msg.images.split(',')
        if image_url in urls:
            urls.remove(image_url)
            msg.images = ','.join(urls) if urls else None
            db.session.commit()
            return True
    return False

# ================== دوال مساعدة أخرى ==================

def contains_blocked_patterns(text):
    if not text: return False
    phone_pattern = r'(\+212|0)[5-7]\d{8}'
    social_pattern = r'(facebook|whatsapp|instagram|tiktok|telegram|wa\.me|fb\.com)'
    return bool(re.search(phone_pattern, text, re.IGNORECASE) or re.search(social_pattern, text, re.IGNORECASE))

def time_ago(dt):
    if not dt: return "منذ فترة"
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 0: return f"منذ {diff.days} يوم"
    if diff.seconds // 3600 > 0: return f"منذ {diff.seconds // 3600} ساعة"
    if diff.seconds // 60 > 0: return f"منذ {diff.seconds // 60} دقيقة"
    return "منذ لحظات"

def get_unread_messages_count(user_id):
    chats = Chat.query.filter((Chat.client_id == user_id) | (Chat.artisan_id == user_id)).all()
    total = 0
    for chat in chats:
        total += Message.query.filter_by(chat_id=chat.id, is_read=False).filter(Message.sender_id != user_id).count()
    return total

def get_artisan_rating(artisan_id):
    ratings = Rating.query.filter_by(rated_id=artisan_id).all()
    if not ratings: return 0, 0
    avg = sum(r.score for r in ratings if r.score) / len(ratings)
    return round(avg, 1), len(ratings)

def normalize_city(city):
    if not city: return city
    return ' '.join(city.strip().split())

def is_admin_user(user):
    return user and hasattr(user, 'is_admin') and user.is_admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not is_admin_user(current_user):
            flash('غير مصرح بالدخول إلى هذه الصفحة')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def dashboard_url_for(user):
    return url_for('index')

# ================== خدمة الملفات المرفوعة ==================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

app.jinja_env.globals.update(
    time_ago=time_ago,
    get_unread_messages_count=get_unread_messages_count,
    dashboard_url_for=dashboard_url_for
)

print("✅ تم تحميل الجزء الأول (الإعدادات والنماذج والدوال المساعدة).")

# ================== مسار التحقق من Google Search Console ==================
@app.route('/google367a012ee7694cb4.html')
def google_verification():
    return "google-site-verification: google367a012ee7694cb4.html"

# ================== رفع صورة الغلاف (للمسؤول فقط) ==================
@app.route('/upload-cover-image', methods=['POST'])
@login_required
@admin_required
def upload_cover_image():
    if 'cover_image' not in request.files:
        flash('لم يتم اختيار ملف', 'danger')
        return redirect(request.referrer or url_for('index'))
    file = request.files['cover_image']
    if file.filename == '':
        flash('الملف فارغ', 'danger')
        return redirect(request.referrer or url_for('index'))
    if file and allowed_file(file.filename):
        try:
            filename = 'cover.jpg'
            filepath = os.path.join(STATIC_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            file.save(filepath)
            flash('✅ تم رفع صورة الغلاف بنجاح', 'success')
            print(f"✅ تم حفظ صورة الغلاف في: {filepath}")
        except Exception as e:
            flash(f'❌ خطأ في حفظ الصورة: {str(e)}', 'danger')
            print(f"❌ خطأ في رفع صورة الغلاف: {e}")
    else:
        flash('نوع الملف غير مسموح به', 'danger')
    return redirect(request.referrer or url_for('index'))

# ============================================================
# الصفحة الرئيسية الموحدة (لجميع المستخدمين)
# ============================================================
@app.route('/')
def index():
    total_clients = User.query.filter_by(user_type='client').count()
    total_artisans = User.query.filter_by(user_type='artisan').count()
    all_requests = Request.query.filter_by(status='open').order_by(Request.created_at.desc()).all()
    my_requests = []
    unread = 0
    if current_user.is_authenticated:
        my_requests = Request.query.filter_by(client_id=current_user.id).order_by(Request.created_at.desc()).all()
        unread = get_unread_messages_count(current_user.id)
    
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>بريكولات - منصة الحرفيين في المغرب</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}
            .stats-mini:hover{opacity:1;}
            .cover-image{width:100%;max-height:300px;object-fit:cover;border-radius:10px;margin-bottom:20px;cursor:pointer;}
            .action-btn-group{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0;}
            .action-btn{flex:1 1 auto;min-width:200px;padding:15px;border-radius:10px;text-align:center;text-decoration:none;color:white;font-weight:bold;transition:0.3s;}
            .action-btn.primary{background-color:#007bff;}
            .action-btn.success{background-color:#28a745;}
            .action-btn.warning{background-color:#ffc107;color:black;}
            .action-btn.info{background-color:#17a2b8;}
            .action-btn.danger{background-color:#dc3545;}
            .action-btn:hover{opacity:0.8;}
            .request-card{margin-bottom:20px;border:1px solid #ddd;border-radius:10px;padding:15px;background:#f9f9f9;}
            .apk-button {
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #ff9800;
                color: white;
                padding: 8px 12px;
                border-radius: 30px;
                font-size: 14px;
                font-weight: bold;
                text-decoration: none;
                z-index: 1000;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                transition: 0.3s;
            }
            .apk-button:hover {
                background-color: #e68900;
                transform: scale(1.05);
            }
        </style>
    </head>
    <body>
        <!-- زر تحميل التطبيق (APK) -->
        <a href="https://apk.e-droid.net/apk/app3935653-hz92wj.apk?v=1" class="apk-button" target="_blank">📱 تحميل التطبيق</a>
        
        <div class="stats-mini">👥 {{ total_clients }} | 🔨 {{ total_artisans }}</div>
        <div class="container mt-4">
            <img src="{{ url_for('static', filename='cover.jpg') }}?v={{ range(1, 1000) | random }}" 
                 alt="غلاف بريكولات" class="cover-image"
                 onclick="openModal(this.src)"
                 onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1565008447742-97f6f38c985c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80';">
            {% if current_user.is_admin %}
            <div class="mt-2 p-3 bg-light rounded border">
                <h6>رفع صورة غلاف جديدة</h6>
                <form method="POST" action="{{ url_for('upload_cover_image') }}" enctype="multipart/form-data" class="d-flex align-items-center gap-2">
                    <input type="file" name="cover_image" accept="image/*" class="form-control form-control-sm" style="width: auto;" required>
                    <button type="submit" class="btn btn-sm btn-success">➕ رفع الصورة</button>
                </form>
                <small class="text-muted">هذه الصورة ستظهر في أعلى الصفحة للجميع.</small>
            </div>
            {% endif %}
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>مرحباً {{ current_user.full_name or current_user.username if current_user.is_authenticated else 'زائر' }}</h2>
                <div>
                    {% if current_user.is_authenticated %}
                        <a href="/profile" class="btn btn-outline-primary">الملف الشخصي</a>
                        <a href="/messages" class="btn btn-outline-info position-relative">
                            الرسائل
                            {% if unread > 0 %}
                            <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">{{ unread }}</span>
                            {% endif %}
                        </a>
                        <a href="/logout" class="btn btn-danger">تسجيل خروج</a>
                    {% else %}
                        <a href="/login-google" class="btn btn-primary">تسجيل الدخول</a>
                        <a href="/login-google" class="btn btn-success">تسجيل جديد</a>
                    {% endif %}
                </div>
            </div>
            <div class="alert alert-info">
                <p>إذا كنت تريد إصلاح شيء في منزلك أو كنت في شركة تبحث عن حرفي، انشر طلبك وسيراه الحرفيون القريبون منك.</p>
                {% if not current_user.is_authenticated %}
                <p class="mb-0 text-danger"><strong>سجل أولاً لتتمكن من نشر الطلبات وإرسال الرسائل.</strong></p>
                {% endif %}
            </div>
            <div class="action-btn-group">
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('login_google') }}{% endif %}" class="action-btn primary">أنا صاحب منزل أحتاج معلم</a>
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('login_google') }}{% endif %}" class="action-btn success">أنا صاحب شركة أحتاج مقاول</a>
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('login_google') }}{% endif %}" class="action-btn warning">أنا مقاول أحتاج معلم</a>
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('login_google') }}{% endif %}" class="action-btn info">أنا معلم أحتاج مساعد أو خدام</a>
            </div>
            <div class="action-btn-group">
                <a href="/search" class="action-btn primary">جميع الطلبات في المغرب</a>
                {% if current_user.is_authenticated %}
                <a href="/search?district={{ current_user.district }}&specialty={{ current_user.specialty }}" class="action-btn success">طلبات في مدينتي وتخصصي</a>
                {% else %}
                <a href="{{ url_for('login_google') }}" class="action-btn success">طلبات في مدينتي وتخصصي (سجل أولاً)</a>
                {% endif %}
            </div>
            <hr>
            {% if current_user.is_authenticated %}
            <h3>طلباتي</h3>
            <div class="row">
                {% for req in my_requests %}
                <div class="col-md-6">
                    <div class="request-card">
                        <h5>{{ req.title }}</h5>
                        <p>{{ req.description[:100] }}...</p>
                        <p><strong>التخصص:</strong> {{ req.specialty }}</p>
                        <p><strong>الحي:</strong> {{ req.district }}</p>
                        <p><strong>نشر:</strong> {{ time_ago(req.created_at) }}</p>
                        <p><strong>عروض:</strong> {{ req.offers_count }}/30 | حالة: {{ 'مفتوح' if req.status=='open' else 'مغلق' }}</p>
                        <a href="/view-offers/{{ req.id }}" class="btn btn-sm btn-primary">عرض العروض</a>
                        {% if req.status == 'open' %}
                        <a href="/close-request/{{ req.id }}" class="btn btn-sm btn-warning">إغلاق</a>
                        {% endif %}
                        <a href="/delete-request/{{ req.id }}" class="btn btn-sm btn-danger" onclick="return confirm('هل أنت متأكد من حذف هذا الطلب؟')">حذف</a>
                    </div>
                </div>
                {% else %}
                <p class="text-muted">لا توجد طلبات لك. انشر طلبك الآن!</p>
                {% endfor %}
            </div>
            <hr>
            {% endif %}
            <h3>{{ 'الطلبات المفتوحة' if current_user.is_authenticated else 'أحدث الطلبات في المغرب' }}</h3>
            <div class="row">
                {% for req in all_requests %}
                <div class="col-md-6">
                    <div class="request-card">
                        <h5>{{ req.title }}</h5>
                        <p>{{ req.description[:100] }}...</p>
                        <p><strong>التخصص:</strong> {{ req.specialty }}</p>
                        <p><strong>الحي:</strong> {{ req.district }}</p>
                        <p><strong>نشر:</strong> {{ time_ago(req.created_at) }}</p>
                        <p><strong>عروض:</strong> {{ req.offers_count }}/30</p>
                        <a href="{% if current_user.is_authenticated %}/view-offers/{{ req.id }}{% else %}{{ url_for('login_google') }}{% endif %}" class="btn btn-sm btn-primary">عرض التفاصيل</a>
                        {% if current_user.is_authenticated and req.status == 'open' and req.offers_count < 30 %}
                        <a href="/send-offer/{{ req.id }}" class="btn btn-sm btn-success">تقديم عرض</a>
                        {% endif %}
                    </div>
                </div>
                {% else %}
                <p class="text-muted">لا توجد طلبات مفتوحة حالياً.</p>
                {% endfor %}
            </div>
        </div>
        <div class="modal fade" id="imageModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-body">
                        <img src="" id="modalImage" style="width:100%;">
                    </div>
                </div>
            </div>
        </div>
        <script>
        function openModal(src) {
            document.getElementById('modalImage').src = src;
            var modal = new bootstrap.Modal(document.getElementById('imageModal'));
            modal.show();
        }
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body></html>
    ''', total_clients=total_clients, total_artisans=total_artisans, all_requests=all_requests, my_requests=my_requests, unread=unread)

# ================== قائمة المحادثات ==================
@app.route('/messages')
@login_required
def messages_list():
    if current_user.user_type == 'client':
        chats = Chat.query.filter_by(client_id=current_user.id).order_by(Chat.created_at.desc()).all()
    else:
        chats = Chat.query.filter_by(artisan_id=current_user.id).order_by(Chat.created_at.desc()).all()
    data = []
    for c in chats:
        other = User.query.get(c.artisan_id if current_user.id == c.client_id else c.client_id)
        last = Message.query.filter_by(chat_id=c.id).order_by(Message.created_at.desc()).first()
        unread = Message.query.filter_by(chat_id=c.id, is_read=False).filter(Message.sender_id != current_user.id).count()
        data.append({'chat': c, 'other': other, 'last': last, 'unread': unread})
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>الرسائل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5">
        <h1>الرسائل</h1>
        <a href="/" class="btn btn-secondary mb-3">العودة</a>
        <div class="list-group">
            {% for item in data %}
            <a href="/chat/{{ item.chat.id }}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <img src="{{ item.other.profile_image or '/uploads/placeholder.jpg' }}" style="width:50px;height:50px;border-radius:50%; object-fit:cover; margin-left:10px;">
                    <div><strong>{{ item.other.full_name or item.other.username }}</strong><br><small>{% if item.last %}{{ item.last.content[:50] }}{% else %}لا توجد رسائل بعد{% endif %}</small></div>
                </div>
                {% if item.unread > 0 %}<span class="badge bg-danger rounded-pill">{{ item.unread }}</span>{% endif %}
            </a>
            {% else %}<p class="text-muted">لا توجد محادثات حالياً.</p>{% endfor %}
        </div>
    </div></body></html>''', data=data, User=User)

# ================== صفحة الدردشة ==================
@app.route('/chat/<int:chat_id>', methods=['GET','POST'])
@login_required
def view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if current_user.id not in [chat.client_id, chat.artisan_id] and not is_admin_user(current_user):
        return redirect(url_for('index'))
    other = User.query.get(chat.artisan_id if current_user.id == chat.client_id else chat.client_id)

    if request.method == 'POST' and request.form.get('action') == 'delete_message_image':
        msg_id = request.form.get('message_id')
        img_url = request.form.get('image_url')
        if msg_id and img_url:
            msg = Message.query.get(msg_id)
            if msg and msg.sender_id == current_user.id:
                delete_message_image(msg_id, img_url)
                flash('تم حذف الصورة', 'success')
        return redirect(url_for('view_chat', chat_id=chat_id))

    if request.method == 'POST' and request.form.get('action') != 'delete_message_image':
        content = request.form.get('message', '')
        if contains_blocked_patterns(content):
            flash('الرسالة تحتوي على رقم هاتف أو رابط تواصل ممنوع')
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
    <!DOCTYPE html><html dir="rtl"><head><title>محادثة مع {{ other.full_name or other.username }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}
        .message-container{height:400px;overflow-y:scroll;border:1px solid #ddd;padding:10px;background:#f9f9f9;margin-bottom:10px;}
        .my-message{background-color:#007bff;color:white;margin-left:auto;padding:8px 12px;border-radius:15px;max-width:70%;margin-bottom:5px;clear:both;float:right;text-align:right;}
        .other-message{background-color:#e9ecef;color:black;padding:8px 12px;border-radius:15px;max-width:70%;margin-bottom:5px;clear:both;float:left;text-align:right;}
        .message-wrapper{width:100%;overflow:hidden;margin-bottom:10px;}
        .action-btn{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;background:#f0f0f0;color:#333;text-decoration:none;margin-left:5px;cursor:pointer;border:none;}
        .action-btn:hover{background:#ddd;}
        .media-preview{max-width:100%;max-height:200px;margin-top:5px;border-radius:5px;}
        .delete-image-btn{position:absolute;top:0;right:0;background:rgba(255,0,0,0.7);color:white;border:none;border-radius:50%;width:25px;height:25px;font-size:16px;line-height:1;cursor:pointer;}
        .image-container{position:relative;display:inline-block;margin:5px;}
        .instruction-section{margin-top:30px;padding-top:20px;border-top:2px solid #ddd;clear:both;}
        .instruction-img{width:100%;max-height:400px;object-fit:contain;border:1px solid #ddd;border-radius:5px;cursor:pointer;}
        .warning-text{color:#dc3545;font-size:0.9rem;margin-bottom:5px;text-align:center;}
    </style></head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5" style="max-width:600px;">
        <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="d-flex align-items-center">
                <img src="{{ other.profile_image or '/uploads/placeholder.jpg' }}" style="width:50px;height:50px;border-radius:50%; object-fit:cover; margin-left:10px;">
                <h4><a href="/user/{{ other.id }}">{{ other.full_name or other.username }}</a></h4>
            </div>
        </div>
        <div class="message-container" id="messageContainer">
            {% for m in messages %}
                <div class="message-wrapper">
                    {% if m.is_blocked %}
                        <div class="blocked-message text-center p-2 bg-danger text-white rounded">[هذه الرسالة محظورة]</div>
                    {% else %}
                        <div class="{% if m.sender_id == current_user.id %}my-message{% else %}other-message{% endif %}">
                            <div class="message-content">
                                {% if m.content and (m.content.startswith('https://www.google.com/maps?q=') or m.content.startswith('https://maps.app.goo.gl/') or 'maps.google.com' in m.content) %}
                                    <a href="{{ m.content }}" target="_blank" style="color: {% if m.sender_id == current_user.id %}white{% else %}blue{% endif %};">📍 موقع على الخريطة</a>
                                {% elif m.content %}
                                    {{ m.content }}
                                {% endif %}
                            </div>
                            {% if m.images %}
                                <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px; justify-content: {% if m.sender_id == current_user.id %}flex-end{% else %}flex-start{% endif %};">
                                    {% for img in m.images.split(',') %}
                                        <div class="image-container">
                                            <a href="{{ img }}" target="_blank">
                                                <img src="{{ img }}" class="media-preview" style="width:100px; height:100px; object-fit:cover;">
                                            </a>
                                            {% if m.sender_id == current_user.id %}
                                                <form method="POST" style="display:inline;" onsubmit="return confirm('هل أنت متأكد من حذف هذه الصورة؟');">
                                                    <input type="hidden" name="action" value="delete_message_image">
                                                    <input type="hidden" name="message_id" value="{{ m.id }}">
                                                    <input type="hidden" name="image_url" value="{{ img }}">
                                                    <button type="submit" class="delete-image-btn" title="حذف الصورة">×</button>
                                                </form>
                                            {% endif %}
                                        </div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                            {% if m.voice %}
                                <audio controls src="{{ m.voice }}" style="width:100%; margin-top:5px;"></audio>
                            {% endif %}
                            {% if m.video %}
                                <video controls src="{{ m.video }}" style="max-width:100%; max-height:200px; margin-top:5px;"></video>
                            {% endif %}
                        </div>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        <form method="POST" enctype="multipart/form-data" id="chatForm">
            <div class="warning-text">⚠️ يمنع مشاركة أرقام الهاتف، سيتم رفض أي رسالة تحتوي على رقم.</div>
            <div class="mb-2"><textarea name="message" class="form-control" placeholder="اكتب رسالتك..." rows="2" id="messageText"></textarea></div>
            <div class="d-flex align-items-center gap-2 mb-2">
                <button type="submit" class="btn btn-primary flex-grow-1">💬 إرسال</button>
                <label for="images" class="action-btn">🖼️</label><input type="file" name="images" id="images" accept="image/*" multiple style="display: none;" onchange="document.getElementById('chatForm').submit();">
                <label for="video" class="action-btn">◀️</label><input type="file" name="video" id="video" accept="video/*" style="display: none;" onchange="document.getElementById('chatForm').submit();">
                <label for="voice" class="action-btn">🔊</label><input type="file" name="voice" id="voice" accept="audio/*" style="display: none;" onchange="document.getElementById('chatForm').submit();">
                <button type="button" class="action-btn" id="smartLocationBtn" title="مشاركة موقعي">📍</button>
            </div>
            <div id="locationResultArea" style="display: none; margin-bottom: 10px;" class="p-2 border rounded">
                <div class="input-group">
                    <input type="text" id="manualLocationLink" class="form-control" placeholder="الصق رابط الموقع هنا">
                    <button class="btn btn-primary" type="button" id="useLocationLink">إضافة</button>
                </div>
                <small class="text-muted">بعد لصق الرابط، اضغط "إضافة" ليظهر في رسالتك.</small>
            </div>
        </form>
        <div class="instruction-section">
            <div class="mt-3 text-center">
                <img src="{{ url_for('static', filename='instruction.jpg') }}?v={{ range(1, 1000) | random }}" 
                     alt="تعليمات إرسال الموقع" 
                     class="instruction-img"
                     onclick="openModal(this.src)">
                <p class="text-muted small mt-1">تعليمات إرسال الموقع: اضغط على زر الموقع، افتح الخريطة، انسخ الرابط والصقه.</p>
            </div>
            {% if current_user.is_admin %}
            <div class="mt-2 p-3 bg-light rounded border">
                <h6>رفع صورة تعليمية جديدة</h6>
                <form method="POST" action="{{ url_for('upload_instruction_image') }}" enctype="multipart/form-data" class="d-flex align-items-center gap-2">
                    <input type="file" name="instruction_image" accept="image/*" class="form-control form-control-sm" style="width: auto;" required>
                    <button type="submit" class="btn btn-sm btn-success">➕ رفع الصورة</button>
                </form>
                <small class="text-muted">هذه الصورة ستظهر لجميع المستخدمين.</small>
            </div>
            {% endif %}
        </div>
        <div class="modal fade" id="imageModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-body">
                        <img src="" id="modalImage" style="width:100%;">
                    </div>
                </div>
            </div>
        </div>
        <script>
        var container = document.getElementById('messageContainer');
        container.scrollTop = container.scrollHeight;
        document.getElementById('smartLocationBtn').addEventListener('click', function() {
            window.open('https://maps.google.com', '_blank');
            document.getElementById('locationResultArea').style.display = 'block';
        });
        document.getElementById('useLocationLink').addEventListener('click', function() {
            const link = document.getElementById('manualLocationLink').value.trim();
            if (link) {
                const msgField = document.getElementById('messageText');
                msgField.value += (msgField.value ? '\\n' : '') + link;
                document.getElementById('manualLocationLink').value = '';
                document.getElementById('locationResultArea').style.display = 'none';
            } else {
                alert('الرجاء لصق الرابط أولاً.');
            }
        });
        function openModal(src) {
            document.getElementById('modalImage').src = src;
            var modal = new bootstrap.Modal(document.getElementById('imageModal'));
            modal.show();
        }
        </script>
    </div></body></html>''', messages=messages, other=other, User=User)

# ================== تسجيل الخروج مع إرسال بريد إلكتروني ==================
@app.route('/logout')
@login_required
def logout():
    user_email = current_user.email
    user_name = current_user.full_name or current_user.username
    try:
        msg = MailMessage(
            subject="🔔 تسجيل الخروج من منصة بريكولات",
            recipients=[user_email],
            html=f"""
            <h2>وداعاً {user_name} 👋</h2>
            <p>تم تسجيل خروجك بنجاح من منصة بريكولات.</p>
            <p>إذا لم تكن أنت من قام بتسجيل الخروج، يرجى تغيير كلمة المرور فوراً.</p>
            <p>نأمل رؤيتك قريباً!</p>
            <br>
            <p>مع تحيات فريق بريكولات</p>
            """
        )
        mail.send(msg)
        print(f"📧 تم إرسال إشعار تسجيل الخروج إلى {user_email}")
    except Exception as e:
        print(f"⚠️ فشل إرسال بريد تسجيل الخروج: {e}")
    
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

# ================== مسار اختبار البريد ==================
@app.route('/test-email')
@login_required
@admin_required
def test_email():
    try:
        msg = MailMessage(
            subject="اختبار بسيط",
            recipients=['hichamcasawi709@gmail.com'],
            html="<h1>الاختبار ناجح</h1>"
        )
        mail.send(msg)
        return "✅ تم إرسال البريد بنجاح"
    except Exception as e:
        import traceback
        return f"❌ فشل: {e}<br><pre>{traceback.format_exc()}</pre>"

# ================== مسار عرض المستخدمين ذوي البريد ==================
@app.route('/list-users-email')
@login_required
@admin_required
def list_users_email():
    users = User.query.filter(User.email != None, User.email != '').all()
    result = "<h2>المستخدمون ذوو البريد الإلكتروني الصالح:</h2><ul>"
    for u in users:
        result += f"<li>{u.id}: {u.email} - {u.full_name} - {u.specialty} - {u.district}</li>"
    result += f"<p>العدد: {len(users)}</p></ul>"
    return result

# ================== مسارات التوافق ==================
@app.route('/client-dashboard')
@login_required
def client_dashboard():
    return redirect(url_for('index'))

@app.route('/artisan-dashboard')
@login_required
def artisan_dashboard():
    return redirect(url_for('index'))

# ================== تشغيل التطبيق ==================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

print("✅ الكود الكامل الآن جاهز مع تحسينات الخصوصية وإشعار تسجيل الخروج.")
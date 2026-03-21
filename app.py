# ============================================================
# منصة بريكولات - الجزء الأول (الإعدادات + الصفحة الرئيسية)
# مع زر تحميل APK وإشعار تسجيل الخروج ومسار الدردشة
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
from flask_mail import Mail, Message

# ================== إعدادات التطبيق ==================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bricolets-super-secret-key')

# إعداد قاعدة البيانات
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///bricolets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# ================== إعدادات البريد الإلكتروني (مضمنة) ==================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hichamcasawi709@gmail.com'
app.config['MAIL_PASSWORD'] = 'kxlafkpzbxuguida'
app.config['MAIL_DEFAULT_SENDER'] = 'hichamcasawi709@gmail.com'

mail = Mail(app)

# ================== إعدادات التخزين المحلي (مسار مطلق) ==================
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
        # تحديث كلمة سر الأدمن
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
    return url_for('index')  # كل المستخدمين يذهبون إلى الصفحة الرئيسية الموحدة

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
                        <a href="/login" class="btn btn-primary">تسجيل الدخول</a>
                        <a href="/register" class="btn btn-success">تسجيل جديد</a>
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
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('register', next=url_for('post_request')) }}{% endif %}" class="action-btn primary">أنا صاحب منزل أحتاج معلم</a>
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('register', next=url_for('post_request')) }}{% endif %}" class="action-btn success">أنا صاحب شركة أحتاج مقاول</a>
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('register', next=url_for('post_request')) }}{% endif %}" class="action-btn warning">أنا مقاول أحتاج معلم</a>
                <a href="{% if current_user.is_authenticated %}{{ url_for('post_request') }}{% else %}{{ url_for('register', next=url_for('post_request')) }}{% endif %}" class="action-btn info">أنا معلم أحتاج مساعد أو خدام</a>
            </div>
            <div class="action-btn-group">
                <a href="/search" class="action-btn primary">جميع الطلبات في المغرب</a>
                {% if current_user.is_authenticated %}
                <a href="/search?district={{ current_user.district }}&specialty={{ current_user.specialty }}" class="action-btn success">طلبات في مدينتي وتخصصي</a>
                {% else %}
                <a href="{{ url_for('register', next=url_for('search', district='', specialty='')) }}" class="action-btn success">طلبات في مدينتي وتخصصي (سجل أولاً)</a>
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
                        <a href="{% if current_user.is_authenticated %}/view-offers/{{ req.id }}{% else %}{{ url_for('register', next=url_for('view_offers', request_id=req.id)) }}{% endif %}" class="btn btn-sm btn-primary">عرض التفاصيل</a>
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
        msg = Message(
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
        # لا نعرض رسالة خطأ للمستخدم حتى لا يتأثر تجربة تسجيل الخروج
    
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

print("✅ الجزء الأول من المسارات تم تحميله بنجاح.")
print("✅ أضف الآن الجزء الثاني (باقي المسارات) لإكمال الموقع.")# ============================================================
# الجزء الثاني: جميع المسارات المتبقية (نهائي - مع تحسين الإرسال)
# ============================================================

# قائمة شاملة لمدن المغرب (للاستخدام في التسجيل وإكمال الملف الشخصي)
MOROCCAN_CITIES = [
    'أكادير', 'أيت ملول', 'أصيلة', 'بني ملال', 'بنسليمان', 'برشيد', 'بوجدور', 'بولمان', 'بوزنيقة', 'الداخلة',
    'الدار البيضاء', 'فاس', 'فكيك', 'كلميم', 'العرائش', 'القصر الكبير', 'الحاجب', 'الحسيمة', 'الجديدة', 'جرادة',
    'آسفي', 'صفرو', 'سطات', 'سلا', 'سيدي قاسم', 'سيدي سليمان', 'سوق الأربعاء', 'تازة', 'طنجة', 'تطوان',
    'تيفلت', 'تيزنيت', 'وزان', 'ورزازات', 'وجدة', 'اليوسفية', 'الرشيدية', 'الرباط', 'تمارة', 'تارودانت',
    'طانطان', 'السمارة', 'العيون', 'بوجدور', 'الفحص أنجرة', 'إفران', 'خنيفرة', 'خريبكة', 'القنيطرة', 'مراكش',
    'مكناس', 'الناظور', 'صفرو', 'زاكورة', 'تاونات', 'الفقيه بن صالح', 'جرسيف', 'الدريوش', 'ميدلت', 'تنجداد',
    'الريصاني', 'طاطا', 'أسا الزاك', 'السمارة', 'بوجدور', 'العيون', 'الداخلة', 'كلميم', 'طانطان', 'تزنيت',
    'سيدي إفني', 'الصويرة', 'شيشاوة', 'الحوز', 'الرحامنة', 'قلعة السراغنة', 'بني ملال', 'الفقيه بن صالح',
    'خريبكة', 'وادي زم', 'سطات', 'ابن احمد', 'سيدي بنور', 'الجديدة', 'آزمور', 'آسفي', 'اليوسفية', 'تارودانت',
    'أولاد تايمة', 'بيوكرى', 'أيت باها', 'إنزكان', 'أيت ملول', 'العيون', 'السمارة', 'بوجدور', 'طانطان',
    'الرشيدية', 'ورزازات', 'زاكورة', 'تنغير', 'بومالن دادس', 'ميدلت', 'الريصاني', 'تنجداد', 'جرسيف',
    'تازة', 'تاونات', 'صفرو', 'إفران', 'الحاجب', 'الفحص أنجرة', 'تطوان', 'المضيق', 'الفنيدق', 'مرتيل',
    'أصيلة', 'العرائش', 'القصر الكبير', 'وزان', 'شفشاون', 'الحسيمة', 'بني بوعياش', 'امزورن', 'الناظور',
    'زايو', 'أفسو', 'الدريوش', 'جرادة', 'بوعرفة', 'فكيك', 'بني ملال', 'القنيطرة', 'سيدي قاسم', 'سيدي سليمان',
    'سوق الأربعاء', 'تيفلت', 'الخميسات', 'تمارة', 'الرباط', 'سلا', 'المحمدية', 'الجديدة', 'برشيد',
    'بنسليمان', 'الدار البيضاء', 'مراكش', 'قلعة السراغنة', 'شيشاوة', 'الحوز', 'أكادير', 'إنزكان',
    'أيت ملول', 'تيزنيت', 'طانطان', 'العيون', 'الداخلة'
]

# قائمة التخصصات (مع خيار "آخر")
SPECIALTIES = [
    'بلومبي', 'نجار', 'سباك', 'كهربائي', 'رسام', 'حدائق', 'جباص', 'المنيوم', 'جلايجي', 'كباص'
]

# ================== تسجيل الدخول ==================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if is_admin_user(user):
                return redirect(url_for('admin_dashboard'))
            if not user.profile_completed:
                return redirect(url_for('complete_profile'))
            return redirect(url_for('index'))
        flash('البريد أو كلمة المرور غير صحيحة')
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>تسجيل الدخول</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container" style="max-width:400px;margin-top:50px">
        <h2 class="text-center">تسجيل الدخول</h2>
        {% with messages = get_flashed_messages() %}{% if messages %}<div class="alert alert-danger">{{ messages[0] }}</div>{% endif %}{% endwith %}
        <form method="POST">
            <div class="mb-3"><input type="email" name="email" class="form-control" placeholder="البريد الإلكتروني" required></div>
            <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="كلمة المرور" required></div>
            <button type="submit" class="btn btn-primary w-100">دخول</button>
        </form>
        <p class="mt-3">ليس لديك حساب؟ <a href="/register">سجل الآن</a></p>
        <p class="mt-2 text-center"><a href="/">العودة للرئيسية</a></p>
    </div></body></html>
    ''', User=User)

# ================== تسجيل جديد (المرحلة الأولى: البريد وكلمة السر) ==================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني موجود بالفعل')
            return redirect(url_for('register'))
        username = email.split('@')[0]
        base = username
        cnt = 1
        while User.query.filter_by(username=username).first():
            username = f"{base}{cnt}"
            cnt += 1
        hashed = generate_password_hash(password)
        is_admin = (email == 'hichamcasawi709@gmail.com')
        new_user = User(
            username=username,
            email=email,
            password=hashed,
            user_type='client',  # مؤقت
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('تم التسجيل بنجاح، يرجى إكمال بياناتك')
        return redirect(url_for('complete_profile'))
    
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>تسجيل جديد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container" style="max-width:500px;margin-top:50px">
        <h2 class="text-center">تسجيل جديد</h2>
        {% with messages = get_flashed_messages() %}{% if messages %}<div class="alert alert-danger">{{ messages[0] }}</div>{% endif %}{% endwith %}
        <form method="POST">
            <div class="mb-3"><input type="email" name="email" class="form-control" placeholder="البريد الإلكتروني" required></div>
            <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="كلمة المرور" required></div>
            <button type="submit" class="btn btn-primary w-100">تسجيل</button>
        </form>
        <p class="mt-3 text-center">لديك حساب؟ <a href="/login">تسجيل دخول</a></p>
        <p class="mt-2 text-center"><a href="/">العودة للرئيسية</a></p>
    </div></body></html>
    ''', User=User)

# ================== إكمال الملف الشخصي (التخصص إجباري) ==================
@app.route('/complete-profile', methods=['GET','POST'])
@login_required
def complete_profile():
    if is_admin_user(current_user):
        return redirect(url_for('admin_dashboard'))
    if current_user.profile_completed:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        district = request.form.get('district', '').strip()
        specialty = request.form.get('specialty', '').strip()
        experience_years = request.form.get('experience_years', '').strip()
        
        errors = []
        if not full_name:
            errors.append('الاسم الكامل مطلوب')
        if not phone:
            errors.append('رقم الهاتف مطلوب')
        elif not re.match(r'^0[5-7]\d{8}$', phone):
            errors.append('رقم الهاتف غير صحيح. يجب أن يبدأ بـ 05 أو 06 أو 07 ويتكون من 10 أرقام')
        if not district:
            errors.append('المدينة مطلوبة')
        if not specialty:
            errors.append('التخصص مطلوب لجميع المستخدمين')
        elif specialty == 'other':
            other_spec = request.form.get('other_specialty', '').strip()
            if not other_spec:
                errors.append('الرجاء كتابة التخصص الجديد')
            else:
                specialty = other_spec
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('complete_profile'))
        
        current_user.full_name = full_name
        current_user.phone = phone
        current_user.district = normalize_city(district)
        current_user.specialty = specialty
        current_user.user_type = 'client'  # نعتبر الجميع عملاء ولكن يحتفظون بالتخصص للإشعارات
        
        if experience_years and experience_years.isdigit():
            current_user.experience_years = int(experience_years)
        
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            url = save_file_to_local(file, subfolder=f"users/{current_user.id}")
            if url:
                current_user.profile_image = url
        
        db.session.commit()
        flash('تم إكمال الملف الشخصي بنجاح')
        return redirect(url_for('index'))
    
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>إكمال الملف الشخصي</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    <script>
    function toggleSpecialtyInput() {
        var select = document.getElementById('specialty_select');
        var otherInput = document.getElementById('other_specialty');
        if (select.value === 'other') {
            otherInput.style.display = 'block';
            otherInput.required = true;
        } else {
            otherInput.style.display = 'none';
            otherInput.required = false;
        }
    }
    </script>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container" style="max-width:600px;margin-top:50px">
        <h2 class="text-center">أكمل ملفك الشخصي</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3">
                <label>الصورة الشخصية (اختياري)</label>
                <input type="file" name="profile_image" class="form-control" accept="image/*">
            </div>
            <div class="mb-3">
                <label>الاسم الكامل <span class="text-danger">*</span></label>
                <input type="text" name="full_name" class="form-control" required>
            </div>
            <div class="mb-3">
                <label>رقم الهاتف <span class="text-danger">*</span></label>
                <input type="tel" name="phone" class="form-control" placeholder="مثال: 0612345678" required>
            </div>
            <div class="mb-3">
                <label>المدينة <span class="text-danger">*</span></label>
                <input list="cities" name="district" class="form-control" required>
                <datalist id="cities">
                    {% for city in MOROCCAN_CITIES %}
                    <option value="{{ city }}">
                    {% endfor %}
                </datalist>
            </div>
            <div class="mb-3">
                <label>التخصص <span class="text-danger">*</span></label>
                <select name="specialty" id="specialty_select" class="form-select" onchange="toggleSpecialtyInput()" required>
                    <option value="">اختر تخصصك</option>
                    {% for spec in SPECIALTIES %}
                    <option value="{{ spec }}">{{ spec }}</option>
                    {% endfor %}
                    <option value="other">تخصص آخر (اكتبه)</option>
                </select>
                <input type="text" name="other_specialty" id="other_specialty" class="form-control mt-2" style="display:none;" placeholder="اكتب تخصصك">
            </div>
            <div class="mb-3">
                <label>سنوات الخبرة (اختياري)</label>
                <input type="number" name="experience_years" class="form-control" min="0" max="50" placeholder="مثال: 5">
            </div>
            <button type="submit" class="btn btn-primary w-100">تم</button>
        </form>
    </div></body></html>
    ''', User=User, MOROCCAN_CITIES=MOROCCAN_CITIES, SPECIALTIES=SPECIALTIES)

# ================== قائمة الحرفيين ==================
@app.route('/artisans')
def artisans_list():
    artisans = User.query.filter_by(user_type='artisan').all()
    artisans_with_rating = []
    for a in artisans:
        avg, num = get_artisan_rating(a.id)
        artisans_with_rating.append({'artisan': a, 'avg': avg, 'num': num})
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>قائمة الحرفيين</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5">
        <h1 class="text-center">جميع الحرفيين في المغرب</h1>
        <div class="row mt-4">
            {% for item in artisans_with_rating %}
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    <img src="{{ item.artisan.profile_image or '/uploads/placeholder.jpg' }}" class="card-img-top" style="height:200px; object-fit:cover;">
                    <div class="card-body">
                        <h5 class="card-title"><a href="/user/{{ item.artisan.id }}">{{ item.artisan.full_name or item.artisan.username }}</a></h5>
                        <p>
                            <strong>التخصص:</strong> {{ item.artisan.specialty }}<br>
                            <strong>الحي:</strong> {{ item.artisan.district or 'غير محدد' }}
                            {% if item.artisan.experience_years %}<br><strong>الخبرة:</strong> {{ item.artisan.experience_years }} سنة{% endif %}
                        </p>
                        {% if item.num > 0 %}
                            <p class="text-warning">{% for i in range(item.avg|int) %}⭐{% endfor %} {{ item.avg }} ({{ item.num }})</p>
                        {% else %}
                            <p class="text-muted">لا توجد تقييمات</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        <a href="/" class="btn btn-secondary">العودة</a>
    </div></body></html>
    ''', artisans_with_rating=artisans_with_rating, User=User)

# ================== الملف الشخصي العام ==================
@app.route('/user/<int:user_id>')
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    avg_rating = 0
    num_ratings = 0
    ratings = []
    portfolio_list = []
    if user.user_type == 'artisan':
        avg_rating, num_ratings = get_artisan_rating(user.id)
        ratings = Rating.query.filter_by(rated_id=user.id).order_by(Rating.created_at.desc()).all()
        if user.portfolio:
            portfolio_list = user.portfolio.split(',')
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>{{ user.full_name or user.username }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}
        .profile-header{background:#fff;border-radius:15px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:20px;text-align:center;}
        .profile-img{width:150px;height:150px;border-radius:50%;object-fit:cover;border:3px solid #007bff;}
        .rating-stars{color:#ffc107;font-size:1.5rem;}
        .portfolio-section{margin-top:30px;}
        .portfolio-title{font-size:1.5rem;margin-bottom:15px;text-align:center;}
        .portfolio-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px;}
        .portfolio-item{position:relative;overflow:hidden;border-radius:10px;box-shadow:0 4px 8px rgba(0,0,0,0.1);cursor:pointer;transition:transform 0.3s;}
        .portfolio-item:hover{transform:scale(1.03);}
        .portfolio-img{width:100%;height:200px;object-fit:cover;}
        .video-thumb{position:relative;}.video-thumb::after{content:"▶";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:3rem;color:white;text-shadow:0 2px 5px rgba(0,0,0,0.5);}
        .modal-body img{width:100%;}
    </style></head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5" style="max-width:800px;">
        <div class="profile-header">
            <img src="{{ user.profile_image or '/uploads/placeholder.jpg' }}" class="profile-img mb-3">
            <h2>{{ user.full_name or user.username }}</h2>
            <p class="text-muted">{{ user.district or 'غير محدد' }}</p>
            <p class="text-muted">🔧 {{ user.specialty or 'لا يوجد تخصص' }}</p>
            {% if user.user_type == 'artisan' %}
                {% if user.experience_years %}<p class="text-muted">خبرة {{ user.experience_years }} سنة</p>{% endif %}
                {% if num_ratings > 0 %}<div class="rating-stars">{% for i in range(5) %}{% if i < avg_rating|int %}★{% else %}☆{% endif %}{% endfor %} <span class="text-muted">({{ num_ratings }})</span></div>{% endif %}
            {% endif %}
            <p class="joined">انضم {{ time_ago(user.created_at) }}</p>
            {% if is_admin_user(current_user) %}
                <p class="text-muted">📞 {{ user.phone or 'رقم غير متوفر' }}</p>
                <p class="text-muted">📧 {{ user.email }}</p>
            {% else %}
                <p class="text-muted text-secondary">📞 رقم الهاتف محفوظ للمسؤول فقط</p>
            {% endif %}
        </div>
        {% if user.user_type == 'artisan' and portfolio_list %}
        <div class="portfolio-section"><h3 class="portfolio-title">📸 أعمالي</h3><div class="portfolio-grid">
            {% for link in portfolio_list %}<div class="portfolio-item" onclick="openModal('{{ link }}')"><img src="{{ link }}" class="portfolio-img" onerror="this.onerror=null; this.src='/uploads/placeholder.jpg';"></div>{% endfor %}
        </div></div>
        {% endif %}
        {% if user.user_type == 'artisan' and user.video_work %}
        <div class="portfolio-section"><h3 class="portfolio-title">🎥 فيديو العمل</h3><div class="portfolio-grid"><div class="portfolio-item video-thumb" onclick="openVideo('{{ user.video_work }}')"><img src="/uploads/placeholder.jpg" class="portfolio-img" onerror="this.onerror=null; this.src='/uploads/placeholder.jpg';"></div></div></div>
        {% endif %}
        {% if ratings %}<div class="card mt-4"><div class="card-header bg-warning">التقييمات</div><div class="card-body">{% for r in ratings %}<div class="border-bottom pb-2 mb-2"><strong>{{ r.rater.full_name or r.rater.username }}</strong> <span class="text-warning ms-2">{% for i in range(r.score|int) %}★{% endfor %}{% for i in range(5 - r.score|int) %}☆{% endfor %}</span><p class="mb-1">{{ r.comment or '' }}</p><small class="text-muted">{{ r.created_at.strftime('%Y-%m-%d') }}</small></div>{% endfor %}</div></div>{% endif %}
        <div class="modal fade" id="imageModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-body"><img src="" id="modalImage" style="width:100%;"></div></div></div></div>
        <a href="javascript:history.back()" class="btn btn-secondary mt-3">رجوع</a>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>function openModal(src){ document.getElementById('modalImage').src = src; new bootstrap.Modal(document.getElementById('imageModal')).show(); } function openVideo(src){ window.open(src, '_blank'); }</script>
    </body></html>''', user=user, avg_rating=avg_rating, num_ratings=num_ratings, ratings=ratings, portfolio_list=portfolio_list, User=User, is_admin_user=is_admin_user)

# ================== الملف الشخصي الخاص ==================
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'delete_profile_image' in request.form:
            if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
                delete_file(current_user.profile_image)
            current_user.profile_image = None
            db.session.commit()
            flash('تم حذف الصورة الشخصية', 'success')
            return redirect(url_for('profile'))
        
        if request.form.get('action') == 'delete_portfolio':
            img_to_delete = request.form.get('delete_image')
            if img_to_delete and current_user.portfolio:
                urls = current_user.portfolio.split(',')
                if img_to_delete in urls:
                    urls.remove(img_to_delete)
                    if img_to_delete.startswith('/uploads/'):
                        delete_file(img_to_delete)
                    current_user.portfolio = ','.join(urls) if urls else None
                    db.session.commit()
                    flash('تم حذف الصورة', 'success')
            return redirect(url_for('profile'))
        
        if 'profile_image' in request.files and len(request.form) == 0:
            file = request.files['profile_image']
            if file and file.filename:
                if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
                    delete_file(current_user.profile_image)
                url = save_file_to_local(file, subfolder=f"users/{current_user.id}")
                if url:
                    current_user.profile_image = url
                    db.session.commit()
                    flash('تم تحديث الصورة الشخصية')
            return redirect(url_for('profile'))

        current_user.full_name = request.form['full_name']
        current_user.district = normalize_city(request.form['district'])
        if 'phone' in request.form:
            current_user.phone = request.form['phone']
        if 'specialty' in request.form:
            current_user.specialty = request.form['specialty']
        exp = request.form.get('experience_years', '').strip()
        if exp and exp.isdigit():
            current_user.experience_years = int(exp)

        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename:
                if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
                    delete_file(current_user.profile_image)
                url = save_file_to_local(file, subfolder=f"users/{current_user.id}")
                if url:
                    current_user.profile_image = url

        if 'video_work' in request.files:
            file = request.files['video_work']
            if file and file.filename:
                if current_user.video_work and current_user.video_work.startswith('/uploads/'):
                    delete_file(current_user.video_work)
                url = save_file_to_local(file, subfolder=f"artisans/{current_user.id}")
                if url:
                    current_user.video_work = url

        if 'new_portfolio' in request.files:
            files = request.files.getlist('new_portfolio')
            if files and files[0].filename:
                urls = save_multiple_files(files, subfolder=f"artisans/{current_user.id}/portfolio")
                if urls:
                    old = current_user.portfolio.split(',') if current_user.portfolio else []
                    all_urls = old + urls.split(',')
                    current_user.portfolio = ','.join(all_urls)

        db.session.commit()
        flash('تم تحديث الملف الشخصي')
        return redirect(url_for('profile'))

    avg_rating = 0
    num_ratings = 0
    portfolio_list = []
    if current_user.user_type == 'artisan':
        avg_rating, num_ratings = get_artisan_rating(current_user.id)
        if current_user.portfolio:
            portfolio_list = current_user.portfolio.split(',')
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>الملف الشخصي</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}
        .profile-header{background:#fff;border-radius:15px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:20px;text-align:center;}
        .profile-img{width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #007bff;}
        .rating-stars{color:#ffc107;font-size:1.2rem;}
        .portfolio-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:15px;}
        .portfolio-item{position:relative;border-radius:10px;overflow:hidden;box-shadow:0 2px 5px rgba(0,0,0,0.1);}
        .portfolio-img{width:100%;height:150px;object-fit:cover;}
        .delete-btn{position:absolute;top:5px;right:5px;background:rgba(255,0,0,0.7);color:white;border:none;border-radius:50%;width:30px;height:30px;cursor:pointer;}
        .image-action-btn{margin:5px;}
    </style></head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5" style="max-width:800px;">
        <div class="profile-header">
            <img src="{{ current_user.profile_image or '/uploads/placeholder.jpg' }}" class="profile-img mb-3">
            <div>
                {% if current_user.profile_image %}
                <form method="POST" enctype="multipart/form-data" style="display:inline;" id="changePhotoForm">
                    <input type="file" name="profile_image" id="profile_image" accept="image/*" style="display:none;" onchange="document.getElementById('changePhotoForm').submit();">
                    <button type="button" class="btn btn-sm btn-outline-primary image-action-btn" onclick="document.getElementById('profile_image').click();">تغيير الصورة</button>
                </form>
                <form method="POST" style="display:inline;" onsubmit="return confirm('هل أنت متأكد من حذف الصورة الشخصية؟');">
                    <input type="hidden" name="delete_profile_image" value="yes">
                    <button type="submit" class="btn btn-sm btn-outline-danger image-action-btn">🗑️ حذف الصورة</button>
                </form>
                {% else %}
                <form method="POST" enctype="multipart/form-data" style="display:inline;" id="addPhotoForm">
                    <input type="file" name="profile_image" id="profile_image_add" accept="image/*" style="display:none;" onchange="document.getElementById('addPhotoForm').submit();">
                    <button type="button" class="btn btn-sm btn-success image-action-btn" onclick="document.getElementById('profile_image_add').click();">إضافة صورة</button>
                </form>
                {% endif %}
            </div>
            <h2 class="mt-2">{{ current_user.full_name or current_user.username }}</h2>
            <p class="text-muted">{{ current_user.district or 'غير محدد' }}</p>
            <p class="text-muted">📞 {{ current_user.phone or 'رقم غير متوفر' }}</p>
            <p class="text-muted">🔧 {{ current_user.specialty or 'لا يوجد تخصص' }}</p>
            {% if current_user.experience_years %}
                <p class="text-muted">خبرة {{ current_user.experience_years }} سنة</p>
            {% endif %}
            <p class="joined">انضم {{ time_ago(current_user.created_at) }}</p>
        </div>

        <button class="btn btn-primary mb-3" type="button" data-bs-toggle="collapse" data-bs-target="#editForm">تعديل البيانات</button>
        <div class="collapse" id="editForm"><div class="card card-body"><form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label>الاسم الكامل</label><input type="text" name="full_name" value="{{ current_user.full_name }}" class="form-control" required></div>
            <div class="mb-3"><label>رقم الهاتف</label><input type="text" name="phone" value="{{ current_user.phone }}" class="form-control" required></div>
            <div class="mb-3"><label>مدينتك الحالية</label><input type="text" name="district" value="{{ current_user.district }}" class="form-control" required></div>
            <div class="mb-3"><label>التخصص</label>
                <select name="specialty" class="form-select">
                    {% for spec in SPECIALTIES %}
                    <option value="{{ spec }}" {% if current_user.specialty == spec %}selected{% endif %}>{{ spec }}</option>
                    {% endfor %}
                    <option value="other" {% if current_user.specialty not in SPECIALTIES %}selected{% endif %}>تخصص آخر</option>
                </select>
            </div>
            <div class="mb-3"><label>سنوات الخبرة</label><input type="number" name="experience_years" class="form-control" value="{{ current_user.experience_years or '' }}"></div>
            <div class="mb-3"><label>فيديو العمل</label><input type="file" name="video_work" class="form-control" accept="video/*"></div>
            <div class="mb-3"><label>إضافة صور أعمال جديدة</label><input type="file" name="new_portfolio" class="form-control" accept="image/*" multiple></div>
            <button type="submit" class="btn btn-primary">حفظ</button>
        </form></div></div>

        {% if portfolio_list %}
        <div class="portfolio-section"><h3 class="mb-3">📸 أعمالي</h3><div class="portfolio-grid">
            {% for img in portfolio_list %}
            <div class="portfolio-item">
                <img src="{{ img }}" class="portfolio-img" onclick="openModal('{{ img }}')">
                <form method="POST" style="display:inline;" onsubmit="return confirm('هل أنت متأكد من حذف هذه الصورة؟');">
                    <input type="hidden" name="delete_image" value="{{ img }}">
                    <input type="hidden" name="action" value="delete_portfolio">
                    <button type="submit" class="delete-btn" title="حذف">×</button>
                </form>
            </div>
            {% endfor %}
        </div></div>
        {% endif %}

        <a href="/" class="btn btn-secondary mt-3">العودة للرئيسية</a>
    </div>
    <div class="modal fade" id="imageModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-body"><img src="" id="modalImage" style="width:100%;"></div></div></div></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>function openModal(src){ document.getElementById('modalImage').src = src; new bootstrap.Modal(document.getElementById('imageModal')).show(); }</script>
    </body></html>''', current_user=current_user, avg_rating=avg_rating, num_ratings=num_ratings, portfolio_list=portfolio_list, User=User, SPECIALTIES=SPECIALTIES)

# ================== البحث عن الطلبات ==================
@app.route('/search')
def search():
    specialty = request.args.get('specialty', '')
    district = request.args.get('district', '')
    q = Request.query.filter_by(status='open')
    if specialty: q = q.filter_by(specialty=specialty)
    if district: q = q.filter_by(district=district)
    requests = q.order_by(Request.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>الطلبات المفتوحة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style> .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;} </style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5">
        <h1>الطلبات المفتوحة</h1>
        <a href="/" class="btn btn-secondary mb-3">العودة</a>
        <div class="row">
            {% for req in requests %}
            <div class="col-md-6 mb-4">
                <div class="card request-card">
                    <div class="card-body">
                        <div class="client-info">
                            <img src="{{ req.client.profile_image or '/uploads/placeholder.jpg' }}" class="client-img">
                            <div>
                                <strong><a href="/user/{{ req.client.id }}">{{ req.client.full_name or req.client.username }}</a></strong><br>
                                <small>{{ req.district }} · {{ time_ago(req.created_at) }}</small>
                            </div>
                        </div>
                        <h5>{{ req.title }}</h5>
                        <p>{{ req.description }}</p>
                        {% if req.images %}
                        <div class="request-images">
                            {% for img in req.images.split(',') %}
                            <img src="{{ img }}" onclick="openModal('{{ img }}')">
                            {% endfor %}
                        </div>
                        {% endif %}
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <span class="badge bg-primary">{{ req.specialty }}</span>
                            <span class="badge bg-info">عروض: {{ req.offers_count }}/30</span>
                        </div>
                        <div class="mt-2">
                            <a href="/user/{{ req.client.id }}" class="btn btn-sm btn-outline-secondary">عرض الملف</a>
                            {% if current_user.is_authenticated and req.status == 'open' and req.offers_count < 30 %}
                            <a href="/send-offer/{{ req.id }}" class="btn btn-sm btn-primary">تقديم عرض</a>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    <div class="modal fade" id="imageModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-body"><img src="" id="modalImage" style="width:100%;"></div></div></div></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>function openModal(src){ document.getElementById('modalImage').src = src; new bootstrap.Modal(document.getElementById('imageModal')).show(); }</script>
    </body></html>
    ''', requests=requests, User=User)

# ================== نشر طلب جديد (يرسل لجميع المستخدمين مع طباعة تفصيلية) ==================
@app.route('/post-request', methods=['GET','POST'])
@login_required
def post_request():
    if request.method == 'POST':
        title = request.form['title'] or 'طلب خدمة'
        description = request.form['description']
        specialty = request.form['specialty']
        if specialty == 'other':
            specialty = request.form.get('other_specialty', '').strip()
            if not specialty:
                flash('الرجاء كتابة التخصص')
                return redirect(url_for('post_request'))
        district = request.form['district']
        images = ''
        if 'images' in request.files:
            files = request.files.getlist('images')
            images = save_multiple_files(files, subfolder="requests")
        new_req = Request(
            title=title,
            description=description,
            specialty=specialty,
            district=district,
            images=images,
            client_id=current_user.id,
            status='open'
        )
        db.session.add(new_req)
        db.session.commit()

        # ===== إرسال إشعارات لجميع المستخدمين ذوي البريد الصالح =====
        try:
            all_users = User.query.filter(User.email.isnot(None), User.email != '').all()
            print("="*60)
            print(f"🚀 نشر طلب جديد: {title}")
            print(f"📧 عدد المستخدمين الذين لديهم بريد إلكتروني: {len(all_users)}")
            for u in all_users:
                print(f"   - {u.email} | {u.full_name} | {u.specialty} | {u.district}")
            print("="*60)

            if all_users:
                subject = f"🔔 طلب جديد: {title}"
                body = f"""
                <h2>طلب جديد على المنصة</h2>
                <p><strong>العنوان:</strong> {title}</p>
                <p><strong>الوصف:</strong> {description}</p>
                <p><strong>التخصص:</strong> {specialty}</p>
                <p><strong>المدينة:</strong> {district}</p>
                <p><a href="https://bricoletsapp.pythonanywhere.com/view-offers/{new_req.id}">عرض التفاصيل</a></p>
                <p>مع تحيات فريق بريكولات</p>
                """
                sent_count = 0
                for user in all_users:
                    try:
                        msg = Message(subject=subject, recipients=[user.email], html=body)
                        mail.send(msg)
                        sent_count += 1
                        print(f"✅ تم الإرسال إلى {user.email}")
                    except Exception as e:
                        print(f"❌ فشل الإرسال إلى {user.email}: {e}")
                flash(f'✅ تم نشر الطلب وإرسال إشعارات إلى {sent_count} من {len(all_users)} مستخدم', 'success')
            else:
                flash('⚠️ لا يوجد أي مستخدم لديه بريد إلكتروني صالح.', 'warning')
        except Exception as e:
            import traceback
            print("❌ خطأ عام:")
            print(traceback.format_exc())
            flash('⚠️ حدث خطأ أثناء إرسال الإشعارات', 'warning')

        return redirect(url_for('index'))

    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>نشر طلب جديد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    <script>
    function toggleSpecialtyInput() {
        var select = document.getElementById('specialty_select');
        var otherInput = document.getElementById('other_specialty');
        if (select.value === 'other') {
            otherInput.style.display = 'block';
            otherInput.required = true;
        } else {
            otherInput.style.display = 'none';
            otherInput.required = false;
        }
    }
    </script>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container" style="max-width:600px;margin-top:50px">
        <h2 class="text-center mb-4">نشر طلب جديد</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label>عنوان الطلب (اختياري)</label><input type="text" name="title" class="form-control" value="طلب خدمة"></div>
            <div class="mb-3"><label>اكتب مشكلتك هنا</label><textarea name="description" class="form-control" rows="4" required></textarea></div>
            <div class="mb-3"><label>التخصص الذي تحتاجه</label>
                <select name="specialty" id="specialty_select" class="form-select" onchange="toggleSpecialtyInput()" required>
                    <option value="">اختر التخصص</option>
                    {% for spec in SPECIALTIES %}
                    <option value="{{ spec }}">{{ spec }}</option>
                    {% endfor %}
                    <option value="other">تخصص آخر (اكتبه)</option>
                </select>
                <input type="text" name="other_specialty" id="other_specialty" class="form-control mt-2" style="display:none;" placeholder="اكتب التخصص">
            </div>
            <div class="mb-3"><label>المدينة أو الحي</label>
                <input list="cities" name="district" class="form-control" required>
                <datalist id="cities">
                    {% for city in MOROCCAN_CITIES %}
                    <option value="{{ city }}">
                    {% endfor %}
                </datalist>
            </div>
            <div class="mb-3"><label>صور المشكلة (اختياري)</label><input type="file" name="images" class="form-control" accept="image/*" multiple></div>
            <button type="submit" class="btn btn-primary w-100">تم النشر</button>
        </form>
        <a href="/" class="btn btn-secondary w-100 mt-2">العودة</a>
    </div></body></html>
    ''', User=User, MOROCCAN_CITIES=MOROCCAN_CITIES, SPECIALTIES=SPECIALTIES)

# ================== تقديم عرض ==================
@app.route('/send-offer/<int:request_id>', methods=['GET','POST'])
@login_required
def send_offer(request_id):
    req = Request.query.get_or_404(request_id)
    if req.status != 'open' or req.offers_count >= 30:
        flash('الطلب مغلق أو اكتمل')
        return redirect(url_for('index'))
    if Offer.query.filter_by(request_id=request_id, artisan_id=current_user.id).first():
        flash('قدمت عرضاً مسبقاً')
        return redirect(url_for('index'))
    if request.method == 'POST':
        message = request.form['message']
        images = voice = video = ''
        if 'images' in request.files:
            files = request.files.getlist('images')
            images = save_multiple_files(files, subfolder=f"offers/{request_id}")
        if 'voice' in request.files:
            f = request.files['voice']
            voice = save_file_to_local(f, subfolder=f"offers/{request_id}")
        if 'video' in request.files:
            f = request.files['video']
            video = save_file_to_local(f, subfolder=f"offers/{request_id}")
        offer = Offer(request_id=request_id, artisan_id=current_user.id, message=message, images=images, voice=voice, video=video)
        db.session.add(offer)
        req.offers_count += 1
        if req.offers_count >= 30:
            req.status = 'cancelled'
        db.session.commit()
        # إنشاء محادثة وإضافة رسالة
        chat = Chat.query.filter_by(request_id=request_id, client_id=req.client_id, artisan_id=current_user.id).first()
        if not chat:
            chat = Chat(request_id=request_id, client_id=req.client_id, artisan_id=current_user.id)
            db.session.add(chat)
            db.session.commit()
        msg = Message(chat_id=chat.id, sender_id=current_user.id, content=f"📌 عرض على طلبك: {message}", images=images, voice=voice, video=video, is_read=False)
        db.session.add(msg)
        db.session.commit()
        flash('تم إرسال العرض وستظهر رسالتك في محادثة مع الزبون')
        return redirect(url_for('index'))
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>تقديم عرض</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container" style="max-width:600px;margin-top:50px">
        <h2>تقديم عرض للطلب: {{ req.title }}</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label>رسالتك</label><textarea name="message" class="form-control" rows="4" required></textarea></div>
            <div class="mb-3"><label>صور</label><input type="file" name="images" class="form-control" accept="image/*" multiple></div>
            <div class="mb-3"><label>مقطع صوتي</label><input type="file" name="voice" class="form-control" accept="audio/*"></div>
            <div class="mb-3"><label>فيديو</label><input type="file" name="video" class="form-control" accept="video/*"></div>
            <button type="submit" class="btn btn-primary">إرسال</button>
        </form>
    </div></body></html>''', req=req, User=User)

# ================== عرض العروض ==================
@app.route('/view-offers/<int:request_id>', methods=['GET','POST'])
@login_required
def view_offers(request_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id != current_user.id and not is_admin_user(current_user):
        return redirect(url_for('index'))
    if request.method == 'POST':
        artisan_id = request.form.get('artisan_id')
        if artisan_id:
            artisan_id = int(artisan_id)
            content = request.form.get('quick_message', '').strip()
            if content:
                chat = Chat.query.filter_by(request_id=request_id, client_id=current_user.id, artisan_id=artisan_id).first()
                if not chat:
                    chat = Chat(request_id=request_id, client_id=current_user.id, artisan_id=artisan_id)
                    db.session.add(chat)
                    db.session.commit()
                msg = Message(chat_id=chat.id, sender_id=current_user.id, content=content, is_read=False)
                db.session.add(msg)
                db.session.commit()
                flash('تم إرسال رسالتك')
            else:
                flash('الرجاء كتابة رسالة')
        return redirect(url_for('view_offers', request_id=request_id))
    offers = Offer.query.filter_by(request_id=request_id).all()
    offers_data = [{'offer': o, 'artisan': User.query.get(o.artisan_id)} for o in offers]
    can_rate = req.status in ['cancelled', 'completed']
    request_images = req.images.split(',') if req.images and req.images.strip() else []
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>العروض</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}
        .request-images { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }
        .request-images img { width: 100px; height: 100px; object-fit: cover; border-radius: 5px; cursor: pointer; transition: transform 0.2s; }
        .modal-body img { width: 100%; }
        .quick-message-box { background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px; }
        .action-btn{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;background-color:#f0f0f0;color:#333;text-decoration:none;margin-left:5px;cursor:pointer;border:none;}
        .action-btn:hover{background-color:#ddd;}
    </style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container mt-5">
        <h1>عروض الطلب: {{ req.title }}</h1>
        {% if request_images %}
        <div class="card mb-4"><div class="card-header bg-info text-white">صور المشكلة</div><div class="card-body"><div class="request-images">{% for img in request_images %}<img src="{{ img }}" onclick="openModal('{{ img }}')">{% endfor %}</div></div></div>
        {% endif %}
        <div class="card mb-4"><div class="card-header bg-primary text-white">تفاصيل الطلب</div><div class="card-body"><h5>{{ req.title }}</h5><p>{{ req.description }}</p><p><strong>التخصص:</strong> {{ req.specialty }} | <strong>الحي:</strong> {{ req.district }}</p><p><strong>نشر:</strong> {{ time_ago(req.created_at) }}</p><p>عروض: {{ req.offers_count }}/30 | حالة: {{ 'مفتوح' if req.status=='open' else 'مغلق' }}</p></div></div>
        <h3>العروض المقدمة</h3><div class="row">
            {% for item in offers %}
            <div class="col-md-4 mb-3">
                <div class="card"><div class="card-body">
                    <div style="display:flex; align-items:center; margin-bottom:10px;">
                        <img src="{{ item.artisan.profile_image or '/uploads/placeholder.jpg' }}" style="width:50px;height:50px;border-radius:50%; object-fit:cover; margin-left:10px;">
                        <div>
                            <h5><a href="/user/{{ item.artisan.id }}">{{ item.artisan.full_name or item.artisan.username }}</a></h5>
                            <p class="text-muted">{{ item.artisan.specialty }}</p>
                            {% if item.artisan.experience_years %}<p class="text-muted small">خبرة {{ item.artisan.experience_years }} سنة</p>{% endif %}
                        </div>
                    </div>
                    <p>{{ item.offer.message }}</p>
                    {% if item.offer.images %}<p>🖼️ <a href="{{ item.offer.images }}" target="_blank">صور</a></p>{% endif %}
                    {% if item.offer.voice %}<p>🎤 <a href="{{ item.offer.voice }}" target="_blank">تسجيل صوتي</a></p>{% endif %}
                    {% if item.offer.video %}<p>🎥 <a href="{{ item.offer.video }}" target="_blank">فيديو</a></p>{% endif %}
                    <div class="quick-message-box mt-2">
                        <form method="POST">
                            <input type="hidden" name="artisan_id" value="{{ item.artisan.id }}">
                            <div class="d-flex align-items-center gap-2">
                                <textarea name="quick_message" class="form-control" rows="1" placeholder="اكتب رسالتك..."></textarea>
                                <button type="submit" class="btn btn-primary btn-sm">💬</button>
                            </div>
                            <div class="d-flex mt-1">
                                <label class="action-btn">🖼️</label>
                                <label class="action-btn">◀️</label>
                                <label class="action-btn">🔊</label>
                                <label class="action-btn">⬆️</label>
                            </div>
                            <small class="text-muted">المدينة: {{ item.artisan.district }}</small>
                        </form>
                    </div>
                    <a href="/start-chat/{{ req.id }}/{{ item.artisan.id }}" class="btn btn-primary btn-sm mt-2">فتح المحادثة</a>
                    {% if can_rate %}<a href="/rate/{{ item.artisan.id }}/{{ req.id }}" class="btn btn-warning btn-sm mt-2">تقييم</a>{% endif %}
                </div></div>
            </div>
            {% endfor %}
        </div>
        <a href="/" class="btn btn-secondary mt-3">العودة</a>
    </div>
    <div class="modal fade" id="imageModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-body"><img src="" id="modalImage" style="width:100%;"></div></div></div></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>function openModal(src){ document.getElementById('modalImage').src = src; new bootstrap.Modal(document.getElementById('imageModal')).show(); }</script>
    </body></html>''', req=req, offers=offers_data, can_rate=can_rate, request_images=request_images, User=User)

# ================== تقييم الحرفي ==================
@app.route('/rate/<int:artisan_id>/<int:request_id>', methods=['GET','POST'])
@login_required
def rate_artisan(artisan_id, request_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id != current_user.id:
        return redirect(url_for('index'))
    if Rating.query.filter_by(rater_id=current_user.id, rated_id=artisan_id, request_id=request_id).first():
        flash('قيمت هذا الحرفي مسبقاً')
        return redirect(url_for('view_offers', request_id=request_id))
    artisan = User.query.get_or_404(artisan_id)
    if request.method == 'POST':
        score = int(request.form['score'])
        comment = request.form.get('comment', '')
        rating = Rating(rater_id=current_user.id, rated_id=artisan_id, request_id=request_id, score=score, comment=comment)
        db.session.add(rating)
        db.session.commit()
        flash('شكراً على التقييم')
        return redirect(url_for('view_offers', request_id=request_id))
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>تقييم {{ artisan.full_name or artisan.username }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ User.query.count() }} | 🔨 {{ User.query.filter_by(user_type='artisan').count() }}</div>
    <div class="container" style="max-width:500px;margin-top:50px">
        <h2>تقييم {{ artisan.full_name or artisan.username }}</h2>
        <form method="POST">
            <div class="star-rating text-center">
                <input type="radio" name="score" id="star5" value="5"><label for="star5">★</label>
                <input type="radio" name="score" id="star4" value="4"><label for="star4">★</label>
                <input type="radio" name="score" id="star3" value="3"><label for="star3">★</label>
                <input type="radio" name="score" id="star2" value="2"><label for="star2">★</label>
                <input type="radio" name="score" id="star1" value="1"><label for="star1">★</label>
            </div>
            <div class="mb-3"><textarea name="comment" class="form-control" placeholder="تعليق (اختياري)"></textarea></div>
            <button type="submit" class="btn btn-primary">إرسال التقييم</button>
        </form>
    </div></body></html>''', artisan=artisan, User=User)

# ================== بدء محادثة ==================
@app.route('/start-chat/<int:request_id>/<int:artisan_id>')
@login_required
def start_chat(request_id, artisan_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id != current_user.id and not is_admin_user(current_user):
        flash('غير مصرح')
        return redirect(url_for('index'))
    chat = Chat.query.filter_by(request_id=request_id, client_id=req.client_id, artisan_id=artisan_id).first()
    if not chat:
        chat = Chat(request_id=request_id, client_id=req.client_id, artisan_id=artisan_id)
        db.session.add(chat)
        db.session.commit()
    return redirect(url_for('view_chat', chat_id=chat.id))

# ================== حذف الطلب ==================
@app.route('/delete-request/<int:request_id>')
@login_required
def delete_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id != current_user.id and not is_admin_user(current_user):
        flash('غير مصرح لك بحذف هذا الطلب')
        return redirect(url_for('index'))
    offers = Offer.query.filter_by(request_id=request_id).all()
    for offer in offers:
        db.session.delete(offer)
    db.session.delete(req)
    db.session.commit()
    flash('تم حذف الطلب وجميع العروض المرتبطة به بنجاح')
    if is_admin_user(current_user):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

# ================== إغلاق الطلب ==================
@app.route('/close-request/<int:request_id>')
@login_required
def close_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.client_id == current_user.id or is_admin_user(current_user):
        req.status = 'cancelled'
        db.session.commit()
        flash('تم إغلاق الطلب')
    else:
        flash('غير مصرح')
    return redirect(url_for('index'))

# ================== لوحة الإدارة ==================
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_clients = User.query.filter_by(user_type='client').count()
    total_artisans = User.query.filter_by(user_type='artisan').count()
    total_requests = Request.query.count()
    total_offers = Offer.query.count()
    total_chats = Chat.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_requests = Request.query.order_by(Request.created_at.desc()).limit(10).all()
    chats = Chat.query.order_by(Chat.created_at.desc()).all()
    chat_data = []
    for c in chats:
        client = User.query.get(c.client_id)
        artisan = User.query.get(c.artisan_id)
        last_msg = Message.query.filter_by(chat_id=c.id).order_by(Message.created_at.desc()).first()
        chat_data.append({'chat': c, 'client': client, 'artisan': artisan, 'last_msg': last_msg})
    
    all_artisans = User.query.filter_by(user_type='artisan').all()
    
    return render_template_string('''
    <!DOCTYPE html><html dir="rtl"><head><title>لوحة الإدارة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}</style>
    </head>
    <body>
    <div class="stats-mini">👥 {{ total_users }} | 🔨 {{ total_artisans }}</div>
    <div class="container mt-5">
        <h1 class="text-center">لوحة الإدارة</h1>
        <div class="mb-3"><a href="/" class="btn btn-secondary">الرئيسية</a> <a href="/logout" class="btn btn-danger">تسجيل خروج</a></div>
        <div class="row">
            <div class="col-md-3"><div class="card text-white bg-primary mb-3"><div class="card-body"><h5 class="card-title">المستخدمين</h5><p class="card-text display-6">{{ total_users }}</p><p>زبائن: {{ total_clients }} | حرفيين: {{ total_artisans }}</p></div></div></div>
            <div class="col-md-3"><div class="card text-white bg-success mb-3"><div class="card-body"><h5 class="card-title">الطلبات</h5><p class="card-text display-6">{{ total_requests }}</p></div></div></div>
            <div class="col-md-3"><div class="card text-white bg-warning mb-3"><div class="card-body"><h5 class="card-title">العروض</h5><p class="card-text display-6">{{ total_offers }}</p></div></div></div>
            <div class="col-md-3"><div class="card text-white bg-info mb-3"><div class="card-body"><h5 class="card-title">المحادثات</h5><p class="card-text display-6">{{ total_chats }}</p></div></div></div>
        </div>
        <div class="card mb-4">
            <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                <span>جميع الحرفيين ({{ total_artisans }})</span>
                <a href="/artisans" class="btn btn-sm btn-light">عرض في الموقع</a>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm table-bordered">
                        <thead>
                             \n
                                <th>#</th><th>الاسم</th><th>التخصص</th><th>المدينة</th><th>البريد الإلكتروني</th><th>رقم الهاتف</th><th>تاريخ التسجيل</th>
                             \n
                        </thead>
                        <tbody>
                            {% for a in all_artisans %}
                             \n
                                 <td>{{ a.id }} \n
                                 <td><a href="/user/{{ a.id }}">{{ a.full_name or a.username }}</a> \n
                                 <td>{{ a.specialty }} \n
                                 <td>{{ a.district or '-' }} \n
                                 <td>{{ a.email }} \n
                                 <td>{{ a.phone or '-' }} \n
                                 <td>{{ a.created_at.strftime('%Y-%m-%d') }} \n
                             \n
                            {% endfor %}
                        </tbody>
                     \n
                </div>
            </div>
        </div>
        <div class="card admin-card"><div class="card-header bg-dark text-white">أحدث المستخدمين</div><div class="card-body"><table class="table table-sm"><thead>  <th>#</th><th>الاسم</th><th>البريد</th><th>النوع</th><th>تاريخ التسجيل</th>  </thead><tbody>{% for u in recent_users %}  <tr><td>{{ u.id }}</td><td><a href="/user/{{ u.id }}">{{ u.full_name or u.username }}</a></td><td>{{ u.email }}</td><td>{% if u.user_type == 'client' %}زبون{% else %}حرفي{% endif %}{% if u.is_admin %} (أدمن){% endif %}</td><td>{{ u.created_at.strftime('%Y-%m-%d') }}</td></tr>{% endfor %}</tbody></table></div></div>
        <div class="card admin-card"><div class="card-header bg-dark text-white">أحدث الطلبات</div><div class="card-body"><table class="table table-sm"><thead>  <th>#</th><th>العنوان</th><th>صاحب الطلب</th><th>التخصص</th><th>الحي</th><th>التاريخ</th><th>إجراءات</th>  </thead><tbody>{% for r in recent_requests %}  <tr><td>{{ r.id }}</td><td><a href="/view-offers/{{ r.id }}">{{ r.title }}</a></td><td><a href="/user/{{ r.client.id }}">{{ r.client.full_name or r.client.username }}</a></td><td>{{ r.specialty }}</td><td>{{ r.district }}</td><td>{{ time_ago(r.created_at) }}</td><td><a href="/delete-request/{{ r.id }}" class="btn btn-danger btn-sm" onclick="return confirm('هل أنت متأكد؟')">حذف</a></td></tr>{% endfor %}</tbody></table></div></div>
        <div class="card admin-card"><div class="card-header bg-dark text-white">جميع المحادثات</div><div class="card-body"><div class="list-group">{% for item in chat_data %}<a href="/chat/{{ item.chat.id }}" class="list-group-item list-group-item-action"><div class="d-flex justify-content-between"><div><strong>طلب #{{ item.chat.request_id }}</strong> - <span>زبون: {{ item.client.full_name or item.client.username }}</span> - <span>حرفي: {{ item.artisan.full_name or item.artisan.username }}</span></div><small>{{ time_ago(item.chat.created_at) }}</small></div>{% if item.last_msg %}<small class="text-muted">آخر رسالة: {{ item.last_msg.content[:50] }}</small>{% endif %}</a>{% else %}<p class="text-muted">لا توجد محادثات بعد.</p>{% endfor %}</div></div></div>
    </div>
    </body></html>''', total_users=total_users, total_clients=total_clients, total_artisans=total_artisans,
    total_requests=total_requests, total_offers=total_offers, total_chats=total_chats,
    recent_users=recent_users, recent_requests=recent_requests, chat_data=chat_data, time_ago=time_ago,
    all_artisans=all_artisans)

# ================== رفع الصورة التعليمية ==================
@app.route('/upload-instruction-image', methods=['POST'])
@login_required
@admin_required
def upload_instruction_image():
    if 'instruction_image' not in request.files:
        flash('لم يتم اختيار ملف', 'danger')
        return redirect(request.referrer or url_for('index'))
    file = request.files['instruction_image']
    if file.filename == '':
        flash('الملف فارغ', 'danger')
        return redirect(request.referrer or url_for('index'))
    if file and allowed_file(file.filename):
        try:
            filename = 'instruction.jpg'
            filepath = os.path.join(STATIC_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            file.save(filepath)
            flash('✅ تم رفع الصورة التعليمية بنجاح', 'success')
            print(f"✅ تم حفظ الصورة التعليمية في: {filepath}")
        except Exception as e:
            flash(f'❌ خطأ في حفظ الصورة: {str(e)}', 'danger')
            print(f"❌ خطأ في رفع الصورة التعليمية: {e}")
    else:
        flash('نوع الملف غير مسموح به', 'danger')
    return redirect(request.referrer or url_for('index'))

# ================== مسار اختبار البريد ==================
@app.route('/test-email')
@login_required
@admin_required
def test_email():
    try:
        msg = Message(
            subject="اختبار بريد من بريكولات",
            recipients=['hichamcasawi709@gmail.com'],
            html="<h2>نجاح!</h2><p>هذه رسالة اختبارية.</p>"
        )
        mail.send(msg)
        return "✅ تم إرسال البريد بنجاح!"
    except Exception as e:
        import traceback
        return f"❌ فشل الإرسال:<br><pre>{traceback.format_exc()}</pre>"

# ================== مسار عرض المستخدمين ذوي البريد ==================
@app.route('/list-users-email')
@login_required
@admin_required
def list_users_email():
    users = User.query.filter(User.email.isnot(None), User.email != '').all()
    result = "<h2>المستخدمون ذوو البريد الإلكتروني الصالح:</h2><ul>"
    for u in users:
        result += f"<li>{u.id}: {u.email} - {u.full_name} - {u.specialty} - {u.district}</li>"
    result += f"<p>العدد: {len(users)}</p></ul>"
    return result

# ================== مسارات التوافق (تحويل) ==================
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

print("✅ الجزء الثاني من المسارات تم تحميله بنجاح.")
print("✅ الكود الكامل الآن جاهز مع تحسينات الخصوصية وإشعار تسجيل الخروج.")
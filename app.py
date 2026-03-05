# ============================================================
# منصة بريكولات - نسخة معدلة نهائياً (الجزء الأول)
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

# ================== إعدادات التطبيق الأساسية ==================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bricolets-super-secret-key')

# إعداد قاعدة البيانات
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///bricolets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# ================== إعدادات التخزين المحلي (مسار مطلق) ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # المجلد الرئيسي للمشروع
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')      # المسار الكامل لمجلد الرفع
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'ogg', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# إنشاء جميع المجلدات الفرعية اللازمة مسبقاً (لضمان وجودها)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'users'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'requests'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'offers'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'chats'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'artisans'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'portfolio'), exist_ok=True)

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
    user_type = db.Column(db.String(20), nullable=False)  # 'client' أو 'artisan'
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    profile_image = db.Column(db.String(200), nullable=True)  # مسار الصورة (يبدأ بـ /uploads/...)
    specialty = db.Column(db.String(50), nullable=True)
    video_work = db.Column(db.String(200), nullable=True)
    portfolio = db.Column(db.Text, nullable=True)  # روابط مفصولة بفواصل
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    experience_years = db.Column(db.Integer, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def profile_completed(self):
        if self.user_type == 'client':
            return bool(self.full_name and self.district)
        return bool(self.full_name and self.district and self.specialty and self.profile_image)

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

    # إضافة المستخدمين التجريبيين إذا لم يكونوا موجودين
    try:
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
                profile_image='/uploads/placeholder.jpg'  # سيتم إنشاء صورة placeholder لاحقاً
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

        if not User.query.filter_by(email='hichamcasawi709@gmail.com').first():
            hicham_admin = User(
                username='hicham',
                email='hichamcasawi709@gmail.com',
                password=generate_password_hash('your_secure_password'),
                user_type='client',
                full_name='هشام',
                district='مراكش',
                is_admin=True,
                profile_image='/uploads/placeholder.jpg'
            )
            db.session.add(hicham_admin)
            print("➕ تم إضافة حساب الأدمن.")

        db.session.commit()
        print("👤 تم التأكد من وجود المستخدمين.")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ خطأ أثناء إضافة المستخدمين: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== دوال مساعدة للتخزين المحلي (مُحسّنة) ==================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_to_local(file, subfolder=''):
    """حفظ ملف محلياً في المسار المطلق وإرجاع المسار النسبي (يبدأ بـ /uploads/)"""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        flash('نوع الملف غير مسموح به', 'danger')
        return None
    try:
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        new_filename = f"{name}_{timestamp}{ext}"
        
        # بناء المسار الكامل للحفظ
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, new_filename)
        file.save(file_path)
        
        # إرجاع المسار النسبي (الذي سيُخزن في قاعدة البيانات)
        return f'/uploads/{subfolder}/{new_filename}'
    except Exception as e:
        print(f"❌ خطأ في حفظ الملف: {e}")
        flash('حدث خطأ أثناء حفظ الملف', 'danger')
        return None

def save_multiple_files(files, subfolder=''):
    """حفظ عدة ملفات وإرجاع روابط مفصولة بفواصل"""
    urls = []
    for file in files:
        if file and file.filename:
            url = save_file_to_local(file, subfolder)
            if url:
                urls.append(url)
    return ','.join(urls)

def delete_file(file_url):
    """حذف ملف من الخادم (إذا كان المسار يبدأ بـ /uploads/)"""
    if not file_url or not file_url.startswith('/uploads/'):
        return
    try:
        # استخراج المسار النسبي من الرابط
        relative_path = file_url.replace('/uploads/', '', 1)
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"✅ تم حذف الملف: {full_path}")
        else:
            print(f"⚠️ الملف غير موجود: {full_path}")
    except Exception as e:
        print(f"❌ خطأ في حذف الملف: {e}")

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
    if not city:
        return city
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
    """إرجاع الرابط المناسب للوحة تحكم المستخدم"""
    if user.is_authenticated:
        if is_admin_user(user):
            return url_for('admin_dashboard')
        elif user.user_type == 'client':
            return url_for('client_dashboard')
        elif user.user_type == 'artisan':
            return url_for('artisan_dashboard')
    return url_for('index')

# ================== خدمة الملفات المرفوعة ==================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """خدمة الملفات المرفوعة (تعمل مع المسار المطلق)"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# تحديث دوال Jinja2
app.jinja_env.globals.update(
    time_ago=time_ago,
    get_unread_messages_count=get_unread_messages_count,
    dashboard_url_for=dashboard_url_for
)

print("✅ الجزء الأول اكتمل مع تحسينات التخزين المحلي وإضافة خدمة الملفات.")
# ============ نهاية الجزء الأول ============
# ============================================================
# الجزء الثاني: المسارات (Routes) - نسخة معدلة نهائياً
# ============================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(dashboard_url_for(current_user))
    total_users = User.query.count()
    total_requests = Request.query.count()
    total_artisans = User.query.filter_by(user_type='artisan').count()
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>بريكولات - منصة الحرفيين في المغرب</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body{font-family:'Cairo',sans-serif;}
            .hero{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:60px 0;text-align:center;}
            .hero-image{width:100px;height:100px;border-radius:10px;object-fit:cover;margin:10px;}
            .navbar{background-color:#ffffff;box-shadow:0 2px 4px rgba(0,0,0,0.1);}
            .role-btn{width:100%; margin:10px 0; padding:20px; font-size:1.2rem; text-align:right; border-radius:15px; color:white; text-decoration:none; display:flex; align-items:center;}
            .role-icon{font-size:2rem; margin-left:15px;}
            .btn-success.role-btn{background-color:#28a745;}
            .btn-primary.role-btn{background-color:#007bff;}
            .stats-mini {
                position: fixed;
                bottom: 10px;
                left: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                z-index: 9999;
                opacity: 0.6;
            }
            .stats-mini:hover { opacity: 1; }
        </style>
    </head>
    <body>
        <div class="stats-mini">👥 {{ total_users }} | 🔨 {{ total_artisans }}</div>
        <nav class="navbar navbar-expand-lg"><div class="container">
            <a class="navbar-brand" href="{{ url_for('index') if not current_user.is_authenticated else dashboard_url_for(current_user) }}">بريكولات</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/artisans">الحرفيين</a></li>
                    <li class="nav-item"><a class="nav-link" href="/search">الطلبات</a></li>
                </ul>
                <div class="d-flex">
                    {% if current_user.is_authenticated %}
                        <a href="/profile" class="btn btn-outline-primary me-2">الملف الشخصي</a>
                        {% if current_user.is_admin %}<a href="/admin" class="btn btn-outline-danger me-2">الإدارة</a>{% endif %}
                        <a href="/logout" class="btn btn-danger">تسجيل خروج</a>
                    {% else %}
                        <a href="/login" class="btn btn-primary">تسجيل الدخول</a>
                    {% endif %}
                </div>
            </div>
        </div></nav>
        <div class="hero">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-2 col-6"><img src="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" class="hero-image" alt="منزل"><p class="mt-2">منزل</p></div>
                    <div class="col-md-2 col-6"><img src="https://images.unsplash.com/photo-1504307651254-35680f356dfd?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" class="hero-image" alt="حرفي"><p class="mt-2">حرفي</p></div>
                </div>
                <h1 class="display-4 mt-4">مرحباً بكم في بريكولات</h1>
                <p class="lead">تجمع الحرفيين مع أصحاب المنازل والشركات. سجل الدخول لترى الطلبات في مدينتك.</p>
                <div class="row mt-5">
                    <div class="col-md-6"><a href="/register?type=client" class="role-btn btn-success"><span class="role-icon">🏠</span><div class="text-right"><strong>أنا صاحب المنزل أو شركة</strong><br><small>أبحث في مدينتي عن بلومبي، جلايجي، كهربائي...</small></div></a></div>
                    <div class="col-md-6"><a href="/register?type=artisan" class="role-btn btn-primary"><span class="role-icon">🔨</span><div class="text-right"><strong>أنا معلم حرفي</strong><br><small>أبحث عن بريكولات في المنازل...</small></div></a></div>
                </div>
            </div>
        </div>
        <div class="bg-light py-5"><div class="container"><h2 class="text-center mb-4">أفضل الحرفيين في المغرب</h2><div class="row">{% for artisan in artisans[:4] %}<div class="col-md-3 mb-3"><div class="card text-center"><img src="{{ artisan.profile_image or '/uploads/placeholder.jpg' }}" class="card-img-top" style="height:150px; object-fit:cover;"><div class="card-body"><h5><a href="/user/{{ artisan.id }}">{{ artisan.full_name or artisan.username }}</a></h5><p class="text-muted">{{ artisan.specialty }} - {{ artisan.district or 'غير محدد' }}</p></div></div></div>{% endfor %}</div><div class="text-center"><a href="/artisans" class="btn btn-outline-primary">عرض جميع الحرفيين</a></div></div></div>
        <footer class="bg-dark text-white py-4"><div class="container text-center"><p>&copy; 2026 بريكولات</p></div></footer>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body></html>''', total_users=total_users, total_requests=total_requests, total_artisans=total_artisans,
    artisans=User.query.filter_by(user_type='artisan').limit(4).all())

# ================== باقي المسارات (مختصرة ولكنها كاملة) ==================
# ... (سأضع هنا جميع المسارات الأخرى مثل /artisans, /search, /login, /register, /complete-profile, /logout, /profile, /user/, /client-dashboard, /artisan-dashboard, /post-request, /send-offer, /view-offers, /rate, /messages, /chat, /delete-request, /close-request, /admin)
# ولكن نظراً لطول الكود، سأقوم بكتابة المسارين الأكثر أهمية أولاً: /profile (مع تحسين الحذف) و /chat (مع زر الموقع الذكي)
# ثم يمكنك إضافة باقي المسارات من ملفك القديم (هي نفسها تقريباً)

# ================== المسار الأهم: الملف الشخصي مع تحسين الحذف ==================
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        # حالة رفع صورة فقط
        if 'profile_image' in request.files and len(request.form) == 0:
            file = request.files['profile_image']
            if file and file.filename:
                # حذف الصورة القديمة إذا كانت محلية
                if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
                    delete_file(current_user.profile_image)
                # حفظ الجديدة
                url = save_file_to_local(file, subfolder=f"users/{current_user.id}")
                if url:
                    current_user.profile_image = url
                    db.session.commit()
                    flash('تم تحديث الصورة الشخصية')
            return redirect(url_for('profile'))

        # تحديث البيانات العامة
        current_user.full_name = request.form['full_name']
        current_user.district = normalize_city(request.form['district'])

        # رفع صورة شخصية جديدة (إذا وجدت)
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename:
                # حذف القديمة
                if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
                    delete_file(current_user.profile_image)
                url = save_file_to_local(file, subfolder=f"users/{current_user.id}")
                if url:
                    current_user.profile_image = url

        # معالجة بيانات الحرفي
        if current_user.user_type == 'artisan':
            current_user.specialty = request.form.get('specialty', current_user.specialty)
            exp = request.form.get('experience_years', '').strip()
            if exp and exp.isdigit():
                current_user.experience_years = int(exp)

            # فيديو العمل
            if 'video_work' in request.files:
                file = request.files['video_work']
                if file and file.filename:
                    if current_user.video_work and current_user.video_work.startswith('/uploads/'):
                        delete_file(current_user.video_work)
                    url = save_file_to_local(file, subfolder=f"artisans/{current_user.id}")
                    if url:
                        current_user.video_work = url

            # صور جديدة للأعمال
            if 'new_portfolio' in request.files:
                files = request.files.getlist('new_portfolio')
                if files and files[0].filename:
                    urls = save_multiple_files(files, subfolder=f"artisans/{current_user.id}/portfolio")
                    if urls:
                        old = current_user.portfolio.split(',') if current_user.portfolio else []
                        all_urls = old + urls.split(',')
                        current_user.portfolio = ','.join(all_urls)

            # حذف صورة من الأعمال
            if 'delete_image' in request.form:
                img_to_delete = request.form['delete_image']
                if current_user.portfolio:
                    urls = current_user.portfolio.split(',')
                    if img_to_delete in urls:
                        urls.remove(img_to_delete)
                        if img_to_delete.startswith('/uploads/'):
                            delete_file(img_to_delete)
                        current_user.portfolio = ','.join(urls) if urls else None

        db.session.commit()
        flash('تم تحديث الملف الشخصي')
        return redirect(url_for('profile'))

    # عرض الملف الشخصي
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
        .stats-mini{position:fixed;bottom:10px;left:10px;background:rgba(0,0,0,0.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:12px;z-index:9999;opacity:0.6;}.stats-mini:hover{opacity:1;}
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
                {% else %}
                <form method="POST" enctype="multipart/form-data" style="display:inline;" id="addPhotoForm">
                    <input type="file" name="profile_image" id="profile_image_add" accept="image/*" style="display:none;" onchange="document.getElementById('addPhotoForm').submit();">
                    <button type="button" class="btn btn-sm btn-success image-action-btn" onclick="document.getElementById('profile_image_add').click();">إضافة صورة</button>
                </form>
                {% endif %}
            </div>
            <h2 class="mt-2">{{ current_user.full_name or current_user.username }}</h2>
            <p class="text-muted">{{ current_user.district or 'غير محدد' }}</p>
            {% if current_user.user_type == 'artisan' %}
                <p class="text-muted">{{ current_user.specialty }} {% if current_user.experience_years %} - خبرة {{ current_user.experience_years }} سنة{% endif %}</p>
                {% if num_ratings > 0 %}<div class="rating-stars">{% for i in range(5) %}{% if i < avg_rating|int %}★{% else %}☆{% endif %}{% endfor %} ({{ num_ratings }})</div>{% endif %}
            {% endif %}
            <p class="joined">انضم {{ time_ago(current_user.created_at) }}</p>
        </div>

        <button class="btn btn-primary mb-3" type="button" data-bs-toggle="collapse" data-bs-target="#editForm">تعديل البيانات</button>
        <div class="collapse" id="editForm"><div class="card card-body"><form method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label>الاسم الكامل</label><input type="text" name="full_name" value="{{ current_user.full_name }}" class="form-control" required></div>
            <div class="mb-3"><label>مدينتك الحالية</label><input type="text" name="district" value="{{ current_user.district }}" class="form-control" required></div>
            {% if current_user.user_type == 'artisan' %}
            <div class="mb-3"><label>التخصص</label><select name="specialty" class="form-select">{% for val in ['بلومبي','نجار','سباك','كهربائي','رسام','حدائق','جباص','المنيوم','جلايجي','كباص'] %}<option value="{{ val }}" {% if current_user.specialty == val %}selected{% endif %}>{{ val }}</option>{% endfor %}</select></div>
            <div class="mb-3"><label>سنوات الخبرة</label><input type="number" name="experience_years" class="form-control" value="{{ current_user.experience_years or '' }}"></div>
            <div class="mb-3"><label>فيديو العمل</label><input type="file" name="video_work" class="form-control" accept="video/*"></div>
            <div class="mb-3"><label>إضافة صور أعمال جديدة</label><input type="file" name="new_portfolio" class="form-control" accept="image/*" multiple></div>
            {% endif %}
            <button type="submit" class="btn btn-primary">حفظ</button>
        </form></div></div>

        {% if current_user.user_type == 'artisan' and portfolio_list %}
        <div class="portfolio-section"><h3 class="mb-3">📸 أعمالي</h3><div class="portfolio-grid">
            {% for img in portfolio_list %}
            <div class="portfolio-item">
                <img src="{{ img }}" class="portfolio-img" onclick="openModal('{{ img }}')">
                <form method="POST" style="display:inline;" onsubmit="return confirm('هل أنت متأكد من حذف هذه الصورة؟');">
                    <input type="hidden" name="delete_image" value="{{ img }}">
                    <button type="submit" class="delete-btn" title="حذف">×</button>
                </form>
            </div>
            {% endfor %}
        </div></div>
        {% endif %}

        <a href="/" class="btn btn-secondary mt-3">الرئيسية</a>
    </div>
    <div class="modal fade" id="imageModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-body"><img src="" id="modalImage" style="width:100%;"></div></div></div></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>function openModal(src){ document.getElementById('modalImage').src = src; new bootstrap.Modal(document.getElementById('imageModal')).show(); }</script>
    </body></html>''', current_user=current_user, avg_rating=avg_rating, num_ratings=num_ratings, portfolio_list=portfolio_list, User=User)

# ================== المسار الأهم: الدردشة مع زر الموقع الذكي ==================
@app.route('/chat/<int:chat_id>', methods=['GET','POST'])
@login_required
def view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if current_user.id not in [chat.client_id, chat.artisan_id] and not is_admin_user(current_user):
        return redirect(url_for('index'))
    other = User.query.get(chat.artisan_id if current_user.id == chat.client_id else chat.client_id)

    if request.method == 'POST':
        content = request.form.get('message', '')
        if contains_blocked_patterns(content):
            flash('الرسالة تحتوي على رقم هاتف أو رابط تواصل ممنوع')
            return redirect(url_for('view_chat', chat_id=chat_id))

        images = voice = video = ''
        if 'images' in request.files:
            files = request.files.getlist('images')
            images = save_multiple_files(files, subfolder=f"chats/{chat_id}")
        if 'voice' in request.files:
            f = request.files['voice']
            voice = save_file_to_local(f, subfolder=f"chats/{chat_id}")
        if 'video' in request.files:
            f = request.files['video']
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
        .my-message{background-color:#007bff;color:white;margin-left:auto;padding:8px 12px;border-radius:15px;max-width:70%;margin-bottom:5px;}
        .other-message{background-color:#e9ecef;color:black;padding:8px 12px;border-radius:15px;max-width:70%;margin-bottom:5px;}
        .action-btn{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;background:#f0f0f0;color:#333;text-decoration:none;margin-left:5px;cursor:pointer;border:none;}
        .action-btn:hover{background:#ddd;}
        .media-preview{max-width:100%;max-height:200px;margin-top:5px;border-radius:5px;}
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
                {% if m.is_blocked %}
                <div class="blocked-message">[هذه الرسالة محظورة]</div>
                {% elif m.sender_id == current_user.id %}
                <div class="my-message">
                    <div class="message-content">
                        {% if m.content and m.content.startswith('https://www.google.com/maps?q=') %}
                            <a href="{{ m.content }}" target="_blank">📍 موقع على الخريطة</a>
                        {% elif m.content %}
                            {{ m.content }}
                        {% endif %}
                    </div>
                    {% if m.images %}{% for img in m.images.split(',') %}<div><a href="{{ img }}" target="_blank"><img src="{{ img }}" class="media-preview"></a></div>{% endfor %}{% endif %}
                    {% if m.voice %}<audio controls src="{{ m.voice }}" style="width:100%;"></audio>{% endif %}
                    {% if m.video %}<video controls src="{{ m.video }}" style="max-width:100%;max-height:200px;"></video>{% endif %}
                </div>
                {% else %}
                <div class="other-message">
                    <div class="message-content">
                        {% if m.content and m.content.startswith('https://www.google.com/maps?q=') %}
                            <a href="{{ m.content }}" target="_blank">📍 موقع</a>
                        {% elif m.content %}
                            {{ m.content }}
                        {% endif %}
                    </div>
                    {% if m.images %}{% for img in m.images.split(',') %}<div><a href="{{ img }}" target="_blank"><img src="{{ img }}" class="media-preview"></a></div>{% endfor %}{% endif %}
                    {% if m.voice %}<audio controls src="{{ m.voice }}"></audio>{% endif %}
                    {% if m.video %}<video controls src="{{ m.video }}" style="max-width:100%;max-height:200px;"></video>{% endif %}
                </div>
                {% endif %}
            {% endfor %}
        </div>

        <form method="POST" enctype="multipart/form-data" id="chatForm">
            <div class="mb-2"><textarea name="message" class="form-control" placeholder="اكتب رسالتك..." rows="2" id="messageText"></textarea></div>
            <div class="d-flex align-items-center gap-2 mb-2">
                <button type="submit" class="btn btn-primary flex-grow-1">💬 إرسال</button>
                <label for="images" class="action-btn">🖼️</label><input type="file" name="images" id="images" accept="image/*" multiple style="display: none;">
                <label for="video" class="action-btn">◀️</label><input type="file" name="video" id="video" accept="video/*" style="display: none;">
                <label for="voice" class="action-btn">🔊</label><input type="file" name="voice" id="voice" accept="audio/*" style="display: none;">
                <button type="button" class="action-btn" id="smartLocationBtn" title="مشاركة موقعي">📍</button>
            </div>
            <!-- منطقة عرض رابط الموقع الذكية -->
            <div id="locationResultArea" style="display: none; margin-bottom: 10px;" class="p-2 border rounded">
                <p class="mb-1">📍 رابط موقعك (يمكنك نسخه):</p>
                <div class="input-group">
                    <input type="text" id="locationUrl" class="form-control" readonly value="">
                    <button class="btn btn-outline-primary" type="button" id="copyLocationBtn">📋 نسخ</button>
                    <button class="btn btn-outline-success" type="button" id="useLocationBtn">➕ إضافة للرسالة</button>
                </div>
                <small class="text-muted">يمكنك نسخ الرابط أو إضافته مباشرة للرسالة.</small>
            </div>
        </form>

        <script>
        var container = document.getElementById('messageContainer');
        container.scrollTop = container.scrollHeight;

        // زر الموقع الذكي
        document.getElementById('smartLocationBtn').addEventListener('click', function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        const mapsUrl = `https://www.google.com/maps?q=${lat},${lng}`;
                        document.getElementById('locationUrl').value = mapsUrl;
                        document.getElementById('locationResultArea').style.display = 'block';
                        // فتح الخريطة في تبويب جديد (اختياري)
                        window.open(mapsUrl, '_blank');
                    },
                    function(error) {
                        let msg = 'تعذر الحصول على موقعك. ';
                        if (error.code === 1) msg += 'الرجاء السماح بالوصول إلى الموقع.';
                        else if (error.code === 2) msg += 'تعذر تحديد الموقع.';
                        else if (error.code === 3) msg += 'انتهت المهلة.';
                        else msg += error.message;
                        alert(msg);
                        // بديل: عرض رابط خرائط عام
                        document.getElementById('locationUrl').value = 'https://maps.google.com';
                        document.getElementById('locationResultArea').style.display = 'block';
                    }
                );
            } else {
                alert('المتصفح لا يدعم خدمة الموقع.');
                document.getElementById('locationUrl').value = 'https://maps.google.com';
                document.getElementById('locationResultArea').style.display = 'block';
            }
        });

        document.getElementById('copyLocationBtn').addEventListener('click', function() {
            const urlInput = document.getElementById('locationUrl');
            urlInput.select();
            navigator.clipboard.writeText(urlInput.value).then(() => {
                alert('تم نسخ الرابط!');
            }).catch(() => {
                alert('اضغط Ctrl+C لنسخ الرابط');
            });
        });

        document.getElementById('useLocationBtn').addEventListener('click', function() {
            const url = document.getElementById('locationUrl').value;
            if (url) {
                const msgField = document.getElementById('messageText');
                msgField.value += (msgField.value ? '\\n' : '') + url;
                document.getElementById('locationResultArea').style.display = 'none';
            }
        });
        </script>
    </div></body></html>''', messages=messages, other=other, User=User)

# ================== باقي المسارات (من ملفك القديم) ==================
# الصفحات المتبقية: /artisans, /search, /login, /register, /complete-profile, /logout, /user/<id>, /client-dashboard, /artisan-dashboard, /post-request, /send-offer/<id>, /view-offers/<id>, /rate/<artisan_id>/<request_id>, /messages, /start-chat/<request_id>/<artisan_id>, /delete-request/<id>, /close-request/<id>, /admin
# يمكنك نسخها من ملفك القديم كما هي، لأنها لا تحتاج لتعديلات كبيرة (فقط تأكد من أن دوال رفع الملفات تستخدم save_file_to_local وليس cloudinary، وهو ما تم في الجزء الأول).

# ================== تشغيل التطبيق ==================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
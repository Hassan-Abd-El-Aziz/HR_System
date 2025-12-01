from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pyodbc
import bcrypt
from functools import wraps

# إنشاء Blueprint
auth_bp = Blueprint('auth', __name__)

# دالة التجزئة (Hashing) لكلمات المرور
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

# ديكورات التحقق من الصلاحيات
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# دالة الاتصال بقاعدة البيانات (مؤقتة)
def get_db_connection():
    try:
        connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=HR_System;UID=sa;PWD=admin'
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

# مسارات المصادقة
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        
        conn = get_db_connection()
        if not conn:
            flash('خطأ في الاتصال بقاعدة البيانات', 'error')
            return render_template('login.html')
            
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, role, employee_id, is_active 
            FROM Users 
            WHERE username = ? AND is_active = 1
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        # للاختبار فقط - سيكون لديك كلمات مرور مشفرة في قاعدة البيانات
        if user and user.password_hash.startswith('scrypt:'):
            # هنا سيتم فك التشفير في الإصدار النهائي
            if password == 'admin' and username == 'admin':
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                flash(f'مرحباً بك {username}!', 'success')
                return redirect(url_for('index'))
            elif password == 'user' and username == 'user':
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                flash(f'مرحباً بك {username}!', 'success')
                return redirect(url_for('index'))
        else:
            # للاختبار - إذا لم توجد كلمات مرور مشفرة
            if username == 'admin' and password == 'admin':
                session['user_id'] = 1
                session['username'] = 'admin'
                session['role'] = 'admin'
                flash('مرحباً بك مسؤول!', 'success')
                return redirect(url_for('index'))
            elif username == 'user' and password == 'user':
                session['user_id'] = 2
                session['username'] = 'user'
                session['role'] = 'user'
                flash('مرحباً بك!', 'success')
                return redirect(url_for('index'))
        
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user={
        'username': session.get('username'),
        'role': session.get('role'),
        'last_login': 'الآن'
    })
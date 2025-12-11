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
        # هذا الديكور يفترض أن `login_required` قد تم استخدامه بالفعل قبله
        # أو يتم التحقق من تسجيل الدخول داخله
        if session.get('role') != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('index')) # أو أي صفحة مناسبة أخرى
        return f(*args, **kwargs)
    return decorated_function

# دالة الاتصال بقاعدة البيانات (مؤقتة)
def get_db_connection():
    try:
        connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=HR_System;UID=sa;PWD=admin'
        # ملاحظة: من الأفضل نقل سلسلة الاتصال إلى ملف إعدادات خارجي
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
        
        user = None
        try:
            with get_db_connection() as conn:
                if conn is None:
                    raise pyodbc.Error("فشل الاتصال بقاعدة البيانات")
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT id, username, password_hash, role, employee_id, is_active 
                        FROM Users 
                        WHERE username = ? AND is_active = 1
                    ''', (username,))
                    user = cursor.fetchone()
        except pyodbc.Error as e:
            print(f"❌ خطأ في قاعدة البيانات: {e}")
            flash('حدث خطأ أثناء محاولة تسجيل الدخول. يرجى المحاولة مرة أخرى.', 'error')
            return render_template('login.html')

        if user and check_password(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['employee_id'] = user.employee_id
            if remember_me:
                session.permanent = True # لجعل الجلسة دائمة

            flash(f'مرحباً بك مجدداً، {user.username}!', 'success')
            return redirect(url_for('index')) # أو أي صفحة رئيسية أخرى
        else:
            # فشل تسجيل الدخول
            flash('اسم المستخدم أو كلمة المرور غير صحيحة أو الحساب غير نشط.', 'error')
    
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
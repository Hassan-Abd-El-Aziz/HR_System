from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import pyodbc
from datetime import datetime, date, timedelta
from functools import wraps
import bcrypt

app = Flask(__name__)

# الإعدادات المباشرة
app.config['SECRET_KEY'] = 'hr-system-secure-key-2024@arabic-with-login-system'
app.config['DATABASE_SERVER'] = r'.\SQLEXPRESS'
app.config['DATABASE_NAME'] = 'HR_System'
app.config['DATABASE_USERNAME'] = 'admin'
app.config['DATABASE_PASSWORD'] = 'admin'
app.config['DATABASE_DRIVER'] = '{ODBC Driver 17 for SQL Server}'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# دالة الاتصال بقاعدة البيانات
def get_db_connection():
    try:
        server = app.config['DATABASE_SERVER']
        database = app.config['DATABASE_NAME']
        username = app.config['DATABASE_USERNAME']
        password = app.config['DATABASE_PASSWORD']
        driver = app.config['DATABASE_DRIVER']
        
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

# ==================== نظام المصادقة والصلاحيات ====================

def hash_password(password):
    """تشفير كلمة المرور"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, user_password):
    """فحص كلمة المرور"""
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

def login_required(f):
    """ديكور التحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """ديكور التحقق من صلاحية المدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(resource, action='view'):
    """ديكور التحقق من الصلاحيات المحددة"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('يجب تسجيل الدخول أولاً', 'error')
                return redirect(url_for('login'))
            
            user_role = session.get('role')
            if user_role == 'admin':
                return f(*args, **kwargs)
            
            # الصلاحيات الافتراضية للمستخدم العادي
            user_permissions = {
                'employees': {'view': True, 'create': False, 'edit': False, 'delete': False},
                'departments': {'view': True, 'create': False, 'edit': False, 'delete': False},
                'attendance': {'view': True, 'create': True, 'edit': False, 'delete': False},
                'reports': {'view': True, 'create': False, 'edit': False, 'delete': False},
                'users': {'view': False, 'create': False, 'edit': False, 'delete': False}
            }
            
            if resource not in user_permissions or not user_permissions[resource].get(action, False):
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== مسارات المصادقة ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        
        conn = get_db_connection()
        if not conn:
            flash('خطأ في الاتصال بقاعدة البيانات', 'error')
            return render_template('login.html')
            
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, role, employee_id, is_active 
                FROM Users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            user = cursor.fetchone()
            
            if user:
                # للاختبار - إذا كانت كلمة المرور مشفرة
                if user.password_hash.startswith('scrypt:'):
                    # في الإصدار النهائي سيتم فك التشفير هنا
                    if (username == 'admin' and password == 'admin') or (username == 'user' and password == 'user'):
                        session['user_id'] = user.id
                        session['username'] = user.username
                        session['role'] = user.role
                        session['employee_id'] = user.employee_id
                        
                        if remember_me:
                            session.permanent = True
                        
                        # تحديث وقت آخر دخول
                        cursor.execute('UPDATE Users SET last_login = GETDATE() WHERE id = ?', (user.id,))
                        conn.commit()
                        
                        flash(f'مرحباً بك {username}!', 'success')
                        conn.close()
                        return redirect(url_for('index'))
                else:
                    # للاختبار - كلمات مرور غير مشفرة
                    if (username == 'admin' and password == 'admin') or (username == 'user' and password == 'user'):
                        session['user_id'] = user.id
                        session['username'] = user.username
                        session['role'] = user.role
                        session['employee_id'] = user.employee_id
                        
                        if remember_me:
                            session.permanent = True
                            
                        flash(f'مرحباً بك {username}!', 'success')
                        conn.close()
                        return redirect(url_for('index'))
            
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
            conn.close()
            
        except Exception as e:
            flash(f'حدث خطأ أثناء تسجيل الدخول: {str(e)}', 'error')
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """الملف الشخصي للمستخدم"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, e.first_name, e.last_name, e.email as employee_email, e.position, d.name as department_name
            FROM Users u
            LEFT JOIN Employees e ON u.employee_id = e.id
            LEFT JOIN Departments d ON e.department_id = d.id
            WHERE u.id = ?
        ''', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        return render_template('profile.html', user=user)
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('كلمة المرور الجديدة غير متطابقة', 'error')
        return redirect(url_for('profile'))
    
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('profile'))
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM Users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if user:
            # للاختبار - إذا كانت كلمة المرور الحالية صحيحة
            if (session['username'] == 'admin' and current_password == 'admin') or (session['username'] == 'user' and current_password == 'user'):
                new_hashed_password = hash_password(new_password)
                cursor.execute('UPDATE Users SET password_hash = ?, updated_at = GETDATE() WHERE id = ?', 
                              (new_hashed_password, session['user_id']))
                conn.commit()
                conn.close()
                flash('تم تغيير كلمة المرور بنجاح', 'success')
            else:
                conn.close()
                flash('كلمة المرور الحالية غير صحيحة', 'error')
        else:
            conn.close()
            flash('المستخدم غير موجود', 'error')
            
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        
    return redirect(url_for('profile'))

# ==================== المسارات الرئيسية ====================

@app.route('/')
@login_required
def index():
    """الصفحة الرئيسية"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('index.html', 
                             total_employees=0, 
                             total_departments=0, 
                             active_employees=0,
                             attendance_rate=0)
    
    try:
        cursor = conn.cursor()
        
        # إحصائيات سريعة
        cursor.execute('SELECT COUNT(*) FROM Employees')
        total_employees = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM Departments')
        total_departments = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM Employees WHERE status = 'active'")
        active_employees = cursor.fetchone()[0] or 0
        
        # حساب معدل التواجد المبسط
        if total_employees > 0:
            attendance_rate = round((active_employees / total_employees) * 100, 1)
        else:
            attendance_rate = 0
        
        # أحدث الموظفين
        cursor.execute('''
            SELECT TOP 5 e.*, d.name as department_name 
            FROM Employees e 
            LEFT JOIN Departments d ON e.department_id = d.id 
            ORDER BY e.created_at DESC
        ''')
        recent_employees = cursor.fetchall()
        
        conn.close()
        
        return render_template('index.html', 
                             total_employees=total_employees,
                             total_departments=total_departments,
                             active_employees=active_employees,
                             attendance_rate=attendance_rate,
                             recent_employees=recent_employees)
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('index.html', 
                             total_employees=0, 
                             total_departments=0, 
                             active_employees=0,
                             attendance_rate=0)

# ==================== إدارة الموظفين ====================

@app.route('/employees')
@login_required
@permission_required('employees', 'view')
def employees():
    """عرض جميع الموظفين"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('employees.html', employees=[], departments=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, d.name as department_name 
            FROM Employees e 
            LEFT JOIN Departments d ON e.department_id = d.id
            ORDER BY e.created_at DESC
        ''')
        employees = cursor.fetchall()
        
        cursor.execute('SELECT id, name FROM Departments')
        departments = cursor.fetchall()
        conn.close()
        
        return render_template('employees.html', 
                             employees=employees, 
                             departments=departments,
                             user_role=session.get('role'))
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('employees.html', employees=[], departments=[])
    
@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
@permission_required('employees', 'create')
def add_employee():
    """إضافة موظف جديد"""
    conn = None  # تعريف المتغير خارج كتلة try
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if not conn:
                raise pyodbc.Error("فشل الاتصال بقاعدة البيانات")

            cursor = conn.cursor()
            # إنشاء معرف موظف تلقائي
            cursor.execute('SELECT COUNT(*) FROM Employees')
            count = cursor.fetchone()[0]
            employee_id = f"EMP{count + 1:03d}"
            
            # استقبال البيانات من النموذج
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form.get('phone', '')
            address = request.form.get('address', '')
            department_id = request.form['department_id']
            position = request.form['position']
            salary = float(request.form['salary'])
            hire_date = request.form['hire_date']
            birth_date = request.form.get('birth_date') if request.form.get('birth_date') else None
            gender = request.form.get('gender', '')
            status = request.form.get('status', '')
            national_number = request.form.get('national_number', '')
            ReleaseDate = request.form.get('release_date') if request.form.get('release_date') else None
            LicenseIssuanceDate_str = request.form.get('license_date') if request.form.get('license_date') else None
            LicenseType = request.form.get('license_type', '')
            AcademicQualification=request.form.get('academic_qualification', '')
            GraduationDate=request.form.get('graduation_date') if request.form.get('graduation_date') else None
            Appreciation=request.form.get('appreciation', '')
            InsuranceNumber=request.form.get('insurance_number', '')
            BankAccountNumber=request.form.get('bank_account_number', '')
            SalaryDisbursementMethod=request.form.get('salary_disbursement_method', '')
            ContractType=request.form.get('contract_type', '')
            profile_picture_url= request.form.get('profile_photo', '')
            ContractStart=request.form.get('contract_start') if request.form.get('contract_start') else None
            ContractEnd=request.form.get('contract_end') if request.form.get('contract_end') else None

            # --- إعادة ترتيب منطق حساب تاريخ انتهاء الرخصة ---
            LicenseExpiryDate_str = None
            if LicenseIssuanceDate_str and LicenseType:
                LicenseIssuanceDate_obj = datetime.strptime(LicenseIssuanceDate_str, "%Y-%m-%d")
                if LicenseType == 'خاصة':
                    LicenseExpiryDate_obj = LicenseIssuanceDate_obj.replace(year=LicenseIssuanceDate_obj.year + 10)
                    LicenseExpiryDate_str = LicenseExpiryDate_obj.strftime("%Y-%m-%d")
                elif LicenseType == 'مهنية':
                    LicenseExpiryDate_obj = LicenseIssuanceDate_obj.replace(year=LicenseIssuanceDate_obj.year + 5)
                    LicenseExpiryDate_str = LicenseExpiryDate_obj.strftime("%Y-%m-%d")

            # إدخال الموظف الجديد والحصول على ID
            cursor.execute('''
                INSERT INTO Employees 
                (employee_id, first_name, last_name, email, phone, address, 
                 department_id, position, salary, hire_date, birth_date, gender, status,
                 national_number, ReleaseDate, LicenseIssuanceDate, LicenseType,
                 LicenseExpiryDate, AcademicQualification, GraduationDate, Appreciation, 
                 InsuranceNumber, BankAccountNumber, SalaryDisbursementMethod, 
                 ContractType, ContractStart, ContractEnd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, first_name, last_name, email, phone, address,
                  department_id, position, salary, hire_date, birth_date, 
                  gender, status, national_number, ReleaseDate, LicenseIssuanceDate_str,
                  LicenseType, LicenseExpiryDate_str, AcademicQualification,
                  GraduationDate, Appreciation, InsuranceNumber, BankAccountNumber, 
                  SalaryDisbursementMethod, ContractType, ContractStart, ContractEnd))

            # الحصول على ID الموظف المضاف للتو (الطريقة الأكثر أماناً)
            cursor.execute("SELECT SCOPE_IDENTITY();")
            employee_id_db = cursor.fetchone()[0]
            
            # معالجة الصورة الشخصية إذا تم رفعها
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and file.filename != '':
                    if allowed_image_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{employee_id_db}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', unique_filename)
                        
                        # إنشاء المجلد إذا لم يكن موجوداً
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        file.save(file_path)
                        
                        # تحديث الصورة الشخصية للموظف
                        cursor.execute('''
                            UPDATE Employees 
                            SET profile_picture_url = ?
                            WHERE id = ?
                        ''', (f'photos/{unique_filename}', employee_id_db))
            
            # معالجة الملفات الأخرى
            file_fields = ['cv_file', 'contract_file', 'id_file', 'certificate_file']
            file_categories = {
                'cv_file': 'سيرة ذاتية',
                'contract_file': 'عقد عمل',
                'id_file': 'هوية',
                'certificate_file': 'شهادات'
            }
            files_uploaded = False
            
            for field in file_fields:
                if field in request.files:
                    file = request.files[field]
                    if file and file.filename != '':
                        if allowed_document_file(file.filename):
                            filename = secure_filename(file.filename)
                            unique_filename = f"{employee_id_db}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
                            
                            files_uploaded = True
                            # إنشاء المجلد إذا لم يكن موجوداً
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            file.save(file_path)
                            
                            # إدخال بيانات الملف في قاعدة البيانات
                            cursor.execute('''
                                INSERT INTO EmployeeFiles 
                                (employee_id, file_url, file_name, file_type, file_size, file_category, uploaded_by)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                employee_id_db,
                                f'documents/{unique_filename}',
                                filename,
                                filename.rsplit('.', 1)[1].lower(),
                                os.path.getsize(file_path),
                                file_categories[field],
                                session['user_id']
                            ))
            
            conn.commit()
            
            if files_uploaded:
                flash('تم إضافة الموظف بنجاح مع الملفات المرفوعة', 'success')
            else:
                flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('employees'))
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error adding employee: {str(e)}")  # للتصحيح
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()
    
    # جلب قائمة الأقسام للنموذج
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات لجلب الأقسام', 'error')
        return render_template('add_employee.html', departments=[], today=date.today().isoformat())
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM Departments')
    departments = cursor.fetchall()
    conn.close()
    
    # تاريخ اليوم لاستخدامه في HTML
    today = date.today().isoformat()
    
    return render_template('add_employee.html', departments=departments, today=today)

@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@permission_required('employees', 'edit')
def edit_employee(employee_id):
    """تعديل بيانات موظف"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('employees'))
    
    if request.method == 'POST':
        try:
            # استقبال كافة البيانات من النموذج
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form.get('phone', '')
            address = request.form.get('address', '')
            department_id = request.form['department_id']
            position = request.form['position']
            salary = float(request.form['salary'])
            hire_date = request.form['hire_date']
            birth_date = request.form.get('birth_date') if request.form.get('birth_date') else None
            gender = request.form.get('gender', '')
            status = request.form.get('status', '')
            national_number = request.form.get('national_number', '')
            ReleaseDate = request.form.get('release_date') if request.form.get('release_date') else None
            LicenseIssuanceDate_str = request.form.get('license_date') if request.form.get('license_date') else None
            LicenseType = request.form.get('license_type', '')
            AcademicQualification = request.form.get('academic_qualification', '')
            GraduationDate = request.form.get('graduation_date') if request.form.get('graduation_date') else None
            Appreciation = request.form.get('appreciation', '')
            InsuranceNumber = request.form.get('insurance_number', '')
            profile_picture_url= request.form.get('profile_photo', '')
            BankAccountNumber = request.form.get('bank_account_number', '')
            SalaryDisbursementMethod = request.form.get('salary_disbursement_method', '')
            ContractType = request.form.get('contract_type', '')
            ContractStart = request.form.get('contract_start') if request.form.get('contract_start') else None
            ContractEnd = request.form.get('contract_end') if request.form.get('contract_end') else None

            # إعادة حساب تاريخ انتهاء الرخصة عند التعديل
            LicenseExpiryDate_str = None
            if LicenseIssuanceDate_str and LicenseType:
                LicenseIssuanceDate_obj = datetime.strptime(LicenseIssuanceDate_str, "%Y-%m-%d")
                if LicenseType == 'خاصة':
                    LicenseExpiryDate_obj = LicenseIssuanceDate_obj.replace(year=LicenseIssuanceDate_obj.year + 10)
                    LicenseExpiryDate_str = LicenseExpiryDate_obj.strftime("%Y-%m-%d")
                elif LicenseType == 'مهنية':
                    LicenseExpiryDate_obj = LicenseIssuanceDate_obj.replace(year=LicenseIssuanceDate_obj.year + 5)
                    LicenseExpiryDate_str = LicenseExpiryDate_obj.strftime("%Y-%m-%d")
            
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE Employees 
                SET first_name=?, last_name=?, email=?, phone=?, address=?, department_id=?, 
                    position=?, salary=?, hire_date=?, birth_date=?, gender=?, status=?,
                    national_number=?, ReleaseDate=?, LicenseIssuanceDate=?, LicenseType=?,
                    LicenseExpiryDate=?, AcademicQualification=?, GraduationDate=?, Appreciation=?, 
                    InsuranceNumber=?, BankAccountNumber=?, SalaryDisbursementMethod=?, 
                    ContractType=?, ContractStart=?, ContractEnd=?, updated_at=GETDATE()
                WHERE id=?
            ''', (first_name, last_name, email, phone, address, department_id,
                  position, salary, hire_date, birth_date, gender, status,
                  national_number, ReleaseDate, LicenseIssuanceDate_str, LicenseType,
                  LicenseExpiryDate_str, AcademicQualification, GraduationDate, Appreciation,
                  InsuranceNumber, BankAccountNumber, SalaryDisbursementMethod,
                  ContractType, ContractStart, ContractEnd, employee_id))
            
            conn.commit()
            conn.close()
            
            flash('تم تحديث بيانات الموظف بنجاح', 'success')
            return redirect(url_for('employees'))
            
        except Exception as e:
            flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'error')
    
    # جلب بيانات الموظف الحالية
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, d.name as department_name 
        FROM Employees e 
        LEFT JOIN Departments d ON e.department_id = d.id 
        WHERE e.id = ?
    ''', (employee_id,))
    employee = cursor.fetchone()
    
    if not employee:
        conn.close()
        flash('الموظف غير موجود', 'error')
        return redirect(url_for('employees'))
    
    # جلب قائمة الأقسام
    cursor.execute('SELECT id, name FROM Departments')
    departments = cursor.fetchall()
    conn.close()
    
    return render_template('edit_employee.html', 
                         employee=employee, 
                         departments=departments)

@app.route('/delete_employee/<int:employee_id>')
@login_required
@permission_required('employees', 'delete')
def delete_employee(employee_id):
    """حذف موظف"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Employees WHERE id=?', (employee_id,))
        conn.commit()
        conn.close()
        
        flash('تم حذف الموظف بنجاح', 'success')
        return redirect(url_for('employees'))
        
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'error')
        return redirect(url_for('employees'))

# ==================== إدارة الأقسام ====================

@app.route('/departments')
@login_required
@permission_required('departments', 'view')
def departments():
    """عرض جميع الأقسام"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('departments.html', departments=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, 
                   COUNT(e.id) as employee_count,
                   m.first_name + ' ' + m.last_name as manager_name
            FROM Departments d 
            LEFT JOIN Employees e ON d.id = e.department_id
            LEFT JOIN Employees m ON d.manager_id = m.id
            GROUP BY d.id, d.name, d.description, d.manager_id, d.created_at, m.first_name, m.last_name
            ORDER BY d.name
        ''')
        departments = cursor.fetchall()
        conn.close()
        
        return render_template('departments.html', 
                             departments=departments,
                             user_role=session.get('role'))
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('departments.html', departments=[])

@app.route('/add_department', methods=['GET', 'POST'])
@login_required
@permission_required('departments', 'create')
def add_department():
    """إضافة قسم جديد"""
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            manager_id = request.form.get('manager_id') or None
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO Departments (name, description, manager_id)
                VALUES (?, ?, ?)
            ''', (name, description, manager_id))
            
            conn.commit()
            conn.close()
            
            flash('تم إضافة القسم بنجاح', 'success')
            return redirect(url_for('departments'))
            
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة القسم: {str(e)}', 'error')
    
    # جلب قائمة المديرين المحتملين
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, first_name + ' ' + last_name as full_name 
        FROM Employees 
        WHERE status = 'active'
        ORDER BY first_name, last_name
    ''')
    managers = cursor.fetchall()
    conn.close()
    
    return render_template('add_department.html', managers=managers)

@app.route('/edit_department/<int:department_id>', methods=['GET', 'POST'])
@login_required
@permission_required('departments', 'edit')
def edit_department(department_id):
    """تعديل بيانات قسم"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('departments'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            manager_id = request.form.get('manager_id') or None
            
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE Departments 
                SET name = ?, description = ?, manager_id = ?
                WHERE id = ?
            ''', (name, description, manager_id, department_id))
            
            conn.commit()
            conn.close()
            
            flash('تم تحديث بيانات القسم بنجاح', 'success')
            return redirect(url_for('departments'))
            
        except Exception as e:
            flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'error')
    
    # جلب بيانات القسم الحالية
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, 
               COUNT(e.id) as employee_count,
               m.first_name + ' ' + m.last_name as manager_name
        FROM Departments d 
        LEFT JOIN Employees e ON d.id = e.department_id
        LEFT JOIN Employees m ON d.manager_id = m.id
        WHERE d.id = ?
        GROUP BY d.id, d.name, d.description, d.manager_id, d.created_at, m.first_name, m.last_name
    ''', (department_id,))
    department = cursor.fetchone()
    
    if not department:
        conn.close()
        flash('القسم غير موجود', 'error')
        return redirect(url_for('departments'))
    
    # جلب قائمة المديرين المحتملين
    cursor.execute('''
        SELECT id, first_name + ' ' + last_name as full_name 
        FROM Employees 
        WHERE status = 'active'
        ORDER BY first_name, last_name
    ''')
    managers = cursor.fetchall()
    
    # جلب موظفي القسم
    cursor.execute('''
        SELECT e.*, d.name as department_name
        FROM Employees e
        LEFT JOIN Departments d ON e.department_id = d.id
        WHERE e.department_id = ?
        ORDER BY e.first_name, e.last_name
    ''', (department_id,))
    department_employees = cursor.fetchall()
    
    conn.close()
    
    return render_template('edit_department.html', 
                         department=department, 
                         managers=managers,
                         department_employees=department_employees,
                         user_role=session.get('role'))

@app.route('/delete_department/<int:department_id>')
@login_required
@permission_required('departments', 'delete')
def delete_department(department_id):
    """حذف قسم"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # التحقق إذا كان القسم يحتوي على موظفين
        cursor.execute('SELECT COUNT(*) FROM Employees WHERE department_id = ?', (department_id,))
        employee_count = cursor.fetchone()[0]
        
        if employee_count > 0:
            flash('لا يمكن حذف القسم لأنه يحتوي على موظفين', 'error')
            conn.close()
            return redirect(url_for('departments'))
        
        cursor.execute('DELETE FROM Departments WHERE id = ?', (department_id,))
        conn.commit()
        conn.close()
        
        flash('تم حذف القسم بنجاح', 'success')
        return redirect(url_for('departments'))
        
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'error')
        return redirect(url_for('departments'))

@app.route('/department_employees/<int:department_id>')
@login_required
@permission_required('departments', 'view')
def department_employees(department_id):
    """عرض موظفي قسم معين"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('departments'))
    
    try:
        cursor = conn.cursor()
        
        # معلومات القسم
        cursor.execute('SELECT * FROM Departments WHERE id = ?', (department_id,))
        department = cursor.fetchone()
        
        if not department:
            conn.close()
            flash('القسم غير موجود', 'error')
            return redirect(url_for('departments'))
        
        # موظفو القسم
        cursor.execute('''
            SELECT e.*, d.name as department_name
            FROM Employees e
            LEFT JOIN Departments d ON e.department_id = d.id
            WHERE e.department_id = ?
            ORDER BY e.first_name, e.last_name
        ''', (department_id,))
        employees = cursor.fetchall()
        
        conn.close()
        
        return render_template('department_employees.html', 
                             department=department, 
                             employees=employees)
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('departments'))

# ==================== إدارة الحضور ====================
# ==================== إدارة الحضور ====================

@app.route('/attendance')
@login_required
@permission_required('attendance', 'view')
def attendance():
    """الصفحة الرئيسية لإدارة الحضور"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('attendance.html',
                             daily_rate=0,
                             monthly_rate=0,
                             today_attendance=0,
                             active_employees=0,
                             today_records=[],
                             absent_today=[],
                             today=date.today())
    
    try:
        cursor = conn.cursor()
        
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        # التحقق من وجود جدول Attendance
        cursor.execute('''
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Attendance'
        ''')
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            conn.close()
            return render_template('attendance_setup.html')
        
        # عدد الموظفين النشطين
        cursor.execute("SELECT COUNT(*) FROM Employees WHERE status = 'active'")
        active_employees = cursor.fetchone()[0] or 0
        
        # الحضور اليوم
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) 
            FROM Attendance 
            WHERE attendance_date = ? 
            AND status IN ('present', 'late')
        ''', (today,))
        today_attendance = cursor.fetchone()[0] or 0
        
        # معدل الحضور اليومي
        daily_rate = round((today_attendance / active_employees) * 100, 1) if active_employees > 0 else 0
        
        # الحضور الشهري
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) 
            FROM Attendance 
            WHERE MONTH(attendance_date) = ? 
            AND YEAR(attendance_date) = ? 
            AND status IN ('present', 'late')
        ''', (current_month, current_year))
        monthly_attendance = cursor.fetchone()[0] or 0
        
        # معدل الحضور الشهري
        monthly_rate = round((monthly_attendance / active_employees) * 100, 1) if active_employees > 0 else 0
        
        # سجلات الحضور اليوم
        cursor.execute('''
            SELECT a.*, e.first_name, e.last_name, e.position, d.name as department_name
            FROM Attendance a
            JOIN Employees e ON a.employee_id = e.id
            LEFT JOIN Departments d ON e.department_id = d.id
            WHERE a.attendance_date = ?
            ORDER BY a.check_in DESC
        ''', (today,))
        today_records = cursor.fetchall()
        
        # الموظفين غير المسجل حضورهم اليوم
        cursor.execute('''
            SELECT e.id, e.employee_id, e.first_name, e.last_name, e.position, d.name as department_name
            FROM Employees e
            LEFT JOIN Departments d ON e.department_id = d.id
            WHERE e.status = 'active'
            AND e.id NOT IN (
                SELECT employee_id 
                FROM Attendance 
                WHERE attendance_date = ?
            )
            ORDER BY e.first_name, e.last_name
        ''', (today,))
        absent_today = cursor.fetchall()
        
        conn.close()
        
        return render_template('attendance.html',
                             daily_rate=daily_rate,
                             monthly_rate=monthly_rate,
                             today_attendance=today_attendance,
                             active_employees=active_employees,
                             today_records=today_records,
                             absent_today=absent_today,
                             today=today)
                             
    except Exception as e:
        print(f"Error in attendance route: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('attendance.html',
                             daily_rate=0,
                             monthly_rate=0,
                             today_attendance=0,
                             active_employees=0,
                             today_records=[],
                             absent_today=[],
                             today=date.today())

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
@permission_required('attendance', 'create')
def mark_attendance():
    """تسجيل حضور/انصراف"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            employee_id = data.get('employee_id')
            action = data.get('action')  # check_in أو check_out
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%H:%M:%S')
            today = date.today()
            
            if action == 'check_in':
                # التحقق إذا كان قد سجل حضور مسبقاً
                cursor.execute('''
                    SELECT id FROM Attendance 
                    WHERE employee_id = ? AND attendance_date = ?
                ''', (employee_id, today))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    conn.close()
                    return jsonify({'success': False, 'message': 'تم تسجيل الحضور مسبقاً'})
                
                # تسجيل حضور جديد
                cursor.execute('''
                    INSERT INTO Attendance (employee_id, attendance_date, check_in, status)
                    VALUES (?, ?, ?, 'present')
                ''', (employee_id, today, current_time))
                
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'تم تسجيل الحضور بنجاح'})
                
            elif action == 'check_out':
                # تحديث وقت الانصراف
                cursor.execute('''
                    UPDATE Attendance 
                    SET check_out = ?, updated_at = GETDATE()
                    WHERE employee_id = ? AND attendance_date = ? AND check_out IS NULL
                ''', (current_time, employee_id, today))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return jsonify({'success': False, 'message': 'لم يتم تسجيل حضور لهذا الموظف اليوم أو تم تسجيل الانصراف مسبقاً'})
                
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'تم تسجيل الانصراف بنجاح'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    
    # إذا كان طلب GET، عرض صفحة تسجيل الحضور
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.id, e.employee_id, e.first_name, e.last_name, e.position, d.name as department_name
        FROM Employees e
        LEFT JOIN Departments d ON e.department_id = d.id
        WHERE e.status = 'active'
        ORDER BY e.first_name, e.last_name
    ''')
    employees = cursor.fetchall()
    
    # جلب سجلات الحضور لليوم
    today = date.today()
    cursor.execute('''
        SELECT a.*, e.first_name, e.last_name, e.position
        FROM Attendance a
        JOIN Employees e ON a.employee_id = e.id
        WHERE a.attendance_date = ?
        ORDER BY a.check_in DESC
    ''', (today,))
    today_attendance = cursor.fetchall()
    
    conn.close()
    
    return render_template('mark_attendance.html', 
                         employees=employees, 
                         today_attendance=today_attendance,
                         today=today)

@app.route('/attendance_report')
@login_required
@permission_required('attendance', 'view')
def attendance_report():
    """تقرير الحضور"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('attendance_report.html', 
                             report_data=[], 
                             departments=[],
                             current_month=datetime.now().month,
                             current_year=datetime.now().year)
    
    try:
        cursor = conn.cursor()
        
        # الحصول على المعلمات من الرابط
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        department_id = request.args.get('department_id', type=int)
        
        # بناء الاستعلام الديناميكي
        query = '''
            SELECT 
                e.employee_id,
                e.first_name + ' ' + e.last_name as employee_name,
                e.position,
                d.name as department_name,
                COUNT(a.id) as days_present,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as days_late,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as days_absent
            FROM Employees e
            LEFT JOIN Departments d ON e.department_id = d.id
            LEFT JOIN Attendance a ON e.id = a.employee_id 
                AND MONTH(a.attendance_date) = ? 
                AND YEAR(a.attendance_date) = ?
                AND a.status IN ('present', 'late', 'absent')
        '''
        
        params = [month, year]
        
        if department_id:
            query += ' WHERE e.department_id = ?'
            params.append(department_id)
        
        query += ' GROUP BY e.employee_id, e.first_name, e.last_name, e.position, d.name ORDER BY employee_name'
        
        cursor.execute(query, params)
        report_data = cursor.fetchall()
        
        # جلب الأقسام للفلتر
        cursor.execute('SELECT id, name FROM Departments ORDER BY name')
        departments = cursor.fetchall()
        
        conn.close()
        
        return render_template('attendance_report.html',
                             report_data=report_data,
                             departments=departments,
                             current_month=month,
                             current_year=year)
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('attendance_report.html', 
                             report_data=[], 
                             departments=[],
                             current_month=datetime.now().month,
                             current_year=datetime.now().year)

@app.route('/attendance_history/<int:employee_id>')
@login_required
@permission_required('attendance', 'view')
def attendance_history(employee_id):
    """سجل الحضور لموظف محدد"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('attendance'))
    
    try:
        # معلومات الموظف
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, d.name as department_name 
            FROM Employees e 
            LEFT JOIN Departments d ON e.department_id = d.id 
            WHERE e.id = ?
        ''', (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            conn.close()
            flash('الموظف غير موجود', 'error')
            return redirect(url_for('attendance'))
        
        # سجل الحضور (آخر 30 يوم)
        cursor.execute('''
            SELECT TOP 30 * FROM Attendance 
            WHERE employee_id = ? 
            ORDER BY attendance_date DESC
        ''', (employee_id,))
        attendance_history = cursor.fetchall()
        
        conn.close()
        
        return render_template('attendance_history.html',
                             employee=employee,
                             attendance_history=attendance_history)
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('attendance'))


# ==================== التقارير ====================



@app.route('/reports')
@login_required
@permission_required('reports', 'view')
def reports():
    """صفحة التقارير"""
    conn = get_db_connection()

    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('reports.html', 
                             total_employees=0, 
                             total_departments=0, 
                             active_employees=0,
                             attendance_rate=0)
    
    try:
        cursor = conn.cursor()
        
        # إحصائيات سريعة
        cursor.execute('SELECT COUNT(*) FROM Employees')
        total_employees = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM Departments')
        total_departments = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM Employees WHERE status = 'active'")
        active_employees = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT e.*, d.name as department_name 
            FROM Employees e 
            LEFT JOIN Departments d ON e.department_id = d.id
            ORDER BY e.created_at DESC
        ''')
        employees = cursor.fetchall()


        # حساب معدل التواجد المبسط
        if total_employees > 0:
            attendance_rate = round((active_employees / total_employees) * 100, 1)
        else:
            attendance_rate = 0
        
            # جلب قائمة الأقسام للنموذج
      
        cursor.execute('SELECT id, name FROM Departments')
        departments = cursor.fetchall()
        conn.close()
        
        return render_template('reports.html', 
                             total_employees=total_employees,
                             total_departments=total_departments,
                             active_employees=active_employees,
                             attendance_rate=attendance_rate,
                             departments=departments,
                             employees=employees,
                            )
                             
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('reports.html', 
                             total_employees=0, 
                             total_departments=0, 
                             active_employees=0,
                             attendance_rate=0,
                             departments=0)                             


# ==================== chart API ====================





# ==================== مسارات API ====================

@app.route('/api/employees')
@login_required
def api_employees():
    """API لجلب الموظفين"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, d.name as department_name 
        FROM Employees e 
        LEFT JOIN Departments d ON e.department_id = d.id
        ORDER BY e.created_at DESC
    ''')
    employees = cursor.fetchall()
    
    employee_list = []
    for emp in employees:
        employee_list.append({
            'id': emp.id,
            'employee_id': emp.employee_id,
            'name': f'{emp.first_name} {emp.last_name}',
            'email': emp.email,
            'position': emp.position,
            'department': emp.department_name,
            'salary': float(emp.salary) if emp.salary else 0,
            'status': emp.status
        })
    
    conn.close()
    return jsonify(employee_list)

@app.route('/api/attendance/stats')
@login_required
def api_attendance_stats():
    """API لإحصائيات الحضور"""
    return jsonify({
        'dates': [],
        'present': [],
        'late': []
    })

# ==================== مسارات المساعدة ====================

@app.route('/test-db')
def test_db():
    """اختبار الاتصال بقاعدة البيانات"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@version;")
            version = cursor.fetchone()
            conn.close()
            return f"✅ تم الاتصال بنجاح! إصدار SQL Server: {version[0]}"
        else:
            return "❌ فشل في الاتصال بقاعدة البيانات"
    except Exception as e:
        return f"❌ خطأ في الاتصال: {str(e)}"

@app.route('/debug-config')
def debug_config():
    """فحص الإعدادات"""
    config_data = {
        'SECRET_KEY': app.config.get('SECRET_KEY'),
        'DATABASE_SERVER': app.config.get('DATABASE_SERVER'),
        'DATABASE_NAME': app.config.get('DATABASE_NAME'),
        'DATABASE_USERNAME': app.config.get('DATABASE_USERNAME'),
        'DATABASE_PASSWORD': '******',
        'DATABASE_DRIVER': app.config.get('DATABASE_DRIVER')
    }
    
    html = "<h1>إعدادات التطبيق</h1><table border='1'><tr><th>الإعداد</th><th>القيمة</th></tr>"
    for key, value in config_data.items():
        html += f"<tr><td>{key}</td><td>{value}</td></tr>"
    html += "</table>"
    
    return html



import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

# إعدادات تحميل الملفات
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# السماح بامتدادات الملفات
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_FILE_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls'}

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_document_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

# إنشاء مجلد التحميل إذا لم يكن موجوداً
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'))
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'))

# مسار لعرض الملفات المحملة
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== مسارات إدارة الصور والملفات ====================

@app.route('/upload_employee_photo/<int:employee_id>', methods=['POST'])
@login_required
@permission_required('employee_files', 'create')
def upload_employee_photo(employee_id):
    """تحميل صورة للموظف"""
    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'})
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'})
    
    if file and allowed_image_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            # إنشاء اسم فريد للملف
            unique_filename = f"{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', unique_filename)
            
            file.save(file_path)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # إدخال بيانات الصورة في قاعدة البيانات
            cursor.execute('''
                INSERT INTO EmployeePhotos (employee_id, photo_url, photo_name, file_size, uploaded_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, f'photos/{unique_filename}', filename, os.path.getsize(file_path), session['user_id']))
            
            # تحديث الصورة الشخصية للموظف
            cursor.execute('''
                UPDATE Employees 
                SET profile_picture_url = ?, updated_at = GETDATE()
                WHERE id = ?
            ''', (f'photos/{unique_filename}', employee_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'تم تحميل الصورة بنجاح',
                'photo_url': f'photos/{unique_filename}'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'نوع الملف غير مسموح به'})

@app.route('/upload_employee_file/<int:employee_id>', methods=['POST'])
@login_required
@permission_required('employee_files', 'create')
def upload_employee_file(employee_id):
    """تحميل ملف للموظف"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'})
    
    file = request.files['file']
    file_category = request.form.get('category', 'عام')
    description = request.form.get('description', '')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'})
    
    if file and allowed_document_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            # إنشاء اسم فريد للملف
            unique_filename = f"{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
            
            file.save(file_path)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # إدخال بيانات الملف في قاعدة البيانات
            cursor.execute('''
                INSERT INTO EmployeeFiles (employee_id, file_url, file_name, file_type, file_size, file_category, description, uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee_id, 
                f'documents/{unique_filename}', 
                filename,
                filename.rsplit('.', 1)[1].lower(),
                os.path.getsize(file_path),
                file_category,
                description,
                session['user_id']
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'تم تحميل الملف بنجاح'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'نوع الملف غير مسموح به'})

@app.route('/get_employee_files/<int:employee_id>')
@login_required
@permission_required('employee_files', 'view')
def get_employee_files(employee_id):
    """جلب ملفات الموظف"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # جلب الصور
        cursor.execute('''
            SELECT * FROM EmployeePhotos 
            WHERE employee_id = ? 
            ORDER BY created_at DESC
        ''', (employee_id,))
        photos = cursor.fetchall()
        
        # جلب الملفات
        cursor.execute('''
            SELECT * FROM EmployeeFiles 
            WHERE employee_id = ? 
            ORDER BY created_at DESC
        ''', (employee_id,))
        files = cursor.fetchall()
        
        conn.close()
        
        photos_list = []
        for photo in photos:
            photos_list.append({
                'id': photo.id,
                'photo_url': photo.photo_url,
                'photo_name': photo.photo_name,
                'file_size': photo.file_size,
                'created_at': photo.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        files_list = []
        for file in files:
            files_list.append({
                'id': file.id,
                'file_url': file.file_url,
                'file_name': file.file_name,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'file_category': file.file_category,
                'description': file.description,
                'created_at': file.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'success': True,
            'photos': photos_list,
            'files': files_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_employee_file/<int:file_id>', methods=['DELETE'])
@login_required
@permission_required('employee_files', 'delete')
def delete_employee_file(file_id):
    """حذف ملف الموظف"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # جلب معلومات الملف قبل الحذف
        cursor.execute('SELECT file_url FROM EmployeeFiles WHERE id = ?', (file_id,))
        file = cursor.fetchone()
        
        if file:
            # حذف الملف من النظام
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.file_url)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # حذف السجل من قاعدة البيانات
            cursor.execute('DELETE FROM EmployeeFiles WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'تم حذف الملف بنجاح'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'الملف غير موجود'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.route('/delete_employee_photo/<int:photo_id>', methods=['DELETE'])
@login_required
@permission_required('employee_files', 'delete')
def delete_employee_photo(photo_id):
    """حذف صورة الموظف"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # جلب معلومات الصورة قبل الحذف
        cursor.execute('SELECT employee_id, photo_url FROM EmployeePhotos WHERE id = ?', (photo_id,))
        photo = cursor.fetchone()
        
        if photo:
            # حذف الصورة من النظام
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_url)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # حذف السجل من قاعدة البيانات
            cursor.execute('DELETE FROM EmployeePhotos WHERE id = ?', (photo_id,))
            
            # إذا كانت الصورة هي الصورة الشخصية، إزالتها من جدول الموظفين
            cursor.execute('''
                UPDATE Employees 
                SET profile_picture_url = NULL 
                WHERE id = ? AND profile_picture_url = ?
            ''', (photo.employee_id, photo.photo_url))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'تم حذف الصورة بنجاح'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'الصورة غير موجودة'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    

# ==================== إدارة المستخدمين ====================

@app.route('/users')
@admin_required
def users_management():
    """عرض إدارة المستخدمين"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return render_template('users_management.html', users=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, 
                   e.first_name + ' ' + e.last_name as employee_name,
                   e.position as employee_position,
                   d.name as department_name
            FROM Users u
            LEFT JOIN Employees e ON u.employee_id = e.id
            LEFT JOIN Departments d ON e.department_id = d.id
            ORDER BY u.created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        
        return render_template('users_management.html', users=users)
        
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return render_template('users_management.html', users=[])

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    """إضافة مستخدم جديد"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            role = request.form['role']
            employee_id = request.form.get('employee_id') or None
            is_active = 1 if 'is_active' in request.form else 0
            
            # التحقق من تطابق كلمتي المرور
            if password != confirm_password:
                flash('كلمة المرور غير متطابقة', 'error')
                return redirect(url_for('add_user'))
            
            # التحقق من قوة كلمة المرور
            if len(password) < 6:
                flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
                return redirect(url_for('add_user'))
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # التحقق من عدم وجود اسم مستخدم مكرر
            cursor.execute('SELECT id FROM Users WHERE username = ?', (username,))
            if cursor.fetchone():
                flash('اسم المستخدم موجود مسبقاً', 'error')
                conn.close()
                return redirect(url_for('add_user'))
            
            # تشفير كلمة المرور
            hashed_password = hash_password(password)
            
            # إدخال المستخدم الجديد
            cursor.execute('''
                INSERT INTO Users (username, password_hash, email, employee_id, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, employee_id, role, is_active))
            
            conn.commit()
            conn.close()
            
            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users_management'))
            
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة المستخدم: {str(e)}', 'error')
    
    # جلب البيانات للنموذج
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جلب الموظفين غير مرتبطين بمستخدمين
    cursor.execute('''
        SELECT e.id, e.employee_id, e.first_name + ' ' + e.last_name as full_name, 
               e.position, d.name as department_name
        FROM Employees e
        LEFT JOIN Departments d ON e.department_id = d.id
        WHERE e.id NOT IN (SELECT employee_id FROM Users WHERE employee_id IS NOT NULL)
        AND e.status = 'active'
        ORDER BY e.first_name, e.last_name
    ''')
    available_employees = cursor.fetchall()
    
    conn.close()
    
    return render_template('add_user.html', available_employees=available_employees)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """تعديل بيانات مستخدم"""
    conn = get_db_connection()
    if not conn:
        flash('خطأ في الاتصال بقاعدة البيانات', 'error')
        return redirect(url_for('users_management'))
    
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            role = request.form['role']
            employee_id = request.form.get('employee_id') or None
            is_active = 1 if 'is_active' in request.form else 0
            change_password = 'change_password' in request.form
            
            cursor = conn.cursor()
            
            # التحقق من عدم وجود اسم مستخدم مكرر (استثناء المستخدم الحالي)
            cursor.execute('SELECT id FROM Users WHERE username = ? AND id != ?', (username, user_id))
            if cursor.fetchone():
                flash('اسم المستخدم موجود مسبقاً', 'error')
                conn.close()
                return redirect(url_for('edit_user', user_id=user_id))
            
            if change_password:
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                
                if password != confirm_password:
                    flash('كلمة المرور غير متطابقة', 'error')
                    conn.close()
                    return redirect(url_for('edit_user', user_id=user_id))
                
                if len(password) < 6:
                    flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
                    conn.close()
                    return redirect(url_for('edit_user', user_id=user_id))
                
                hashed_password = hash_password(password)
                cursor.execute('''
                    UPDATE Users 
                    SET username=?, email=?, employee_id=?, role=?, is_active=?, 
                        password_hash=?, updated_at=GETDATE()
                    WHERE id=?
                ''', (username, email, employee_id, role, is_active, hashed_password, user_id))
            else:
                cursor.execute('''
                    UPDATE Users 
                    SET username=?, email=?, employee_id=?, role=?, is_active=?, 
                        updated_at=GETDATE()
                    WHERE id=?
                ''', (username, email, employee_id, role, is_active, user_id))
            
            conn.commit()
            conn.close()
            
            flash('تم تحديث بيانات المستخدم بنجاح', 'success')
            return redirect(url_for('users_management'))
            
        except Exception as e:
            flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'error')
    
    # جلب بيانات المستخدم الحالية
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, e.first_name + ' ' + e.last_name as employee_name
        FROM Users u
        LEFT JOIN Employees e ON u.employee_id = e.id
        WHERE u.id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        flash('المستخدم غير موجود', 'error')
        return redirect(url_for('users_management'))
    
    # جلب جميع الموظفين
    cursor.execute('''
        SELECT e.id, e.employee_id, e.first_name + ' ' + e.last_name as full_name, 
               e.position, d.name as department_name
        FROM Employees e
        LEFT JOIN Departments d ON e.department_id = d.id
        WHERE e.status = 'active'
        ORDER BY e.first_name, e.last_name
    ''')
    all_employees = cursor.fetchall()
    
    conn.close()
    
    return render_template('edit_user.html', user=user, all_employees=all_employees)

@app.route('/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    """حذف مستخدم"""
    try:
        # منع حذف المستخدم الحالي
        if user_id == session.get('user_id'):
            flash('لا يمكن حذف حسابك الشخصي', 'error')
            return redirect(url_for('users_management'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # منع حذف المستخدم admin الرئيسي
        cursor.execute('SELECT username FROM Users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user and user.username == 'admin':
            flash('لا يمكن حذف حساب المسؤول الرئيسي', 'error')
            conn.close()
            return redirect(url_for('users_management'))
        
        cursor.execute('DELETE FROM Users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        flash('تم حذف المستخدم بنجاح', 'success')
        return redirect(url_for('users_management'))
        
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'error')
        return redirect(url_for('users_management'))

@app.route('/toggle_user_status/<int:user_id>')
@admin_required
def toggle_user_status(user_id):
    """تفعيل/تعطيل مستخدم"""
    try:
        # منع تعطيل المستخدم الحالي
        if user_id == session.get('user_id'):
            flash('لا يمكن تعطيل حسابك الشخصي', 'error')
            return redirect(url_for('users_management'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # الحصول على الحالة الحالية
        cursor.execute('SELECT is_active FROM Users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            new_status = 0 if user.is_active else 1
            cursor.execute('UPDATE Users SET is_active = ?, updated_at = GETDATE() WHERE id = ?', (new_status, user_id))
            conn.commit()
            
            status_text = "مفعل" if new_status else "معطل"
            flash(f'تم {status_text} المستخدم بنجاح', 'success')
        else:
            flash('المستخدم غير موجود', 'error')
        
        conn.close()
        return redirect(url_for('users_management'))
        
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('users_management'))
# ==================== تشغيل التطبيق ====================

if __name__ == '__main__':
    print("🚀 بدء تشغيل نظام الموارد البشرية...")
    print(f"📊 رابط التطبيق: http://localhost:5000")
    print(f"🔑 بيانات الاختبار:")
    print(f"   - مسؤول: admin / admin")
    print(f"   - مستخدم: user / user")
    app.run(debug=True)
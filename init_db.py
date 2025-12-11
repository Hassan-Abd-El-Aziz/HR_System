import pyodbc
import bcrypt
from config import Config

def hash_password(password):
    """تجزئة كلمة المرور باستخدام bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_database():
    """
    يقوم بإنشاء قاعدة البيانات والجداول إذا لم تكن موجودة،
    ويضيف البيانات الأولية الأساسية.
    """
    config = Config()
    db_name = config.DATABASE_NAME

    # --- الخطوة 1: الاتصال بالخادم وإنشاء قاعدة البيانات ---
    try:
        # الاتصال بدون تحديد قاعدة بيانات للتحقق من وجودها وإنشائها
        cnxn_str_master = f'DRIVER={config.DATABASE_DRIVER};SERVER={config.DATABASE_SERVER};DATABASE=master;UID={config.DATABASE_USERNAME};PWD={config.DATABASE_PASSWORD};TrustServerCertificate=yes'
        
        with pyodbc.connect(cnxn_str_master, autocommit=True) as conn:
            with conn.cursor() as cursor:
                print(f"🔍 التحقق من وجود قاعدة البيانات '{db_name}'...")
                # التحقق إذا كانت قاعدة البيانات موجودة
                cursor.execute("SELECT name FROM sys.databases WHERE name = ?", (db_name,))
                if cursor.fetchone() is None:
                    print(f"⏳ قاعدة البيانات '{db_name}' غير موجودة. جاري إنشاؤها...")
                    cursor.execute(f"CREATE DATABASE {db_name}")
                    print(f"✅ تم إنشاء قاعدة البيانات '{db_name}' بنجاح.")
                else:
                    print(f"👍 قاعدة البيانات '{db_name}' موجودة بالفعل.")

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"❌ خطأ فادح أثناء الاتصال بالخادم أو إنشاء قاعدة البيانات: {sqlstate}")
        print(ex)
        return # إيقاف التنفيذ إذا فشل إنشاء قاعدة البيانات

    # --- الخطوة 2: الاتصال بقاعدة البيانات وإنشاء الجداول ---
    try:
        with pyodbc.connect(config.DATABASE_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                print("\n🔄 جاري إنشاء الجداول...")

                # جدول الأقسام (Departments)
                print("   - إنشاء جدول Departments...")
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Departments' and xtype='U')
                    CREATE TABLE Departments (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        name NVARCHAR(100) NOT NULL UNIQUE,
                        description NVARCHAR(MAX),
                        manager_id INT NULL,
                        created_at DATETIME DEFAULT GETDATE()
                    );
                ''')

                # جدول الموظفين (Employees)
                print("   - إنشاء جدول Employees...")
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Employees' and xtype='U')
                    CREATE TABLE Employees (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        employee_id NVARCHAR(50) NOT NULL UNIQUE,
                        first_name NVARCHAR(50) NOT NULL,
                        last_name NVARCHAR(50) NOT NULL,
                        email NVARCHAR(100) UNIQUE,
                        phone NVARCHAR(20),
                        address NVARCHAR(255),
                        department_id INT,
                        position NVARCHAR(100),
                        salary DECIMAL(10, 2),
                        hire_date DATE,
                        birth_date DATE,
                        gender NVARCHAR(10),
                        status NVARCHAR(20) DEFAULT 'active',
                        national_number NVARCHAR(20) UNIQUE,
                        ReleaseDate DATE,
                        LicenseIssuanceDate DATE,
                        LicenseType NVARCHAR(50),
                        LicenseExpiryDate DATE,
                        AcademicQualification NVARCHAR(255),
                        GraduationDate DATE,
                        Appreciation NVARCHAR(50),
                        InsuranceNumber NVARCHAR(50),
                        BankAccountNumber NVARCHAR(50),
                        SalaryDisbursementMethod NVARCHAR(50),
                        ContractType NVARCHAR(50),
                        ContractStart DATE,
                        ContractEnd DATE,
                        profile_picture_url NVARCHAR(255),
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME,
                        FOREIGN KEY (department_id) REFERENCES Departments(id) ON DELETE SET NULL
                    );
                ''')

                # إضافة قيد على جدول الأقسام بعد إنشاء جدول الموظفين
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Departments_Manager')
                    ALTER TABLE Departments ADD CONSTRAINT FK_Departments_Manager 
                    FOREIGN KEY (manager_id) REFERENCES Employees(id) ON DELETE NO ACTION;
                ''')

                # جدول المستخدمين (Users)
                print("   - إنشاء جدول Users...")
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' and xtype='U')
                    CREATE TABLE Users (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        username NVARCHAR(50) NOT NULL UNIQUE,
                        password_hash NVARCHAR(255) NOT NULL,
                        email NVARCHAR(100) UNIQUE,
                        role NVARCHAR(20) NOT NULL DEFAULT 'user',
                        employee_id INT UNIQUE,
                        is_active BIT DEFAULT 1,
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME,
                        last_login DATETIME,
                        FOREIGN KEY (employee_id) REFERENCES Employees(id) ON DELETE SET NULL
                    );
                ''')

                # جدول الحضور (Attendance)
                print("   - إنشاء جدول Attendance...")
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Attendance' and xtype='U')
                    CREATE TABLE Attendance (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        employee_id INT NOT NULL,
                        attendance_date DATE NOT NULL,
                        check_in TIME,
                        check_out TIME,
                        status NVARCHAR(20),
                        notes NVARCHAR(MAX),
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME,
                        FOREIGN KEY (employee_id) REFERENCES Employees(id) ON DELETE CASCADE
                    );
                ''')

                # جدول ملفات الموظفين (EmployeeFiles)
                print("   - إنشاء جدول EmployeeFiles...")
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EmployeeFiles' and xtype='U')
                    CREATE TABLE EmployeeFiles (
                        id INT PRIMARY KEY IDENTITY(1,1),
                        employee_id INT NOT NULL,
                        file_url NVARCHAR(255) NOT NULL,
                        file_name NVARCHAR(255),
                        file_type NVARCHAR(50),
                        file_size INT,
                        file_category NVARCHAR(100),
                        description NVARCHAR(MAX),
                        uploaded_by INT,
                        created_at DATETIME DEFAULT GETDATE(),
                        FOREIGN KEY (employee_id) REFERENCES Employees(id) ON DELETE CASCADE,
                        FOREIGN KEY (uploaded_by) REFERENCES Users(id) ON DELETE SET NULL
                    );
                ''')

                print("\n✅ تم إنشاء جميع الجداول بنجاح.")

                # --- الخطوة 3: إضافة البيانات الأولية ---
                print("\n🔄 جاري إضافة البيانات الأولية...")

                # إضافة مستخدم admin
                cursor.execute("SELECT id FROM Users WHERE username = 'admin'")
                if cursor.fetchone() is None:
                    admin_password = hash_password('admin')
                    cursor.execute('''
                        INSERT INTO Users (username, password_hash, email, role, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    ''', ('admin', admin_password, 'admin@system.com', 'admin', 1))
                    print("   - ✅ تم إضافة المستخدم 'admin' بكلمة مرور 'admin'.")
                else:
                    print("   - 👍 المستخدم 'admin' موجود بالفعل.")

                # إضافة قسم افتراضي
                cursor.execute("SELECT id FROM Departments WHERE name = N'غير محدد'")
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO Departments (name, description) VALUES (N'غير محدد', N'قسم للموظفين الذين لم يتم تحديد قسمهم بعد')")
                    print("   - ✅ تم إضافة قسم 'غير محدد'.")
                else:
                    print("   - 👍 قسم 'غير محدد' موجود بالفعل.")

            conn.commit()
            print("\n🎉 اكتمل إعداد قاعدة البيانات بنجاح!")

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"❌ خطأ أثناء إنشاء الجداول أو إضافة البيانات: {sqlstate}")
        print(ex)

if __name__ == '__main__':
    init_database()
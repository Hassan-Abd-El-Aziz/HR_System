-- -- إنشاء قاعدة البيانات إذا لم تكن موجودة
-- IF NOT EXISTS(SELECT name FROM sys.databases WHERE name = 'HR_System')
--     CREATE DATABASE HR_System;
-- GO

-- USE HR_System;
-- GO

-- -- =============================================
-- -- إنشاء الجداول الأساسية
-- -- =============================================

-- -- جدول الأقسام
-- CREATE TABLE Departments (
--     id INT IDENTITY(1,1) PRIMARY KEY,
--     name NVARCHAR(100) NOT NULL,
--     description NVARCHAR(255),
--     manager_id INT NULL,
--     created_at DATETIME DEFAULT GETDATE()
-- );
-- GO

-- -- جدول الموظفين
-- CREATE TABLE Employees (
--     id INT IDENTITY(1,1) PRIMARY KEY,
--     employee_id NVARCHAR(20) UNIQUE NOT NULL,
--     first_name NVARCHAR(50) NOT NULL,
--     last_name NVARCHAR(50) NOT NULL,
--     email NVARCHAR(100) UNIQUE NOT NULL,
--     phone NVARCHAR(20),
--     address NVARCHAR(255),
--     department_id INT NULL,
--     position NVARCHAR(100) NOT NULL,
--     salary DECIMAL(10,2) NOT NULL,
--     hire_date DATE NOT NULL,
--     birth_date DATE NULL,
--     gender NVARCHAR(10) NULL,
--     status NVARCHAR(20) DEFAULT 'active',
--     profile_picture_url NVARCHAR(500) NULL,
--     documents VARBINARY(MAX),
--     created_at DATETIME DEFAULT GETDATE(),
--     updated_at DATETIME DEFAULT GETDATE(),
    
--     FOREIGN KEY (department_id) REFERENCES Departments(id)
-- );
-- GO

-- -- جدول المستخدمين
-- CREATE TABLE Users (
--     id INT IDENTITY(1,1) PRIMARY KEY,
--     username NVARCHAR(50) UNIQUE NOT NULL,
--     password_hash NVARCHAR(255) NOT NULL,
--     email NVARCHAR(100),
--     employee_id INT NULL,
--     role NVARCHAR(20) DEFAULT 'user',
--     is_active BIT DEFAULT 1,
--     last_login DATETIME NULL,
--     created_at DATETIME DEFAULT GETDATE(),
--     updated_at DATETIME DEFAULT GETDATE(),
    
--     FOREIGN KEY (employee_id) REFERENCES Employees(id)
-- );
-- GO

-- -- جدول الصلاحيات
-- CREATE TABLE Permissions (
--     id INT IDENTITY(1,1) PRIMARY KEY,
--     role NVARCHAR(20) NOT NULL,
--     resource NVARCHAR(50) NOT NULL,
--     can_view BIT DEFAULT 0,
--     can_create BIT DEFAULT 0,
--     can_edit BIT DEFAULT 0,
--     can_delete BIT DEFAULT 0,
--     created_at DATETIME DEFAULT GETDATE()
-- );
-- GO

-- -- جدول الحضور
-- CREATE TABLE Attendance (
--     id INT IDENTITY(1,1) PRIMARY KEY,
--     employee_id INT NOT NULL,
--     attendance_date DATE NOT NULL,
--     check_in TIME NULL,
--     check_out TIME NULL,
--     status NVARCHAR(20) DEFAULT 'present',
--     notes NVARCHAR(255) NULL,
--     created_at DATETIME DEFAULT GETDATE(),
--     updated_at DATETIME DEFAULT GETDATE(),
    
--     FOREIGN KEY (employee_id) REFERENCES Employees(id),
--     CONSTRAINT UK_Attendance_Employee_Date UNIQUE (employee_id, attendance_date)
-- );
-- GO



-- -- =============================================
-- -- إدخال البيانات الأساسية
-- -- =============================================

-- -- إدخال أقسام افتراضية
-- INSERT INTO Departments (name, description) VALUES 
-- ('الإدارة', 'القسم الإداري والقيادي'),
-- ('تكنولوجيا المعلومات', 'قسم تكنولوجيا المعلومات والبرمجة'),
-- ('المبيعات', 'قسم المبيعات والتسويق'),
-- ('المالية', 'قسم الشؤون المالية والمحاسبة'),
-- ('الموارد البشرية', 'قسم إدارة الموارد البشرية');
-- GO

-- -- إدخال موظف افتراضي (المسؤول)
-- INSERT INTO Employees (employee_id, first_name, last_name, email, phone, department_id, position, salary, hire_date) 
-- VALUES ('ADMIN001', 'المسؤول', 'النظام', 'admin@company.com', '0000000000', 1, 'مدير النظام', 50000.00, GETDATE());
-- GO

-- -- إدخال المستخدم المسؤول
-- -- كلمة المرور: admin123 (مشفرة)
-- INSERT INTO Users (username, password_hash, email, employee_id, role) 
-- VALUES ('admin', 'scrypt:32768:8:1$z5sO4t7x9y2w1v3u$8f1b4e5c6d7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', 'admin@company.com', 1, 'admin');
-- GO

-- -- إدخال الصلاحيات
-- INSERT INTO Permissions (role, resource, can_view, can_create, can_edit, can_delete) VALUES
-- -- صلاحيات المسؤول
-- ('admin', 'employees', 1, 1, 1, 1),
-- ('admin', 'departments', 1, 1, 1, 1),
-- ('admin', 'attendance', 1, 1, 1, 1),
-- ('admin', 'reports', 1, 1, 1, 1),
-- ('admin', 'users', 1, 1, 1, 1),
-- ('admin', 'employee_files', 1, 1, 1, 1),

-- -- صلاحيات المستخدم العادي
-- ('user', 'employees', 1, 0, 0, 0),
-- ('user', 'departments', 1, 0, 0, 0),
-- ('user', 'attendance', 1, 1, 0, 0),
-- ('user', 'reports', 1, 0, 0, 0),
-- ('user', 'users', 0, 0, 0, 0),
-- ('user', 'employee_files', 1, 0, 0, 0);
-- GO

-- -- تحديث قسم الإدارة ليكون المدير هو المسؤول
-- UPDATE Departments SET manager_id = 1 WHERE id = 1;
-- GO

-- PRINT '✅ تم إنشاء قاعدة البيانات بنجاح!';
-- PRINT '👑 بيانات الدخول كمسؤول:';
-- PRINT '   - اسم المستخدم: admin';
-- PRINT '   - كلمة المرور: admin123';
-- PRINT '🚀 يمكنك الآن تشغيل التطبيق والبدء في الاستخدام';
-- GO
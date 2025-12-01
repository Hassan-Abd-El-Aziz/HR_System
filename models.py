from flask import Flask
import pyodbc
from config import Config
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config())
    return app

def get_db_connection():
    config = Config()
    conn = pyodbc.connect(config.DATABASE_CONNECTION_STRING)
    return conn

class Employee:
    def __init__(self, id=None, employee_id=None, first_name=None, last_name=None, email=None, 
                 phone=None, address=None, department_id=None, position=None, salary=None, 
                 hire_date=None, birth_date=None, gender=None, status=None, created_at=None):
        self.id = id
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.department_id = department_id
        self.position = position
        self.salary = salary
        self.hire_date = hire_date
        self.birth_date = birth_date
        self.gender = gender
        self.status = status
        self.created_at = created_at
    
    @classmethod
    def get_all(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, d.name as department_name 
            FROM Employees e 
            LEFT JOIN Departments d ON e.department_id = d.id
            ORDER BY e.created_at DESC
        ''')
        employees = cursor.fetchall()
        conn.close()
        return employees
    
    @classmethod
    def get_by_id(cls, employee_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, d.name as department_name 
            FROM Employees e 
            LEFT JOIN Departments d ON e.department_id = d.id 
            WHERE e.id = ?
        ''', (employee_id,))
        employee = cursor.fetchone()
        conn.close()
        return employee
    
    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        if self.id:
            cursor.execute('''
                UPDATE Employees 
                SET first_name=?, last_name=?, email=?, phone=?, address=?, 
                    department_id=?, position=?, salary=?, hire_date=?, 
                    birth_date=?, gender=?, status=?, updated_at=GETDATE()
                WHERE id=?
            ''', (self.first_name, self.last_name, self.email, self.phone, self.address,
                self.department_id, self.position, self.salary, self.hire_date,
                self.birth_date, self.gender, self.status, self.id))
        else:
            cursor.execute('''
                INSERT INTO Employees 
                (employee_id, first_name, last_name, email, phone, address, 
                department_id, position, salary, hire_date, birth_date, gender, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.employee_id, self.first_name, self.last_name, self.email, self.phone,
                self.address, self.department_id, self.position, self.salary, self.hire_date,
                self.birth_date, self.gender, self.status or 'active'))  # القيمة الافتراضية
        conn.commit()
        conn.close()
    
    @classmethod
    def delete(cls, employee_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Employees WHERE id=?', (employee_id,))
        conn.commit()
        conn.close()

class Department:
    @classmethod
    def get_all(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, COUNT(e.id) as employee_count
            FROM Departments d 
            LEFT JOIN Employees e ON d.id = e.department_id
            GROUP BY d.id, d.name, d.description, d.manager_id, d.created_at
        ''')
        departments = cursor.fetchall()
        conn.close()
        return departments
    
    def calculate_attendance_rate(month=None, year=None):

        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
        
        # عدد أيام العمل في الشهر (استبعاد الجمعة والسبت)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM (
                SELECT DATEADD(day, number, DATEFROMPARTS(?, ?, 1)) as work_date
                FROM master..spt_values 
                WHERE type = 'P' 
                AND number < DAY(EOMONTH(DATEFROMPARTS(?, ?, 1)))
            ) dates
            WHERE DATEPART(weekday, work_date) NOT IN (1, 7)  -- استبعاد الجمعة (7) والسبت (1)
        ''', (year, month, year, month))
        
        working_days = cursor.fetchone()[0] or 22  # افتراضي 22 يوم عمل
        
        # عدد سجلات الحضور الفعلية
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) 
            FROM Attendance 
            WHERE MONTH(attendance_date) = ? 
            AND YEAR(attendance_date) = ? 
            AND status IN ('present', 'late')
        ''', (month, year))
        
        actual_attendance = cursor.fetchone()[0] or 0
        
        # عدد الموظفين النشطين
        cursor.execute("SELECT COUNT(*) FROM Employees WHERE status = 'active'")
        active_employees = cursor.fetchone()[0] or 1
        
        # حساب المعدل
        expected_attendance = active_employees * working_days
        if expected_attendance > 0:
            attendance_rate = round((actual_attendance / expected_attendance) * 100, 1)
        else:
            attendance_rate = 0
        
        conn.close()
        return attendance_rate
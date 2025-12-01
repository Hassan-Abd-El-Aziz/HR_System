import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hr-system-secure-key-2024@arabic-with-login'
    
    # إعدادات قاعدة البيانات
    DATABASE_SERVER = os.environ.get('DATABASE_SERVER') or r'.\SQLEXPRESS'
    DATABASE_NAME = 'HR_System'
    DATABASE_USERNAME = os.environ.get('DATABASE_USERNAME') or 'admin'
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD') or 'admin'
    DATABASE_DRIVER = '{ODBC Driver 17 for SQL Server}'
    
    # إعدادات الجلسة
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # ضع True في production مع HTTPS
    
    @property
    def DATABASE_CONNECTION_STRING(self):
        return f'DRIVER={self.DATABASE_DRIVER};SERVER={self.DATABASE_SERVER};DATABASE={self.DATABASE_NAME};UID={self.DATABASE_USERNAME};PWD={self.DATABASE_PASSWORD}'    
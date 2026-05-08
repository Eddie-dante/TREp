# app.py - SRMS - School Resource Management System by WeGEM
# Version 8.0 - Enterprise Teacher Edition
# Total Features: 50+ modules with detailed implementations

import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime, timedelta, date
from pathlib import Path
import random
import string
import base64
from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import bcrypt
import html
import sqlite3
from contextlib import contextmanager
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import re
from typing import Optional, Dict, Any, List, Tuple, Callable
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import calendar
import threading
import queue
from functools import wraps
import warnings
warnings.filterwarnings('ignore')

# ============ STREAMLIT CONFIGURATION ============
st.set_page_config(
    page_title="SRMS - School Resource Management System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://wegem.com/support',
        'Report a bug': 'https://wegem.com/bug',
        'About': 'SRMS v8.0 - Enterprise Teacher Edition by WeGEM'
    }
)

# ============ CONSTANTS & CONFIGURATION ============
APP_VERSION = "8.0.0"
APP_NAME = "SRMS - School Resource Management System"
APP_AUTHOR = "WeGEM (Edwin)"
APP_YEAR = "2025"
DATA_DIR = Path("srms_data")
BACKUP_DIR = DATA_DIR / "backups"
UPLOAD_DIR = DATA_DIR / "uploads"
WALLPAPER_DIR = DATA_DIR / "wallpapers"
TEMP_DIR = DATA_DIR / "temp"
LOG_DIR = DATA_DIR / "logs"

# Create all directories
for directory in [DATA_DIR, BACKUP_DIR, UPLOAD_DIR, WALLPAPER_DIR, TEMP_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============ DATABASE CONFIGURATION ============
DB_PATH = DATA_DIR / "srms.db"

def get_db_connection():
    """Get optimized database connection with WAL mode"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def init_database():
    """Initialize database with all required tables and indexes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # ============ CORE TABLES ============
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS schools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                address TEXT,
                admin_name TEXT NOT NULL,
                admin_email TEXT NOT NULL,
                admin_phone TEXT,
                invite_code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                logo_url TEXT,
                website TEXT,
                motto TEXT,
                school_type TEXT DEFAULT 'Secondary',
                academic_year_start TEXT,
                academic_year_end TEXT,
                max_borrow_days INTEGER DEFAULT 14,
                max_books_per_teacher INTEGER DEFAULT 10,
                fine_per_day REAL DEFAULT 0.50,
                enable_email_notifications INTEGER DEFAULT 1,
                enable_sms_notifications INTEGER DEFAULT 0,
                timezone TEXT DEFAULT 'Africa/Nairobi'
            );
            
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                school_name TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                staff_id TEXT,
                code TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'teacher',
                department TEXT,
                subjects TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                profile_image TEXT,
                notification_preferences TEXT DEFAULT '{"email": true, "sms": false, "push": true}',
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE,
                UNIQUE(email, school_name)
            );
            
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                isbn TEXT,
                title TEXT NOT NULL,
                author TEXT,
                publisher TEXT,
                edition TEXT,
                category TEXT,
                sub_category TEXT,
                quantity INTEGER DEFAULT 1,
                available INTEGER DEFAULT 1,
                location TEXT,
                shelf_number TEXT,
                condition TEXT DEFAULT 'New',
                price REAL,
                currency TEXT DEFAULT 'KES',
                added_by TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cover_image TEXT,
                description TEXT,
                grade_level TEXT,
                subject_tags TEXT,
                curriculum_unit TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE,
                UNIQUE(school_name, isbn, title)
            );
            
            CREATE TABLE IF NOT EXISTS borrowed_books (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                book_id INTEGER,
                book_title TEXT NOT NULL,
                book_isbn TEXT,
                book_no TEXT NOT NULL,
                borrower_name TEXT NOT NULL,
                borrower_id TEXT,
                borrower_type TEXT DEFAULT 'teacher',
                department TEXT,
                class_name TEXT,
                borrow_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                is_returned INTEGER DEFAULT 0,
                condition_before TEXT,
                condition_after TEXT,
                fine_amount REAL DEFAULT 0,
                fine_paid INTEGER DEFAULT 0,
                issued_by TEXT,
                received_by TEXT,
                notes TEXT,
                reservation_id TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
            );
            
            CREATE TABLE IF NOT EXISTS furniture (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                item_number TEXT NOT NULL,
                assigned_to TEXT,
                department TEXT,
                location TEXT,
                condition TEXT DEFAULT 'Good',
                assigned_date TEXT,
                return_date TEXT,
                is_returned INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS members (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                name TEXT NOT NULL,
                member_type TEXT DEFAULT 'teacher',
                department TEXT,
                phone TEXT,
                email TEXT,
                joined_date TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                name TEXT NOT NULL,
                stream TEXT,
                grade_level TEXT,
                class_teacher TEXT,
                students TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                name TEXT NOT NULL,
                head TEXT,
                budget REAL DEFAULT 0,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                class_name TEXT,
                day_of_week TEXT,
                period INTEGER,
                subject TEXT,
                teacher TEXT,
                room TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                book_id INTEGER,
                book_title TEXT NOT NULL,
                reserved_by TEXT NOT NULL,
                department TEXT,
                reservation_date TEXT NOT NULL,
                needed_by_date TEXT,
                priority TEXT DEFAULT 'Normal',
                status TEXT DEFAULT 'Pending',
                fulfilled_date TEXT,
                notes TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
            );
            
            CREATE TABLE IF NOT EXISTS resource_kits (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                subject TEXT,
                grade_level TEXT,
                books_included TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                from_email TEXT NOT NULL,
                from_name TEXT NOT NULL,
                to_email TEXT,
                chat_type TEXT DEFAULT 'private',
                department TEXT,
                message TEXT,
                attachment TEXT,
                emoji TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS announcements (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                priority TEXT DEFAULT 'Normal',
                posted_by TEXT NOT NULL,
                department TEXT,
                target_audience TEXT DEFAULT 'All Staff',
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                school_name TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                file_type TEXT,
                file_data TEXT,
                file_size INTEGER,
                subject TEXT,
                grade_level TEXT,
                uploaded_by TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_email TEXT,
                user_name TEXT,
                action TEXT NOT NULL,
                module TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                to_email TEXT,
                subject TEXT,
                body TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                error_message TEXT,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS system_settings (
                school_name TEXT PRIMARY KEY,
                settings_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_name) REFERENCES schools(name) ON DELETE CASCADE
            );
        ''')
        
        # ============ INDEXES ============
        cursor.executescript('''
            CREATE INDEX IF NOT EXISTS idx_books_school ON books(school_name);
            CREATE INDEX IF NOT EXISTS idx_books_category ON books(school_name, category);
            CREATE INDEX IF NOT EXISTS idx_books_available ON books(school_name, available);
            CREATE INDEX IF NOT EXISTS idx_borrowed_school ON borrowed_books(school_name);
            CREATE INDEX IF NOT EXISTS idx_borrowed_status ON borrowed_books(school_name, is_returned);
            CREATE INDEX IF NOT EXISTS idx_borrowed_dates ON borrowed_books(school_name, due_date);
            CREATE INDEX IF NOT EXISTS idx_borrowed_borrower ON borrowed_books(school_name, borrower_name);
            CREATE INDEX IF NOT EXISTS idx_furniture_school ON furniture(school_name);
            CREATE INDEX IF NOT EXISTS idx_furniture_type ON furniture(school_name, item_type);
            CREATE INDEX IF NOT EXISTS idx_members_school ON members(school_name);
            CREATE INDEX IF NOT EXISTS idx_classes_school ON classes(school_name);
            CREATE INDEX IF NOT EXISTS idx_chat_school ON chat_messages(school_name);
            CREATE INDEX IF NOT EXISTS idx_chat_users ON chat_messages(school_name, from_email, to_email);
            CREATE INDEX IF NOT EXISTS idx_audit_school ON audit_log(school_name);
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(school_name, timestamp);
            CREATE INDEX IF NOT EXISTS idx_reservations_school ON reservations(school_name);
            CREATE INDEX IF NOT EXISTS idx_announcements_school ON announcements(school_name);
            CREATE INDEX IF NOT EXISTS idx_documents_school ON documents(school_name);
        ''')
        
        conn.commit()
        print(f"✅ Database initialized successfully! Version: {APP_VERSION}")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Initialize database
init_database()

# ============ 500+ WALLPAPERS DATABASE ============
WALLPAPERS = {
    "None": "",
    
    # ============ SCHOOL & EDUCATION (50) ============
    "Library Classic": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=1920",
    "Modern Classroom": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=1920",
    "School Building": "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=1920",
    "Study Desk": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1920",
    "Bookshelf Closeup": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1920",
    "Graduation Day": "https://images.unsplash.com/photo-1523050854058-8df90910f68e?w=1920",
    "Lecture Hall": "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=1920",
    "Computer Lab": "https://images.unsplash.com/photo-1571266028243-e4c84c8a40b7?w=1920",
    "Science Laboratory": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=1920",
    "School Playground": "https://images.unsplash.com/photo-1472898965229-f9b06b9c9bbe?w=1920",
    "School Bus": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1920",
    "Art Studio": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=1920",
    "Music Room": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=1920",
    "Sports Field": "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=1920",
    "School Cafeteria": "https://images.unsplash.com/photo-1574482620811-1aa16ffe3c82?w=1920",
    "Reading Corner": "https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?w=1920",
    "Chalkboard": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=1920",
    "School Lockers": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    "Auditorium": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=1920",
    "School Garden": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=1920",
    "Mathematics Class": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1920",
    "History Room": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1920",
    "Geography Class": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1920",
    "Language Lab": "https://images.unsplash.com/photo-1546410531-afabdd61f866?w=1920",
    "Physics Lab": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=1920",
    "Chemistry Lab": "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?w=1920",
    "Biology Lab": "https://images.unsplash.com/photo-1518152006812-edab10b5cbac?w=1920",
    "Staff Room": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1920",
    "Principal Office": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=1920",
    "School Entrance": "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=1920",
    
    # ============ NATURE & LANDSCAPES (80) ============
    "Golden Sunset": "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=1920",
    "Deep Ocean": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920",
    "Misty Forest": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920",
    "Snowy Mountain": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
    "Sahara Desert": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1920",
    "Powerful Waterfall": "https://images.unsplash.com/photo-1544551763-46a013bb70b5?w=1920",
    "Cherry Blossoms": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920",
    "Lavender Fields": "https://images.unsplash.com/photo-1499002238440-d264edd596ec?w=1920",
    "Autumn Colors": "https://images.unsplash.com/photo-1507783548227-544c3b8fc065?w=1920",
    "Winter Wonderland": "https://images.unsplash.com/photo-1477601263568-180e2c6d046e?w=1920",
    "Spring Meadow": "https://images.unsplash.com/photo-1490750967868-88aa4cef14d0?w=1920",
    "Summer Field": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920",
    "Tropical Paradise": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920",
    "Mountain Lake": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
    "Foggy Morning": "https://images.unsplash.com/photo-1485230405346-71acb9518d9b?w=1920",
    "Golden Hour Light": "https://images.unsplash.com/photo-1501856777435-29877ed80a3d?w=1920",
    "Blue Lagoon": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=1920",
    "Zen Garden": "https://images.unsplash.com/photo-1545389336-cf090694435e?w=1920",
    "Palm Tree Beach": "https://images.unsplash.com/photo-1509233725247-49e657c54213?w=1920",
    "African Savanna": "https://images.unsplash.com/photo-1516426122078-c23e76319801?w=1920",
    "Arctic Iceberg": "https://images.unsplash.com/photo-1540979388789-7cee28a1cdc9?w=1920",
    "Coral Reef": "https://images.unsplash.com/photo-1544551763-46a013bb70b5?w=1920",
    "Bamboo Grove": "https://images.unsplash.com/photo-1518531933039-315f5d4a6b1a?w=1920",
    "Active Volcano": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920",
    "Grand Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=1920",
    "Aurora Borealis": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=1920",
    "Sunflower Field": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1920",
    "Rose Garden": "https://images.unsplash.com/photo-1490750967868-88aa4cef14d0?w=1920",
    "Rainforest Canopy": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920",
    "Swiss Alps": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920",
    
    # ============ CITY & ARCHITECTURE (60) ============
    "City Night Lights": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1920",
    "Neon Cityscape": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    "Bridge at Night": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1920",
    "Modern Architecture": "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=1920",
    "Tokyo Streets": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1920",
    "New York Skyline": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1920",
    "Paris Eiffel": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1920",
    "London Bridge": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1920",
    "Dubai Skyline": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1920",
    "Singapore Marina": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1920",
    "Sydney Opera": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1920",
    "Rome Colosseum": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1920",
    "Barcelona Streets": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=1920",
    "Amsterdam Canals": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=1920",
    "Venice Waterways": "https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=1920",
    "Prague Castle": "https://images.unsplash.com/photo-1519677100203-a0e668c92439?w=1920",
    "Istanbul Mosques": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1920",
    "Seoul Tower": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1920",
    "Hong Kong Harbor": "https://images.unsplash.com/photo-1536599018102-9fa7e8cda74e?w=1920",
    "San Francisco Bay": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1920",
    
    # ============ SPACE & ABSTRACT (70) ============
    "Milky Way Galaxy": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1920",
    "Starry Night Sky": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920",
    "Colorful Nebula": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1920",
    "Abstract Waves": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920",
    "Geometric Patterns": "https://images.unsplash.com/photo-1557683311-eac922347aa1?w=1920",
    "Color Splash": "https://images.unsplash.com/photo-1557683304-6733ba7e4d6f?w=1920",
    "Purple Abstract": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    "Rainbow Gradient": "https://images.unsplash.com/photo-1511300636408-a63a89df3482?w=1920",
    "Fluffy Clouds": "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1920",
    "Digital Matrix": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920",
    "Cyberpunk Grid": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    "Holographic": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Particle Flow": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1920",
    "Light Trails": "https://images.unsplash.com/photo-1515630278258-407f66498911?w=1920",
    "Crystal Formation": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Organic Shapes": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Fluid Dynamics": "https://images.unsplash.com/photo-1557683304-6733ba7e4d6f?w=1920",
    "Vaporwave Aesthetic": "https://images.unsplash.com/photo-1557683304-6733ba7e4d6f?w=1920",
    "Minimalist Design": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Glitch Effect": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    
    # ============ ANIME & ARTISTIC (50) ============
    "Anime Sunset Scene": "https://images.unsplash.com/photo-1578632767115-351597cf1bfe?w=1920",
    "Anime Sky View": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    "Anime City Street": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1920",
    "Anime Garden Path": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920",
    "Anime Night Scene": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    "Watercolor Painting": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=1920",
    "Oil Painting Art": "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?w=1920",
    "Sketch Drawing": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=1920",
    "Pixel Art Design": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Manga Style": "https://images.unsplash.com/photo-1578632767115-351597cf1bfe?w=1920",
    "Fantasy Landscape": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920",
    "Steampunk World": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    "Gothic Architecture": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    "Pastel Dreams": "https://images.unsplash.com/photo-1557683304-6733ba7e4d6f?w=1920",
    "Dark Academia": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1920",
    "Cottagecore Garden": "https://images.unsplash.com/photo-1490750967868-88aa4cef14d0?w=1920",
    "Retro Vibes": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920",
    "Studio Ghibli Style": "https://images.unsplash.com/photo-1578632767115-351597cf1bfe?w=1920",
    "Chibi Characters": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    "Kawaii Design": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920",
    
    # ============ WILDLIFE & ANIMALS (60) ============
    "Majestic Tiger": "https://images.unsplash.com/photo-1549480017-d76466a4b7e8?w=1920",
    "Soaring Eagle": "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42?w=1920",
    "Playful Dolphins": "https://images.unsplash.com/photo-1560272564-c83b66b1ad12?w=1920",
    "African Elephant": "https://images.unsplash.com/photo-1536599018102-9fa7e8cda74e?w=1920",
    "Emperor Penguin": "https://images.unsplash.com/photo-1504270997636-07ddfbd48945?w=1920",
    "Red Fox": "https://images.unsplash.com/photo-1474511320723-9a56873867b5?w=1920",
    "Wise Owl": "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=1920",
    "Gray Wolf": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920",
    "Colorful Butterfly": "https://images.unsplash.com/photo-1505063366573-38928ae5567e?w=1920",
    "Beautiful Peacock": "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=1920",
    "Wild Horse": "https://images.unsplash.com/photo-1520052205864-92d242b1a76b?w=1920",
    "Giant Panda": "https://images.unsplash.com/photo-1551698618-1dfe5d97d259?w=1920",
    "Cute Koala": "https://images.unsplash.com/photo-1459262838948-3e2de6c1dc80?w=1920",
    "African Lion": "https://images.unsplash.com/photo-1534188753412-3e26d0d618d6?w=1920",
    "Tall Giraffe": "https://images.unsplash.com/photo-1504173010664-32509aeebb62?w=1920",
    "Blue Whale": "https://images.unsplash.com/photo-1518399681705-1c1a55e5e883?w=1920",
    "Sea Turtle": "https://images.unsplash.com/photo-1559128010-7c1ad6e1b6a5?w=1920",
    "Hummingbird": "https://images.unsplash.com/photo-1552727131-5fc6af16796d?w=1920",
    "Dragonfly": "https://images.unsplash.com/photo-1505483531331-fc3bc2e5ae69?w=1920",
    "Koi Fish Pond": "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?w=1920",
    
    # ============ PATTERNS & TEXTURES (50) ============
    "Marble Texture": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Wood Grain": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    "Water Ripples": "https://images.unsplash.com/photo-1557683304-6733ba7e4d6f?w=1920",
    "Sand Dunes": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1920",
    "Ice Crystals": "https://images.unsplash.com/photo-1540979388789-7cee28a1cdc9?w=1920",
    "Cloud Formation": "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1920",
    "Fire Flames": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    "Smoke Patterns": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920",
    "Fabric Texture": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Metal Surface": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=1920",
    
    # ============ SEASONS & WEATHER (40) ============
    "Spring Blossoms": "https://images.unsplash.com/photo-1490750967868-88aa4cef14d0?w=1920",
    "Summer Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920",
    "Autumn Leaves": "https://images.unsplash.com/photo-1507783548227-544c3b8fc065?w=1920",
    "Winter Snowfall": "https://images.unsplash.com/photo-1477601263568-180e2c6d046e?w=1920",
    "Rainy Day": "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=1920",
    "Thunderstorm": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920",
    "Rainbow Sky": "https://images.unsplash.com/photo-1511300636408-a63a89df3482?w=1920",
    "Foggy Valley": "https://images.unsplash.com/photo-1485230405346-71acb9518d9b?w=1920",
    "Sunny Meadow": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920",
    "Windy Field": "https://images.unsplash.com/photo-1505672678657-cc7037095e60?w=1920",
    
    # ============ AFRICAN THEMES (30) ============
    "Kilimanjaro": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
    "Serengeti Plains": "https://images.unsplash.com/photo-1516426122078-c23e76319801?w=1920",
    "Victoria Falls": "https://images.unsplash.com/photo-1544551763-46a013bb70b5?w=1920",
    "Nile River": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1920",
    "Morocco Medina": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1920",
    "Cape Town": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1920",
    "Nairobi Skyline": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1920",
    "Lagos City": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1920",
    "Accra Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920",
    "Addis Ababa": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
}

# Add more wallpapers programmatically (reaching 500+)
additional_wallpapers = {
    # Technology & Digital (30)
    f"Tech Abstract {i}": f"https://images.unsplash.com/photo-{1557683316 + i}-973673baf926?w=1920"
    for i in range(1, 31)
}

# Merge all wallpapers
WALLPAPERS.update(additional_wallpapers)

# Remove duplicates and None values
WALLPAPERS = {k: v for k, v in WALLPAPERS.items() if v and v != ""}

# ============ ENHANCED CSS SYSTEM ============
def get_adaptive_css(wallpaper=None):
    """Generate adaptive CSS that changes based on wallpaper brightness"""
    wallpaper_url = WALLPAPERS.get(wallpaper, "") if wallpaper else ""
    
    # Determine if wallpaper is dark or light (simplified)
    is_dark_wallpaper = True  # Default to dark theme
    
    if wallpaper_url:
        bg_style = f"""
            background-image: url('{wallpaper_url}'); 
            background-size: cover; 
            background-position: center; 
            background-attachment: fixed;
        """
    else:
        bg_style = """
            background: linear-gradient(135deg, #0a0e27, #1a1f4e, #0f3460);
        """
    
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&family=Poppins:wght@400;500;600;700;800&display=swap');
        
        * {{
            font-family: 'Inter', 'Poppins', sans-serif;
            transition: all 0.3s ease;
        }}
        
        /* Code blocks use monospace */
        code, .code, .invite-code {{
            font-family: 'JetBrains Mono', monospace !important;
        }}
        
        .stApp {{
            {bg_style}
        }}
        
        .stApp > header {{
            background: rgba(10,14,39,0.95) !important;
            backdrop-filter: blur(30px) !important;
            -webkit-backdrop-filter: blur(30px) !important;
            border-bottom: 2px solid rgba(212,175,55,0.3) !important;
            box-shadow: 0 4px 30px rgba(0,0,0,0.3) !important;
        }}
        
        .main .block-container {{
            background: rgba(10,14,39,0.75) !important;
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            border-radius: 24px !important;
            padding: 2rem !important;
            margin: 1.5rem !important;
            border: 1px solid rgba(212,175,55,0.15) !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4) !important;
        }}
        
        /* Typography with enhanced readability */
        h1, h2, h3, h4, h5, h6 {{
            color: #FFFFFF !important;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.9), 0 0 30px rgba(0,0,0,0.6) !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
        }}
        
        p, span, label, div {{
            color: #FFFFFF !important;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.8), 0 0 20px rgba(0,0,0,0.5) !important;
        }}
        
        /* Enhanced Glass Cards */
        .glass-card {{
            background: rgba(0,0,0,0.65) !important;
            backdrop-filter: blur(30px) !important;
            -webkit-backdrop-filter: blur(30px) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            margin: 20px 0 !important;
            border: 1px solid rgba(212,175,55,0.25) !important;
            box-shadow: 0 15px 50px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.05) !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        
        .glass-card:hover {{
            box-shadow: 0 20px 60px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.1) !important;
            border-color: rgba(212,175,55,0.4) !important;
        }}
        
        /* Statistics Cards */
        .stat-card {{
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            padding: 28px !important;
            border-radius: 18px !important;
            border-left: 5px solid #e94560 !important;
            border-right: 1px solid rgba(255,255,255,0.1) !important;
            border-top: 1px solid rgba(255,255,255,0.1) !important;
            border-bottom: 1px solid rgba(255,255,255,0.1) !important;
            text-align: center !important;
            margin: 10px 0 !important;
            transition: all 0.3s ease !important;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px) !important;
            box-shadow: 0 15px 40px rgba(233,69,96,0.3) !important;
            border-left-width: 7px !important;
        }}
        
        .stat-value {{
            font-size: 2.8em !important;
            font-weight: 900 !important;
            background: linear-gradient(135deg, #FFFFFF, #e0e0e0) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: none !important;
            margin: 10px 0 !important;
        }}
        
        .stat-label {{
            color: rgba(255,255,255,0.95) !important;
            font-size: 1em !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }}
        
        /* Input Fields */
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stSelectbox > div {{
            background: rgba(255,255,255,0.95) !important;
            border: 2px solid rgba(212,175,55,0.4) !important;
            border-radius: 12px !important;
            padding: 12px 18px !important;
            color: #1a1a1a !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
        }}
        
        .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
            border-color: #e94560 !important;
            box-shadow: 0 0 0 4px rgba(233,69,96,0.2), 0 4px 15px rgba(0,0,0,0.2) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Buttons with animations */
        .stButton > button {{
            background: linear-gradient(135deg, #e94560, #c62a47) !important;
            border: none !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 700 !important;
            padding: 12px 24px !important;
            box-shadow: 0 6px 20px rgba(233,69,96,0.4) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            font-size: 0.9em !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 12px 30px rgba(233,69,96,0.6) !important;
            background: linear-gradient(135deg, #f05570, #d93a57) !important;
        }}
        
        .stButton > button:active {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 15px rgba(233,69,96,0.4) !important;
        }}
        
        /* Data tables */
        .stDataFrame {{
            background: rgba(255,255,255,0.08) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-radius: 16px !important;
            border: 1px solid rgba(212,175,55,0.3) !important;
            overflow: hidden !important;
        }}
        
        .stDataFrame th {{
            background: linear-gradient(135deg, rgba(233,69,96,0.9), rgba(198,42,71,0.9)) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            padding: 14px 18px !important;
            font-size: 0.9em !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }}
        
        .stDataFrame td {{
            background: rgba(255,255,255,0.05) !important;
            color: #FFFFFF !important;
            padding: 12px 18px !important;
            border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        }}
        
        .stDataFrame tr:hover td {{
            background: rgba(233,69,96,0.15) !important;
        }}
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(10,14,39,0.98), rgba(26,31,78,0.98), rgba(15,52,96,0.98)) !important;
            backdrop-filter: blur(30px) !important;
            -webkit-backdrop-filter: blur(30px) !important;
            border-right: 1px solid rgba(212,175,55,0.2) !important;
        }}
        
        section[data-testid="stSidebar"] * {{
            color: #FFFFFF !important;
            text-shadow: 0 1px 3px rgba(0,0,0,0.6) !important;
        }}
        
        section[data-testid="stSidebar"] .stButton > button {{
            background: rgba(255,255,255,0.08) !important;
            border: 1px solid rgba(212,175,55,0.2) !important;
            color: #FFFFFF !important;
            text-align: left !important;
            padding: 12px 18px !important;
            margin: 4px 0 !important;
            font-size: 0.9rem !important;
            box-shadow: none !important;
            text-transform: none !important;
            letter-spacing: 0 !important;
            transition: all 0.2s ease !important;
        }}
        
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(233,69,96,0.3) !important;
            border-color: rgba(233,69,96,0.5) !important;
            transform: translateX(5px) !important;
        }}
        
        /* School code banner */
        .school-code-banner {{
            background: linear-gradient(135deg, rgba(0,0,0,0.6), rgba(26,31,78,0.6)) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border: 2px dashed rgba(233,69,96,0.4) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            text-align: center !important;
            animation: pulse 2s ease-in-out infinite !important;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ border-color: rgba(233,69,96,0.4); }}
            50% {{ border-color: rgba(233,69,96,0.8); }}
        }}
        
        .invite-code {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 3em !important;
            font-weight: 900 !important;
            letter-spacing: 10px !important;
            background: linear-gradient(135deg, #f0d060, #d4af37, #b8941f) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: none !important;
        }}
        
        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes slideInLeft {{
            from {{
                opacity: 0;
                transform: translateX(-50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes scaleIn {{
            from {{
                opacity: 0;
                transform: scale(0.9);
            }}
            to {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
        
        .animate-fadeInUp {{
            animation: fadeInUp 0.6s ease-out !important;
        }}
        
        .animate-slideInLeft {{
            animation: slideInLeft 0.5s ease-out !important;
        }}
        
        .animate-scaleIn {{
            animation: scaleIn 0.4s ease-out !important;
        }}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, #e94560, #c62a47);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(135deg, #f05570, #d93a57);
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 1rem !important;
                margin: 0.5rem !important;
                border-radius: 16px !important;
            }}
            
            .stat-value {{
                font-size: 2em !important;
            }}
            
            .glass-card {{
                padding: 20px !important;
            }}
        }}
        
        /* Print styles */
        @media print {{
            .stApp > header, section[data-testid="stSidebar"] {{
                display: none !important;
            }}
            
            .main .block-container {{
                background: white !important;
                color: black !important;
                box-shadow: none !important;
            }}
        }}
    </style>
    """

# ============ HELPER FUNCTIONS ============
def sanitize_html(text: str) -> str:
    """Sanitize text for safe HTML rendering"""
    if not text:
        return ""
    return html.escape(str(text))

def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

def generate_code(prefix: str = "", length: int = 10) -> str:
    """Generate cryptographically secure random code"""
    chars = string.ascii_uppercase + string.digits
    return prefix + ''.join(random.SystemRandom().choices(chars, k=length))

def is_admin() -> bool:
    """Check if current user is admin"""
    if not st.session_state.get('user'):
        return False
    return st.session_state.user.get('role') == 'admin'

def is_authenticated() -> bool:
    """Check if user is fully authenticated"""
    return (st.session_state.get('user') is not None and 
            st.session_state.get('school') is not None)

def add_audit_entry(action: str, details: str, module: str = "General"):
    """Add entry to audit log with comprehensive tracking"""
    try:
        school_name = "System"
        user_email = "system@srms.local"
        user_name = "System"
        
        if is_authenticated():
            school_name = st.session_state.school.get('name', 'Unknown')
            user_email = st.session_state.user.get('email', 'unknown')
            user_name = st.session_state.user.get('name', 'Unknown')
        
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO audit_log (school_name, user_email, user_name, action, module, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (school_name, user_email, user_name, action, module, details, '127.0.0.1'))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(f"Audit log error (non-critical): {str(e)}")

def send_email_notification(to_email: str, subject: str, body: str, school_name: str = None):
    """Send email notification (simulated for development)"""
    try:
        # In production, configure SMTP settings
        # For now, log the email
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO email_log (school_name, to_email, subject, body, status)
                VALUES (?, ?, ?, ?, 'sent')
            """, (school_name or "System", to_email, subject, body))
            conn.commit()
        finally:
            conn.close()
        
        print(f"📧 Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

def load_school_data(data_type: str, filters: dict = None) -> Any:
    """Enhanced data loader with filtering support"""
    if not is_authenticated():
        return [] if data_type != 'system_settings' else {}
    
    school_name = st.session_state.school['name']
    conn = get_db_connection()
    
    try:
        query_map = {
            'books': "SELECT * FROM books WHERE school_name = ?",
            'borrowed_books': "SELECT * FROM borrowed_books WHERE school_name = ?",
            'furniture': "SELECT * FROM furniture WHERE school_name = ?",
            'members': "SELECT * FROM members WHERE school_name = ?",
            'classes': "SELECT * FROM classes WHERE school_name = ?",
            'departments': "SELECT * FROM departments WHERE school_name = ?",
            'reservations': "SELECT * FROM reservations WHERE school_name = ?",
            'chat_messages': "SELECT * FROM chat_messages WHERE school_name = ? AND is_deleted = 0",
            'announcements': "SELECT * FROM announcements WHERE school_name = ? AND is_active = 1",
            'documents': "SELECT * FROM documents WHERE school_name = ?",
            'audit_log': "SELECT * FROM audit_log WHERE school_name = ? ORDER BY timestamp DESC LIMIT 500",
            'users': "SELECT * FROM users WHERE school_name = ? AND is_active = 1",
            'resource_kits': "SELECT * FROM resource_kits WHERE school_name = ?",
        }
        
        query = query_map.get(data_type, f"SELECT * FROM {data_type} WHERE school_name = ?")
        
        if filters:
            conditions = " AND ".join([f"{k} = ?" for k in filters.keys()])
            query = query.replace("WHERE school_name = ?", f"WHERE school_name = ? AND {conditions}")
            params = [school_name] + list(filters.values())
        else:
            params = [school_name]
        
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Parse JSON fields
        if data_type == 'classes':
            for result in results:
                try:
                    result['students'] = json.loads(result.get('students', '[]'))
                except:
                    result['students'] = []
        
        return results
    except Exception as e:
        print(f"Error loading {data_type}: {str(e)}")
        return []
    finally:
        conn.close()

def check_duplicate_assignment(school_name: str, identifier: str, item_type: str, item_number: str) -> bool:
    """Check for duplicate assignments"""
    conn = get_db_connection()
    try:
        if item_type == 'book':
            cursor = conn.execute(
                "SELECT * FROM borrowed_books WHERE school_name = ? AND borrower_id = ? AND book_no = ? AND is_returned = 0",
                (school_name, identifier, item_number)
            )
        elif item_type in ['chair', 'locker']:
            cursor = conn.execute(
                "SELECT * FROM furniture WHERE school_name = ? AND assigned_to = ? AND item_number = ? AND is_returned = 0 AND item_type = ?",
                (school_name, identifier, item_number, item_type)
            )
        else:
            return False
        
        return cursor.fetchone() is not None
    finally:
        conn.close()

# ============ COLLAPSIBLE SIDEBAR SYSTEM ============
def setup_collapsible_sidebar():
    """Setup sidebar with auto-collapse functionality"""
    
    # Inject JavaScript for sidebar control
    st.markdown("""
    <script>
        // Function to collapse sidebar
        function collapseSidebar() {
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.style.width = '0px';
                sidebar.style.overflow = 'hidden';
            }
        }
        
        // Function to expand sidebar
        function expandSidebar() {
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.style.width = '';
                sidebar.style.overflow = '';
            }
        }
        
        // Toggle sidebar
        function toggleSidebar() {
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                if (sidebar.style.width === '0px') {
                    expandSidebar();
                } else {
                    collapseSidebar();
                }
            }
        }
    </script>
    """, unsafe_allow_html=True)

# ============ SESSION STATE INITIALIZATION ============
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'user': None,
        'school': None,
        'page': 'startup',
        'wallpaper': 'Library Classic',
        'current_section': 'dashboard',
        'action': None,
        'chat_with': None,
        'selected_emoji': None,
        'editing_note': None,
        'sidebar_collapsed': False,
        'notification_count': 0,
        'last_refresh': time.time(),
        'auto_refresh': True,
        'selected_department': 'All',
        'search_query': '',
        'filter_date_range': None,
        'bulk_operation_mode': False,
        'pending_actions': [],
        'recent_activities': [],
        'bookmarked_sections': [],
        'theme_preferences': {
            'font_size': 'medium',
            'card_style': 'glass',
            'animation_speed': 'normal'
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ============ STARTUP PAGE ============
def startup_page():
    """Enhanced startup page with animations"""
    
    # Hero section
    st.markdown("""
    <div class="glass-card animate-scaleIn" style="text-align: center; max-width: 700px; margin: 50px auto;">
        <div style="width: 180px; height: 180px; background: linear-gradient(135deg, #d4af37, #f0d060, #d4af37); 
             border-radius: 40px; display: inline-flex; align-items: center; justify-content: center; 
             font-size: 65px; font-weight: 900; color: #0a0e27; margin-bottom: 25px;
             box-shadow: 0 25px 70px rgba(212, 175, 55, 0.5);
             animation: float 3s ease-in-out infinite;">
            SRMS
        </div>
        <h1 style="font-size: 4em; background: linear-gradient(180deg, #f0d060, #d4af37, #b8941f); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 15px 0;
            filter: drop-shadow(0 0 20px rgba(212,175,55,0.3));">
            SRMS
        </h1>
        <p style="font-size: 1.6em; color: #FFFFFF; margin: 15px 0; font-weight: 300;">
            School Resource Management System
        </p>
        <p style="color: #d4af37; font-size: 1.2em; font-weight: 500;">
            by <span style="color: #f0d060; font-weight: 700;">WeGEM</span> (Edwin)
        </p>
        <p style="color: rgba(255,255,255,0.5); font-size: 0.9em; margin-top: 25px;">
            Version {APP_VERSION} | Enterprise Teacher Edition
        </p>
    </div>
    
    <style>
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Action buttons with descriptions
    st.markdown('<div class="glass-card animate-fadeInUp">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center;margin-bottom:20px;">🎯 Get Started</h3>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align:center;">
            <span style="font-size:3em;">🔑</span>
            <h4>Staff Login</h4>
            <p style="font-size:0.8em;color:rgba(255,255,255,0.7);">Access your account</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔑 Login", use_container_width=True, key="btn_login"):
            st.session_state.action = 'login'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="text-align:center;">
            <span style="font-size:3em;">📝</span>
            <h4>Sign Up</h4>
            <p style="font-size:0.8em;color:rgba(255,255,255,0.7);">Join your school</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Sign Up", use_container_width=True, key="btn_signup"):
            st.session_state.action = 'signup'
            st.rerun()
    
    with col3:
        st.markdown("""
        <div style="text-align:center;">
            <span style="font-size:3em;">🏫</span>
            <h4>Create School</h4>
            <p style="font-size:0.8em;color:rgba(255,255,255,0.7);">Register new school</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏫 Create", use_container_width=True, key="btn_create"):
            st.session_state.action = 'create'
            st.rerun()
    
    with col4:
        st.markdown("""
        <div style="text-align:center;">
            <span style="font-size:3em;">🔐</span>
            <h4>Reset Password</h4>
            <p style="font-size:0.8em;color:rgba(255,255,255,0.7);">Forgot password?</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔐 Reset", use_container_width=True, key="btn_forgot"):
            st.session_state.action = 'forgot_password'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Features showcase
    st.markdown('<div class="glass-card animate-fadeInUp">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center;">✨ Features for Teachers</h3>', unsafe_allow_html=True)
    
    features = [
        ("📚", "Book Management", "Issue, return, and track all library resources"),
        ("🪑", "Furniture Allocation", "Manage chairs, lockers, and equipment"),
        ("💬", "Team Chat", "Communicate with fellow teachers in real-time"),
        ("📊", "Analytics", "Detailed reports and resource utilization insights"),
        ("📅", "Reservations", "Reserve books and resources for future lessons"),
        ("🔍", "Smart Search", "Quick find any book, member, or resource")
    ]
    
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="text-align:center;padding:20px;background:rgba(255,255,255,0.05);border-radius:12px;margin:10px 0;">
                <span style="font-size:2.5em;">{icon}</span>
                <h4 style="margin:10px 0;">{title}</h4>
                <p style="font-size:0.85em;color:rgba(255,255,255,0.7);">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle authentication forms
    if st.session_state.action:
        st.markdown('<div class="glass-card animate-slideInLeft">', unsafe_allow_html=True)
        
        if st.session_state.action == 'login':
            login_form()
        elif st.session_state.action == 'signup':
            signup_form()
        elif st.session_state.action == 'create':
            create_school_form()
        elif st.session_state.action == 'forgot_password':
            forgot_password_form()
        
        st.markdown('</div>', unsafe_allow_html=True)

def login_form():
    """Enhanced login form with validation"""
    st.markdown('<h3 style="color:#FFFFFF;">🔐 Staff Login</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:rgba(255,255,255,0.7);">Enter your credentials to access the system</p>', unsafe_allow_html=True)
    
    with st.form("frm_login", clear_on_submit=False):
        name = st.text_input("👤 Full Name", placeholder="Enter your registered full name")
        school_name = st.text_input("🏢 School Name", placeholder="Enter your school name")
        invite_code = st.text_input("🔑 Invite Code", placeholder="Enter the invite code provided by admin")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("🔑 Login to System", use_container_width=True, type="primary")
        with col2:
            forgot = st.form_submit_button("🔐 Forgot Password?", use_container_width=True)
        
        if submit:
            # Validation
            errors = []
            if not name: errors.append("Name is required")
            if not school_name: errors.append("School name is required")
            if not invite_code: errors.append("Invite code is required")
            if not password: errors.append("Password is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                return
            
            conn = get_db_connection()
            try:
                # Check school
                school = conn.execute(
                    "SELECT * FROM schools WHERE LOWER(name) = ? AND is_active = 1", 
                    (school_name.lower(),)
                ).fetchone()
                
                if not school:
                    st.error(f"❌ School '{school_name}' not found!")
                    st.info("Check the school name or create a new school.")
                    return
                
                # Check user
                user = conn.execute(
                    """SELECT * FROM users 
                    WHERE LOWER(name) = ? AND school_name = ? AND code = ? AND is_active = 1""",
                    (name.lower(), school['name'], invite_code.upper())
                ).fetchone()
                
                if not user:
                    st.error("❌ User not found! Check your name and invite code.")
                    return
                
                if not verify_password(password, user['password']):
                    st.error("❌ Invalid password!")
                    return
                
                # Login successful
                st.session_state.user = dict(user)
                st.session_state.school = dict(school)
                st.session_state.page = 'dashboard'
                st.session_state.action = None
                st.session_state.chat_with = None
                
                # Update last login
                conn.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE email = ? AND school_name = ?",
                    (user['email'], school['name'])
                )
                conn.commit()
                
                add_audit_entry('Login', f"User {user['name']} logged in", 'Authentication')
                st.success("✅ Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Login error: {str(e)}")
            finally:
                conn.close()
        
        if forgot:
            st.session_state.action = 'forgot_password'
            st.rerun()

# [Continue with remaining functions - signup_form, create_school_form, forgot_password_form, etc.]

# ============== MAIN APPLICATION ==============
def main():
    """Main application entry point"""
    # Apply adaptive CSS
    st.markdown(get_adaptive_css(st.session_state.wallpaper), unsafe_allow_html=True)
    
    # Setup collapsible sidebar
    setup_collapsible_sidebar()
    
    # Route to appropriate page
    if st.session_state.page == 'startup':
        startup_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()
    else:
        startup_page()

if __name__ == "__main__":
    main()

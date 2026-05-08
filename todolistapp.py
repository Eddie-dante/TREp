# app.py - SRMS - School Resource Management System by WeGEM
import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import random
import string
import base64
from io import BytesIO
import qrcode
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import bcrypt
import html
import sqlite3
from typing import Optional, Dict, Any, List

# Page config
st.set_page_config(
    page_title="SRMS - School Resource Management System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DATA_DIR = Path("srms_data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "srms.db"

# ============ DATABASE SETUP ============
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize all database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables one by one to avoid errors
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schools (
                name TEXT PRIMARY KEY,
                address TEXT DEFAULT '',
                admin_name TEXT DEFAULT '',
                admin_email TEXT DEFAULT '',
                admin_phone TEXT DEFAULT '',
                invite_code TEXT DEFAULT '',
                created TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT,
                school_name TEXT,
                name TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                staff_id TEXT DEFAULT '',
                code TEXT DEFAULT '',
                password TEXT DEFAULT '',
                role TEXT DEFAULT 'teacher',
                department TEXT DEFAULT '',
                joined TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                PRIMARY KEY (email, school_name)
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT DEFAULT '',
                title TEXT DEFAULT '',
                author TEXT DEFAULT '',
                category TEXT DEFAULT '',
                quantity INTEGER DEFAULT 1,
                available INTEGER DEFAULT 1,
                added_by TEXT DEFAULT '',
                added_at TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS borrowed (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                book_title TEXT DEFAULT '',
                book_no TEXT DEFAULT '',
                borrower_name TEXT DEFAULT '',
                borrower_id TEXT DEFAULT '',
                department TEXT DEFAULT '',
                borrow_date TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                return_date TEXT DEFAULT '',
                returned INTEGER DEFAULT 0,
                fine REAL DEFAULT 0,
                fine_paid INTEGER DEFAULT 0,
                issued_by TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS furniture (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                item_type TEXT DEFAULT '',
                item_number TEXT DEFAULT '',
                assigned_to TEXT DEFAULT '',
                department TEXT DEFAULT '',
                assigned_date TEXT DEFAULT '',
                returned INTEGER DEFAULT 0
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                name TEXT DEFAULT '',
                department TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                email TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT DEFAULT '',
                name TEXT DEFAULT '',
                students TEXT DEFAULT '[]',
                created_by TEXT DEFAULT '',
                created TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                book_title TEXT DEFAULT '',
                reserved_by TEXT DEFAULT '',
                department TEXT DEFAULT '',
                reservation_date TEXT DEFAULT '',
                needed_by TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending'
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                from_email TEXT DEFAULT '',
                from_name TEXT DEFAULT '',
                to_email TEXT DEFAULT '',
                department TEXT DEFAULT '',
                message TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                is_read INTEGER DEFAULT 0
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                priority TEXT DEFAULT 'Normal',
                posted_by TEXT DEFAULT '',
                department TEXT DEFAULT '',
                posted_at TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                school_name TEXT DEFAULT '',
                title TEXT DEFAULT '',
                file_type TEXT DEFAULT '',
                file_data TEXT DEFAULT '',
                subject TEXT DEFAULT '',
                uploaded_by TEXT DEFAULT '',
                uploaded_at TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                user TEXT DEFAULT '',
                action TEXT DEFAULT '',
                details TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallpapers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT DEFAULT '',
                name TEXT DEFAULT '',
                url TEXT DEFAULT '',
                uploaded_by TEXT DEFAULT ''
            )
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                email TEXT,
                school_name TEXT,
                token TEXT DEFAULT '',
                expiry TEXT DEFAULT '',
                used INTEGER DEFAULT 0
            )
        """)
    except:
        pass
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

# Initialize database
init_db()

# ============ WALLPAPERS ============
WALLPAPERS = {
    "None": "",
    "Library": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=1920",
    "Classroom": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=1920",
    "School Building": "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=1920",
    "Bookshelf": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1920",
    "Graduation": "https://images.unsplash.com/photo-1523050854058-8df90910f68e?w=1920",
    "Sunset": "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=1920",
    "Ocean": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920",
    "Forest": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920",
    "Mountain": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
    "Desert": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1920",
    "Waterfall": "https://images.unsplash.com/photo-1544551763-46a013bb70b5?w=1920",
    "Cherry Blossom": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920",
    "Northern Lights": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=1920",
    "Galaxy": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1920",
    "City Lights": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1920",
    "Tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1920",
    "New York": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1920",
    "Autumn": "https://images.unsplash.com/photo-1507783548227-544c3b8fc065?w=1920",
    "Winter Snow": "https://images.unsplash.com/photo-1477601263568-180e2c6d046e?w=1920",
    "Spring": "https://images.unsplash.com/photo-1490750967868-88aa4cef14d0?w=1920",
    "Summer": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920",
    "Tropical Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920",
    "Lavender": "https://images.unsplash.com/photo-1499002238440-d264edd596ec?w=1920",
    "Abstract": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920",
    "Starry Night": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920",
    "Clouds": "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1920",
    "Tiger": "https://images.unsplash.com/photo-1549480017-d76466a4b7e8?w=1920",
    "Lion": "https://images.unsplash.com/photo-1534188753412-3e26d0d618d6?w=1920",
    "Eagle": "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42?w=1920",
    "Butterfly": "https://images.unsplash.com/photo-1505063366573-38928ae5567e?w=1920",
}

# ============ EMOJIS ============
EMOJIS = ["😀", "😂", "😍", "🥰", "😘", "👍", "👎", "👏", "🙌", "💪", "❤️", "💙", "💚", "💛", "🧡", "💜", "🖤", "🤍", "⭐", "🌟", "✨", "🔥", "💯", "✅", "❌", "⚠️", "📚", "📖", "📝", "✏️", "🎓", "🏫", "🎯", "🔑", "🔒", "📢", "💡", "🎁", "🏆", "📅", "⏰", "☕", "🍕", "🚀", "✈️", "🏠", "🎨", "🎵", "⚽", "🏀"]

# ============ HELPER FUNCTIONS ============
def sanitize(text):
    if not text:
        return ""
    return html.escape(str(text))

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def is_admin():
    return st.session_state.get('user') and st.session_state.user.get('role') == 'admin'

def add_audit(action, details):
    try:
        if not st.session_state.get('school') or not st.session_state.get('user'):
            return
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_log (school_name, timestamp, user, action, details) VALUES (?, ?, ?, ?, ?)",
            (st.session_state.school.get('name', ''), datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             st.session_state.user.get('name', ''), action, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit error: {e}")

def load_data(table, filters=None):
    if not st.session_state.get('school'):
        return []
    
    conn = get_db()
    try:
        school = st.session_state.school.get('name', '')
        query = f"SELECT * FROM {table} WHERE school_name = ?"
        params = [school]
        
        if filters:
            for k, v in filters.items():
                query += f" AND {k} = ?"
                params.append(v)
        
        data = conn.execute(query, params).fetchall()
        return [dict(row) for row in data]
    except Exception as e:
        print(f"Load error for {table}: {e}")
        return []
    finally:
        conn.close()

# ============ CSS ============
def get_css(wallpaper=None):
    bg = WALLPAPERS.get(wallpaper, "")
    if bg:
        bg_style = f"background-image: url('{bg}'); background-size: cover; background-position: center; background-attachment: fixed;"
    else:
        bg_style = "background: linear-gradient(135deg, #0a0e27, #1a1f4e, #0f3460);"
    
    return f"""
    <style>
        .stApp {{ {bg_style} }}
        .main .block-container {{
            background: rgba(10,14,39,0.8);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem;
            border: 1px solid rgba(212,175,55,0.2);
        }}
        h1, h2, h3, h4 {{ color: #FFFFFF !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
        p, span, label {{ color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.7); }}
        .glass-card {{
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 25px;
            margin: 15px 0;
            border: 1px solid rgba(212,175,55,0.25);
        }}
        .stat-card {{
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(15px);
            padding: 25px;
            border-radius: 16px;
            border-left: 4px solid #e94560;
            text-align: center;
            margin: 8px 0;
        }}
        .stat-value {{ font-size: 2.5em; font-weight: 900; color: #FFFFFF; }}
        .stat-label {{ color: rgba(255,255,255,0.9); font-size: 0.9em; font-weight: 600; }}
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stSelectbox > div {{
            background: rgba(255,255,255,0.95) !important;
            border: 2px solid rgba(212,175,55,0.4) !important;
            border-radius: 10px !important;
            color: #1a1a1a !important;
        }}
        .stButton > button {{
            background: linear-gradient(135deg, #e94560, #c62a47) !important;
            border: none !important;
            border-radius: 10px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
        }}
        .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(233,69,96,0.5); }}
        .stDataFrame {{ background: rgba(255,255,255,0.08); border-radius: 12px; border: 1px solid rgba(212,175,55,0.3); }}
        .stDataFrame th {{ background: rgba(233,69,96,0.8); color: #FFFFFF; font-weight: 700; }}
        .stDataFrame td {{ background: rgba(255,255,255,0.05); color: #FFFFFF; }}
        .invite-code {{
            font-family: 'Courier New', monospace;
            font-size: 2.5em;
            font-weight: 800;
            letter-spacing: 8px;
            color: #FFD700 !important;
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(10,14,39,0.95), rgba(26,31,78,0.95), rgba(15,52,96,0.95));
            backdrop-filter: blur(20px);
        }}
        section[data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
        section[data-testid="stSidebar"] .stButton > button {{
            background: rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(212,175,55,0.3) !important;
            text-align: left !important;
            padding: 10px 15px !important;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(233,69,96,0.4) !important;
            transform: translateX(5px) !important;
        }}
    </style>
    """

# ============ SESSION STATE ============
if 'user' not in st.session_state: st.session_state.user = None
if 'school' not in st.session_state: st.session_state.school = None
if 'page' not in st.session_state: st.session_state.page = 'startup'
if 'wallpaper' not in st.session_state: st.session_state.wallpaper = "Library"
if 'section' not in st.session_state: st.session_state.section = 'dashboard'
if 'action' not in st.session_state: st.session_state.action = None
if 'chat_with' not in st.session_state: st.session_state.chat_with = None
if 'emoji' not in st.session_state: st.session_state.emoji = None
if 'students' not in st.session_state: st.session_state.students = None
if 'fur_students' not in st.session_state: st.session_state.fur_students = None
if 'reset_email' not in st.session_state: st.session_state.reset_email = None
if 'reset_school' not in st.session_state: st.session_state.reset_school = None

st.markdown(get_css(st.session_state.wallpaper), unsafe_allow_html=True)

# ============ STARTUP PAGE ============
def startup_page():
    st.markdown("""
    <div class="glass-card" style="text-align:center;max-width:600px;margin:50px auto;">
        <h1 style="font-size:3.5em;color:#FFD700 !important;">SRMS</h1>
        <p style="font-size:1.4em;">School Resource Management System</p>
        <p style="color:#d4af37;">by WeGEM (Edwin)</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🔑 Login", use_container_width=True): 
            st.session_state.action = 'login'
            st.rerun()
    with c2:
        if st.button("📝 Sign Up", use_container_width=True): 
            st.session_state.action = 'signup'
            st.rerun()
    with c3:
        if st.button("🏫 Create School", use_container_width=True): 
            st.session_state.action = 'create'
            st.rerun()
    with c4:
        if st.button("🔐 Forgot Password", use_container_width=True): 
            st.session_state.action = 'forgot'
            st.rerun()
    
    if st.session_state.action:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if st.session_state.action == 'login':
            login_form()
        elif st.session_state.action == 'signup':
            signup_form()
        elif st.session_state.action == 'create':
            create_school_form()
        elif st.session_state.action == 'forgot':
            forgot_password_form()
        st.markdown('</div>', unsafe_allow_html=True)

def login_form():
    st.subheader("🔐 Staff Login")
    with st.form("login"):
        name = st.text_input("Full Name")
        school = st.text_input("School Name")
        code = st.text_input("Invite Code")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", use_container_width=True, type="primary"):
            if not all([name, school, code, password]):
                st.error("All fields required!")
                return
            
            try:
                conn = get_db()
                sch = conn.execute("SELECT * FROM schools WHERE LOWER(name) = LOWER(?) AND is_active = 1", (school,)).fetchone()
                if not sch:
                    st.error("School not found!")
                    conn.close()
                    return
                
                usr = conn.execute(
                    "SELECT * FROM users WHERE LOWER(name) = LOWER(?) AND school_name = ? AND code = ? AND is_active = 1",
                    (name, sch['name'], code.upper())
                ).fetchone()
                conn.close()
                
                if not usr:
                    st.error("User not found! Check your name and invite code.")
                    return
                
                if not verify_password(password, usr['password']):
                    st.error("Invalid password!")
                    return
                
                st.session_state.user = dict(usr)
                st.session_state.school = dict(sch)
                st.session_state.page = 'dashboard'
                st.session_state.action = None
                
                # Update last login
                conn = get_db()
                conn.execute("UPDATE users SET last_login = ? WHERE email = ? AND school_name = ?",
                           (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usr['email'], sch['name']))
                conn.commit()
                conn.close()
                
                add_audit('Login', f"{usr['name']} logged in")
                st.success("Login successful!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def signup_form():
    st.subheader("📝 Staff Sign Up")
    with st.form("signup"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone")
        with c2:
            school = st.text_input("School Name *")
            code = st.text_input("Invite Code *")
            dept = st.selectbox("Department", ["Sciences", "Mathematics", "Languages", "Humanities", "Technical", "Other"])
        
        password = st.text_input("Password *", type="password", placeholder="Min 6 characters")
        
        if st.form_submit_button("Sign Up", use_container_width=True, type="primary"):
            if not all([name, email, school, code, password]):
                st.error("All fields with * are required!")
                return
            if len(password) < 6:
                st.error("Password min 6 characters!")
                return
            
            try:
                conn = get_db()
                sch = conn.execute("SELECT * FROM schools WHERE LOWER(name) = LOWER(?) AND is_active = 1", (school,)).fetchone()
                if not sch:
                    st.error("School not found! Check the school name.")
                    conn.close()
                    return
                
                if sch['invite_code'] != code.upper():
                    st.error("Invalid invite code!")
                    conn.close()
                    return
                
                exists = conn.execute("SELECT * FROM users WHERE email = ? AND school_name = ?", (email, sch['name'])).fetchone()
                if exists:
                    st.error("Email already registered!")
                    conn.close()
                    return
                
                conn.execute(
                    "INSERT INTO users (email, school_name, name, phone, staff_id, code, password, role, department, joined) VALUES (?, ?, ?, ?, ?, ?, ?, 'teacher', ?, ?)",
                    (email, sch['name'], name, phone, f"STAFF-{generate_code(4)}", code.upper(), hash_password(password), dept, datetime.now().strftime("%Y-%m-%d"))
                )
                conn.commit()
                conn.close()
                
                st.success("Registration successful! Please login.")
                st.session_state.action = 'login'
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def create_school_form():
    st.subheader("🏫 Create New School")
    with st.form("create_school"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("School Name *")
            address = st.text_input("Address")
            admin_name = st.text_input("Admin Name *")
        with c2:
            admin_email = st.text_input("Admin Email *")
            admin_phone = st.text_input("Admin Phone")
        
        password = st.text_input("Admin Password *", type="password", placeholder="Min 8 characters")
        confirm = st.text_input("Confirm Password *", type="password")
        
        if st.form_submit_button("Create School", use_container_width=True, type="primary"):
            if not all([name, admin_name, admin_email, password]):
                st.error("Required fields missing!")
                return
            if password != confirm:
                st.error("Passwords don't match!")
                return
            if len(password) < 8:
                st.error("Password min 8 characters!")
                return
            
            try:
                conn = get_db()
                
                # Check if school exists
                existing = conn.execute("SELECT * FROM schools WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
                if existing:
                    st.error("School already exists!")
                    conn.close()
                    return
                
                invite = generate_code()
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Insert school
                conn.execute(
                    "INSERT INTO schools (name, address, admin_name, admin_email, admin_phone, invite_code, created, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                    (name, address or '', admin_name, admin_email, admin_phone or '', invite, today)
                )
                
                # Insert admin user
                conn.execute(
                    "INSERT INTO users (email, school_name, name, phone, staff_id, code, password, role, department, joined, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 'admin', 'Administration', ?, 1)",
                    (admin_email, name, admin_name, admin_phone or '', "ADMIN-001", invite, hash_password(password), today)
                )
                
                conn.commit()
                conn.close()
                
                st.success(f"✅ School created successfully!")
                st.info(f"🔑 Invite Code: `{invite}`")
                st.info(f"📧 Admin Email: `{admin_email}`")
                st.info("Please login with your credentials.")
                
                st.session_state.action = 'login'
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def forgot_password_form():
    st.subheader("🔐 Reset Password")
    
    with st.form("forgot"):
        email = st.text_input("Registered Email")
        school = st.text_input("School Name")
        
        if st.form_submit_button("Send Reset Token", use_container_width=True):
            if not email or not school:
                st.error("All fields required!")
                return
            
            try:
                conn = get_db()
                user = conn.execute(
                    "SELECT * FROM users WHERE email = ? AND LOWER(school_name) = LOWER(?) AND is_active = 1",
                    (email, school)
                ).fetchone()
                
                if user:
                    token = hashlib.sha256(os.urandom(32)).hexdigest()
                    expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    conn.execute(
                        "INSERT OR REPLACE INTO password_resets (email, school_name, token, expiry, used) VALUES (?, ?, ?, ?, 0)",
                        (email, user['school_name'], token, expiry)
                    )
                    conn.commit()
                    
                    st.success(f"Reset token generated! (Dev mode)")
                    st.code(token[:20] + "...")
                    st.session_state.reset_email = email
                    st.session_state.reset_school = user['school_name']
                else:
                    st.error("User not found!")
                conn.close()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.get('reset_email'):
        st.markdown("---")
        with st.form("reset"):
            token = st.text_input("Reset Token")
            new_pw = st.text_input("New Password", type="password", placeholder="Min 6 characters")
            confirm_pw = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Reset Password", use_container_width=True):
                if new_pw != confirm_pw:
                    st.error("Passwords don't match!")
                    return
                if len(new_pw) < 6:
                    st.error("Password min 6 characters!")
                    return
                
                try:
                    conn = get_db()
                    reset = conn.execute(
                        "SELECT * FROM password_resets WHERE email = ? AND school_name = ? AND token = ? AND expiry > ? AND used = 0",
                        (st.session_state.reset_email, st.session_state.reset_school, token, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    ).fetchone()
                    
                    if reset:
                        conn.execute(
                            "UPDATE users SET password = ? WHERE email = ? AND school_name = ?",
                            (hash_password(new_pw), st.session_state.reset_email, st.session_state.reset_school)
                        )
                        conn.execute(
                            "UPDATE password_resets SET used = 1 WHERE email = ? AND school_name = ?",
                            (st.session_state.reset_email, st.session_state.reset_school)
                        )
                        conn.commit()
                        st.success("Password reset! Please login.")
                        st.session_state.action = 'login'
                        st.session_state.reset_email = None
                        st.session_state.reset_school = None
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Invalid or expired token!")
                    conn.close()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============ DASHBOARD ============
def dashboard_page():
    user = st.session_state.user
    school = st.session_state.school
    
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;margin-bottom:25px;">
        <h2>🏫 {sanitize(school.get('name', ''))}</h2>
        <p>👤 {sanitize(user.get('name', ''))} 
        <span style="background:{'#e94560' if user.get('role')=='admin' else '#0f3460'};padding:4px 12px;border-radius:20px;">
        {sanitize(user.get('role', '').upper())}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    if is_admin():
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <p>🏫 School Invite Code</p>
            <div class="invite-code">{sanitize(school.get('invite_code', ''))}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:15px;background:rgba(255,255,255,0.08);border-radius:12px;margin-bottom:15px;">
            <h4>{sanitize(user.get('name', ''))}</h4>
            <p style="color:#d4af37;">{sanitize(user.get('role', '').upper())}</p>
            <p style="font-size:0.8em;">{sanitize(user.get('department', ''))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Theme
        with st.expander("🎨 Theme"):
            keys = list(WALLPAPERS.keys())
            idx = keys.index(st.session_state.wallpaper) if st.session_state.wallpaper in keys else 0
            wp = st.selectbox("Wallpaper:", keys, index=idx)
            if wp != st.session_state.wallpaper:
                st.session_state.wallpaper = wp
                st.rerun()
            
            with st.form("upload_wp", clear_on_submit=True):
                wp_name = st.text_input("Name")
                wp_url = st.text_input("URL")
                if st.form_submit_button("Add"):
                    if wp_name and wp_url:
                        try:
                            conn = get_db()
                            conn.execute("INSERT INTO wallpapers (school_name, name, url, uploaded_by) VALUES (?, ?, ?, ?)",
                                       (school.get('name', ''), wp_name, wp_url, user.get('name', '')))
                            conn.commit()
                            conn.close()
                            st.success("Added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        st.markdown("---")
        
        # Navigation
        nav_items = [
            ("📊 MAIN", [("📊 Dashboard", "dashboard")]),
            ("📖 LIBRARY", [
                ("📖 Book Issuing", "bookIssuing"),
                ("👤 Lend Book", "individualLending"),
                ("↩️ Returns", "return"),
                ("📋 Borrowed", "borrowedLog"),
                ("📚 Catalog", "bookCatalog"),
            ]),
            ("🪑 RESOURCES", [
                ("🪑 Furniture", "furnitureAllocation"),
                ("📱 QR Codes", "qr"),
                ("📅 Reservations", "reservations"),
            ]),
            ("👥 PEOPLE", [
                ("👥 Members", "memberManagement"),
                ("📋 Classes", "classListManager"),
            ]),
            ("💬 COMMUNICATION", [
                ("💬 Private Chat", "chat"),
                ("📢 Announcements", "announcements"),
                ("📄 Documents", "documents"),
            ]),
            ("📈 TOOLS", [
                ("🔍 Overview", "systemOverview"),
                ("📝 Audit Log", "auditLog"),
                ("📈 Reports", "reports"),
            ]),
        ]
        
        if is_admin():
            nav_items.append(("⚙️ ADMIN", [
                ("⚙️ Settings", "settings"),
                ("🗄️ Database", "databaseManager"),
            ]))
        
        for category, items in nav_items:
            with st.expander(category, expanded=False):
                for label, section in items:
                    if st.button(label, use_container_width=True, key=f"nav_{section}"):
                        st.session_state.section = section
                        st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.user = None
            st.session_state.school = None
            st.session_state.page = 'startup'
            st.rerun()
    
    # Main content
    section = st.session_state.section
    
    if section == 'dashboard': render_dashboard()
    elif section == 'bookIssuing': render_book_issuing()
    elif section == 'individualLending': render_individual_lending()
    elif section == 'return': render_returns()
    elif section == 'borrowedLog': render_borrowed()
    elif section == 'bookCatalog': render_catalog()
    elif section == 'furnitureAllocation': render_furniture()
    elif section == 'qr': render_qr()
    elif section == 'reservations': render_reservations()
    elif section == 'memberManagement': render_members()
    elif section == 'classListManager': render_classes()
    elif section == 'chat': render_chat()
    elif section == 'announcements': render_announcements()
    elif section == 'documents': render_documents()
    elif section == 'systemOverview': render_overview()
    elif section == 'auditLog': render_audit()
    elif section == 'reports': render_reports()
    elif section == 'settings': render_settings()
    elif section == 'databaseManager': render_db_manager()

# ============ RENDER FUNCTIONS ============
def render_dashboard():
    books = load_data('books')
    borrowed = load_data('borrowed')
    members = load_data('members')
    
    total_books = sum(b.get('quantity', 0) for b in books)
    active = len([b for b in borrowed if not b.get('returned')])
    
    st.markdown('<div class="glass-card"><h2>📊 Dashboard</h2>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{total_books}</div><div class="stat-label">Total Books</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{active}</div><div class="stat-label">Active Loans</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{total_books - active}</div><div class="stat-label">Available</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{len(members)}</div><div class="stat-label">Members</div></div>', unsafe_allow_html=True)
    
    st.markdown('<h3>⚡ Quick Actions</h3>', unsafe_allow_html=True)
    ca, cb, cc, cd = st.columns(4)
    with ca:
        if st.button("📖 Issue Books", use_container_width=True): 
            st.session_state.section = 'bookIssuing'
            st.rerun()
    with cb:
        if st.button("↩️ Returns", use_container_width=True): 
            st.session_state.section = 'return'
            st.rerun()
    with cc:
        if st.button("💬 Chat", use_container_width=True): 
            st.session_state.section = 'chat'
            st.rerun()
    with cd:
        if st.button("📊 Reports", use_container_width=True): 
            st.session_state.section = 'reports'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_book_issuing():
    books = load_data('books')
    classes = load_data('classes')
    
    st.markdown('<div class="glass-card"><h2>📖 Book Issuing to Class</h2>', unsafe_allow_html=True)
    
    if not books:
        st.warning("No books in catalog. Add books first.")
        if st.button("Go to Catalog"):
            st.session_state.section = 'bookCatalog'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    book_opts = [b['title'] for b in books if b.get('available', 0) > 0]
    if not book_opts:
        st.warning("No books available. All books are currently borrowed.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    c1, c2 = st.columns(2)
    with c1:
        book = st.selectbox("Book:", book_opts)
    with c2:
        class_opts = [c['name'] for c in classes] if classes else ["No classes"]
        cls = st.selectbox("Class:", class_opts)
    
    c3, c4 = st.columns(2)
    with c3: issue_date = st.date_input("Issue Date:", datetime.now())
    with c4: due_date = st.date_input("Due Date:", datetime.now() + timedelta(days=14))
    
    if st.button("📋 Load Students", use_container_width=True):
        if cls != "No classes":
            cd = next((c for c in classes if c['name'] == cls), None)
            if cd:
                students_str = cd.get('students', '[]')
                if isinstance(students_str, str):
                    try:
                        st.session_state.students = json.loads(students_str)
                    except:
                        st.session_state.students = []
                else:
                    st.session_state.students = students_str
                st.success(f"Loaded {len(st.session_state.students)} students!")
    
    if st.session_state.students:
        df = pd.DataFrame(st.session_state.students)
        cols = df.columns.tolist()
        ncol = cols[0] if cols else 'name'
        acol = cols[1] if len(cols) > 1 else 'adm'
        
        df['Book No'] = ""
        df['Issue'] = False
        edited = st.data_editor(df, use_container_width=True, key="bi_editor")
        
        if st.button("✅ Issue Books", use_container_width=True, type="primary"):
            count = 0
            conn = get_db()
            for _, row in edited.iterrows():
                if row.get('Issue') and row.get('Book No'):
                    try:
                        conn.execute(
                            "INSERT INTO borrowed (id, school_name, book_title, book_no, borrower_name, borrower_id, department, borrow_date, due_date, returned, issued_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                            (generate_code("BOR"), st.session_state.school.get('name', ''), book, str(row['Book No']),
                             str(row.get(ncol, '')), str(row.get(acol, '')), 
                             st.session_state.user.get('department', ''),
                             issue_date.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'),
                             st.session_state.user.get('name', ''))
                        )
                        conn.execute("UPDATE books SET available = available - 1 WHERE school_name = ? AND title = ? AND available > 0",
                                    (st.session_state.school.get('name', ''), book))
                        count += 1
                    except Exception as e:
                        st.warning(f"Error: {e}")
            
            conn.commit()
            conn.close()
            
            if count > 0:
                add_audit('Books Issued', f"{count} copies of '{book}' to {cls}")
                st.success(f"✅ Issued {count} books!")
                st.session_state.students = None
                time.sleep(1)
                st.rerun()
            else:
                st.warning("No books were issued. Check Book No and Issue checkbox.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_individual_lending():
    books = load_data('books')
    st.markdown('<div class="glass-card"><h2>👤 Individual Book Lending</h2>', unsafe_allow_html=True)
    
    book_opts = [b['title'] for b in books if b.get('available', 0) > 0]
    if not book_opts:
        st.warning("No books available.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    with st.form("ind_lend"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Borrower Name")
            adm = st.text_input("ID/ADM")
            dept = st.text_input("Department")
        with c2:
            book = st.selectbox("Book:", book_opts)
            book_no = st.text_input("Book Number")
        
        c3, c4 = st.columns(2)
        with c3: issue_date = st.date_input("Issue:", datetime.now())
        with c4: due_date = st.date_input("Due:", datetime.now() + timedelta(days=14))
        
        if st.form_submit_button("📖 Lend Book", use_container_width=True, type="primary"):
            if name and book and book_no:
                try:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO borrowed (id, school_name, book_title, book_no, borrower_name, borrower_id, department, borrow_date, due_date, returned, issued_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                        (generate_code("BOR"), st.session_state.school.get('name', ''), book, book_no,
                         name, adm, dept, issue_date.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'),
                         st.session_state.user.get('name', ''))
                    )
                    conn.execute("UPDATE books SET available = available - 1 WHERE school_name = ? AND title = ? AND available > 0",
                                (st.session_state.school.get('name', ''), book))
                    conn.commit()
                    conn.close()
                    add_audit('Lend Book', f"{name} - '{book}' (#{book_no})")
                    st.success("✅ Book lent successfully!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please fill in Name, Book, and Book Number!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_returns():
    st.markdown('<div class="glass-card"><h2>↩️ Return Items</h2>', unsafe_allow_html=True)
    
    search = st.text_input("🔍 Search by name, ID, or book number")
    
    if st.button("🔍 Search", use_container_width=True) or search:
        borrowed = load_data('borrowed')
        active = [b for b in borrowed if not b.get('returned') and (
            search.lower() in str(b.get('borrower_name', '')).lower() or 
            search.lower() in str(b.get('borrower_id', '')).lower() or 
            search.lower() in str(b.get('book_no', '')).lower()
        )]
        
        if active:
            st.markdown(f"### Found {len(active)} active loan(s)")
            for item in active:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1: 
                    st.write(f"**{sanitize(item.get('borrower_name', ''))}** - {sanitize(item.get('book_title', ''))} (#{sanitize(item.get('book_no', ''))})")
                with c2: 
                    st.write(f"Due: {sanitize(item.get('due_date', ''))}")
                with c3:
                    if st.button("↩️ Return", key=f"ret_{item['id']}"):
                        try:
                            conn = get_db()
                            today = datetime.now().strftime('%Y-%m-%d')
                            conn.execute("UPDATE borrowed SET returned = 1, return_date = ? WHERE id = ?", (today, item['id']))
                            conn.execute("UPDATE books SET available = available + 1 WHERE school_name = ? AND title = ?",
                                        (st.session_state.school.get('name', ''), item['book_title']))
                            
                            # Calculate fine
                            due_str = item.get('due_date', '')
                            if due_str:
                                try:
                                    due = datetime.strptime(due_str, '%Y-%m-%d')
                                    if datetime.now() > due:
                                        days = (datetime.now() - due).days
                                        fine = round(days * 0.50, 2)
                                        conn.execute("UPDATE borrowed SET fine = ? WHERE id = ?", (fine, item['id']))
                                        st.warning(f"⚠️ Overdue by {days} days. Fine: ${fine:.2f}")
                                except:
                                    pass
                            
                            conn.commit()
                            conn.close()
                            add_audit('Book Returned', f"{item.get('borrower_name', '')} returned '{item.get('book_title', '')}'")
                            st.success("✅ Book returned!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                st.divider()
        else:
            st.info("No matching active loans found.")
    
    # Also show furniture returns
    st.markdown("---")
    st.markdown("### 🪑 Furniture Returns")
    
    fur_search = st.text_input("🔍 Search furniture by name, ID, or item number")
    
    if st.button("🔍 Search Furniture", use_container_width=True) or fur_search:
        furniture = load_data('furniture')
        active_fur = [f for f in furniture if not f.get('returned') and (
            fur_search.lower() in str(f.get('assigned_to', '')).lower() or 
            fur_search.lower() in str(f.get('item_number', '')).lower()
        )]
        
        if active_fur:
            for item in active_fur:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1: 
                    st.write(f"**{sanitize(item.get('assigned_to', ''))}** - {sanitize(item.get('item_type', ''))}: {sanitize(item.get('item_number', ''))}")
                with c2: 
                    st.write(f"Date: {sanitize(item.get('assigned_date', ''))}")
                with c3:
                    if st.button("↩️ Return", key=f"retf_{item['id']}"):
                        try:
                            conn = get_db()
                            conn.execute("UPDATE furniture SET returned = 1 WHERE id = ?", (item['id'],))
                            conn.commit()
                            conn.close()
                            st.success("✅ Returned!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                st.divider()
        else:
            st.info("No matching active furniture found.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_borrowed():
    st.markdown('<div class="glass-card"><h2>📋 Borrowed Books</h2>', unsafe_allow_html=True)
    
    filt = st.radio("Filter:", ["All", "Active", "Overdue", "Returned"], horizontal=True)
    
    borrowed = load_data('borrowed')
    today = datetime.now().strftime('%Y-%m-%d')
    
    if filt == "Active":
        data = [b for b in borrowed if not b.get('returned')]
    elif filt == "Overdue":
        data = [b for b in borrowed if not b.get('returned') and b.get('due_date', '2000-01-01') < today]
    elif filt == "Returned":
        data = [b for b in borrowed if b.get('returned')]
    else:
        data = borrowed
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        if st.button("📥 Export to Excel", use_container_width=True):
            try:
                buf = BytesIO()
                df.to_excel(buf, index=False, engine='openpyxl')
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="borrowed.xlsx">📥 Click to Download</a>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Export error: {e}")
    else:
        st.info("No records found")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_catalog():
    st.markdown('<div class="glass-card"><h2>📚 Book Catalog</h2>', unsafe_allow_html=True)
    
    with st.form("add_book"):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1: title = st.text_input("Title")
        with c2: author = st.text_input("Author")
        with c3: category = st.selectbox("Category", ["Textbook", "Novel", "Reference", "Magazine", "Other"])
        with c4: qty = st.number_input("Quantity", 1, 100, 1)
        
        if st.form_submit_button("📖 Add Book", use_container_width=True):
            if title:
                try:
                    conn = get_db()
                    existing = conn.execute(
                        "SELECT * FROM books WHERE school_name = ? AND LOWER(title) = LOWER(?)",
                        (st.session_state.school.get('name', ''), title)
                    ).fetchone()
                    
                    if existing:
                        conn.execute("UPDATE books SET quantity = quantity + ?, available = available + ? WHERE id = ?",
                                    (qty, qty, existing['id']))
                    else:
                        conn.execute(
                            "INSERT INTO books (school_name, title, author, category, quantity, available, added_by, added_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (st.session_state.school.get('name', ''), title, author, category, qty, qty,
                             st.session_state.user.get('name', ''), datetime.now().strftime("%Y-%m-%d"))
                        )
                    conn.commit()
                    conn.close()
                    add_audit('Book Added', f"{title} (Qty: {qty})")
                    st.success("✅ Book added/updated!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    books = load_data('books')
    if books:
        for b in books:
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            with c1: st.write(f"📖 **{sanitize(b.get('title', ''))}**")
            with c2: st.write(sanitize(b.get('author', '-')))
            with c3: st.write(sanitize(b.get('category', '-')))
            with c4: st.write(f"Qty: {b.get('quantity', 0)} | Avail: {b.get('available', 0)}")
            with c5:
                if is_admin() and st.button("🗑️", key=f"delb_{b['id']}"):
                    try:
                        conn = get_db()
                        conn.execute("DELETE FROM books WHERE id = ?", (b['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Deleted!")
                        time.sleep(0.3)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            st.divider()
    else:
        st.info("No books in catalog")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_furniture():
    classes = load_data('classes')
    st.markdown('<div class="glass-card"><h2>🪑 Furniture Allocation</h2>', unsafe_allow_html=True)
    
    if not classes:
        st.warning("No classes available. Import class lists first.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    cls = st.selectbox("Class:", [c['name'] for c in classes])
    
    c1, c2 = st.columns(2)
    with c1:
        chair_prefix = st.text_input("Chair Prefix:", "CH-")
        chair_start = st.number_input("Chair Start:", 1, 1000, 1)
        chair_end = st.number_input("Chair End:", 1, 1000, chair_start)
    with c2:
        locker_prefix = st.text_input("Locker Prefix:", "LK-")
        locker_start = st.number_input("Locker Start:", 1, 1000, 1)
        locker_end = st.number_input("Locker End:", 1, 1000, locker_start)
    
    if st.button("📋 Load Class", use_container_width=True):
        cd = next((c for c in classes if c['name'] == cls), None)
        if cd:
            students_str = cd.get('students', '[]')
            if isinstance(students_str, str):
                try:
                    st.session_state.fur_students = json.loads(students_str)
                except:
                    st.session_state.fur_students = []
            else:
                st.session_state.fur_students = students_str
            st.success(f"Loaded {len(st.session_state.fur_students)} students!")
    
    if st.session_state.fur_students:
        df = pd.DataFrame(st.session_state.fur_students)
        cols = df.columns.tolist()
        ncol = cols[0] if cols else 'name'
        acol = cols[1] if len(cols) > 1 else 'adm'
        
        df['Chair'] = ""
        df['Locker'] = ""
        df['Allocate'] = False
        edited = st.data_editor(df, use_container_width=True, key="fur_editor")
        
        if st.button("✅ Assign Furniture", use_container_width=True, type="primary"):
            count = 0
            conn = get_db()
            for _, row in edited.iterrows():
                if row.get('Allocate'):
                    chair_no = str(row.get('Chair', ''))
                    locker_no = str(row.get('Locker', ''))
                    
                    if chair_no:
                        try:
                            conn.execute(
                                "INSERT INTO furniture (id, school_name, item_type, item_number, assigned_to, department, assigned_date, returned) VALUES (?, ?, 'chair', ?, ?, ?, ?, 0)",
                                (generate_code("FUR"), st.session_state.school.get('name', ''), chair_no,
                                 str(row.get(acol, '')), st.session_state.user.get('department', ''), datetime.now().strftime('%Y-%m-%d'))
                            )
                            count += 1
                        except:
                            pass
                    
                    if locker_no:
                        try:
                            conn.execute(
                                "INSERT INTO furniture (id, school_name, item_type, item_number, assigned_to, department, assigned_date, returned) VALUES (?, ?, 'locker', ?, ?, ?, ?, 0)",
                                (generate_code("FUR"), st.session_state.school.get('name', ''), locker_no,
                                 str(row.get(acol, '')), st.session_state.user.get('department', ''), datetime.now().strftime('%Y-%m-%d'))
                            )
                            count += 1
                        except:
                            pass
            conn.commit()
            conn.close()
            
            if count > 0:
                add_audit('Furniture Allocated', f"{count} items to {cls}")
                st.success(f"✅ Allocated {count} items!")
                st.session_state.fur_students = None
                time.sleep(1)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_qr():
    st.markdown('<div class="glass-card"><h2>📱 QR Codes</h2>', unsafe_allow_html=True)
    
    qr_type = st.selectbox("Type:", ["book", "chair", "locker"])
    c1, c2 = st.columns(2)
    with c1: start = st.number_input("Start:", 1, 10000, 1)
    with c2: end = st.number_input("End:", 1, 10000, min(start, start+9))
    
    if st.button("Generate QR Codes", use_container_width=True):
        try:
            cols = st.columns(4)
            for i in range(start, min(end + 1, start + 20)):
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(f"{qr_type}-{i}")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                with cols[(i - start) % 4]:
                    st.image(buf, caption=f"{qr_type}: {i}", width=150)
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reservations():
    st.markdown('<div class="glass-card"><h2>📅 Book Reservations</h2>', unsafe_allow_html=True)
    
    books = load_data('books')
    book_opts = [b['title'] for b in books]
    
    with st.form("reserve"):
        book = st.selectbox("Book:", book_opts if book_opts else ["No books"])
        needed = st.date_input("Needed By:", datetime.now() + timedelta(days=7))
        priority = st.selectbox("Priority:", ["Normal", "Urgent", "Low"])
        
        if st.form_submit_button("📅 Reserve", use_container_width=True):
            if book and book != "No books":
                try:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO reservations (id, school_name, book_title, reserved_by, department, reservation_date, needed_by, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')",
                        (generate_code("RES"), st.session_state.school.get('name', ''), book,
                         st.session_state.user.get('name', ''), st.session_state.user.get('department', ''),
                         datetime.now().strftime('%Y-%m-%d'), needed.strftime('%Y-%m-%d'))
                    )
                    conn.commit()
                    conn.close()
                    add_audit('Reservation', f"{book} reserved by {st.session_state.user.get('name', '')}")
                    st.success("✅ Book reserved!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    reservations = load_data('reservations')
    if reservations:
        st.markdown("### Current Reservations")
        for r in reservations:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1: st.write(f"📅 **{sanitize(r.get('book_title', ''))}** - {sanitize(r.get('reserved_by', ''))}")
            with c2: st.write(f"Needed: {sanitize(r.get('needed_by', ''))}")
            with c3: st.write(sanitize(r.get('status', 'Pending')))
            st.divider()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_members():
    st.markdown('<div class="glass-card"><h2>👥 Members</h2>', unsafe_allow_html=True)
    
    with st.form("add_member"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: name = st.text_input("Name")
        with c2: dept = st.text_input("Department")
        with c3: phone = st.text_input("Phone")
        with c4: email = st.text_input("Email")
        
        if st.form_submit_button("➕ Add Member", use_container_width=True):
            if name:
                try:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO members (id, school_name, name, department, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                        (generate_code("MEM"), st.session_state.school.get('name', ''), name, dept, phone, email)
                    )
                    conn.commit()
                    conn.close()
                    add_audit('Member Added', name)
                    st.success("✅ Member added!")
                    time.sleep(0.3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    members = load_data('members')
    if members:
        for m in members:
            c1, c2 = st.columns([4, 1])
            with c1: st.write(f"👤 **{sanitize(m.get('name', ''))}** ({sanitize(m.get('department', '-'))})")
            with c2:
                if is_admin() and st.button("🗑️", key=f"delm_{m['id']}"):
                    try:
                        conn = get_db()
                        conn.execute("DELETE FROM members WHERE id = ?", (m['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Deleted!")
                        time.sleep(0.3)
                        st.rerun()
                    except:
                        pass
            st.divider()
    else:
        st.info("No members added")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_classes():
    st.markdown('<div class="glass-card"><h2>📋 Class Lists</h2>', unsafe_allow_html=True)
    
    uploaded = st.file_uploader("📥 Import Excel File", type=['xlsx', 'xls'])
    if uploaded:
        try:
            df = pd.read_excel(uploaded)
            st.write("Preview:")
            st.dataframe(df.head(), use_container_width=True)
            cls_name = st.text_input("Class Name:")
            
            if st.button("💾 Save Class", use_container_width=True):
                if cls_name:
                    students = [{str(col): str(row[col]) if not pd.isna(row[col]) else "" for col in df.columns} for _, row in df.iterrows()]
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO classes (school_name, name, students, created_by, created) VALUES (?, ?, ?, ?, ?)",
                        (st.session_state.school.get('name', ''), cls_name, json.dumps(students),
                         st.session_state.user.get('name', ''), datetime.now().strftime("%Y-%m-%d"))
                    )
                    conn.commit()
                    conn.close()
                    add_audit('Class Added', f"{cls_name} ({len(students)} students)")
                    st.success(f"✅ Saved '{cls_name}' with {len(students)} students!")
                    time.sleep(0.5)
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    classes = load_data('classes')
    if classes:
        for c in classes:
            students = c.get('students', '[]')
            if isinstance(students, str):
                try:
                    students = json.loads(students)
                except:
                    students = []
            with st.expander(f"📋 {sanitize(c.get('name', ''))} ({len(students)} students)"):
                if students:
                    st.dataframe(pd.DataFrame(students), use_container_width=True)
                if is_admin() and st.button("🗑️ Delete", key=f"delc_{c['id']}"):
                    try:
                        conn = get_db()
                        conn.execute("DELETE FROM classes WHERE id = ?", (c['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Deleted!")
                        time.sleep(0.3)
                        st.rerun()
                    except:
                        pass
    else:
        st.info("No class lists saved")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat():
    users = load_data('users')
    user = st.session_state.user
    
    st.markdown('<div class="glass-card"><h2>💬 Private Chat</h2>', unsafe_allow_html=True)
    
    others = [u for u in users if u.get('email') != user.get('email')]
    
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown("### Staff")
        for u in others:
            if st.button(f"{u.get('name', '')} ({u.get('department', '')})", key=f"cht_{u['email']}", use_container_width=True):
                st.session_state.chat_with = u['email']
                st.rerun()
    
    with c2:
        if st.session_state.chat_with:
            cu = next((u for u in users if u.get('email') == st.session_state.chat_with), None)
            if cu:
                st.markdown(f"### 💬 Chat with {sanitize(cu.get('name', ''))}")
                
                msgs = load_data('chat_messages')
                chat_msgs = [m for m in msgs if (
                    (m.get('from_email') == user.get('email') and m.get('to_email') == cu.get('email')) or 
                    (m.get('from_email') == cu.get('email') and m.get('to_email') == user.get('email'))
                )]
                
                for m in sorted(chat_msgs, key=lambda x: x.get('timestamp', '')):
                    is_mine = m.get('from_email') == user.get('email')
                    bg = "rgba(233,69,96,0.4)" if is_mine else "rgba(255,255,255,0.15)"
                    align = "flex-end" if is_mine else "flex-start"
                    
                    st.markdown(f"""
                    <div style="display:flex;justify-content:{align};margin:5px 0;">
                        <div style="background:{bg};padding:10px 16px;border-radius:16px;max-width:70%;color:#FFF;">
                            <strong>{sanitize(m.get('from_name', ''))}:</strong> {sanitize(m.get('message', ''))}
                            <br><small>{sanitize(m.get('timestamp', '')[:16])}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Emoji picker
                with st.expander("😀 Emoji"):
                    cols = st.columns(10)
                    for i, emoji in enumerate(EMOJIS):
                        with cols[i % 10]:
                            if st.button(emoji, key=f"emo_{i}"):
                                st.session_state.emoji = emoji
                
                with st.form("send_msg", clear_on_submit=True):
                    placeholder = f"Type a message... {st.session_state.emoji or ''}"
                    msg = st.text_input("Message", placeholder=placeholder, label_visibility="collapsed")
                    
                    if st.form_submit_button("📤 Send"):
                        final_msg = msg
                        if st.session_state.emoji:
                            final_msg = f"{msg} {st.session_state.emoji}"
                        
                        if final_msg.strip():
                            try:
                                conn = get_db()
                                conn.execute(
                                    "INSERT INTO chat_messages (id, school_name, from_email, from_name, to_email, department, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (generate_code("MSG"), st.session_state.school.get('name', ''),
                                     user.get('email', ''), user.get('name', ''),
                                     cu.get('email', ''), user.get('department', ''),
                                     final_msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                )
                                conn.commit()
                                conn.close()
                                st.session_state.emoji = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_announcements():
    st.markdown('<div class="glass-card"><h2>📢 Announcements</h2>', unsafe_allow_html=True)
    
    with st.form("announce"):
        title = st.text_input("Title")
        content = st.text_area("Content", height=100)
        priority = st.selectbox("Priority:", ["Normal", "Urgent", "Low"])
        dept = st.selectbox("Department:", ["All", "Sciences", "Mathematics", "Languages", "Humanities", "Other"])
        
        if st.form_submit_button("📢 Post Announcement", use_container_width=True):
            if title and content:
                try:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO announcements (id, school_name, title, content, priority, posted_by, department, posted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (generate_code("ANN"), st.session_state.school.get('name', ''), title, content,
                         priority, st.session_state.user.get('name', ''), dept,
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    conn.commit()
                    conn.close()
                    add_audit('Announcement', title)
                    st.success("✅ Posted!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    announcements = load_data('announcements')
    if announcements:
        for a in reversed(announcements):
            color = "#e94560" if a.get('priority') == 'Urgent' else "#FFD700" if a.get('priority') == 'Normal' else "#888"
            st.markdown(f"""
            <div style="border-left:4px solid {color};background:rgba(255,255,255,0.08);padding:15px;border-radius:8px;margin:10px 0;">
                <strong style="color:{color};">{'🔴' if a.get('priority') == 'Urgent' else '🟡' if a.get('priority') == 'Normal' else '🟢'} {sanitize(a.get('title', ''))}</strong>
                <br>{sanitize(a.get('content', ''))}
                <br><small>By {sanitize(a.get('posted_by', ''))} | {sanitize(a.get('department', ''))} | {sanitize(a.get('posted_at', '')[:16])}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No announcements")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_documents():
    st.markdown('<div class="glass-card"><h2>📄 Documents Repository</h2>', unsafe_allow_html=True)
    
    uploaded = st.file_uploader("📤 Upload Document", type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'pptx', 'jpg', 'png'])
    if uploaded:
        subject = st.text_input("Subject/Topic:")
        if st.button("📤 Upload", use_container_width=True):
            try:
                file_data = base64.b64encode(uploaded.read()).decode()
                conn = get_db()
                conn.execute(
                    "INSERT INTO documents (id, school_name, title, file_type, file_data, subject, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (generate_code("DOC"), st.session_state.school.get('name', ''), uploaded.name,
                     uploaded.type, file_data, subject or 'General',
                     st.session_state.user.get('name', ''), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                add_audit('Document Uploaded', uploaded.name)
                st.success("✅ Document uploaded!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    docs = load_data('documents')
    if docs:
        for d in docs:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05);padding:10px;border-radius:8px;margin:5px 0;">
                    📄 **{sanitize(d.get('title', ''))}** ({sanitize(d.get('subject', '-'))})
                    <br><small>By {sanitize(d.get('uploaded_by', ''))} | {sanitize(d.get('uploaded_at', '')[:16])}</small>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("📥 Download", key=f"dld_{d['id']}"):
                    try:
                        b64 = d.get('file_data', '')
                        mime = d.get('file_type', 'application/octet-stream')
                        name = d.get('title', 'document')
                        st.markdown(f'<a href="data:{mime};base64,{b64}" download="{name}">Click to download</a>', unsafe_allow_html=True)
                    except:
                        pass
            st.divider()
    else:
        st.info("No documents uploaded")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_overview():
    st.markdown('<div class="glass-card"><h2>🔍 System Overview</h2>', unsafe_allow_html=True)
    
    books = load_data('books')
    borrowed = load_data('borrowed')
    members = load_data('members')
    users = load_data('users')
    reservations = load_data('reservations')
    documents = load_data('documents')
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📚 Total Books", sum(b.get('quantity', 0) for b in books))
    with c2: st.metric("📖 Active Loans", len([b for b in borrowed if not b.get('returned')]))
    with c3: st.metric("👥 Staff", len(users))
    
    c4, c5, c6 = st.columns(3)
    with c4: st.metric("👤 Members", len(members))
    with c5: st.metric("📅 Reservations", len(reservations))
    with c6: st.metric("📄 Documents", len(documents))
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_audit():
    if not is_admin():
        st.error("🔒 Admin access required!")
        return
    
    st.markdown('<div class="glass-card"><h2>📝 Audit Log</h2>', unsafe_allow_html=True)
    
    audit = load_data('audit_log')
    if audit:
        st.dataframe(pd.DataFrame(list(reversed(audit))), use_container_width=True)
    else:
        st.info("No audit entries")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reports():
    st.markdown('<div class="glass-card"><h2>📈 Reports</h2>', unsafe_allow_html=True)
    
    rtype = st.selectbox("Report Type:", ["Books Overview", "Overdue Analysis", "Department Usage"])
    
    if st.button("📊 Generate Report", use_container_width=True):
        borrowed = load_data('borrowed')
        
        if rtype == "Books Overview":
            if borrowed:
                df = pd.DataFrame(borrowed)
                counts = df['returned'].value_counts()
                fig = px.bar(
                    x=['Active', 'Returned'], 
                    y=[counts.get(0, 0), counts.get(1, 0)],
                    color_discrete_sequence=['#e94560', '#28a745'],
                    title="Books by Status"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data")
        
        elif rtype == "Overdue Analysis":
            today = datetime.now().strftime('%Y-%m-%d')
            overdue = [b for b in borrowed if not b.get('returned') and b.get('due_date', '2000-01-01') < today]
            st.metric("🔴 Overdue Books", len(overdue))
            if overdue:
                st.dataframe(pd.DataFrame(overdue), use_container_width=True)
            else:
                st.success("No overdue books!")
        
        elif rtype == "Department Usage":
            depts = {}
            for b in borrowed:
                dept = b.get('department', 'Unknown')
                depts[dept] = depts.get(dept, 0) + 1
            if depts:
                fig = px.pie(
                    values=list(depts.values()), 
                    names=list(depts.keys()),
                    title="Borrowing by Department"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_settings():
    if not is_admin():
        st.error("🔒 Admin access required!")
        return
    
    st.markdown('<div class="glass-card"><h2>⚙️ Admin Settings</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👥 Staff Management", "💾 Data Management"])
    
    with tab1:
        st.subheader("Add Staff Member")
        with st.form("add_staff"):
            c1, c2, c3 = st.columns(3)
            with c1: email = st.text_input("Email")
            with c2: name = st.text_input("Name")
            with c3: dept = st.selectbox("Department", ["Sciences", "Mathematics", "Languages", "Humanities", "Technical", "Other"])
            pwd = st.text_input("Password (leave empty for auto-generate)")
            
            if st.form_submit_button("➕ Add Staff"):
                if email and name:
                    try:
                        conn = get_db()
                        exists = conn.execute(
                            "SELECT * FROM users WHERE email = ? AND school_name = ?",
                            (email, st.session_state.school.get('name', ''))
                        ).fetchone()
                        
                        if exists:
                            st.error("Email already exists!")
                        else:
                            pw = pwd if pwd else generate_code(8)
                            conn.execute(
                                "INSERT INTO users (email, school_name, name, code, password, role, department, joined, is_active) VALUES (?, ?, ?, ?, ?, 'teacher', ?, ?, 1)",
                                (email, st.session_state.school.get('name', ''), name,
                                 st.session_state.school.get('invite_code', ''), hash_password(pw),
                                 dept, datetime.now().strftime("%Y-%m-%d"))
                            )
                            conn.commit()
                            st.success(f"✅ Staff added! Password: `{pw}`")
                            time.sleep(1)
                            st.rerun()
                        conn.close()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        st.markdown("---")
        st.subheader("Current Staff")
        users = load_data('users')
        for u in users:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1: st.write(f"{'👑' if u.get('role')=='admin' else '👨‍🏫'} **{sanitize(u.get('name', ''))}** ({sanitize(u.get('role', ''))})")
            with c2:
                if u.get('email') != st.session_state.user.get('email') and u.get('role') != 'admin':
                    if st.button("👑 Promote", key=f"prom_{u['email']}"):
                        try:
                            conn = get_db()
                            conn.execute("UPDATE users SET role = 'admin' WHERE email = ? AND school_name = ?",
                                       (u['email'], st.session_state.school.get('name', '')))
                            conn.commit()
                            conn.close()
                            st.success("Promoted!")
                            time.sleep(0.3)
                            st.rerun()
                        except:
                            pass
            with c3:
                if u.get('email') != st.session_state.user.get('email'):
                    if st.button("🗑️ Deactivate", key=f"delu_{u['email']}"):
                        try:
                            conn = get_db()
                            conn.execute("UPDATE users SET is_active = 0 WHERE email = ? AND school_name = ?",
                                       (u['email'], st.session_state.school.get('name', '')))
                            conn.commit()
                            conn.close()
                            st.success("Deactivated!")
                            time.sleep(0.3)
                            st.rerun()
                        except:
                            pass
            st.divider()
    
    with tab2:
        st.subheader("Backup Database")
        if st.button("📥 Generate Backup", use_container_width=True):
            try:
                conn = get_db()
                tables = ['schools', 'users', 'books', 'borrowed', 'furniture', 'members', 'classes', 'reservations', 'chat_messages', 'announcements', 'documents', 'audit_log']
                backup = {}
                for t in tables:
                    data = conn.execute(f"SELECT * FROM {t} WHERE school_name = ?", (st.session_state.school.get('name', ''),)).fetchall()
                    backup[t] = [dict(row) for row in data]
                conn.close()
                
                b64 = base64.b64encode(json.dumps(backup, indent=2, default=str).encode()).decode()
                st.markdown(f'<a href="data:application/json;base64,{b64}" download="srms_backup.json">📥 Download Backup</a>', unsafe_allow_html=True)
                st.success("✅ Backup ready!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_db_manager():
    if not is_admin():
        st.error("🔒 Admin access required!")
        return
    
    st.markdown('<div class="glass-card"><h2>🗄️ Database Manager</h2>', unsafe_allow_html=True)
    st.warning("⚠️ Admin only - handle with care!")
    
    tables = ["schools", "users", "books", "borrowed", "furniture", "members", "classes", "reservations", "chat_messages", "announcements", "documents", "audit_log"]
    selected = st.selectbox("Select Table:", tables)
    
    try:
        conn = get_db()
        data = conn.execute(f"SELECT * FROM {selected} WHERE school_name = ?", (st.session_state.school.get('name', ''),)).fetchall()
        conn.close()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            st.dataframe(df, use_container_width=True, height=400)
            
            if st.button(f"📥 Export {selected}", use_container_width=True):
                buf = BytesIO()
                df.to_excel(buf, index=False, engine='openpyxl')
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{selected}.xlsx">📥 Download Excel</a>', unsafe_allow_html=True)
        else:
            st.info(f"No records in {selected}")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============ MAIN ============
def main():
    if st.session_state.page == 'startup':
        startup_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()

if __name__ == "__main__":
    main()

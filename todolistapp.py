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
from contextlib import contextmanager
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

# ============ DATABASE ============
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS schools (
            name TEXT PRIMARY KEY,
            address TEXT,
            admin_name TEXT,
            admin_email TEXT,
            invite_code TEXT,
            created TEXT
        );
        
        CREATE TABLE IF NOT EXISTS users (
            email TEXT,
            school_name TEXT,
            name TEXT,
            phone TEXT,
            staff_id TEXT,
            code TEXT,
            password TEXT,
            role TEXT DEFAULT 'teacher',
            department TEXT,
            joined TEXT,
            is_active INTEGER DEFAULT 1,
            PRIMARY KEY (email, school_name)
        );
        
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT,
            title TEXT,
            author TEXT,
            category TEXT,
            quantity INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1,
            added_by TEXT,
            added_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS borrowed (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            book_title TEXT,
            book_no TEXT,
            borrower_name TEXT,
            borrower_id TEXT,
            department TEXT,
            borrow_date TEXT,
            due_date TEXT,
            return_date TEXT,
            returned INTEGER DEFAULT 0,
            fine REAL DEFAULT 0,
            fine_paid INTEGER DEFAULT 0,
            issued_by TEXT
        );
        
        CREATE TABLE IF NOT EXISTS furniture (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            item_type TEXT,
            item_number TEXT,
            assigned_to TEXT,
            department TEXT,
            assigned_date TEXT,
            returned INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS members (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            name TEXT,
            department TEXT,
            phone TEXT,
            email TEXT
        );
        
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT,
            name TEXT,
            students TEXT,
            created_by TEXT,
            created TEXT
        );
        
        CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            book_title TEXT,
            reserved_by TEXT,
            department TEXT,
            reservation_date TEXT,
            needed_by TEXT,
            status TEXT DEFAULT 'Pending'
        );
        
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            from_email TEXT,
            from_name TEXT,
            to_email TEXT,
            department TEXT,
            message TEXT,
            timestamp TEXT,
            is_read INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS announcements (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            title TEXT,
            content TEXT,
            priority TEXT DEFAULT 'Normal',
            posted_by TEXT,
            department TEXT,
            posted_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            school_name TEXT,
            title TEXT,
            file_type TEXT,
            file_data TEXT,
            subject TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT,
            timestamp TEXT,
            user TEXT,
            action TEXT,
            details TEXT
        );
        
        CREATE TABLE IF NOT EXISTS wallpapers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT,
            name TEXT,
            url TEXT,
            uploaded_by TEXT
        );
        
        CREATE TABLE IF NOT EXISTS password_resets (
            email TEXT,
            school_name TEXT,
            token TEXT,
            expiry TEXT,
            used INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    conn.close()

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
    "Zen Garden": "https://images.unsplash.com/photo-1545389336-cf090694435e?w=1920",
    "Abstract": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920",
    "Geometric": "https://images.unsplash.com/photo-1557683311-eac922347aa1?w=1920",
    "Cyberpunk": "https://images.unsplash.com/photo-1557682257-2f9c97a8a469?w=1920",
    "Minimalist": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1920",
    "Starry Night": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920",
    "Clouds": "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1920",
    "Rainbow": "https://images.unsplash.com/photo-1511300636408-a63a89df3482?w=1920",
    "Anime": "https://images.unsplash.com/photo-1578632767115-351597cf1bfe?w=1920",
    "Fantasy": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920",
    "Tiger": "https://images.unsplash.com/photo-1549480017-d76466a4b7e8?w=1920",
    "Eagle": "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42?w=1920",
    "Dolphin": "https://images.unsplash.com/photo-1560272564-c83b66b1ad12?w=1920",
    "Lion": "https://images.unsplash.com/photo-1534188753412-3e26d0d618d6?w=1920",
    "Elephant": "https://images.unsplash.com/photo-1536599018102-9fa7e8cda74e?w=1920",
    "Butterfly": "https://images.unsplash.com/photo-1505063366573-38928ae5567e?w=1920",
}

# ============ EMOJIS ============
EMOJIS = ["😀", "😂", "😍", "🥰", "😘", "👍", "👎", "👏", "🙌", "💪", "❤️", "💙", "💚", "💛", "🧡", "💜", "🖤", "🤍", "⭐", "🌟", "✨", "🔥", "💯", "✅", "❌", "⚠️", "📚", "📖", "📝", "✏️", "🎓", "🏫", "🎯", "🔑", "🔒", "📢", "💡", "🎁", "🏆", "📅", "⏰", "☕", "🍕", "🚀", "✈️", "🏠", "🎨", "🎵", "⚽", "🏀"]

# ============ HELPER FUNCTIONS ============
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
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_log (school_name, timestamp, user, action, details) VALUES (?, ?, ?, ?, ?)",
            (st.session_state.school['name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             st.session_state.user['name'], action, details)
        )
        conn.commit()
        conn.close()
    except:
        pass

def load_data(table, filters=None):
    conn = get_db()
    try:
        query = f"SELECT * FROM {table} WHERE school_name = ?"
        params = [st.session_state.school['name']]
        
        if filters:
            for k, v in filters.items():
                query += f" AND {k} = ?"
                params.append(v)
        
        data = conn.execute(query, params).fetchall()
        return [dict(row) for row in data]
    except:
        return []
    finally:
        conn.close()

# ============ CSS ============
def get_css(wallpaper=None):
    bg = WALLPAPERS.get(wallpaper, "")
    bg_style = f"background-image: url('{bg}'); background-size: cover; background-position: center; background-attachment: fixed;" if bg else "background: linear-gradient(135deg, #0a0e27, #1a1f4e, #0f3460);"
    
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
        section[data-testid="stSidebar"] * {{ color: #FFFFFF !important; text-shadow: 0 1px 3px rgba(0,0,0,0.5); }}
        section[data-testid="stSidebar"] .stButton > button {{
            background: rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(212,175,55,0.3) !important;
            text-align: left !important;
            padding: 10px 15px !important;
            margin: 2px 0 !important;
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
if 'sidebar_collapsed' not in st.session_state: st.session_state.sidebar_collapsed = False

st.markdown(get_css(st.session_state.wallpaper), unsafe_allow_html=True)

# ============ AUTH PAGES ============
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
        if st.button("🔑 Login", use_container_width=True): st.session_state.action = 'login'; st.rerun()
    with c2:
        if st.button("📝 Sign Up", use_container_width=True): st.session_state.action = 'signup'; st.rerun()
    with c3:
        if st.button("🏫 Create School", use_container_width=True): st.session_state.action = 'create'; st.rerun()
    with c4:
        if st.button("🔐 Forgot Password", use_container_width=True): st.session_state.action = 'forgot'; st.rerun()
    
    if st.session_state.action:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if st.session_state.action == 'login': login_form()
        elif st.session_state.action == 'signup': signup_form()
        elif st.session_state.action == 'create': create_school_form()
        elif st.session_state.action == 'forgot': forgot_password_form()
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
            
            conn = get_db()
            sch = conn.execute("SELECT * FROM schools WHERE LOWER(name) = ? AND is_active = 1", (school.lower(),)).fetchone()
            if not sch:
                st.error("School not found!")
                conn.close()
                return
            
            usr = conn.execute("SELECT * FROM users WHERE LOWER(name) = ? AND school_name = ? AND code = ? AND is_active = 1",
                              (name.lower(), sch['name'], code.upper())).fetchone()
            conn.close()
            
            if not usr or not verify_password(password, usr['password']):
                st.error("Invalid credentials!")
                return
            
            st.session_state.user = dict(usr)
            st.session_state.school = dict(sch)
            st.session_state.page = 'dashboard'
            st.session_state.action = None
            st.rerun()

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
                st.error("Password must be at least 6 characters!")
                return
            
            conn = get_db()
            sch = conn.execute("SELECT * FROM schools WHERE LOWER(name) = ? AND is_active = 1", (school.lower(),)).fetchone()
            if not sch:
                st.error("School not found!")
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
            
            conn.execute("INSERT INTO users (email, school_name, name, phone, staff_id, code, password, role, department, joined) VALUES (?, ?, ?, ?, ?, ?, ?, 'teacher', ?, ?)",
                        (email, sch['name'], name, phone, f"STAFF-{generate_code(4)}", code.upper(), hash_password(password), dept, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            
            st.success("Registration successful! Please login.")
            st.session_state.action = 'login'
            time.sleep(1)
            st.rerun()

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
            
            conn = get_db()
            if conn.execute("SELECT * FROM schools WHERE LOWER(name) = ?", (name.lower(),)).fetchone():
                st.error("School already exists!")
                conn.close()
                return
            
            invite = generate_code()
            conn.execute("INSERT INTO schools (name, address, admin_name, admin_email, invite_code, created) VALUES (?, ?, ?, ?, ?, ?)",
                        (name, address, admin_name, admin_email, invite, datetime.now().strftime("%Y-%m-%d")))
            conn.execute("INSERT INTO users (email, school_name, name, phone, staff_id, code, password, role, joined) VALUES (?, ?, ?, ?, ?, ?, ?, 'admin', ?)",
                        (admin_email, name, admin_name, admin_phone, "ADMIN-001", invite, hash_password(password), datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            
            st.success(f"School created! Invite Code: {invite}")
            st.session_state.action = 'login'
            time.sleep(2)
            st.rerun()

def forgot_password_form():
    st.subheader("🔐 Reset Password")
    with st.form("forgot"):
        email = st.text_input("Registered Email")
        school = st.text_input("School Name")
        
        if st.form_submit_button("Send Reset Token", use_container_width=True):
            if not email or not school:
                st.error("All fields required!")
                return
            
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE email = ? AND LOWER(school_name) = ? AND is_active = 1",
                               (email, school.lower())).fetchone()
            if user:
                token = hashlib.sha256(os.urandom(32)).hexdigest()
                expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("INSERT OR REPLACE INTO password_resets (email, school_name, token, expiry, used) VALUES (?, ?, ?, ?, 0)",
                            (email, user['school_name'], token, expiry))
                conn.commit()
                st.success(f"Token generated! (Dev mode): {token[:16]}...")
                st.session_state.reset_email = email
                st.session_state.reset_school = user['school_name']
            else:
                st.error("User not found!")
            conn.close()
    
    if st.session_state.get('reset_email'):
        st.markdown("---")
        with st.form("reset"):
            token = st.text_input("Reset Token")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Reset Password", use_container_width=True):
                if new_pw != confirm_pw:
                    st.error("Passwords don't match!")
                    return
                
                conn = get_db()
                reset = conn.execute("SELECT * FROM password_resets WHERE email = ? AND school_name = ? AND token = ? AND expiry > ? AND used = 0",
                                    (st.session_state.reset_email, st.session_state.reset_school, token, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))).fetchone()
                if reset:
                    conn.execute("UPDATE users SET password = ? WHERE email = ? AND school_name = ?",
                                (hash_password(new_pw), st.session_state.reset_email, st.session_state.reset_school))
                    conn.execute("UPDATE password_resets SET used = 1 WHERE email = ? AND school_name = ?",
                                (st.session_state.reset_email, st.session_state.reset_school))
                    conn.commit()
                    st.success("Password reset! Please login.")
                    st.session_state.action = 'login'
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Invalid or expired token!")
                conn.close()

# ============ DASHBOARD ============
def dashboard_page():
    user = st.session_state.user
    school = st.session_state.school
    
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;margin-bottom:25px;">
        <h2>🏫 {school['name']}</h2>
        <p>👤 {user['name']} <span style="background:{'#e94560' if user['role']=='admin' else '#0f3460'};padding:4px 12px;border-radius:20px;">{user['role'].upper()}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    if is_admin():
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <p>🏫 School Invite Code</p>
            <div class="invite-code">{school['invite_code']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:15px;background:rgba(255,255,255,0.08);border-radius:12px;margin-bottom:15px;">
            <h4>{user['name']}</h4>
            <p style="color:#d4af37;">{user['role'].upper()}</p>
            <p style="font-size:0.8em;">{user.get('department', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Theme
        with st.expander("🎨 Theme"):
            idx = list(WALLPAPERS.keys()).index(st.session_state.wallpaper) if st.session_state.wallpaper in WALLPAPERS else 0
            wp = st.selectbox("Wallpaper:", list(WALLPAPERS.keys()), index=idx)
            if wp != st.session_state.wallpaper:
                st.session_state.wallpaper = wp
                st.rerun()
            
            # Upload custom wallpaper
            with st.form("upload_wp", clear_on_submit=True):
                wp_name = st.text_input("Name")
                wp_url = st.text_input("URL")
                if st.form_submit_button("Add Wallpaper"):
                    if wp_name and wp_url:
                        conn = get_db()
                        conn.execute("INSERT INTO wallpapers (school_name, name, url, uploaded_by) VALUES (?, ?, ?, ?)",
                                    (school['name'], wp_name, wp_url, user['name']))
                        conn.commit()
                        conn.close()
                        st.success("Wallpaper added!")
                        st.rerun()
        
        st.markdown("---")
        
        # Navigation with auto-collapse
        nav_items = [
            ("📊 MAIN", [
                ("📊 Dashboard", "dashboard"),
            ]),
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
                        # Auto-collapse sidebar after selection
                        st.session_state.sidebar_collapsed = True
                        st.rerun()
        
        st.markdown("---")
        
        # Collapse button
        if st.button("📌 Toggle Sidebar", use_container_width=True):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
            st.rerun()
        
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
    overdue = len([b for b in borrowed if not b.get('returned') and b.get('due_date', '2000-01-01') < datetime.now().strftime('%Y-%m-%d')])
    
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
        if st.button("📖 Issue Books", use_container_width=True): st.session_state.section = 'bookIssuing'; st.rerun()
    with cb:
        if st.button("↩️ Returns", use_container_width=True): st.session_state.section = 'return'; st.rerun()
    with cc:
        if st.button("💬 Chat", use_container_width=True): st.session_state.section = 'chat'; st.rerun()
    with cd:
        if st.button("📊 Reports", use_container_width=True): st.session_state.section = 'reports'; st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_book_issuing():
    books = load_data('books')
    classes = load_data('classes')
    
    st.markdown('<div class="glass-card"><h2>📖 Book Issuing</h2>', unsafe_allow_html=True)
    
    if not books:
        st.warning("No books in catalog. Add books first.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    c1, c2 = st.columns(2)
    with c1:
        book = st.selectbox("Book:", [b['title'] for b in books if b.get('available', 0) > 0])
    with c2:
        cls = st.selectbox("Class:", [c['name'] for c in classes])
    
    c3, c4 = st.columns(2)
    with c3: issue_date = st.date_input("Issue Date:", datetime.now())
    with c4: due_date = st.date_input("Due Date:", datetime.now() + timedelta(days=14))
    
    if st.button("📋 Load Students", use_container_width=True):
        cd = next((c for c in classes if c['name'] == cls), None)
        if cd:
            st.session_state.students = json.loads(cd.get('students', '[]')) if isinstance(cd.get('students'), str) else cd.get('students', [])
            st.success(f"Loaded {len(st.session_state.students)} students!")
    
    if 'students' in st.session_state and st.session_state.students:
        df = pd.DataFrame(st.session_state.students)
        cols = df.columns.tolist()
        ncol = cols[0] if cols else 'name'
        acol = cols[1] if len(cols) > 1 else 'adm'
        
        df['Book No'] = ""
        df['Issue'] = False
        edited = st.data_editor(df, use_container_width=True, key="bi_editor")
        
        if st.button("✅ Issue", use_container_width=True, type="primary"):
            count = 0
            conn = get_db()
            for _, row in edited.iterrows():
                if row.get('Issue') and row.get('Book No'):
                    conn.execute(
                        "INSERT INTO borrowed (id, school_name, book_title, book_no, borrower_name, borrower_id, department, borrow_date, due_date, returned, issued_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                        (generate_code("BOR"), st.session_state.school['name'], book, str(row['Book No']),
                         str(row[ncol]), str(row[acol]), st.session_state.user.get('department', ''),
                         issue_date.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'),
                         st.session_state.user['name'])
                    )
                    conn.execute("UPDATE books SET available = available - 1 WHERE school_name = ? AND title = ? AND available > 0",
                                (st.session_state.school['name'], book))
                    count += 1
            conn.commit()
            conn.close()
            
            if count > 0:
                add_audit('Books Issued', f"{count} copies of '{book}'")
                st.success(f"Issued {count} books!")
                del st.session_state.students
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_individual_lending():
    books = load_data('books')
    st.markdown('<div class="glass-card"><h2>👤 Individual Lending</h2>', unsafe_allow_html=True)
    
    with st.form("ind_lend"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name")
            adm = st.text_input("ID")
            dept = st.text_input("Department")
        with c2:
            book = st.selectbox("Book:", [b['title'] for b in books if b.get('available', 0) > 0])
            book_no = st.text_input("Book No")
        
        c3, c4 = st.columns(2)
        with c3: issue_date = st.date_input("Issue:", datetime.now())
        with c4: due_date = st.date_input("Due:", datetime.now() + timedelta(days=14))
        
        if st.form_submit_button("📖 Lend", use_container_width=True, type="primary"):
            if name and book and book_no:
                conn = get_db()
                conn.execute(
                    "INSERT INTO borrowed (id, school_name, book_title, book_no, borrower_name, borrower_id, department, borrow_date, due_date, returned, issued_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                    (generate_code("BOR"), st.session_state.school['name'], book, book_no,
                     name, adm, dept, issue_date.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'),
                     st.session_state.user['name'])
                )
                conn.execute("UPDATE books SET available = available - 1 WHERE school_name = ? AND title = ? AND available > 0",
                            (st.session_state.school['name'], book))
                conn.commit()
                conn.close()
                add_audit('Lend Book', f"{name} - '{book}'")
                st.success("Book lent!")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_returns():
    st.markdown('<div class="glass-card"><h2>↩️ Returns</h2>', unsafe_allow_html=True)
    
    search = st.text_input("🔍 Search")
    
    if st.button("Search", use_container_width=True) or search:
        borrowed = load_data('borrowed')
        active = [b for b in borrowed if not b['returned'] and (search.lower() in str(b.get('borrower_name', '')).lower() or search in str(b.get('book_no', '')))]
        
        if active:
            for item in active:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1: st.write(f"**{item['borrower_name']}** - {item['book_title']} (#{item['book_no']})")
                with c2: st.write(f"Due: {item['due_date']}")
                with c3:
                    if st.button("↩️ Return", key=f"ret_{item['id']}"):
                        conn = get_db()
                        conn.execute("UPDATE borrowed SET returned = 1, return_date = ? WHERE id = ?",
                                    (datetime.now().strftime('%Y-%m-%d'), item['id']))
                        conn.execute("UPDATE books SET available = available + 1 WHERE school_name = ? AND title = ?",
                                    (st.session_state.school['name'], item['book_title']))
                        
                        # Calculate fine
                        due = datetime.strptime(item['due_date'], '%Y-%m-%d')
                        if datetime.now() > due:
                            days = (datetime.now() - due).days
                            fine = days * 0.50
                            conn.execute("UPDATE borrowed SET fine = ? WHERE id = ?", (fine, item['id']))
                            st.warning(f"Overdue by {days} days. Fine: ${fine:.2f}")
                        
                        conn.commit()
                        conn.close()
                        add_audit('Book Returned', item['borrower_name'])
                        st.success("Returned!")
                        st.rerun()
                st.divider()
        else:
            st.info("No matching active loans")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_borrowed():
    st.markdown('<div class="glass-card"><h2>📋 Borrowed Books</h2>', unsafe_allow_html=True)
    
    filt = st.radio("Filter:", ["All", "Active", "Overdue", "Returned"], horizontal=True)
    
    borrowed = load_data('borrowed')
    today = datetime.now().strftime('%Y-%m-%d')
    
    if filt == "Active":
        data = [b for b in borrowed if not b['returned']]
    elif filt == "Overdue":
        data = [b for b in borrowed if not b['returned'] and b['due_date'] < today]
    elif filt == "Returned":
        data = [b for b in borrowed if b['returned']]
    else:
        data = borrowed
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        if st.button("📥 Export", use_container_width=True):
            buf = BytesIO()
            df.to_excel(buf, index=False)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="borrowed.xlsx">Download</a>', unsafe_allow_html=True)
    else:
        st.info("No records")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_catalog():
    st.markdown('<div class="glass-card"><h2>📚 Catalog</h2>', unsafe_allow_html=True)
    
    with st.form("add_book"):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1: title = st.text_input("Title")
        with c2: author = st.text_input("Author")
        with c3: category = st.selectbox("Category", ["Textbook", "Novel", "Reference", "Magazine", "Other"])
        with c4: qty = st.number_input("Qty", 1, 100, 1)
        
        if st.form_submit_button("Add Book", use_container_width=True):
            if title:
                conn = get_db()
                existing = conn.execute("SELECT * FROM books WHERE school_name = ? AND LOWER(title) = ?",
                                       (st.session_state.school['name'], title.lower())).fetchone()
                if existing:
                    conn.execute("UPDATE books SET quantity = quantity + ?, available = available + ? WHERE id = ?",
                                (qty, qty, existing['id']))
                else:
                    conn.execute("INSERT INTO books (school_name, title, author, category, quantity, available, added_by, added_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (st.session_state.school['name'], title, author, category, qty, qty, st.session_state.user['name'], datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                add_audit('Book Added', title)
                st.success("Book added!")
                st.rerun()
    
    books = load_data('books')
    if books:
        for b in books:
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            with c1: st.write(f"📖 **{b['title']}**")
            with c2: st.write(b.get('author', '-'))
            with c3: st.write(b.get('category', '-'))
            with c4: st.write(f"Qty: {b.get('quantity', 0)} | Avail: {b.get('available', 0)}")
            with c5:
                if is_admin() and st.button("🗑️", key=f"delb_{b['id']}"):
                    conn = get_db()
                    conn.execute("DELETE FROM books WHERE id = ?", (b['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.divider()
    else:
        st.info("No books in catalog")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_furniture():
    classes = load_data('classes')
    st.markdown('<div class="glass-card"><h2>🪑 Furniture Allocation</h2>', unsafe_allow_html=True)
    
    if not classes:
        st.warning("No classes available.")
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
            st.session_state.fur_students = json.loads(cd.get('students', '[]')) if isinstance(cd.get('students'), str) else cd.get('students', [])
            st.success(f"Loaded {len(st.session_state.fur_students)} students!")
    
    if 'fur_students' in st.session_state and st.session_state.fur_students:
        df = pd.DataFrame(st.session_state.fur_students)
        cols = df.columns.tolist()
        ncol = cols[0] if cols else 'name'
        acol = cols[1] if len(cols) > 1 else 'adm'
        
        df['Chair'] = ""
        df['Locker'] = ""
        df['Allocate'] = False
        edited = st.data_editor(df, use_container_width=True, key="fur_editor")
        
        if st.button("✅ Assign", use_container_width=True, type="primary"):
            count = 0
            conn = get_db()
            for _, row in edited.iterrows():
                if row.get('Allocate'):
                    conn.execute(
                        "INSERT INTO furniture (id, school_name, item_type, item_number, assigned_to, department, assigned_date, returned) VALUES (?, ?, 'chair', ?, ?, ?, ?, 0)",
                        (generate_code("FUR"), st.session_state.school['name'], str(row['Chair']),
                         str(row[acol]), st.session_state.user.get('department', ''), datetime.now().strftime('%Y-%m-%d'))
                    )
                    conn.execute(
                        "INSERT INTO furniture (id, school_name, item_type, item_number, assigned_to, department, assigned_date, returned) VALUES (?, ?, 'locker', ?, ?, ?, ?, 0)",
                        (generate_code("FUR"), st.session_state.school['name'], str(row['Locker']),
                         str(row[acol]), st.session_state.user.get('department', ''), datetime.now().strftime('%Y-%m-%d'))
                    )
                    count += 1
            conn.commit()
            conn.close()
            add_audit('Furniture Allocated', f"{count} items")
            st.success(f"Allocated {count} items!")
            del st.session_state.fur_students
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_qr():
    st.markdown('<div class="glass-card"><h2>📱 QR Codes</h2>', unsafe_allow_html=True)
    
    qr_type = st.selectbox("Type:", ["book", "chair", "locker"])
    c1, c2 = st.columns(2)
    with c1: start = st.number_input("Start:", 1, 10000, 1)
    with c2: end = st.number_input("End:", 1, 10000, start)
    
    if st.button("Generate", use_container_width=True):
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
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reservations():
    st.markdown('<div class="glass-card"><h2>📅 Book Reservations</h2>', unsafe_allow_html=True)
    
    books = load_data('books')
    
    with st.form("reserve"):
        book = st.selectbox("Book:", [b['title'] for b in books])
        needed = st.date_input("Needed By:", datetime.now() + timedelta(days=7))
        priority = st.selectbox("Priority:", ["Normal", "Urgent", "Low"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Reserve", use_container_width=True):
            conn = get_db()
            conn.execute(
                "INSERT INTO reservations (id, school_name, book_title, reserved_by, department, reservation_date, needed_by, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')",
                (generate_code("RES"), st.session_state.school['name'], book, st.session_state.user['name'],
                 st.session_state.user.get('department', ''), datetime.now().strftime('%Y-%m-%d'),
                 needed.strftime('%Y-%m-%d'))
            )
            conn.commit()
            conn.close()
            add_audit('Reservation', f"{book} reserved by {st.session_state.user['name']}")
            st.success("Book reserved!")
            st.rerun()
    
    reservations = load_data('reservations')
    if reservations:
        st.markdown("### Current Reservations")
        for r in reservations:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1: st.write(f"📅 **{r['book_title']}** - {r['reserved_by']}")
            with c2: st.write(f"Needed: {r['needed_by']}")
            with c3:
                if r['status'] == 'Pending':
                    if st.button("✅ Fulfill", key=f"ful_{r['id']}"):
                        conn = get_db()
                        conn.execute("UPDATE reservations SET status = 'Fulfilled', fulfilled_date = ? WHERE id = ?",
                                    (datetime.now().strftime('%Y-%m-%d'), r['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
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
        
        if st.form_submit_button("Add", use_container_width=True):
            if name:
                conn = get_db()
                conn.execute("INSERT INTO members (id, school_name, name, department, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                            (generate_code("MEM"), st.session_state.school['name'], name, dept, phone, email))
                conn.commit()
                conn.close()
                st.success("Member added!")
                st.rerun()
    
    members = load_data('members')
    if members:
        for m in members:
            c1, c2 = st.columns([4, 1])
            with c1: st.write(f"👤 **{m['name']}** ({m.get('department', '-')})")
            with c2:
                if is_admin() and st.button("🗑️", key=f"delm_{m['id']}"):
                    conn = get_db()
                    conn.execute("DELETE FROM members WHERE id = ?", (m['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.divider()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_classes():
    st.markdown('<div class="glass-card"><h2>📋 Classes</h2>', unsafe_allow_html=True)
    
    uploaded = st.file_uploader("Import Excel", type=['xlsx', 'xls'])
    if uploaded:
        df = pd.read_excel(uploaded)
        st.dataframe(df.head(), use_container_width=True)
        cls_name = st.text_input("Class Name:")
        
        if st.button("Save", use_container_width=True):
            if cls_name:
                students = [{col: str(row[col]) if not pd.isna(row[col]) else "" for col in df.columns} for _, row in df.iterrows()]
                conn = get_db()
                conn.execute("INSERT INTO classes (school_name, name, students, created_by, created) VALUES (?, ?, ?, ?, ?)",
                            (st.session_state.school['name'], cls_name, json.dumps(students), st.session_state.user['name'], datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                add_audit('Class Added', cls_name)
                st.success(f"Saved '{cls_name}'!")
                st.rerun()
    
    classes = load_data('classes')
    if classes:
        for c in classes:
            with st.expander(f"📋 {c['name']} ({len(json.loads(c.get('students', '[]')) if isinstance(c.get('students'), str) else c.get('students', []))} students)"):
                students = json.loads(c['students']) if isinstance(c['students'], str) else c['students']
                if students:
                    st.dataframe(pd.DataFrame(students), use_container_width=True)
                if is_admin() and st.button("Delete", key=f"delc_{c['id']}"):
                    conn = get_db()
                    conn.execute("DELETE FROM classes WHERE id = ?", (c['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat():
    users = load_data('users')
    user = st.session_state.user
    
    st.markdown('<div class="glass-card"><h2>💬 Private Chat</h2>', unsafe_allow_html=True)
    
    others = [u for u in users if u['email'] != user['email']]
    
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown("### Staff")
        for u in others:
            if st.button(f"{u['name']} ({u.get('department', '')})", key=f"cht_{u['email']}", use_container_width=True):
                st.session_state.chat_with = u['email']
                st.rerun()
    
    with c2:
        if st.session_state.chat_with:
            cu = next((u for u in users if u['email'] == st.session_state.chat_with), None)
            if cu:
                st.markdown(f"### Chat with {cu['name']}")
                
                msgs = load_data('chat_messages')
                chat_msgs = [m for m in msgs if (m['from_email'] == user['email'] and m['to_email'] == cu['email']) or (m['from_email'] == cu['email'] and m['to_email'] == user['email'])]
                
                for m in sorted(chat_msgs, key=lambda x: x.get('timestamp', '')):
                    is_mine = m['from_email'] == user['email']
                    bg = "rgba(233,69,96,0.4)" if is_mine else "rgba(255,255,255,0.15)"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:{'flex-end' if is_mine else 'flex-start'};margin:5px 0;">
                        <div style="background:{bg};padding:10px 16px;border-radius:16px;max-width:70%;color:#FFF;">
                            <strong>{m['from_name']}:</strong> {m['message']}
                            <br><small>{m['timestamp'][:16]}</small>
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
                
                with st.form(f"send_msg", clear_on_submit=True):
                    msg = st.text_input("Message", placeholder=f"Type... {st.session_state.emoji or ''}")
                    if st.form_submit_button("📤"):
                        if msg:
                            conn = get_db()
                            conn.execute(
                                "INSERT INTO chat_messages (id, school_name, from_email, from_name, to_email, department, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (generate_code("MSG"), st.session_state.school['name'], user['email'], user['name'],
                                 cu['email'], user.get('department', ''), msg + (f" {st.session_state.emoji}" if st.session_state.emoji else ""),
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            conn.commit()
                            conn.close()
                            st.session_state.emoji = None
                            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_announcements():
    st.markdown('<div class="glass-card"><h2>📢 Announcements</h2>', unsafe_allow_html=True)
    
    with st.form("announce"):
        title = st.text_input("Title")
        content = st.text_area("Content", height=100)
        priority = st.selectbox("Priority:", ["Normal", "Urgent", "Low"])
        dept = st.selectbox("Department:", ["All", "Sciences", "Mathematics", "Languages", "Humanities", "Other"])
        
        if st.form_submit_button("Post", use_container_width=True):
            if title and content:
                conn = get_db()
                conn.execute(
                    "INSERT INTO announcements (id, school_name, title, content, priority, posted_by, department, posted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (generate_code("ANN"), st.session_state.school['name'], title, content, priority,
                     st.session_state.user['name'], dept, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                st.success("Posted!")
                st.rerun()
    
    announcements = load_data('announcements')
    if announcements:
        for a in reversed(announcements):
            color = "#e94560" if a['priority'] == 'Urgent' else "#FFD700" if a['priority'] == 'Normal' else "#888"
            st.markdown(f"""
            <div style="border-left:4px solid {color};background:rgba(255,255,255,0.08);padding:15px;border-radius:8px;margin:10px 0;">
                <strong style="color:{color};">{'🔴' if a['priority'] == 'Urgent' else '🟡' if a['priority'] == 'Normal' else '🟢'} {a['title']}</strong>
                <br>{a['content']}
                <br><small>By {a['posted_by']} | {a['department']} | {a['posted_at'][:16]}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No announcements")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_documents():
    st.markdown('<div class="glass-card"><h2>📄 Documents</h2>', unsafe_allow_html=True)
    
    uploaded = st.file_uploader("Upload Document", type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'pptx'])
    if uploaded:
        subject = st.text_input("Subject/Topic")
        if st.button("Upload"):
            file_data = base64.b64encode(uploaded.read()).decode()
            conn = get_db()
            conn.execute(
                "INSERT INTO documents (id, school_name, title, file_type, file_data, subject, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (generate_code("DOC"), st.session_state.school['name'], uploaded.name,
                 uploaded.type, file_data, subject, st.session_state.user['name'],
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            conn.close()
            add_audit('Document Uploaded', uploaded.name)
            st.success("Uploaded!")
            st.rerun()
    
    docs = load_data('documents')
    if docs:
        for d in docs:
            st.markdown(f"📄 **{d['title']}** ({d.get('subject', '-')}) - {d['uploaded_by']} - {d['uploaded_at'][:16]}")
            st.divider()
    else:
        st.info("No documents")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_overview():
    st.markdown('<div class="glass-card"><h2>🔍 System Overview</h2>', unsafe_allow_html=True)
    
    books = load_data('books')
    borrowed = load_data('borrowed')
    members = load_data('members')
    users = load_data('users')
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📚 Total Books", sum(b['quantity'] for b in books))
    with c2: st.metric("📖 Active Loans", len([b for b in borrowed if not b['returned']]))
    with c3: st.metric("👥 Staff", len(users))
    
    c4, c5, c6 = st.columns(3)
    with c4: st.metric("👤 Members", len(members))
    with c5: st.metric("📅 Reservations", len(load_data('reservations')))
    with c6: st.metric("📄 Documents", len(load_data('documents')))
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_audit():
    if not is_admin():
        st.error("Admin access required!")
        return
    
    st.markdown('<div class="glass-card"><h2>📝 Audit Log</h2>', unsafe_allow_html=True)
    
    audit = load_data('audit_log')
    if audit:
        st.dataframe(pd.DataFrame(audit), use_container_width=True)
    else:
        st.info("No entries")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reports():
    st.markdown('<div class="glass-card"><h2>📈 Reports</h2>', unsafe_allow_html=True)
    
    rtype = st.selectbox("Report:", ["Books Overview", "Overdue Analysis", "Department Usage"])
    
    if st.button("Generate", use_container_width=True):
        borrowed = load_data('borrowed')
        
        if rtype == "Books Overview":
            if borrowed:
                df = pd.DataFrame(borrowed)
                returned = df['returned'].value_counts()
                fig = px.bar(x=['Active', 'Returned'], y=[returned.get(0, 0), returned.get(1, 0)],
                            color_discrete_sequence=['#e94560', '#28a745'], title="Books Status")
                st.plotly_chart(fig, use_container_width=True)
        
        elif rtype == "Overdue Analysis":
            today = datetime.now().strftime('%Y-%m-%d')
            overdue = [b for b in borrowed if not b['returned'] and b['due_date'] < today]
            st.metric("🔴 Overdue", len(overdue))
            if overdue:
                st.dataframe(pd.DataFrame(overdue), use_container_width=True)
        
        elif rtype == "Department Usage":
            depts = {}
            for b in borrowed:
                dept = b.get('department', 'Unknown')
                depts[dept] = depts.get(dept, 0) + 1
            if depts:
                fig = px.pie(values=list(depts.values()), names=list(depts.keys()), title="Department Usage")
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_settings():
    if not is_admin():
        st.error("Admin access required!")
        return
    
    st.markdown('<div class="glass-card"><h2>⚙️ Settings</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Staff", "Data"])
    
    with tab1:
        st.subheader("Staff Management")
        with st.form("add_staff"):
            c1, c2, c3 = st.columns(3)
            with c1: email = st.text_input("Email")
            with c2: name = st.text_input("Name")
            with c3: dept = st.selectbox("Department", ["Sciences", "Mathematics", "Languages", "Humanities", "Technical", "Other"])
            pwd = st.text_input("Password (auto if empty)")
            
            if st.form_submit_button("Add Staff"):
                if email and name:
                    conn = get_db()
                    exists = conn.execute("SELECT * FROM users WHERE email = ? AND school_name = ?",
                                         (email, st.session_state.school['name'])).fetchone()
                    if exists:
                        st.error("Email exists!")
                    else:
                        pw = pwd if pwd else generate_code(8)
                        conn.execute(
                            "INSERT INTO users (email, school_name, name, code, password, role, department, joined) VALUES (?, ?, ?, ?, ?, 'teacher', ?, ?)",
                            (email, st.session_state.school['name'], name, st.session_state.school['invite_code'],
                             hash_password(pw), dept, datetime.now().strftime("%Y-%m-%d"))
                        )
                        conn.commit()
                        st.success(f"Staff added! Password: {pw}")
                        st.rerun()
                    conn.close()
        
        users = load_data('users')
        for u in users:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1: st.write(f"{'👑' if u['role']=='admin' else '👨‍🏫'} **{u['name']}** ({u['role']})")
            with c2:
                if u['email'] != st.session_state.user['email'] and u['role'] != 'admin':
                    if st.button("👑 Promote", key=f"prom_{u['email']}"):
                        conn = get_db()
                        conn.execute("UPDATE users SET role = 'admin' WHERE email = ? AND school_name = ?",
                                    (u['email'], st.session_state.school['name']))
                        conn.commit()
                        conn.close()
                        st.rerun()
            with c3:
                if u['email'] != st.session_state.user['email']:
                    if st.button("🗑️", key=f"delu_{u['email']}"):
                        conn = get_db()
                        conn.execute("UPDATE users SET is_active = 0 WHERE email = ? AND school_name = ?",
                                    (u['email'], st.session_state.school['name']))
                        conn.commit()
                        conn.close()
                        st.rerun()
            st.divider()
    
    with tab2:
        st.subheader("Data Management")
        if st.button("📥 Backup Database"):
            conn = get_db()
            tables = ['schools', 'users', 'books', 'borrowed', 'furniture', 'members', 'classes', 'reservations', 'chat_messages', 'announcements', 'documents', 'audit_log']
            backup = {}
            for t in tables:
                data = conn.execute(f"SELECT * FROM {t} WHERE school_name = ?", (st.session_state.school['name'],)).fetchall()
                backup[t] = [dict(row) for row in data]
            conn.close()
            
            b64 = base64.b64encode(json.dumps(backup, indent=2, default=str).encode()).decode()
            st.markdown(f'<a href="data:application/json;base64,{b64}" download="backup.json">Download Backup</a>', unsafe_allow_html=True)
            st.success("Backup ready!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_db_manager():
    if not is_admin():
        st.error("Admin access required!")
        return
    
    st.markdown('<div class="glass-card"><h2>🗄️ Database Manager</h2>', unsafe_allow_html=True)
    st.warning("Admin only!")
    
    tables = ["schools", "users", "books", "borrowed", "furniture", "members", "classes", "reservations", "chat_messages", "announcements", "documents", "audit_log"]
    selected = st.selectbox("Table:", tables)
    
    conn = get_db()
    data = conn.execute(f"SELECT * FROM {selected} WHERE school_name = ?", (st.session_state.school['name'],)).fetchall()
    conn.close()
    
    if data:
        df = pd.DataFrame([dict(row) for row in data])
        st.dataframe(df, use_container_width=True, height=400)
        
        if st.button(f"Export {selected}"):
            buf = BytesIO()
            df.to_excel(buf, index=False)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{selected}.xlsx">Download</a>', unsafe_allow_html=True)
    else:
        st.info("No records")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============ MAIN ============
def main():
    if st.session_state.page == 'startup':
        startup_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()

if __name__ == "__main__":
    main()

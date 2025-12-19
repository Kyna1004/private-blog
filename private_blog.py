# -*- coding: utf-8 -*-
"""
kyna.london — Digital Garden
Updated: Fixed Flickering, Layout Stability & CSS Injection
"""

import sys
import sqlite3
import hashlib
from datetime import datetime
import streamlit as st
import pandas as pd
from PIL import Image
import io

# =====================================================
# Page Config (Must be first)
# =====================================================
st.set_page_config(
    page_title="kyna.london",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# Database Functions
# =====================================================
DB_FILE = "blog_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        nickname TEXT,
        avatar BLOB,
        role TEXT,
        is_active INTEGER
    )""")

    # Posts Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT,
        image BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Comments Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # Activity Logs Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Create Admin if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", pwd, "Admin", None, "admin", 1)
        )

    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

# =====================================================
# Helpers
# =====================================================
def make_hash(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def save_image(upload):
    return upload.getvalue() if upload else None

def log_activity(username, action):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO activity_logs (username, action) VALUES (?, ?)", (username, action))
    conn.commit()
    conn.close()

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = "guest"
        st.session_state.username = "Guest"

# =====================================================
# Global CSS & UI Components
# =====================================================
def inject_custom_css():
    st.markdown("""
    <style>
    /* ========== Global Theme ========== */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Fix Streamlit top padding to prevent content from jumping */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Hide standard elements */
    header[data-testid="stHeader"] {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    h1, h2, h3, h4 {
        font-weight: 600;
        color: #ffffff !important;
    }

    /* ========== Sidebar ========== */
    [data-testid="stSidebar"] {
        background-color: #0f0f0f;
        border-right: 1px solid #222;
    }
    
    /* Sidebar text fix */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ffffff;
    }

    /* ========== Inputs ========== */
    input, textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
    }
    
    /* Radio Button Fix */
    div[role="radiogroup"] label {
        color: #ffffff !important;
    }

    /* ========== Buttons ========== */
    .stButton button {
        background: #1a1a1a;
        color: #fff;
        border: 1px solid #333;
        transition: all 0.2s;
    }
    .stButton button:hover {
        border-color: #666;
        background: #222;
        color: #fff;
    }

    /* ========== Cards ========== */
    .notion-card {
        background-color: #0f0f0f;
        padding: 24px;
        margin-bottom: 24px;
        border-radius: 14px;
        border: 1px solid #222;
    }

    .comment-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #222;
    }

    .comment-box {
        background: #141414;
        padding: 10px;
        margin-top: 8px;
        border-radius: 8px;
        font-size: 14px;
        border-left: 2px solid #444;
    }
    
    .comment-user {
        font-weight: bold;
        color: #888;
        font-size: 12px;
        margin-bottom: 4px;
    }
    
    /* Logs Table Style */
    .dataframe {
        font-size: 12px !important;
        color: #ddd !important;
    }

    /* =================================================
       Mobile Layout Tweaks
       ================================================= */
    @media (max-width: 768px) {
        /* Hide sidebar on mobile */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* Adjust padding for mobile navbar */
        .block-container {
            padding-top: 80px !important;
            padding-left: 16px !important;
            padding-right: 16px !important;
        }

        .notion-card {
            padding: 16px;
        }
    }

    /* =================================================
       Mobile Navbar Components
       ================================================= */
    .mobile-header {
        display: none;
    }

    @media (max-width: 768px) {
        .mobile-header {
            display: flex;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 56px;
            background: #000;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            z-index: 1000;
            border-bottom: 1px solid #222;
        }

        .mobile-title {
            font-size: 16px;
            font-weight: 600;
            color: #fff;
        }
    }

    #menu-toggle {
        display: none;
    }

    .mobile-menu {
        position: fixed;
        inset: 0;
        background: #000;
        padding: 80px 32px;
        display: none;
        z-index: 999;
    }

    #menu-toggle:checked ~ .mobile-menu {
        display: block;
    }

    .mobile-menu a {
        display: block;
        font-size: 22px;
        margin-bottom: 28px;
        text-decoration: none;
        color: white;
    }
    </style>
    
    <!-- Mobile Navbar HTML injected here to reduce flicker -->
    <div class="mobile-header">
        <label for="menu-toggle" style="font-size:24px;cursor:pointer;color:#fff;">☰</label>
        <div class="mobile-title">kyna.london</div>
        <div style="width:24px;"></div>
    </div>
    <input type="checkbox" id="menu-toggle"/>
    <div class="mobile-menu">
        <label for="menu-toggle" style="font-size:24px;cursor:pointer;color:#fff;">✕</label>
        <a href="#" onclick="document.getElementById('menu-toggle').checked = false;">Close Menu</a>
        <div style="margin-top:20px; font-size:14px; color:#666;">
           (Use Desktop Sidebar for full navigation & login)
        </div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# User System (Collapsed at bottom)
# =====================================================
def sidebar_user_system():
    if not st.session_state.logged_in:
        with st.sidebar.expander("👤 Log in / Sign up", expanded=False):
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                user = st.text_input("Username", key="login_user")
                pwd = st.text_input("Password", type="password", key="login_pwd")
                
                if st.button("Login", use_container_width=True):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT password, role, is_active FROM users WHERE username=?", (user,))
                    data = c.fetchone()
                    conn.close()
                    
                    if data and make_hash(pwd) == data[0]:
                        if data[2] == 1:
                            st.session_state.logged_in = True
                            st.session_state.role = data[1]
                            st.session_state.username = user
                            log_activity(user, "Logged In")
                            st.success("Welcome!")
                            st.rerun()
                        else:
                            st.warning("Pending approval.")
                    else:
                        st.error("Invalid credentials.")

            with tab2:
                new_user = st.text_input("New Username", key="reg_user")
                new_pwd = st.text_input("New Password", type="password", key="reg_pwd")
                confirm_pwd = st.text_input("Confirm Password", type="password", key="reg_pwd2")
                
                if st.button("Sign Up", use_container_width=True):
                    if new_pwd != confirm_pwd:
                        st.error("Passwords mismatch.")
                    elif not new_user or not new_pwd:
                        st.error("Fill all fields.")
                    else:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        try:
                            hashed_pwd = make_hash(new_pwd)
                            c.execute(
                                "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, ?, ?)", 
                                (new_user, hashed_pwd, "subscriber", 0)
                            )
                            conn.commit()
                            log_activity(new_user, "Registered")
                            st.info("Created! Wait for approval.")
                        except sqlite3.IntegrityError:
                            st.error("User exists.")
                        finally:
                            conn.close()

    else:
        st.sidebar.markdown("---")
        st.sidebar.caption("Logged in as:")
        st.sidebar.markdown(f"**{st.session_state.username}** ({st.session_state.role.capitalize()})")
        
        if st.sidebar.button("Logout", use_container_width=True):
            log_activity(st.session_state.username, "Logged Out")
            st.session_state.logged_in = False
            st.session_state.role = "guest"
            st.session_state.username = "Guest"
            st.rerun()

# =====================================================
# Content Renderers
# =====================================================
def render_feed(category):
    st.markdown(f"## {category}")

    if st.session_state.get("role") == "admin":
        with st.expander("➕ Write New Post"):
            with st.form(f"new_{category}"):
                title = st.text_input("Title")
                content = st.text_area("Content", height=150)
                img = st.file_uploader("Image", type=["png", "jpg"])
                if st.form_submit_button("Publish"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO posts (category,title,content,image) VALUES (?,?,?,?)",
                        (category, title, content, save_image(img))
                    )
                    conn.commit()
                    conn.close()
                    log_activity(st.session_state.username, f"Published: {title}")
                    st.rerun()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, content, created_at, image FROM posts WHERE category=? ORDER BY created_at DESC", (category,))
    posts = c.fetchall()
    conn.close()

    for post_id, t, ctt, d, img in posts:
        st.markdown("<div class='notion-card'>", unsafe_allow_html=True)
        st.subheader(t)
        st.caption(f"📅 {d}")
        if img:
            st.image(img, use_column_width=True)
        st.markdown(ctt)
        
        st.markdown("<div class='comment-section'><h6>Comments</h6>", unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_FILE)
        cc = conn.cursor()
        cc.execute("SELECT username, content, created_at FROM comments WHERE post_id=? ORDER BY created_at ASC", (post_id,))
        comments = cc.fetchall()
        conn.close()
        
        if not comments:
            st.markdown("<p style='color:#666;font-size:13px;font-style:italic;'>No comments yet.</p>", unsafe_allow_html=True)
        
        for c_user, c_text, c_date in comments:
            st.markdown(f"""
            <div class='comment-box'>
                <div class='comment-user'>{c_user} <span style='font-weight:normal;opacity:0.6;'>• {c_date}</span></div>
                {c_text}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.logged_in and st.session_state.role in ['admin', 'subscriber']:
            with st.form(key=f"comment_form_{post_id}"):
                new_comment = st.text_area("Add a comment...", height=60, label_visibility="collapsed")
                c_submit = st.form_submit_button("Post Comment")
                if c_submit and new_comment:
                    conn = sqlite3.connect(DB_FILE)
                    cx = conn.cursor()
                    cx.execute("INSERT INTO comments (post_id, username, content) VALUES (?, ?, ?)", (post_id, st.session_state.username, new_comment))
                    conn.commit()
                    conn.close()
                    log_activity(st.session_state.username, f"Commented on {post_id}")
                    st.rerun()
        elif not st.session_state.logged_in:
             st.markdown("<p style='font-size:12px;color:#444;margin-top:10px;'>Log in to comment.</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

def render_gallery():
    st.markdown("## Gallery")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, image FROM posts WHERE category='Gallery'")
    items = c.fetchall()
    conn.close()

    cols = st.columns(2)
    for i, (t, img) in enumerate(items):
        with cols[i % 2]:
            if img:
                st.image(img, use_column_width=True)
            st.caption(t)
    
    if st.session_state.get("role") == "admin":
        with st.expander("Add to Gallery"):
            with st.form("gallery_upload"):
                g_title = st.text_input("Caption")
                g_img = st.file_uploader("Image", type=["png", "jpg"])
                if st.form_submit_button("Upload"):
                    if g_img:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("INSERT INTO posts (category, title, content, image) VALUES (?, ?, ?, ?)", ("Gallery", g_title, "", save_image(g_img)))
                        conn.commit()
                        conn.close()
                        log_activity(st.session_state.username, "Uploaded to Gallery")
                        st.rerun()

def render_admin_panel():
    st.markdown("## 🛡️ Admin Panel")
    tab1, tab2 = st.tabs(["User Approvals", "Activity Logs"])
    
    with tab1:
        st.subheader("Pending User Approvals")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE is_active=0")
        pending_users = c.fetchall()
        
        if not pending_users:
            st.info("No pending approvals.")
        else:
            st.markdown("---")
            for user_tuple in pending_users:
                username = user_tuple[0]
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1: st.markdown(f"**{username}**")
                with col2:
                    if st.button("✅ Approve", key=f"approve_{username}"):
                        c.execute("UPDATE users SET is_active=1 WHERE username=?", (username,))
                        conn.commit()
                        log_activity(st.session_state.username, f"Approved user: {username}")
                        st.rerun()
                with col3:
                    if st.button("❌ Reject", key=f"reject_{username}"):
                        c.execute("DELETE FROM users WHERE username=?", (username,))
                        conn.commit()
                        log_activity(st.session_state.username, f"Rejected user: {username}")
                        st.rerun()
                st.markdown("---")
        conn.close()

    with tab2:
        st.subheader("Global User Activity Logs")
        conn = sqlite3.connect(DB_FILE)
        df_logs = pd.read_sql_query("SELECT timestamp, username, action FROM activity_logs ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        st.dataframe(df_logs, use_container_width=True)

# =====================================================
# Main
# =====================================================
def main():
    # 1. Inject CSS FIRST to prevent flickering
    inject_custom_css()
    
    # 2. Initialize Session
    init_session_state()

    # 3. Sidebar Navigation
    st.sidebar.title("kyna.london")
    
    menu_options = ["Introduce", "Blogs", "Writing", "Gallery"]
    if st.session_state.get("logged_in") and st.session_state.get("role") == "admin":
        menu_options.append("Admin Panel")

    # Fixed key to prevent state loss
    menu = st.sidebar.radio("Navigate", menu_options, key="main_navigation")
    
    # 4. User System (Bottom Sidebar)
    sidebar_user_system()
    
    # 5. Logging (Only log if page changed to prevent loops)
    if "last_page" not in st.session_state or st.session_state.last_page != menu:
        log_activity(st.session_state.get("username", "Guest"), f"Viewed Page: {menu}")
        st.session_state.last_page = menu

    # 6. Page Routing
    if menu == "Introduce":
        st.markdown("## About")
        st.markdown("A quiet place for writing, memory, and thinking.")
    elif menu == "Blogs":
        render_feed("Blogs")
    elif menu == "Writing":
        render_feed("Writing")
    elif menu == "Gallery":
        render_gallery()
    elif menu == "Admin Panel":
        if st.session_state.get("role") == "admin":
            render_admin_panel()
        else:
            st.error("Access Denied")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
kyna.london — Digital Garden
Updated with User Registration & Comment System
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
# Page Config
# =====================================================
st.set_page_config(
    page_title="kyna.london",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# Global CSS (Desktop + Mobile)
# =====================================================
def local_css():
    st.markdown("""
    <style>
    /* ========== Base ========== */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }

    header, footer {
        visibility: hidden;
    }

    h1, h2, h3, h4 {
        font-weight: 600;
        color: #ffffff;
    }

    /* ========== Sidebar ========== */
    [data-testid="stSidebar"] {
        background-color: #0f0f0f;
        border-right: 1px solid #222;
    }

    /* ========== Inputs ========== */
    input, textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
    }

    /* ========== Buttons ========== */
    .stButton button {
        background: #1a1a1a;
        color: #fff;
        border: 1px solid #333;
    }
    
    .stButton button:hover {
        border-color: #666;
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

    /* =================================================
       Mobile Layout
       ================================================= */
    @media (max-width: 768px) {
        /* Hide sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            padding: 80px 16px 32px 16px;
            max-width: 100%;
        }

        .notion-card {
            padding: 16px;
        }

        h2 {
            font-size: 18px;
        }

        p {
            font-size: 15px;
            line-height: 1.6;
        }
    }

    /* =================================================
       Mobile Navbar
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
        }

        .mobile-title {
            font-size: 16px;
            font-weight: 600;
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
    """, unsafe_allow_html=True)

local_css()

# =====================================================
# Mobile Navbar
# =====================================================
def mobile_navbar():
    st.markdown("""
    <div class="mobile-header">
        <label for="menu-toggle" style="font-size:24px;cursor:pointer;">☰</label>
        <div class="mobile-title">kyna.london</div>
        <div style="width:24px;"></div>
    </div>

    <input type="checkbox" id="menu-toggle"/>

    <div class="mobile-menu">
        <label for="menu-toggle" style="font-size:24px;cursor:pointer;">✕</label>
        <a href="#Introduce">About</a>
        <a href="#Blogs">Blogs</a>
        <a href="#Writing">Writings</a>
        <a href="#Gallery">Gallery</a>
        <br/><br/>
        <span style="color:#666; font-size:14px;">Use Sidebar on Desktop to Login</span>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# Database
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

    # Create Admin if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        # Admin role is explicitly 'admin'
        c.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", pwd, "Admin", None, "admin", 1)
        )

    conn.commit()
    conn.close()

init_db()

# =====================================================
# Helpers
# =====================================================
def make_hash(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def save_image(upload):
    return upload.getvalue() if upload else None

# =====================================================
# User System (Login / Register)
# =====================================================
def sidebar_user_system():
    st.sidebar.title("Account")

    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = "guest"
        st.session_state.username = "Guest"

    # If logged out, show Login/Register tabs
    if not st.session_state.logged_in:
        tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
        
        # --- LOGIN TAB ---
        with tab1:
            user = st.text_input("Username", key="login_user")
            pwd = st.text_input("Password", type="password", key="login_pwd")
            
            if st.button("Login"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT password, role, is_active FROM users WHERE username=?", (user,))
                data = c.fetchone()
                conn.close()
                
                if data and make_hash(pwd) == data[0]:
                    if data[2] == 1: # check active
                        st.session_state.logged_in = True
                        st.session_state.role = data[1] # admin or subscriber
                        st.session_state.username = user
                        st.success("Welcome back!")
                        st.rerun()
                    else:
                        st.error("Account suspended.")
                else:
                    st.error("Invalid credentials.")

        # --- REGISTER TAB ---
        with tab2:
            new_user = st.text_input("New Username", key="reg_user")
            new_pwd = st.text_input("New Password", type="password", key="reg_pwd")
            confirm_pwd = st.text_input("Confirm Password", type="password", key="reg_pwd2")
            
            if st.button("Sign Up"):
                if new_pwd != confirm_pwd:
                    st.error("Passwords do not match.")
                elif not new_user or not new_pwd:
                    st.error("Please fill all fields.")
                else:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    try:
                        # Default role is 'subscriber'
                        hashed_pwd = make_hash(new_pwd)
                        c.execute(
                            "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, ?, ?)", 
                            (new_user, hashed_pwd, "subscriber", 1)
                        )
                        conn.commit()
                        st.success("Account created! Please log in.")
                    except sqlite3.IntegrityError:
                        st.error("Username already taken.")
                    finally:
                        conn.close()

    # If logged in, show info and Logout
    else:
        st.sidebar.markdown(f"User: **{st.session_state.username}**")
        st.sidebar.markdown(f"Role: **{st.session_state.role.capitalize()}**")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.role = "guest"
            st.session_state.username = "Guest"
            st.rerun()

# =====================================================
# Pages
# =====================================================
def render_feed(category):
    st.markdown(f"## {category}")

    # --- ADMIN: Create Post ---
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
                    st.rerun()

    # --- Fetch Posts ---
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Updated Query to include ID for comments linkage
    c.execute("SELECT id, title, content, created_at, image FROM posts WHERE category=? ORDER BY created_at DESC", (category,))
    posts = c.fetchall()
    conn.close()

    # --- Render Posts ---
    for post_id, t, ctt, d, img in posts:
        st.markdown("<div class='notion-card'>", unsafe_allow_html=True)
        
        # Post Content
        st.subheader(t)
        st.caption(f"📅 {d}")
        if img:
            st.image(img, use_column_width=True)
        st.markdown(ctt)
        
        # --- Comment Section ---
        st.markdown("<div class='comment-section'><h6>Comments</h6>", unsafe_allow_html=True)
        
        # 1. Fetch Comments
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

        st.markdown("</div>", unsafe_allow_html=True) # End comment section div

        # 2. Add Comment Form (Only for Admin or Subscriber)
        if st.session_state.logged_in and st.session_state.role in ['admin', 'subscriber']:
            with st.form(key=f"comment_form_{post_id}"):
                new_comment = st.text_area("Add a comment...", height=60, label_visibility="collapsed")
                c_submit = st.form_submit_button("Post Comment")
                
                if c_submit and new_comment:
                    conn = sqlite3.connect(DB_FILE)
                    cx = conn.cursor()
                    cx.execute(
                        "INSERT INTO comments (post_id, username, content) VALUES (?, ?, ?)",
                        (post_id, st.session_state.username, new_comment)
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()
        elif not st.session_state.logged_in:
             st.markdown("<p style='font-size:12px;color:#444;margin-top:10px;'>Log in to comment.</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True) # End notion-card

def render_gallery():
    st.markdown("## Gallery")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Assuming Gallery items are also stored in posts but usually just images
    c.execute("SELECT title, image FROM posts WHERE category='Gallery'")
    items = c.fetchall()
    conn.close()

    cols = st.columns(2)
    for i, (t, img) in enumerate(items):
        with cols[i % 2]:
            if img:
                st.image(img, use_column_width=True)
            st.caption(t)
    
    # Admin upload for gallery
    if st.session_state.get("role") == "admin":
        with st.expander("Add to Gallery"):
            with st.form("gallery_upload"):
                g_title = st.text_input("Caption")
                g_img = st.file_uploader("Image", type=["png", "jpg"])
                if st.form_submit_button("Upload"):
                    if g_img:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO posts (category, title, content, image) VALUES (?, ?, ?, ?)",
                            ("Gallery", g_title, "", save_image(g_img))
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

# =====================================================
# Main
# =====================================================
def main():
    mobile_navbar()
    
    # Sidebar only visible on desktop (handled by CSS), but logic runs here
    sidebar_user_system()

    menu = st.sidebar.radio("Navigate", ["Introduce", "Blogs", "Writing", "Gallery"])

    if menu == "Introduce":
        st.markdown("## About")
        st.markdown("A quiet place for writing, memory, and thinking.")
    elif menu == "Blogs":
        render_feed("Blogs")
    elif menu == "Writing":
        render_feed("Writing")
    elif menu == "Gallery":
        render_gallery()

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
kyna.london — Digital Garden
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

    /* ========== Cards ========== */
    .notion-card {
        background-color: #0f0f0f;
        padding: 24px;
        margin-bottom: 24px;
        border-radius: 14px;
        border: 1px solid #222;
    }

    .comment-box {
        background: #1a1a1a;
        padding: 12px;
        margin-top: 8px;
        border-radius: 8px;
        font-size: 14px;
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
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# Database
# =====================================================
DB_FILE = "blog_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        nickname TEXT,
        avatar BLOB,
        role TEXT,
        is_active INTEGER
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT,
        image BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
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
# Sidebar User System (Desktop)
# =====================================================
def sidebar_user_system():
    st.sidebar.title("Account")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = "guest"

    if not st.session_state.logged_in:
        user = st.sidebar.text_input("Username")
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT password, role, is_active FROM users WHERE username=?", (user,))
            data = c.fetchone()
            conn.close()
            if data and make_hash(pwd) == data[0] and data[2] == 1:
                st.session_state.logged_in = True
                st.session_state.role = data[1]
                st.session_state.username = user
                st.rerun()
    else:
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# =====================================================
# Pages
# =====================================================
def render_feed(category):
    st.markdown(f"## {category}")

    if st.session_state.get("role") == "admin":
        with st.expander("New Post"):
            with st.form(f"new_{category}"):
                title = st.text_input("Title")
                content = st.text_area("Content", height=200)
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

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, content, created_at, image FROM posts WHERE category=? ORDER BY created_at DESC", (category,))
    posts = c.fetchall()
    conn.close()

    for t, ctt, d, img in posts:
        st.markdown("<div class='notion-card'>", unsafe_allow_html=True)
        st.subheader(t)
        st.caption(d)
        if img:
            st.image(img, use_column_width=True)
        st.markdown(ctt)
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

# =====================================================
# Main
# =====================================================
def main():
    mobile_navbar()
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

# -*- coding: utf-8 -*-
"""
kyna.london — Digital Garden
Backend: Google Firestore (Cloud Database)
"""

import sys
import hashlib
import time
from datetime import datetime
import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64

# --- FIREBASE IMPORTS ---
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

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
# Database Connection (Firestore)
# =====================================================

# 使用 Streamlit 的缓存功能，防止每次刷新都重新连接 Firebase
@st.cache_resource
def get_db():
    # 检查 Firebase 是否已经初始化，避免重复初始化报错
    if not firebase_admin._apps:
        # 从 .streamlit/secrets.toml 读取密钥
        try:
            key_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            st.stop()
    
    db = firestore.client()
    return db

# 初始化数据库连接
try:
    db = get_db()
except Exception as e:
    st.error(f"无法连接到 Firestore 数据库。请检查 secrets.toml 配置。\n错误信息: {e}")
    st.stop()

# =====================================================
# Helpers
# =====================================================
def make_hash(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def image_to_base64(upload):
    """将上传的图片转换为 Base64 字符串以便存入 Firestore"""
    if upload is None:
        return None
    bytes_data = upload.getvalue()
    base64_str = base64.b64encode(bytes_data).decode('utf-8')
    return base64_str

def base64_to_image(base64_str):
    """将 Firestore 取出的 Base64 字符串转回图片"""
    if not base64_str:
        return None
    try:
        image_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(image_data))
    except Exception:
        return None

def log_activity(username, action):
    """记录日志到 Firestore"""
    try:
        db.collection('activity_logs').add({
            'username': username,
            'action': action,
            'timestamp': datetime.now()
        })
    except Exception as e:
        print(f"Log error: {e}")

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = "guest"
        st.session_state.username = "Guest"

# =====================================================
# Global CSS
# =====================================================
def inject_custom_css():
    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    header[data-testid="stHeader"], footer { visibility: hidden; }
    h1, h2, h3, h4 { font-weight: 600; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #0f0f0f; border-right: 1px solid #222; }
    input, textarea { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #333 !important; }
    div[role="radiogroup"] label { color: #ffffff !important; }
    .stButton button { background: #1a1a1a; color: #fff; border: 1px solid #333; transition: all 0.2s; }
    .stButton button:hover { border-color: #666; background: #222; color: #fff; }
    
    .notion-card { background-color: #0f0f0f; padding: 24px; margin-bottom: 24px; border-radius: 14px; border: 1px solid #222; }
    .comment-section { margin-top: 16px; padding-top: 16px; border-top: 1px solid #222; }
    .comment-box { background: #141414; padding: 10px; margin-top: 8px; border-radius: 8px; font-size: 14px; border-left: 2px solid #444; }
    .comment-user { font-weight: bold; color: #888; font-size: 12px; margin-bottom: 4px; }
    .dataframe { font-size: 12px !important; color: #ddd !important; }

    @media (max-width: 768px) {
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 80px !important; }
    }
    
    .mobile-header { display: none; }
    @media (max-width: 768px) {
        .mobile-header { display: flex; position: fixed; top: 0; left: 0; right: 0; height: 56px; background: #000; align-items: center; justify-content: space-between; padding: 0 16px; z-index: 1000; border-bottom: 1px solid #222; }
        .mobile-title { font-size: 16px; font-weight: 600; color: #fff; }
    }
    </style>
    
    <div class="mobile-header">
        <label style="font-size:24px;color:#fff;">☰</label>
        <div class="mobile-title">kyna.london</div>
        <div style="width:24px;"></div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# User System (Firestore)
# =====================================================
def create_admin_if_not_exists():
    """Check if admin exists in Firestore, if not create one"""
    try:
        doc_ref = db.collection('users').document('admin')
        doc = doc_ref.get()
        if not doc.exists:
            pwd = make_hash("admin123")
            doc_ref.set({
                'username': 'admin',
                'password': pwd,
                'nickname': 'Admin',
                'role': 'admin',
                'is_active': 1,
                'is_deleted': 0,
                'created_at': datetime.now()
            })
    except Exception as e:
        st.warning(f"Could not check/create admin: {e}")

def sidebar_user_system():
    # Ensure admin exists on startup
    create_admin_if_not_exists()

    if not st.session_state.logged_in:
        with st.sidebar.expander("👤 Log in / Sign up", expanded=False):
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            # --- LOGIN ---
            with tab1:
                user = st.text_input("Username", key="login_user")
                pwd = st.text_input("Password", type="password", key="login_pwd")
                
                if st.button("Login", use_container_width=True):
                    if not user or not pwd:
                        st.error("Please enter username and password")
                    else:
                        # Query Firestore: Collection 'users', Document ID = username
                        doc_ref = db.collection('users').document(user)
                        doc = doc_ref.get()
                        
                        if doc.exists:
                            data = doc.to_dict()
                            # Check password and flags
                            if make_hash(pwd) == data.get('password') and data.get('is_deleted') == 0:
                                if data.get('is_active') == 1:
                                    st.session_state.logged_in = True
                                    st.session_state.role = data.get('role')
                                    st.session_state.username = user
                                    log_activity(user, "Logged In")
                                    st.success("Welcome!")
                                    st.rerun()
                                else:
                                    st.warning("Pending approval.")
                            else:
                                st.error("Invalid credentials.")
                        else:
                            st.error("User not found.")

            # --- REGISTER ---
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
                        # Check if user already exists
                        doc_ref = db.collection('users').document(new_user)
                        if doc_ref.get().exists:
                            st.error("User exists.")
                        else:
                            hashed_pwd = make_hash(new_pwd)
                            doc_ref.set({
                                'username': new_user,
                                'password': hashed_pwd,
                                'role': 'subscriber',
                                'is_active': 0, # Pending
                                'is_deleted': 0,
                                'created_at': datetime.now()
                            })
                            log_activity(new_user, "Registered")
                            st.info("Created! Wait for approval.")

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
# Content Renderers (Firestore)
# =====================================================
def render_feed(category):
    st.markdown(f"## {category}")

    # --- WRITE POST ---
    if st.session_state.get("role") == "admin":
        with st.expander("➕ Write New Post"):
            with st.form(f"new_{category}"):
                title = st.text_input("Title")
                content = st.text_area("Content", height=150)
                img = st.file_uploader("Image", type=["png", "jpg"])
                if st.form_submit_button("Publish"):
                    # Add to 'posts' collection
                    # Firestore auto-generates ID if we use .add()
                    db.collection('posts').add({
                        'category': category,
                        'title': title,
                        'content': content,
                        'image_base64': image_to_base64(img),
                        'created_at': datetime.now(),
                        'is_deleted': 0
                    })
                    log_activity(st.session_state.username, f"Published: {title}")
                    st.rerun()

    # --- FETCH POSTS ---
    # Query: posts where category == X and is_deleted == 0
    posts_ref = db.collection('posts')
    query = posts_ref.where('category', '==', category).where('is_deleted', '==', 0)
    
    docs = list(query.stream())
    
    # Sorting Safe Fix: Use timestamp() to avoid naive/aware datetime comparison errors
    docs.sort(
        key=lambda x: x.to_dict().get('created_at').timestamp() if x.to_dict().get('created_at') else 0, 
        reverse=True
    )

    for doc in docs:
        post = doc.to_dict()
        post_id = doc.id # Firestore Document ID
        
        st.markdown("<div class='notion-card'>", unsafe_allow_html=True)
        col_head, col_action = st.columns([8, 1])
        with col_head:
            st.subheader(post.get('title'))
        
        # Soft Delete
        if st.session_state.get("role") == "admin":
            with col_action:
                if st.button("🗑️", key=f"del_post_{post_id}"):
                    db.collection('posts').document(post_id).update({'is_deleted': 1})
                    log_activity(st.session_state.username, f"Deleted post {post_id}")
                    st.rerun()

        # Display Date
        created_at = post.get('created_at')
        if created_at:
            # Convert Firestore timestamp to readable string
            try:
                date_str = created_at.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = str(created_at)
        else:
            date_str = ""
        st.caption(f"{date_str}")

        # Display Image
        if post.get('image_base64'):
            img_obj = base64_to_image(post.get('image_base64'))
            if img_obj:
                st.image(img_obj, use_column_width=True)
        
        st.markdown(post.get('content', ''))
        
        # --- COMMENTS ---
        st.markdown("<div class='comment-section'><h6>Comments</h6>", unsafe_allow_html=True)
        
        # Fetch Comments for this post
        c_query = db.collection('comments').where('post_id', '==', post_id).where('is_deleted', '==', 0).stream()
        c_list = list(c_query)
        # Sorting Safe Fix for comments
        c_list.sort(key=lambda x: x.to_dict().get('created_at').timestamp() if x.to_dict().get('created_at') else 0)

        if not c_list:
            st.markdown("<p style='color:#666;font-size:13px;font-style:italic;'>No comments yet.</p>", unsafe_allow_html=True)
        
        for c_doc in c_list:
            c_data = c_doc.to_dict()
            c_time_val = c_data.get('created_at')
            c_date = c_time_val.strftime("%Y-%m-%d %H:%M") if c_time_val else ""
            
            st.markdown(f"""
            <div class='comment-box'>
                <div class='comment-user'>{c_data.get('username')} <span style='font-weight:normal;opacity:0.6;'>• {c_date}</span></div>
                {c_data.get('content')}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Add Comment Form
        if st.session_state.logged_in and st.session_state.role in ['admin', 'subscriber']:
            with st.form(key=f"comment_form_{post_id}"):
                new_comment = st.text_area("Add a comment...", height=60, label_visibility="collapsed")
                c_submit = st.form_submit_button("Post Comment")
                if c_submit and new_comment:
                    db.collection('comments').add({
                        'post_id': post_id,
                        'username': st.session_state.username,
                        'content': new_comment,
                        'is_deleted': 0,
                        'created_at': datetime.now()
                    })
                    log_activity(st.session_state.username, f"Commented on {post_id}")
                    st.rerun()
        elif not st.session_state.logged_in:
             st.markdown("<p style='font-size:12px;color:#444;margin-top:10px;'>Log in to comment.</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

def render_gallery():
    st.markdown("## Gallery")
    # Fetch Gallery posts
    query = db.collection('posts').where('category', '==', 'Gallery').where('is_deleted', '==', 0)
    docs = list(query.stream())
    
    cols = st.columns(2)
    for i, doc in enumerate(docs):
        post = doc.to_dict()
        with cols[i % 2]:
            if post.get('image_base64'):
                img_obj = base64_to_image(post.get('image_base64'))
                if img_obj:
                    st.image(img_obj, use_column_width=True)
            st.caption(post.get('title'))
            
            if st.session_state.get("role") == "admin":
                 if st.button("Delete", key=f"del_gal_{doc.id}"):
                    db.collection('posts').document(doc.id).update({'is_deleted': 1})
                    st.rerun()
    
    if st.session_state.get("role") == "admin":
        with st.expander("Add to Gallery"):
            with st.form("gallery_upload"):
                g_title = st.text_input("Caption")
                g_img = st.file_uploader("Image", type=["png", "jpg"])
                if st.form_submit_button("Upload"):
                    if g_img:
                        db.collection('posts').add({
                            'category': 'Gallery',
                            'title': g_title,
                            'content': '',
                            'image_base64': image_to_base64(g_img),
                            'created_at': datetime.now(),
                            'is_deleted': 0
                        })
                        log_activity(st.session_state.username, "Uploaded to Gallery")
                        st.rerun()

def render_admin_panel():
    st.markdown("## 🛡️ Admin Panel")
    tab1, tab2, tab3 = st.tabs(["User Approvals", "Activity Logs", "Recycle Bin"])
    
    # 1. Approvals
    with tab1:
        st.subheader("Pending Users")
        query = db.collection('users').where('is_active', '==', 0).where('is_deleted', '==', 0)
        docs = list(query.stream())
        
        if not docs:
            st.info("No pending approvals.")
        else:
            for doc in docs:
                data = doc.to_dict()
                username = data.get('username')
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"**{username}**")
                if c2.button("✅ Approve", key=f"app_{username}"):
                    db.collection('users').document(username).update({'is_active': 1})
                    log_activity(st.session_state.username, f"Approved {username}")
                    st.rerun()
                if c3.button("❌ Reject", key=f"rej_{username}"):
                    db.collection('users').document(username).update({'is_deleted': 1})
                    log_activity(st.session_state.username, f"Rejected {username}")
                    st.rerun()
                st.markdown("---")

    # 2. Logs
    with tab2:
        st.subheader("Logs")
        logs_ref = db.collection('activity_logs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50)
        logs = [x.to_dict() for x in logs_ref.stream()]
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)

    # 3. Recycle Bin
    with tab3:
        st.subheader("🗑️ Recycle Bin")
        
        # Deleted Posts
        st.markdown("##### Deleted Posts")
        del_posts = list(db.collection('posts').where('is_deleted', '==', 1).stream())
        if not del_posts: st.caption("No deleted posts.")
        for doc in del_posts:
            data = doc.to_dict()
            c1, c2 = st.columns([3, 1])
            c1.text(f"[{data.get('category')}] {data.get('title')}")
            if c2.button("Restore", key=f"res_post_{doc.id}"):
                db.collection('posts').document(doc.id).update({'is_deleted': 0})
                st.rerun()

        st.markdown("---")
        # Deleted Users
        st.markdown("##### Deleted Users")
        del_users = list(db.collection('users').where('is_deleted', '==', 1).stream())
        if not del_users: st.caption("No deleted users.")
        for doc in del_users:
            username = doc.id
            c1, c2 = st.columns([3, 1])
            c1.text(username)
            if c2.button("Restore", key=f"res_user_{username}"):
                db.collection('users').document(username).update({'is_deleted': 0})
                st.rerun()

# =====================================================
# Main
# =====================================================
def main():
    inject_custom_css()
    init_session_state()

    st.sidebar.title("kyna.london")
    menu_options = ["Introduce", "Blogs", "Writing", "Gallery"]
    if st.session_state.get("logged_in") and st.session_state.get("role") == "admin":
        menu_options.append("Admin Panel")

    menu = st.sidebar.radio("Navigate", menu_options, key="nav")
    sidebar_user_system()
    
    if "last_page" not in st.session_state or st.session_state.last_page != menu:
        log_activity(st.session_state.get("username", "Guest"), f"Viewed Page: {menu}")
        st.session_state.last_page = menu

    if menu == "Introduce":
        st.markdown("## About")
        st.markdown("A quiet place for writing, memory, and thinking.")
    elif menu == "Blogs": render_feed("Blogs")
    elif menu == "Writing": render_feed("Writing")
    elif menu == "Gallery": render_gallery()
    elif menu == "Admin Panel":
        if st.session_state.get("role") == "admin": render_admin_panel()
        else: st.error("Access Denied")

if __name__ == "__main__":
    main()

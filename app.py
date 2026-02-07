import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import base64

# 初始化資料庫
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', avatar TEXT DEFAULT NULL)''')
conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; color: #333; }
    h1, h2, h3 { color: #4a90e2; font-family: 'Arial', sans-serif; }
    .stButton > button { background-color: #4a90e2; color: white; border-radius: 8px; border: none; padding: 8px 16px; font-weight: bold; }
    .stButton > button:hover { background-color: #357ae8; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { border-radius: 8px; border: 1px solid #ddd; padding: 8px; }
    .stExpander { border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; background-color: white; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    img { border-radius: 50%; }
    .message { background-color: #f9f9f9; padding: 10px; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

def auth_page():
    st.header("用戶認證")
    tab1, tab2 = st.tabs(["登入", "註冊"])
    
    with tab1:
        username = st.text_input("用戶名")
        password = st.text_input("密碼", type="password")
        if st.button("登入"):
            c.execute("SELECT password_hash, role, avatar FROM users WHERE username=?", (username,))
            result = c.fetchone()
            if result and result[0] == hash_password(password):
                st.session_state['user'] = username
                st.session_state['role'] = result[1]
                st.session_state['avatar'] = result[2]
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("用戶名或密碼錯誤")
    
    with tab2:
        new_username = st.text_input("新用戶名")
        new_password = st.text_input("新密碼", type="password")
        confirm_password = st.text_input("確認密碼", type="password")
        avatar_upload = st.file_uploader("上傳頭像 (可選)", type=["jpg", "png", "jpeg"])
        if st.button("註冊"):
            if new_password != confirm_password:
                st.error("密碼不匹配")
            else:
                avatar_data = None
                if avatar_upload:
                    avatar_data = base64.b64encode(avatar_upload.read()).decode()
                try:
                    c.execute("SELECT COUNT(*) FROM users")
                    user_count = c.fetchone()[0]
                    role = 'admin' if user_count == 0 else 'user'
                    c.execute("INSERT INTO users (username, password_hash, role, avatar) VALUES (?, ?, ?, ?)", (new_username, hash_password(new_password), role, avatar_data))
                    conn.commit()
                    st.success("註冊成功！請登入。" + ("你是管理員。" if role == 'admin' else ""))
                except sqlite3.IntegrityError:
                    st.error("用戶名已存在")

st.title("Gay Spa 香港討論區")

if 'user' not in st.session_state:
    auth_page()
else:
    role = st.session_state.get('role', 'user')
    
    with st.sidebar:
        if st.session_state.get('avatar'):
            st.image(f"data:image/png;base64,{st.session_state['avatar']}", width=80)
        st.write(f"歡迎，{st.session_state['user']}！（{role}）")
        
        st.subheader("更新頭像")
        new_avatar = st.file_uploader("選擇圖片", type=["jpg", "png", "jpeg"])
        if st.button("上傳") and new_avatar:
            avatar_data = base64.b64encode(new_avatar.read()).decode()
            c.execute("UPDATE users SET avatar=? WHERE username=?", (avatar_data, st.session_state['user']))
            conn.commit()
            st.session_state['avatar'] = avatar_data
            st.success("頭像更新成功！")
            st.rerun()
        
        if st.button("登出"):
            del st.session_state['user']
            del st.session_state['role']
            del st.session_state['avatar']
            st.rerun()
        
        st.subheader("發新帖")
        title = st.text_input("標題", key="new_title")
        content = st.text_area("內容", key="new_content")
        if st.button("發布"):
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO posts (title, content, author, date) VALUES (?, ?, ?, ?)", (title, content, st.session_state['user'], date))
            conn.commit()
            st.success("帖子發布成功！")

    search_query = st.text_input("搜尋帖子（標題或內容）", "")
    query = f"%{search_query}%" if search_query else "%"
    posts = c.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY date DESC", (query, query)).fetchall()
    
    for post in posts:
        c.execute("SELECT avatar FROM users WHERE username=?", (post[3],))
        result = c.fetchone()
        post_avatar = result[0] if result else None
        
        with st.expander(f"📝 {post[1]} - {post[3]} ({post[4]})"):
            col1, col2 = st.columns([1, 5])
            with col1:
                if post_avatar:
                    st.image(f"data:image/png;base64,{post_avatar}", width=40)
            with col2:
                st.write(post[2])
            
            if role == 'admin' and st.button("刪除帖子", key=f"del_post_{post[0]}"):
                c.execute("DELETE FROM posts WHERE id=?", (post[0],))
                c.execute("DELETE FROM messages WHERE post_id=?", (post[0],))
                conn.commit()
                st.rerun()
            
            st.subheader("留言區")
            messages = c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],)).fetchall()
            for msg in messages:
                c.execute("SELECT avatar FROM users WHERE username=?", (msg[3],))
                result = c.fetchone()
                msg_avatar = result[0] if result else None
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if msg_avatar:
                            st.image(f"data:image/png;base64,{msg_avatar}", width=30)
                    with col2:
                        st.markdown(f"<div class='message'>{msg[3]} ({msg[4]}): {msg[2]}</div>", unsafe_allow_html=True)
                    if role == 'admin' and st.button("刪除", key=f"del_msg_{msg[0]}"):
                        c.execute("DELETE FROM messages WHERE id=?", (msg[0],))
                        conn.commit()
                        st.rerun()
            
            msg_content = st.text_input("新增留言", key=f"msg_{post[0]}")
            if st.button("發送", key=f"send_{post[0]}"):
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)", (post[0], msg_content, st.session_state['user'], date))
                conn.commit()
                st.rerun()

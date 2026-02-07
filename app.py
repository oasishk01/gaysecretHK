import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import base64
import os

# 初始化資料庫 - 先刪除舊的
if os.path.exists('forum.db'):
    os.remove('forum.db')

conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()

# 重新建立 tables (加咗 avatar)
c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', avatar TEXT)''')
conn.commit()

# 哈希密碼函數
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 登入/註冊功能
def auth_page():
    st.header("用戶認證")
    tab1, tab2 = st.tabs(["登入", "註冊"])
    
    with tab1:
        username = st.text_input("用戶名", key="login_username")
        password = st.text_input("密碼", type="password", key="login_password")
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
        new_username = st.text_input("新用戶名", key="reg_username")
        new_password = st.text_input("新密碼", type="password", key="reg_password")
        confirm_password = st.text_input("確認密碼", type="password", key="reg_confirm")
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
                    msg = "註冊成功！請登入。"
                    if role == 'admin':
                        msg += "你是管理員！"
                    st.success(msg)
                except sqlite3.IntegrityError:
                    st.error("用戶名已存在")

# Streamlit 應用
st.title("Gay Spa 香港討論區")

if 'user' not in st.session_state:
    auth_page()
else:
    role = st.session_state.get('role', 'user')
    avatar = st.session_state.get('avatar')
    
    if avatar:
        st.sidebar.image(f"data:image/png;base64,{avatar}", width=100)
    st.sidebar.write(f"歡迎，{st.session_state['user']}！（角色：{role}）")
    
    with st.sidebar:
        st.header("更新頭像")
        new_avatar = st.file_uploader("選擇新頭像", type=["jpg", "png", "jpeg"], key="update_avatar")
        if st.button("上傳頭像") and new_avatar:
            avatar_data = base64.b64encode(new_avatar.read()).decode()
            c.execute("UPDATE users SET avatar=? WHERE username=?", (avatar_data, st.session_state['user']))
            conn.commit()
            st.session_state['avatar'] = avatar_data
            st.success("頭像已更新！")
            st.rerun()
    
    if st.sidebar.button("登出"):
        del st.session_state['user']
        del st.session_state['role']
        del st.session_state['avatar']
        st.rerun()
    
    with st.sidebar:
        st.header("發新帖")
        title = st.text_input("標題")
        content = st.text_area("內容")
        if st.button("提交"):
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO posts (title, content, author, date) VALUES (?, ?, ?, ?)", (title, content, st.session_state['user'], date))
            conn.commit()
            st.success("帖子已發佈！")

    posts = c.execute("SELECT * FROM posts ORDER BY date DESC").fetchall()
    for post in posts:
        c.execute("SELECT avatar FROM users WHERE username=?", (post[3],))
        result = c.fetchone()
        post_avatar = result[0] if result else None
        with st.expander(f"{post[1]} by {post[3]} on {post[4]}"):
            if post_avatar:
                st.image(f"data:image/png;base64,{post_avatar}", width=50, caption=f"{post[3]} 的頭像")
            st.write(post[2])
            
            if role == 'admin':
                if st.button("刪除此帖子", key=f"del_post_{post[0]}"):
                    c.execute("DELETE FROM posts WHERE id=?", (post[0],))
                    c.execute("DELETE FROM messages WHERE post_id=?", (post[0],))
                    conn.commit()
                    st.rerun()
            
            st.subheader("實時留言")
            messages = c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],)).fetchall()
            for msg in messages:
                c.execute("SELECT avatar FROM users WHERE username=?", (msg[3],))
                result = c.fetchone()
                msg_avatar = result[0] if result else None
                if msg_avatar:
                    st.image(f"data:image/png;base64,{msg_avatar}", width=30)
                st.write(f"{msg[3]} ({msg[4]}): {msg[2]}")
                if role == 'admin':
                    if st.button("刪除", key=f"del_msg_{msg[0]}"):
                        c.execute("DELETE FROM messages WHERE id=?", (msg[0],))
                        conn.commit()
                        st.rerun()
            
            msg_content = st.text_input("留言", key=f"msg_{post[0]}")
            if st.button("發送", key=f"send_{post[0]}"):
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)", (post[0], msg_content, st.session_state['user'], date))
                conn.commit()
                st.rerun()

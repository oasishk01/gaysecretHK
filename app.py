import streamlit as st
import sqlite3
from datetime import datetime
import hashlib

# 初始化資料庫
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)''')
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
            c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
            result = c.fetchone()
            if result and result[0] == hash_password(password):
                st.session_state['user'] = username
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("用戶名或密碼錯誤")    
    with tab2:
        new_username = st.text_input("新用戶名", key="reg_username")
        new_password = st.text_input("新密碼", type="password", key="reg_password")
        confirm_password = st.text_input("確認密碼", type="password", key="reg_confirm")
        if st.button("註冊"):
            if new_password != confirm_password:
                st.error("密碼不匹配")
            else:
                try:
                    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (new_username, hash_password(new_password)))
                    conn.commit()
                    st.success("註冊成功！請登入。")
                except sqlite3.IntegrityError:
                    st.error("用戶名已存在")

# Streamlit 應用
st.title("Gay Spa 香港討論區")

# 檢查登入狀態
if 'user' not in st.session_state:
    auth_page()
else:
    st.sidebar.write(f"歡迎，{st.session_state['user']}！")
    if st.sidebar.button("登出"):
        del st.session_state['user']
        st.rerun()
    
    # 側邊欄：發新帖（僅登入用戶）
    with st.sidebar:
        st.header("發新帖")
        title = st.text_input("標題")
        content = st.text_area("內容")
        if st.button("提交"):
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO posts (title, content, author, date) VALUES (?, ?, ?, ?)", (title, content, st.session_state['user'], date))
            conn.commit()
            st.success("帖子已發佈！")

    # 主頁：顯示所有帖子
    posts = c.execute("SELECT * FROM posts ORDER BY date DESC").fetchall()
    for post in posts:
        with st.expander(f"{post[1]} by {post[3]} on {post[4]}"):
            st.write(post[2])            
            # 實時留言區
            st.subheader("實時留言")
            messages = c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],)).fetchall()
            for msg in messages:
                st.write(f"{msg[3]} ({msg[4]}): {msg[2]}")            
            # 發留言（僅登入用戶）
            msg_content = st.text_input("留言", key=f"msg_{post[0]}")
            if st.button("發送", key=f"send_{post[0]}"):
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)", (post[0], msg_content, st.session_state['user'], date))
                conn.commit()
                st.rerun()

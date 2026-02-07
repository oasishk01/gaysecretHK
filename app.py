"""
討論區 v2.0 - 學習MCP Pattern後優化版
"""

import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
from datetime import datetime

# ==================== 數據庫 ====================
def init_db():
    """初始化數據庫"""
    with sqlite3.connect('users.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT
            )
        ''')
    
    with sqlite3.connect('forum.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                author TEXT,
                date TEXT,
                category TEXT DEFAULT '一般'
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                post_id INTEGER,
                content TEXT,
                author TEXT,
                date TEXT
            )
        ''')

def get_users():
    """拎所有用戶"""
    try:
        with sqlite3.connect('users.db') as conn:
            rows = conn.execute('SELECT * FROM users').fetchall()
            return {row[0]: {'name': row[1], 'password': row[2], 'email': row[3]} for row in rows}
    except:
        return {}

def save_user(username, name, password, email=''):
    """保存用戶"""
    with sqlite3.connect('users.db') as conn:
        conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)',
                   (username, name, password, email))

def get_posts(search=''):
    """拎帖子"""
    with sqlite3.connect('forum.db') as conn:
        if search:
            rows = conn.execute(
                'SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY date DESC',
                (f'%{search}%', f'%{search}%')
            ).fetchall()
        else:
            rows = conn.execute('SELECT * FROM posts ORDER BY date DESC').fetchall()
        return rows

def save_post(title, content, author, category):
    """保存帖子"""
    with sqlite3.connect('forum.db') as conn:
        conn.execute(
            'INSERT INTO posts (title, content, author, date, category) VALUES (?, ?, ?, ?, ?)',
            (title, content, author, datetime.now().strftime('%Y-%m-%d %H:%M'), category)
        )

# ==================== 初始化 ====================
init_db()
credentials = get_users()

# ==================== Authenticator ====================
authenticator = stauth.Authenticate(
    credentials,
    'forum_cookie',
    'forum_secret',
    cookie_expiry_days=30
)

# ==================== 頁面設置 ====================
st.set_page_config(page_title="討論區", page_icon="💬", layout="wide")

# CSS - 白底黑字
st.markdown('''
<style>
.stApp { background: #fff; color: #000; }
* { color: #000 !important; }
h1, h2, h3 { font-weight: bold; }
.stButton > button {
    background: #333 !important; color: #fff !important;
    border-radius: 4px !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #fff !important; color: #000 !important;
    border: 1px solid #000 !important;
}
footer { visibility: hidden; }
</style>
''', unsafe_allow_html=True)

# 標題
st.markdown('''
<div style="background: #fff; padding: 16px 24px; margin: -20px -20px 16px -20px; border-bottom: 2px solid #000;">
    <h1>討論區</h1>
    <p style="color: #666;">分享 · 傾偈 · 交流</p>
</div>
''', unsafe_allow_html=True)

# ==================== 側邊欄 ====================
with st.sidebar:
    st.markdown('### 用戶')
    
    if st.session_state.get('authentication_status'):
        st.markdown(f'**歡迎 {st.session_state.name}**')
        authenticator.logout('登出', 'main')
    else:
        # 登入
        st.markdown('#### 登入')
        name, auth_status, username = authenticator.login('登入', 'main')
        
        if auth_status:
            st.session_state.authentication_status = True
            st.session_state.name = name
            st.session_state.username = username
            st.success(f'歡迎 {name}！')
        elif auth_status is False:
            st.error('用戶名或密碼錯誤')
        
        # 註冊
        st.markdown('---')
        st.markdown('#### 註冊')
        try:
            if authenticator.register_user('註冊', preauthorization=False):
                users = get_users()
                if users:
                    new_user = list(users.keys())[-1]
                    user_data = users[new_user]
                    save_user(
                        new_user,
                        user_data['name'],
                        user_data['password'],
                        user_data.get('email', '')
                    )
                st.success('註冊成功！請登入。')
        except Exception as e:
            if 'already exists' not in str(e):
                st.error(str(e))

# ==================== 主頁 ====================
st.title('討論區')

if st.session_state.get('authentication_status'):
    user = st.session_state.username
    st.success(f'你已登入為 {user}')
    
    # 發帖
    with st.expander('發佈新帖'):
        title = st.text_input('標題')
        content = st.text_area('內容')
        category = st.selectbox('分類', ['一般', '討論', '問題', '分享', '吹水'])
        if st.button('發佈'):
            if title and content:
                save_post(title, content, user, category)
                st.success('發佈成功！')
                st.rerun()

# 搜尋
search = st.text_input('🔍 搜尋', placeholder='輸入關鍵詞...')

# 帖子列表
posts = get_posts(search)
st.markdown(f'**帖子 ({len(posts)})**')

for post in posts:
    with st.expander(f'📌 {post[1]}'):
        st.markdown(f'''
        <span style="background: #000; color: #fff; padding: 2px 8px; border-radius: 2px; font-size: 12px;">{post[5]}</span>
        <span style="color: #666; font-size: 12px;">{post[4]} · {post[3]}</span>
        ''', unsafe_allow_html=True)
        st.write(post[2])

# ==================== 底部 ====================
st.markdown('''
<hr style="margin: 24px 0; border: none; border-top: 1px solid #000;">
<div style="text-align: center; font-size: 12px; padding: 16px;">討論區</div>
''', unsafe_allow_html=True)

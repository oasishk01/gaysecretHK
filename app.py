"""
討論區 - 簡潔有力版
"""
import streamlit as st
import streamlit_authenticator as stauth
import sqlite3

# ==================== 數據庫 ====================
def init_users_db():
    """創建用戶表"""
    with sqlite3.connect('users.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT
            )
        ''')

def get_all_users():
    """拎所有用戶"""
    try:
        with sqlite3.connect('users.db') as conn:
            rows = conn.execute('SELECT * FROM users').fetchall()
            users = {}
            for row in rows:
                users[row[0]] = {
                    'name': row[1],
                    'password': row[2],
                    'email': row[3] or ''
                }
            return users
    except:
        return {}

def save_user(username, name, password, email=''):
    """保存新用戶"""
    with sqlite3.connect('users.db') as conn:
        conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)',
                   (username, name, password, email))

# ==================== 初始化 ====================
init_users_db()
credentials = get_all_users()

# ==================== Authenticator ====================
authenticator = stauth.Authenticate(
    credentials,
    'forum_cookie',
    'forum_secret_key',
    cookie_expiry_days=30
)

# ==================== 頁面設置 ====================
st.set_page_config(page_title="討論區", page_icon="💬", layout="wide")

# CSS
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
.post-card {
    background: #fff !important; border: 1px solid #000 !important;
    border-radius: 4px !important; padding: 8px; margin: 8px 0;
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
                # Save new user to database
                users = get_all_users()
                if users:
                    new_username = list(users.keys())[-1]
                    new_user = users[new_username]
                    save_user(
                        new_username,
                        new_user['name'],
                        new_user['password'],
                        new_user.get('email', '')
                    )
                st.success('註冊成功！請登入。')
        except Exception as e:
            if 'already exists' not in str(e):
                st.error(str(e))

# ==================== 主頁 ====================
st.title('討論區')

if st.session_state.get('authentication_status'):
    st.success(f'你已登入為 {st.session_state.username}')
else:
    st.warning('請登入或註冊以發帖和留言')

st.markdown('---')
st.markdown('**最新帖文**')
st.write('暫時未有帖子，快啲登入發第一個啦！')

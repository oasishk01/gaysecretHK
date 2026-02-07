import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
from datetime import datetime

# ==================== 初始化數據庫 ====================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')
    conn.commit()
    conn.close()

def init_forum_db():
    conn = sqlite3.connect('forum.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, 
        date TEXT, category TEXT DEFAULT '一般'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT
    )''')
    conn.commit()
    conn.close()

init_db()
init_forum_db()

# ==================== 用戶數據庫函數 ====================
def load_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, name, password, email FROM users")
    users = c.fetchall()
    conn.close()
    credentials = {"usernames": {}}
    for user in users:
        credentials["usernames"][user[0]] = {
            "name": user[1],
            "password": user[2],
            "email": user[3]
        }
    return credentials

def save_user(username, name, hashed_password, email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, name, password, email) VALUES (?, ?, ?, ?)",
              (username, name, hashed_password, email))
    conn.commit()
    conn.close()

def safe_fetch(query, params=()):
    conn = sqlite3.connect('forum.db')
    c = conn.cursor()
    c.execute(query, params)
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def time_ago(d):
    try:
        diff = (datetime.now() - datetime.strptime(d, "%Y-%m-%d %H:%M")).total_seconds()
        if diff < 60: return "剛才"
        if diff < 3600: return f"{int(diff/60)}分鐘前"
        if diff < 86400: return f"{int(diff/3600)}小時前"
        return d
    except: return d

# ==================== 頁面設置 ====================
st.set_page_config(page_title="討論區", page_icon="💬", layout="wide")

# ==================== CSS - 白底黑字 ====================
st.markdown("""
<style>
.stApp { background-color: #ffffff; color: #000000; }
* { color: #000000 !important; }
h1, h2, h3 { font-weight: bold; }
.stButton > button {
    background-color: #333333 !important;
    color: #ffffff !important;
    border-radius: 4px !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #000000 !important;
}
.post-card {
    background-color: #ffffff !important;
    border: 1px solid #000000 !important;
    border-radius: 4px !important;
    padding: 8px !important;
    margin: 8px 0 !important;
}
.category-tag {
    display: inline-block;
    padding: 2px 8px;
    background-color: #000000;
    color: #ffffff !important;
    border-radius: 2px;
    font-size: 12px;
}
[data-testid="stSidebar"] { background-color: #ffffff !important; }
.streamlit-expanderHeader {
    background-color: #ffffff !important;
    border: 1px solid #000000 !important;
}
footer { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 標題 ====================
st.markdown("""
<div style="background-color: #ffffff; padding: 16px 24px; margin: -20px -20px 16px -20px; border-bottom: 2px solid #000000;">
    <h1>討論區</h1>
    <p style="color: #666666;">分享 · 傾偈 · 交流</p>
</div>
""", unsafe_allow_html=True)

# ==================== 初始化Authenticator ====================
credentials = load_users()
authenticator = stauth.Authenticate(
    credentials,
    "gaysecreet_cookie",
    "gaysecreet_key",
    cookie_expiry_days=30
)

# ==================== 側邊欄 ====================
with st.sidebar:
    st.markdown("### 用戶")
    
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    
    name, auth_status, username = authenticator.login('登入', 'main')
    
    if auth_status:
        st.session_state.authentication_status = True
        st.session_state.username = username
        st.session_state.name = name
        st.markdown(f"**歡迎 {name}！**")
    
    if auth_status is False:
        st.error('用戶名/密碼錯誤')
    
    if auth_status is None:
        # 註冊
        st.markdown("---")
        st.markdown("### 註冊")
        try:
            if authenticator.register_user('註冊', preauthorization=False):
                new_username = list(credentials["usernames"].keys())[-1]
                new_name = credentials["usernames"][new_username]["name"]
                new_password = credentials["usernames"][new_username]["password"]
                new_email = credentials["usernames"][new_username].get("email", "")
                save_user(new_username, new_name, new_password, new_email)
                st.success('註冊成功！請登入。')
        except Exception as e:
            if "already exists" not in str(e):
                st.error(str(e))
    
    if st.session_state.authentication_status:
        authenticator.logout('登出', 'main')
        st.session_state.authentication_status = None
        st.rerun()

# ==================== 主頁 ====================
if st.session_state.authentication_status:
    user = st.session_state.username
    name = st.session_state.name
    
    with st.sidebar:
        st.markdown(f"**{name}**")
        st.markdown("---")
        st.markdown("### 發新帖")
        new_title = st.text_input("標題", key="new_title", placeholder="標題")
        new_content = st.text_area("內容", key="new_content", placeholder="內容...", height=80)
        category = st.selectbox("分類", ["一般", "討論", "問題", "分享", "吹水"])
        
        if st.button("發布"):
            if new_title and new_content:
                conn = sqlite3.connect('forum.db')
                c = conn.cursor()
                c.execute("""INSERT INTO posts (title, content, author, date, category) 
                          VALUES (?, ?, ?, ?, ?)""",
                         (new_title, new_content, name, datetime.now().strftime("%Y-%m-%d %H:%M"), category))
                conn.commit()
                conn.close()
                st.success("發布成功！")
                st.rerun()
            else:
                st.error("請填寫標題和內容")
    
    search_term = st.text_input("🔍 搜尋帖子...", placeholder="輸入關鍵詞...")
    
    # 統計
    u_cnt = safe_fetch("SELECT COUNT(*) FROM users")
    p_cnt = safe_fetch("SELECT COUNT(*) FROM posts")
    m_cnt = safe_fetch("SELECT COUNT(*) FROM messages")
    
    st.markdown(f"""
    <div style="display: flex; gap: 12px; margin: 16px 0;">
        <div style="background: #fff; padding: 12px 20px; border: 1px solid #000; flex: 1; text-align: center;">
            <div style="font-size: 20px; font-weight: bold;">{u_cnt}</div>
            <div style="color: #666;">用戶</div>
        </div>
        <div style="background: #fff; padding: 12px 20px; border: 1px solid #000; flex: 1; text-align: center;">
            <div style="font-size: 20px; font-weight: bold;">{p_cnt}</div>
            <div style="color: #666;">帖子</div>
        </div>
        <div style="background: #fff; padding: 12px 20px; border: 1px solid #000; flex: 1; text-align: center;">
            <div style="font-size: 20px; font-weight: bold;">{m_cnt}</div>
            <div style="color: #666;">留言</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 帖子列表
    conn = sqlite3.connect('forum.db')
    c = conn.cursor()
    query = f"%{search_term}%" if search_term else "%"
    c.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY date DESC", (query, query))
    posts = c.fetchall()
    conn.close()
    
    st.markdown(f"**帖子 ({len(posts)})**")
    
    for post in posts:
        with st.expander(f" {post[1]}"):
            col_author, col_content = st.columns([1, 5])
            with col_author:
                st.markdown(f"""<div style="width:40px;height:40px;background:#000;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;color:#fff;
                            font-weight:bold;font-size:14px;">{post[3][0].upper()}</div>""", unsafe_allow_html=True)
            
            with col_content:
                st.markdown(f"""<span class="category-tag">{post[5]}</span>
                <span style="color:#666;font-size:12px;">{post[4]} · {post[3]}</span>""", unsafe_allow_html=True)
                st.write(post[2])
            
            st.markdown("---")
            st.markdown("**留言**")
            
            conn = sqlite3.connect('forum.db')
            c = conn.cursor()
            c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],))
            msgs = c.fetchall()
            conn.close()
            
            for msg in msgs:
                st.markdown(f"- **{msg[3]}**: {msg[2]} <span style='color:#666;'>({time_ago(msg[4])})</span>", unsafe_allow_html=True)
            
            msg_content = st.text_input("留言", key=f"msg_{post[0]}", placeholder="寫留言...")
            if st.button("發送", key=f"send_{post[0]}"):
                if msg_content:
                    conn = sqlite3.connect('forum.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)",
                             (post[0], msg_content, name, datetime.now().strftime("%H:%M")))
                    conn.commit()
                    conn.close()
                    st.rerun()

else:
    st.warning("請登入或註冊以發帖和留言。")
    
    # 匿名瀏覽
    st.markdown("### 瀏覽帖文")
    
    conn = sqlite3.connect('forum.db')
    c = conn.cursor()
    c.execute("SELECT * FROM posts ORDER BY date DESC LIMIT 10")
    posts = c.fetchall()
    conn.close()
    
    for post in posts:
        st.markdown(f"**{post[1]}**")
        st.write(post[2])
        st.markdown(f"<span style='color:#666;font-size:12px;'>{post[4]} · {post[3]}</span>", unsafe_allow_html=True)
        st.markdown("---")

# 底部
st.markdown("""
<hr style="margin: 24px 0; border: none; border-top: 1px solid #000;">
<div style="text-align: center; font-size: 12px; padding: 16px;">討論區</div>
""", unsafe_allow_html=True)

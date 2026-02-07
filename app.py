import streamlit as st
import sqlite3
from datetime import datetime
import hashlib

# ==================== 初始化 ====================
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, 
    role TEXT DEFAULT 'user', join_date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, 
    date TEXT, category TEXT DEFAULT '一般'
)''')

c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT
)''')
conn.commit()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

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
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 4px !important;
    }
    .stButton > button:hover {
        background-color: #333333 !important;
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
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==================== 標題 ====================
st.markdown("""
<div style="background-color: #ffffff; padding: 16px 24px; margin: -20px -20px 16px -20px; border-bottom: 2px solid #000000;">
    <h1>討論區</h1>
    <p style="color: #666666;">分享 · 傾偈 · 交流</p>
</div>
""", unsafe_allow_html=True)

# ==================== 登入/註冊 ====================
if 'user' not in st.session_state:
    col_login, col_reg = st.columns([1, 1])
    
    with col_login:
        st.markdown('<div class="post-card">', unsafe_allow_html=True)
        st.markdown("### 登入")
        username = st.text_input("用戶名", key="login_user", placeholder="用戶名")
        password = st.text_input("密碼", type="password", key="login_pass", placeholder="密碼")
        
        if st.button("登入", key="btn_login"):
            c.execute("SELECT password_hash, role FROM users WHERE username=?", (username,))
            user = c.fetchone()
            if user and user[0] == hash_pw(password):
                st.session_state['user'] = username
                st.session_state['role'] = user[1]
                st.rerun()
            else:
                st.error("用戶名或密碼錯誤")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_reg:
        st.markdown('<div class="post-card">', unsafe_allow_html=True)
        st.markdown("### 註冊")
        new_username = st.text_input("用戶名", key="reg_user", placeholder="用戶名")
        new_password = st.text_input("密碼", type="password", key="reg_pass", placeholder="密碼")
        confirm_password = st.text_input("確認密碼", type="password", key="reg_confirm", placeholder="確認密碼")
        
        if st.button("註冊", key="btn_reg"):
            if not new_username:
                st.error("用戶名不能為空")
            elif not new_password:
                st.error("密碼不能為空")
            elif new_password != confirm_password:
                st.error("密碼不一致")
            else:
                try:
                    c.execute("SELECT COUNT(*) FROM users")
                    is_first = c.fetchone()[0] == 0
                    role = 'admin' if is_first else 'user'
                    c.execute("""INSERT INTO users (username, password_hash, role, join_date) 
                              VALUES (?, ?, ?, ?)""",
                             (new_username, hash_pw(new_password), role, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("註冊成功！請登入")
                except sqlite3.IntegrityError:
                    st.error("用戶名已被使用")
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== 主頁 ====================
else:
    user = st.session_state['user']
    role = st.session_state.get('role', 'user')
    
    with st.sidebar:
        st.markdown(f"""<div style="background: #fff; padding: 12px; border: 1px solid #000; margin-bottom: 12px;">
            <strong>{user}</strong>
            <span style="background: #000; color: #fff; padding: 2px 8px; font-size: 12px; margin-left: 8px;">{role}</span>
        </div>""", unsafe_allow_html=True)
        
        if st.button("登出"):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("**發新帖**")
        new_title = st.text_input("標題", key="new_title", placeholder="標題")
        new_content = st.text_area("內容", key="new_content", placeholder="內容...", height=80)
        category = st.selectbox("分類", ["一般", "討論", "問題", "分享", "吹水"])
        
        if st.button("發布"):
            if new_title and new_content:
                c.execute("""INSERT INTO posts (title, content, author, date, category) 
                          VALUES (?, ?, ?, ?, ?)""",
                         (new_title, new_content, user, datetime.now().strftime("%Y-%m-%d %H:%M"), category))
                conn.commit()
                st.success("發布成功！")
                st.rerun()
            else:
                st.error("請填寫標題和內容")
    
    search_term = st.text_input("搜尋帖子...", placeholder="輸入關鍵詞...")
    
    c.execute("SELECT COUNT(*) FROM users")
    c.execute("SELECT COUNT(*) FROM posts")
    c.execute("SELECT COUNT(*) FROM messages")
    u_cnt = c.fetchone()[0]
    p_cnt = c.fetchone()[0]
    m_cnt = c.fetchone()[0]
    
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
    
    query = f"%{search_term}%" if search_term else "%"
    c.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY date DESC", (query, query))
    posts = c.fetchall()
    
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
            c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],))
            msgs = c.fetchall()
            for msg in msgs:
                st.markdown(f"- **{msg[3]}**: {msg[2]} <span style='color:#666;'>({time_ago(msg[4])})</span>", unsafe_allow_html=True)
            
            msg_content = st.text_input("留言", key=f"msg_{post[0]}", placeholder="寫留言...")
            if st.button("發送", key=f"send_{post[0]}"):
                if msg_content:
                    c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)",
                             (post[0], msg_content, user, datetime.now().strftime("%H:%M")))
                    conn.commit()
                    st.rerun()

st.markdown("""
<hr style="margin: 24px 0; border: none; border-top: 1px solid #000;">
<div style="text-align: center; font-size: 12px; padding: 16px;">討論區</div>
""", unsafe_allow_html=True)

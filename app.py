import streamlit as st
import sqlite3
from datetime import datetime
import hashlib

# ==================== 初始化 ====================
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()

# 確保tables存在
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, 
    role TEXT DEFAULT 'user', avatar TEXT, bio TEXT, email TEXT,
    join_date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, 
    date TEXT, category TEXT DEFAULT '一般', view_count INTEGER DEFAULT 0
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
st.set_page_config(page_title="討論區", page_icon="💬", layout="centered")

# ==================== CSS - 柔和配色 ====================
st.markdown("""
<style>
    /* 柔和配色方案 */
    .stApp {
        background-color: #fafafa;
        color: #333333;
    }
    
    /* 標題 */
    h1 {
        color: #2d3748 !important;
        font-size: 28px !important;
        font-weight: 600 !important;
        text-align: center;
        margin-bottom: 8px !important;
    }
    
    h2, h3, h4 {
        color: #2d3748 !important;
        font-weight: 500 !important;
    }
    
    /* 按鈕 - 柔和藍 */
    .stButton > button {
        background-color: #5c7cfa !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background-color: #4263eb !important;
        transform: translateY(-1px);
    }
    
    /* 輸入框 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 10px 12px !important;
        background-color: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #5c7cfa !important;
        box-shadow: 0 0 0 3px rgba(92, 124, 250, 0.15) !important;
    }
    
    /* 卡片 */
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 1px solid #eee;
    }
    
    /* 標籤 */
    .tag {
        display: inline-block;
        padding: 4px 10px;
        background-color: #5c7cfa;
        color: white;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 6px;
    }
    
    /* 側邊欄 */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid #eee !important;
    }
    
    /* 擴展器 */
    .streamlit-expanderHeader {
        background-color: white !important;
        border: 1px solid #eee !important;
        border-radius: 10px !important;
        color: #333 !important;
    }
    
    /* 占位符 */
    ::placeholder {
        color: #adb5bd !important;
    }
    
    /* 成功/錯誤訊息 */
    .stSuccess, .stError {
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 標題 ====================
st.markdown("""
<div style="text-align: center; padding: 24px 0 20px;">
    <h1>💬 討論區</h1>
    <p style="color: #868e96; font-size: 14px; margin: 0;">分享 · 傾偈 · 交流</p>
</div>
""", unsafe_allow_html=True)

# ==================== 登入/註冊 ====================
if 'user' not in st.session_state:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["登入", "註冊"])
    
    with tab1:
        st.markdown("#### 🔐 登入")
        username = st.text_input("用戶名", key="login_user", placeholder="輸入用戶名")
        password = st.text_input("密碼", type="password", key="login_pass", placeholder="輸入密碼")
        
        if st.button("登入", key="login_btn"):
            if username and password:
                c.execute("SELECT password_hash, role, avatar FROM users WHERE username=?", (username,))
                user = c.fetchone()
                if user and user[0] == hash_pw(password):
                    st.session_state['user'] = username
                    st.session_state['role'] = user[1]
                    st.session_state['avatar'] = user[2]
                    st.rerun()
                else:
                    st.error("用戶名或密碼錯誤")
            else:
                st.error("請輸入用戶名和密碼")
        else:
            st.markdown("")
    
    with tab2:
        st.markdown("#### ✨ 註冊")
        new_username = st.text_input("用戶名", key="reg_user", placeholder="選擇用戶名")
        new_password = st.text_input("密碼", type="password", key="reg_pass", placeholder="設定密碼")
        confirm_password = st.text_input("確認密碼", type="password", key="reg_confirm", placeholder="再次輸入密碼")
        email = st.text_input("Email（可選）", key="reg_email", placeholder="你的電郵")
        bio = st.text_area("個人簡介（可選）", key="reg_bio", placeholder="介紹一下自己...", height=60)
        
        if st.button("註冊", key="reg_btn"):
            if not new_username:
                st.error("用戶名不能為空")
            elif not new_password:
                st.error("密碼不能為空")
            elif new_password != confirm_password:
                st.error("兩次密碼不一致")
            else:
                try:
                    c.execute("SELECT COUNT(*) FROM users")
                    is_first = c.fetchone()[0] == 0
                    role = 'admin' if is_first else 'user'
                    
                    c.execute("""INSERT INTO users (username, password_hash, role, bio, email, join_date) 
                              VALUES (?, ?, ?, ?, ?, ?)""",
                             (new_username, hash_pw(new_password), role, bio or '', email or '', datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("註冊成功！請登入")
                except sqlite3.IntegrityError:
                    st.error("用戶名已被使用")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 主頁 ====================
else:
    user = st.session_state['user']
    role = st.session_state.get('role', 'user')
    
    # 側邊欄
    with st.sidebar:
        st.markdown(f"### 👤 {user}")
        st.markdown(f"<span class='tag'>{role}</span>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("登出"):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("**📝 發新帖**")
        new_title = st.text_input("標題", key="new_title", placeholder="輸入標題")
        new_content = st.text_area("內容", key="new_content", placeholder="寫啲咩...", height=80)
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
                st.error("標題和內容都要填")
    
    # 搜尋
    search_term = st.text_input("🔍 搜尋", placeholder="輸入關鍵詞...")
    
    # 統計
    c.execute("SELECT COUNT(*) FROM users")
    c.execute("SELECT COUNT(*) FROM posts")
    c.execute("SELECT COUNT(*) FROM messages")
    u_cnt = c.fetchone()[0]
    p_cnt = c.fetchone()[0]
    m_cnt = c.fetchone()[0]
    
    st.markdown(f"""
    <div style="display: flex; gap: 16px; margin: 20px 0;">
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 24px; font-weight: 600; color: #5c7cfa;">{u_cnt}</div>
            <div style="color: #868e96; font-size: 13px;">用戶</div>
        </div>
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 24px; font-weight: 600; color: #5c7cfa;">{p_cnt}</div>
            <div style="color: #868e96; font-size: 13px;">帖子</div>
        </div>
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 24px; font-weight: 600; color: #5c7cfa;">{m_cnt}</div>
            <div style="color: #868e96; font-size: 13px;">留言</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 帖子列表
    query = f"%{search_term}%" if search_term else "%"
    c.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY date DESC", (query, query))
    posts = c.fetchall()
    
    st.markdown(f"**📋 帖子 ({len(posts)})**")
    
    for post in posts:
        with st.expander(f"📌 {post[1]}"):
            # 作者信息
            col1, col2 = st.columns([1, 5])
            with col1:
                c.execute("SELECT avatar FROM users WHERE username=?", (post[3],))
                av = c.fetchone()
                if av and av[0]:
                    st.markdown(f'<img src="data:image/png;base64,{av[0]}" style="width:36px;height:36px;border-radius:50%;">', unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="width:36px;height:36px;background:#5c7cfa;border-radius:50%;
                                display:flex;align-items:center;justify-content:center;color:white;
                                font-weight:500;font-size:14px;">
                        {post[3][0].upper()}
                    </div>
                    """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <span class='tag'>{post[5]}</span>
                <span style="color:#868e96;font-size:12px;">{post[4]} · {post[3]}</span>
                """, unsafe_allow_html=True)
                st.write(post[2])
            
            # 留言
            st.markdown("---")
            st.markdown("**💬 留言**")
            c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],))
            msgs = c.fetchall()
            for msg in msgs:
                st.markdown(f"- **{msg[3]}**: {msg[2]} ({time_ago(msg[4])})")
            
            # 發留言
            msg_content = st.text_input("寫留言...", key=f"msg_{post[0]}", label_visibility="collapsed")
            if st.button("發送", key=f"send_{post[0]}"):
                if msg_content:
                    c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)",
                             (post[0], msg_content, user, datetime.now().strftime("%H:%M")))
                    conn.commit()
                    st.rerun()

# 底部
st.markdown("""
<hr style="margin: 30px 0 20px; border: none; border-top: 1px solid #eee;">
<div style="text-align: center; color: #adb5bd; font-size: 12px;">
    💬 討論區
</div>
""", unsafe_allow_html=True)

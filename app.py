import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import base64

# ==================== 初始化 ====================
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, 
    role TEXT DEFAULT 'user', avatar TEXT, bio TEXT DEFAULT '', email TEXT DEFAULT '',
    join_date TEXT, last_active TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, 
    date TEXT, category TEXT DEFAULT '一般', view_count INTEGER DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY, user TEXT, message TEXT, date TEXT, read INTEGER DEFAULT 0
)''')
conn.commit()

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def time_ago(d):
    try:
        diff = (datetime.now() - datetime.strptime(d, "%Y-%m-%d %H:%M")).total_seconds()
        if diff < 60: return "剛才"
        if diff < 3600: return f"{int(diff/60)}分鐘前"
        if diff < 86400: return f"{int(diff/3600)}小時前"
        return d
    except: return d

# ==================== CSS ====================
st.set_page_config(page_title="Gay Spa 香港討論區", page_icon="💬", layout="wide")

st.markdown("""
<style>
    /* 全局 - 白底黑字 */
    .stApp { background: #ffffff; color: #333333 !important; }
    h1 { color: #222222 !important; text-align: center; font-size: 32px !important; margin-bottom: 10px !important; }
    h2, h3, h4 { color: #222222 !important; }
    p, div, span { color: #333333 !important; }
    
    /* 卡片 */
    .card { background: #fafafa; border-radius: 12px; padding: 20px; margin: 12px 0; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #eeeeee; }
    
    /* 按鈕 */
    .stButton > button { 
        background: #2563eb !important; color: white !important; 
        border-radius: 8px !important; border: none !important; 
        padding: 8px 20px !important; font-weight: 500 !important; 
    }
    
    /* 標籤 */
    .tag { display: inline-block; padding: 4px 12px; background: #2563eb; 
           color: white !important; border-radius: 15px; font-size: 12px; margin-right: 8px; }
    
    /* 輸入框 */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px !important; border: 1px solid #dddddd !important; 
        background: white !important; color: #333333 !important;
    }
    
    /* 側邊欄 */
    [data-testid="stSidebar"] { background: #f8f9fa !important; border-right: 1px solid #eeeeee !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div { color: #333333 !important; }
    
    /* 擴展器 */
    .streamlit-expanderHeader { background: #f8f9fa !important; color: #333333 !important; border-radius: 8px !important; }
    
    /* 輸入框 placeholder */
    ::placeholder { color: #999999 !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 標題 ====================
st.markdown("""
<div style="text-align: center; padding: 20px 0 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: -20px -20px 20px -20px;">
    <h1 style="color: white !important; margin: 0 !important;">💬 Gay Spa 香港討論區</h1>
    <p style="color: rgba(255,255,255,0.9) !important; margin: 10px 0 0 !important;">分享 · 傾偈 · 搵資料</p>
</div>
<hr style="margin: 20px 0;">
""", unsafe_allow_html=True)

# ==================== 登入/註冊 ====================
if 'user' not in st.session_state:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🔐 登入")
        username = st.text_input("用戶名", key="login_user")
        password = st.text_input("密碼", type="password", key="login_pass")
        if st.button("登入"):
            c.execute("SELECT password_hash, role, avatar FROM users WHERE username=?", (username,))
            r = c.fetchone()
            if r and r[0] == hash_pw(password):
                st.session_state['user'] = username
                st.session_state['role'] = r[1]
                st.session_state['avatar'] = r[2]
                st.rerun()
            else:
                st.error("登入失敗")
    
    with col2:
        st.markdown("### ✨ 註冊")
        new_user = st.text_input("用戶名", key="reg_user")
        new_pass = st.text_input("密碼", type="password", key="reg_pass")
        confirm = st.text_input("確認密碼", type="password", key="reg_confirm")
        email = st.text_input("Email", key="reg_email")
        bio = st.text_area("個人簡介", key="reg_bio")
        
        if st.button("註冊"):
            if new_pass != confirm:
                st.error("密碼唔匹配")
            else:
                try:
                    c.execute("SELECT COUNT(*) FROM users")
                    role = 'admin' if c.fetchone()[0] == 0 else 'user'
                    c.execute("""INSERT INTO users (username, password_hash, role, bio, email, join_date) 
                              VALUES (?, ?, ?, ?, ?, ?)""",
                             (new_user, hash_pw(new_pass), role, bio, email, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("註冊成功！請登入")
                except:
                    st.error("用戶名已存在")

# ==================== 主頁 ====================
else:
    user = st.session_state['user']
    role = st.session_state.get('role', 'user')
    
    with st.sidebar:
        st.markdown(f"### 👤 {user}")
        st.markdown(f"<span class='tag'>{role}</span>", unsafe_allow_html=True)
        
        c.execute("SELECT COUNT(*) FROM posts WHERE author=?", (user,))
        st.markdown(f"**帖子:** {c.fetchone()[0]}")
        
        if st.button("登出"):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📝 發新帖")
        title = st.text_input("標題", key="new_title")
        content = st.text_area("內容", key="new_content", height=80)
        cat = st.selectbox("分類", ["一般", "討論", "問題", "分享", "吹水"])
        
        if st.button("發布"):
            if title and content:
                c.execute("INSERT INTO posts (title, content, author, date, category) VALUES (?, ?, ?, ?, ?)",
                         (title, content, user, datetime.now().strftime("%Y-%m-%d %H:%M"), cat))
                conn.commit()
                st.success("發布成功！")
                st.rerun()
    
    # 搜尋 + 篩選
    col_s1, col_s2 = st.columns([3, 1])
    search = col_s1.text_input("🔍 搜尋", placeholder="輸入關鍵詞...")
    filter_cat = col_s2.selectbox("🏷️ 分類", ["全部"] + ["一般", "討論", "問題", "分享", "吹水"])
    
    # 統計
    c.execute("SELECT COUNT(*) FROM users")
    c.execute("SELECT COUNT(*) FROM posts")
    c.execute("SELECT COUNT(*) FROM messages")
    u_count = c.fetchone()[0]
    p_count = c.fetchone()[0]
    m_count = c.fetchone()[0]
    
    st.markdown(f"""
    <div style="display: flex; gap: 20px; margin: 20px 0;">
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 28px; font-weight: bold; color: #2563eb;">{u_count}</div>
            <div style="color: #666; font-size: 14px;">用戶</div>
        </div>
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 28px; font-weight: bold; color: #2563eb;">{p_count}</div>
            <div style="color: #666; font-size: 14px;">帖子</div>
        </div>
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 28px; font-weight: bold; color: #2563eb;">{m_count}</div>
            <div style="color: #666; font-size: 14px;">留言</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 帖子列表
    q = f"%{search}%" if search else "%"
    cat_q = f" AND category='{filter_cat}'" if filter_cat != "全部" else ""
    c.execute(f"SELECT * FROM posts WHERE (title LIKE ? OR content LIKE ?){cat_q} ORDER BY date DESC", (q, q))
    posts = c.fetchall()
    
    st.markdown(f"### 📋 帖子 ({len(posts)})")
    
    for post in posts:
        with st.expander(f"📌 {post[1]}"):
            c.execute("SELECT avatar FROM users WHERE username=?", (post[3],))
            av = c.fetchone()
            av_data = av[0] if av else None
            
            col_info, col_text = st.columns([1, 5])
            with col_info:
                if av_data:
                    st.markdown(f'<img src="data:image/png;base64,{av_data}" style="width:40px;height:40px;border-radius:50%;">', unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='width:40px;height:40px;background:#2563eb;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;'>{post[3][0].upper()}</div>", unsafe_allow_html=True)
            with col_text:
                st.markdown(f"""
                <span class='tag'>{post[5]}</span>
                <span style='color:#666;font-size:12px;'>{post[4]} · {post[3]}</span>
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
            mc = st.text_input("寫留言...", key=f"msg_{post[0]}", label_visibility="collapsed")
            if st.button("發送", key=f"send_{post[0]}"):
                if mc:
                    c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)",
                             (post[0], mc, user, datetime.now().strftime("%H:%M")))
                    conn.commit()
                    st.rerun()

# 底部
st.markdown("""
<hr style="margin: 30px 0;">
<div style="text-align: center; color: #999999; font-size: 12px;">
    💬 Gay Spa 香港討論區
</div>
""", unsafe_allow_html=True)

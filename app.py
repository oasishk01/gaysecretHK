import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import base64
import re

# ==================== 初始化資料庫 ====================
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()

# 新增 tables (如果未存在)
c.execute('''CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, 
    date TEXT, category TEXT DEFAULT '一般', view_count INTEGER DEFAULT 0
)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, 
    author TEXT, date TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, 
    role TEXT DEFAULT 'user', avatar TEXT DEFAULT NULL,
    bio TEXT DEFAULT '', email TEXT DEFAULT '',
    join_date TEXT, last_active TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY, user TEXT, type TEXT, 
    message TEXT, link TEXT, date TEXT, read INTEGER DEFAULT 0
)''')
conn.commit()

# ==================== 幫助函數 ====================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def send_notification(user, msg_type, message, link=''):
    c.execute("INSERT INTO notifications (user, type, message, link, date) VALUES (?, ?, ?, ?, ?)",
             (user, msg_type, message, link, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

def get_unread_count(user):
    c.execute("SELECT COUNT(*) FROM notifications WHERE user=? AND read=0", (user,))
    return c.fetchone()[0]

def time_ago(date_str):
    """將日期轉為 'X分鐘前' 格式"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        now = datetime.now()
        diff = (now - date).total_seconds()
        if diff < 60: return "剛才"
        if diff < 3600: return f"{int(diff/60)}分鐘前"
        if diff < 86400: return f"{int(diff/3600)}小時前"
        return f"{int(diff/86400)}日前"
    except: return date_str

# ==================== CSS 靚靚樣式 ====================
st.markdown("""
<style>
/* 全局 */
.stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
h1 { color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); text-align: center; font-size: 42px !important; }
h2, h3, h4 { color: #5a4a7a !important; }

/* 卡片 */
.card { background: white; border-radius: 20px; padding: 25px; margin: 15px 0; 
        box-shadow: 0 8px 30px rgba(0,0,0,0.12); transition: all 0.3s !important; }
.card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.18) !important; }

/* 按鈕 */
.stButton > button { 
    background: linear-gradient(90deg, #667eea, #764ba2) !important; 
    color: white !important; border-radius: 25px !important; 
    border: none !important; padding: 12px 30px !important; 
    font-weight: 600 !important; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important; 
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important; }

/* 輸入框 */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    border-radius: 12px !important; border: 2px solid #ddd !important; padding: 12px !important;
}

/* 標籤 */
.tag { display: inline-block; padding: 5px 15px; background: linear-gradient(90deg, #667eea, #764ba2);
       color: white; border-radius: 20px; font-size: 12px; font-weight: 600; margin-right: 5px; }
.tag.hot { background: linear-gradient(90deg, #f093fb, #f5576c); }

/* 通知 */
.notif { background: white; padding: 15px; border-radius: 15px; margin: 10px 0;
         box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-left: 4px solid #667eea; }
.notif.unread { border-left-color: #f5576c; }

/* 統計 */
.stat-box { background: white; border-radius: 15px; padding: 20px; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
.stat-num { font-size: 32px; font-weight: 700; background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stat-label { color: #666; font-size: 14px; }

/* 頭像 */
.avatar { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 3px solid #667eea; }
.avatar.small { width: 40px; height: 40px; }
.avatar.large { width: 120px; height: 120px; }

/* 擴展器 */
.stExpander summary { 
    background: linear-gradient(90deg, #667eea, #764ba2) !important; 
    color: white !important; padding: 20px !important; border-radius: 20px !important; 
}

/* Profile */
.profile-header { background: white; border-radius: 20px; padding: 30px; text-align: center; 
                   box-shadow: 0 8px 30px rgba(0,0,0,0.12); margin: 20px 0; }

/* Tab */
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, #667eea, #764ba2) !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 類別定義 ====================
CATEGORIES = ['一般', '討論', '問題', "分享", '吹水', '通知']

# ==================== 主頁標題 ====================
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h1>💬 Gay Spa 香港討論區</h1>
    <p style="color: rgba(255,255,255,0.9); font-size: 18px;">分享 · 傾偈 · 搵資料 📱</p>
</div>
<hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent); margin: 20px 0;">
""", unsafe_allow_html=True)

# ==================== 登入/註冊頁面 ====================
if 'user' not in st.session_state:
    st.markdown("""
    <div class="card" style="max-width: 450px; margin: 50px auto;">
        <h2 style="text-align: center; margin-bottom: 30px;">💬 歡迎加入！</h2>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 登入", "✨ 註冊"])
    
    with tab1:
        username = st.text_input("用戶名", placeholder="輸入用戶名")
        password = st.text_input("密碼", type="password", placeholder="輸入密碼")
        if st.button("🚀 登入"):
            c.execute("SELECT password_hash, role, avatar FROM users WHERE username=?", (username,))
            result = c.fetchone()
            if result and result[0] == hash_password(password):
                st.session_state['user'] = username
                st.session_state['role'] = result[1]
                st.session_state['avatar'] = result[2]
                # 更新最後上線時間
                c.execute("UPDATE users SET last_active=? WHERE username=?", (datetime.now().isoformat(), username))
                conn.commit()
                st.balloons()
                st.rerun()
            else:
                st.error("用戶名或密碼錯誤 😅")
    
    with tab2:
        new_username = st.text_input("用戶名", placeholder="選擇用戶名")
        new_password = st.text_input("密碼", type="password", placeholder="設定密碼")
        confirm_password = st.text_input("確認密碼", type="password", placeholder="再次輸入密碼")
        email = st.text_input("Email (用於通知)", placeholder="your@email.com")
        avatar_upload = st.file_uploader("上傳頭像 (可選)", type=["jpg", "png", "jpeg"])
        bio = st.text_area("個人簡介", placeholder="介绍一下你自己...")
        
        if st.button("✨ 註冊"):
            if new_password != confirm_password:
                st.error("密碼不匹配 😅")
            elif not new_username:
                st.error("用戶名不能為空 😅")
            else:
                avatar_data = None
                if avatar_upload:
                    avatar_data = base64.b64encode(avatar_upload.read()).decode()
                try:
                    c.execute("SELECT COUNT(*) FROM users")
                    user_count = c.fetchone()[0]
                    role = 'admin' if user_count == 0 else 'user'
                    c.execute("INSERT INTO users (username, password_hash, role, avatar, bio, email, join_date, last_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (new_username, hash_password(new_password), role, avatar_data, bio, email, datetime.now().isoformat(), datetime.now().isoformat()))
                    conn.commit()
                    st.success("🎉 註冊成功！歡迎加入！")
                    # 通知所有admin有新用戶
                    c.execute("SELECT username FROM users WHERE role='admin'")
                    admins = c.fetchall()
                    for admin in admins:
                        if admin[0] != new_username:
                            send_notification(admin[0], 'new_user', f'🎉 新用戶加入：{new_username}', '')
                except sqlite3.IntegrityError:
                    st.error("用戶名已存在 😅")

# ==================== 登入後主頁 ====================
else:
    user = st.session_state['user']
    role = st.session_state.get('role', 'user')
    avatar = st.session_state.get('avatar')
    
    # ==================== 側邊欄 ====================
    with st.sidebar:
        st.markdown("### 👤 用戶中心")
        
        # 頭像 + 名字
        col1, col2 = st.columns([1, 2])
        with col1:
            if avatar:
                st.markdown(f'<img src="data:image/png;base64,{avatar}" class="avatar">', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #667eea, #764ba2); 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 20px;">👤</div>
                """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{user}**")
            st.markdown(f"<span class='tag'>{role}</span>", unsafe_allow_html=True)
        
        # 未讀通知數
        unread = get_unread_count(user)
        if unread > 0:
            st.markdown(f"<span class='tag hot'>🔔 {unread} 未讀</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 用戶統計
        c.execute("SELECT COUNT(*) FROM posts WHERE author=?", (user,))
        user_posts = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM messages WHERE author=?", (user,))
        user_messages = c.fetchone()[0]
        
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-num">{user_posts}</div>
            <div class="stat-label">帖子</div>
        </div>
        <div style="height: 10px;"></div>
        <div class="stat-box">
            <div class="stat-num">{user_messages}</div>
            <div class="stat-label">留言</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 更新頭像
        st.markdown("#### 📷 頭像")
        new_avatar = st.file_uploader("選擇圖片", type=["jpg", "png", "jpeg"], key="update_avatar")
        if st.button("上傳頭像") and new_avatar:
            avatar_data = base64.b64encode(new_avatar.read()).decode()
            c.execute("UPDATE users SET avatar=? WHERE username=?", (avatar_data, user))
            conn.commit()
            st.session_state['avatar'] = avatar_data
            st.success("頭像更新成功！✨")
            st.rerun()
        
        st.markdown("---")
        
        # Profile按鈕
        if st.button("👤 個人檔案"):
            st.session_state['show_profile'] = True
            st.rerun()
        
        # 登出
        if st.button("🚪 登出"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # 發新帖
        st.markdown("#### 📝 發新帖")
        title = st.text_input("標題", placeholder="輸入標題...")
        content = st.text_area("內容", placeholder="寫啲咩好...", height=100)
        category = st.selectbox("分類", CATEGORIES)
        
        if st.button("🚀 發布"):
            if title and content:
                date = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO posts (title, content, author, date, category) VALUES (?, ?, ?, ?, ?)",
                         (title, content, user, date, category))
                conn.commit()
                
                # 通知所有admin
                c.execute("SELECT username FROM users WHERE role='admin'")
                for admin in c.fetchall():
                    if admin[0] != user:
                        send_notification(admin[0], 'new_post', f'📝 {user} 發了新帖：{title}', '')
                
                st.success("發布成功！🎉")
                st.rerun()
            else:
                st.error("標題同內容都要填喎 😅")
    
    # ==================== 個人檔案頁面 ====================
    if st.session_state.get('show_profile'):
        if st.button("← 返回討論區"):
            st.session_state['show_profile'] = False
            st.rerun()
        
        # 拎用戶資料
        c.execute("SELECT bio, email, join_date, last_active, role FROM users WHERE username=?", (user,))
        user_data = c.fetchone()
        
        st.markdown(f"""
        <div class="profile-header">
            <img src="data:image/png;base64,{avatar if avatar else ''}" class="avatar large" style="margin: 0 auto 20px; display: {'none' if not avatar else 'block'};">
            <div style="width: 120px; height: 120px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 48px; margin: 0 auto 20px;">
                {user[0].upper()}
            </div>
            <h2 style="margin-bottom: 10px;">{user}</h2>
            <span class="tag">{user_data[3] if user_data else 'user'}</span>
            <p style="color: #666; margin-top: 20px;">{user_data[0] if user_data[0] else '呢個人好神秘，乜都冇寫...'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 編輯資料
        with st.expander("✏️ 編輯個人檔案"):
            new_bio = st.text_area("個人簡介", value=user_data[0] if user_data[0] else "")
            new_email = st.text_input("Email", value=user_data[1] if user_data[1] else "")
            if st.button("💾 保存"):
                c.execute("UPDATE users SET bio=?, email=? WHERE username=?", (new_bio, new_email, user))
                conn.commit()
                st.success("資料已保存！")
                st.rerun()
        
        # 用戶帖子
        st.markdown("### 📝 我的帖子")
        c.execute("SELECT id, title, date, category FROM posts WHERE author=? ORDER BY date DESC", (user,))
        my_posts = c.fetchall()
        for p in my_posts:
            st.markdown(f"""
            <div class="card">
                <span class="tag">{p[3]}</span>
                <strong>{p[1]}</strong>
                <span style="color: #999; font-size: 12px;">{p[2]}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 通知中心
        st.markdown("### 🔔 通知中心")
        c.execute("SELECT * FROM notifications WHERE user=? ORDER BY date DESC LIMIT 10", (user,))
        notifs = c.fetchall()
        for n in notifs:
            style = "notif unread" if n[6] == 0 else "notif"
            st.markdown(f"""
            <div class="{style}">
                <strong>{n[2]}</strong> · {time_ago(n[5])}
                <p style="margin: 5px 0 0; color: #666;">{n[3]}</p>
            </div>
            """, unsafe_allow_html=True)
            if n[6] == 0:
                c.execute("UPDATE notifications SET read=1 WHERE id=?", (n[0],))
        conn.commit()
        
        st.stop()
    
    # ==================== 主內容區 ====================
    # 搜尋 + 篩選
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 搜尋討論區", placeholder="輸入關鍵詞...")
    with col2:
        filter_cat = st.selectbox("🏷️ 分類", ['全部'] + CATEGORIES)
    
    # 統計行
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM posts")
    total_posts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    total_messages = c.fetchone()[0]
    c.execute("SELECT SUM(view_count) FROM posts")
    total_views = c.fetchone()[0] or 0
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap;">
        <div class="stat-box" style="flex: 1; min-width: 120px;">
            <div class="stat-num">{total_users}</div>
            <div class="stat-label">👥 用戶</div>
        </div>
        <div class="stat-box" style="flex: 1; min-width: 120px;">
            <div class="stat-num">{total_posts}</div>
            <div class="stat-label">📝 帖子</div>
        </div>
        <div class="stat-box" style="flex: 1; min-width: 120px;">
            <div class="stat-num">{total_messages}</div>
            <div class="stat-label">💬 留言</div>
        </div>
        <div class="stat-box" style="flex: 1; min-width: 120px;">
            <div class="stat-num">{total_views}</div>
            <div class="stat-label">👁️ 瀏覽</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 人氣帖子
    c.execute("SELECT id, title, author, view_count, date FROM posts ORDER BY view_count DESC LIMIT 5")
    hot_posts = c.fetchall()
    if hot_posts:
        st.markdown("### 🔥 人氣帖子")
        for p in hot_posts:
            st.markdown(f"""
            <div class="card" style="padding: 15px 20px;">
                <span class="tag hot">🔥 {p[3]} 👁️</span>
                <strong>{p[1]}</strong>
                <span style="color: #999;">by {p[2]}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # 帖子列表
    query = f"%{search}%" if search else "%"
    cat_filter = f" AND category='{filter_cat}'" if filter_cat != '全部' else ""
    c.execute(f"SELECT * FROM posts WHERE (title LIKE ? OR content LIKE ?){cat_filter} ORDER BY date DESC", (query, query))
    posts = c.fetchall()
    
    st.markdown(f"### 📋 討論區 ({len(posts)} 個帖子)")
    
    if not posts:
        st.markdown("""
        <div style="text-align: center; padding: 50px; color: rgba(255,255,255,0.8);">
            <p style="font-size: 48px;">💭</p>
            <p>暫時未有帖子</p>
            <p>快啲發第一個啦！</p>
        </div>
        """, unsafe_allow_html=True)
    
    for post in posts:
        c.execute("SELECT avatar FROM users WHERE username=?", (post[3],))
        result = c.fetchone()
        post_avatar = result[0] if result else None
        author_name = post[3]
        
        with st.expander(f"📌 {post[1]}"):
            col_info, col_content = st.columns([1, 6])
            with col_info:
                if post_avatar:
                    st.markdown(f'<img src="data:image/png;base64,{post_avatar}" class="avatar small">', unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #667eea, #764ba2); 
                                border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                                color: white; font-size: 16px;">{author_name[0].upper()}</div>
                    """, unsafe_allow_html=True)
            with col_content:
                st.markdown(f"""
                <span class="tag">{post[5]}</span>
                <span style="color: #999; font-size: 12px;">{post[4]} · by {author_name}</span>
                """, unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(f"<div style='font-size: 16px; line-height: 1.8;'>{post[2]}</div>", unsafe_allow_html=True)
            
            # 增加瀏覽
            c.execute("UPDATE posts SET view_count = view_count + 1 WHERE id=?", (post[0],))
            conn.commit()
            
            # Admin刪除
            if role == 'admin':
                if st.button("🗑️ 刪除", key=f"del_{post[0]}"):
                    c.execute("DELETE FROM posts WHERE id=?", (post[0],))
                    c.execute("DELETE FROM messages WHERE post_id=?", (post[0],))
                    conn.commit()
                    st.rerun()
            
            # 留言區
            st.markdown("#### 💬 留言")
            messages = c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],)).fetchall()
            
            for msg in messages:
                c.execute("SELECT avatar FROM users WHERE username=?", (msg[3],))
                result = c.fetchone()
                msg_avatar = result[0] if result else None
                msg_author = msg[3]
                is_own = msg_author == user
                
                col_avatar, col_bubble = st.columns([1, 7])
                with col_avatar:
                    if msg_avatar:
                        st.markdown(f'<img src="data:image/png;base64,{msg_avatar}" class="avatar small" style="width:30px;height:30px;">', unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="width: 30px; height: 30px; background: #ddd; border-radius: 50%; 
                                    display: flex; align-items: center; justify-content: center; font-size: 12px;">
                                    {msg_author[0].upper()}</div>
                        """, unsafe_allow_html=True)
                with col_bubble:
                    bubble_style = "background: linear-gradient(135deg, #667eea, #764ba2); color: white;" if is_own else "background: #f5f5f5;"
                    st.markdown(f"""
                    <div style="{bubble_style} padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 80%;">
                        <strong>{msg_author}</strong> · <span style="opacity: 0.7;">{time_ago(msg[4])}</span><br>
                        {msg[2]}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Admin刪除留言
                if role == 'admin' and st.button("🗑️", key=f"del_msg_{msg[0]}", help="刪除留言"):
                    c.execute("DELETE FROM messages WHERE id=?", (msg[0],))
                    conn.commit()
                    st.rerun()
            
            # 發留言
            msg_content = st.text_input("寫留言...", key=f"msg_{post[0]}", placeholder="輸入留言...")
            if st.button("💬 發送", key=f"send_{post[0]}"):
                if msg_content:
                    date = datetime.now().strftime("%H:%M")
                    c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)",
                             (post[0], msg_content, user, date))
                    conn.commit()
                    
                    # 通知帖子作者
                    if post[3] != user:
                        send_notification(post[3], 'new_comment', f'💬 {user} 回了你的帖：{post[1]}', f'#{post[0]}')
                    
                    st.rerun()

# 底部
st.markdown("""
<hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent); margin: 30px 0;">
<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.7); font-size: 14px;">
    <p>💬 Gay Spa 香港討論區</p>
    <p>Made with ❤️ by OpenClaw</p>
</div>
""", unsafe_allow_html=True)

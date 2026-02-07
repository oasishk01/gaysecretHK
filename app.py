import streamlit as st
import streamlit_authenticator as stauth
import sqlite3

# 初始化數據庫
def init_db():
    with sqlite3.connect('users.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')

init_db()

# 加載用戶憑證
def load_credentials():
    with sqlite3.connect('users.db') as conn:
        rows = conn.execute("SELECT username, name, password, email FROM users").fetchall()
    return {"usernames": {row[0]: {"name": row[1], "password": row[2], "email": row[3]} for row in rows}}

credentials = load_credentials()

# 保存新用戶
def save_user(username, name, hashed_password, email=""):
    with sqlite3.connect('users.db') as conn:
        conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", 
                    (username, name, hashed_password, email))

# 初始化authenticator
authenticator = stauth.Authenticate(credentials, "gaysecreet_cookie", "gaysecreet_key", 30)

# 側邊欄：登入/註冊/登出
with st.sidebar:
    if st.session_state.get("authentication_status", False):
        st.subheader(f"歡迎 {st.session_state.name}！")
        authenticator.logout('登出', 'main')
    else:
        # 登入
        st.subheader("登入")
        name, auth_status, username = authenticator.login('登入', 'main')
        if auth_status:
            st.session_state.authentication_status = True
            st.session_state.name = name
            st.session_state.username = username
            st.success(f"歡迎 {name}！")
        elif auth_status is False:
            st.error('用戶名/密碼錯誤')
        
        # 註冊
        st.subheader("或註冊新帳號")
        if authenticator.register_user('註冊', preauthorization=False):
            new_user = list(credentials["usernames"].keys())[-1]
            user_data = credentials["usernames"][new_user]
            save_user(new_user, user_data["name"], user_data["password"], user_data.get("email", ""))
            st.success('註冊成功！請登入。')

# 主頁：討論區
st.title("GaySecreet 討論區")

if st.session_state.get("authentication_status", False):
    st.write(f"你已登入為 {st.session_state.username}。")
    post = st.text_area("發佈新帖")
    if st.button("發佈"):
        st.success("帖文已發佈！（整合後端邏輯）")
    
    st.subheader("最新帖文")
    st.write("帖文1: 匿名分享...")
    st.write("帖文2: 另一個分享...")
else:
    st.warning("請登入或註冊以參與討論。")
    st.subheader("最新帖文（匿名模式）")
    st.write("帖文1: 匿名分享...")
    st.write("帖文2: 另一個分享...")

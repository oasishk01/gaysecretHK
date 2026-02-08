import streamlit as st
import sqlite3
from datetime import datetime

# 初始化數據庫
def init_db():
    conn = sqlite3.connect("forum.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT, timestamp TEXT, replies TEXT)""")
    conn.commit()
    conn.close()

init_db()

# 主頁
st.title("GaySecret 討論區 - 香港LGBTQ+社區 🌈")
st.write("安全匿名空間，一起分享！")

# 發帖
title = st.text_input("標題")
content = st.text_area("內容")
if st.button("提交"):
    if title and content:
        conn = sqlite3.connect("forum.db")
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, content, timestamp) VALUES (?, ?, ?)",
                  (title, content, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        st.success("發佈成功！")
    else:
        st.error("請填寫標題同內容")

# 顯示帖子
conn = sqlite3.connect("forum.db")
c = conn.cursor()
c.execute("SELECT * FROM posts ORDER BY timestamp DESC")
posts = c.fetchall()
conn.close()

for post in posts:
    st.subheader(post[1])
    st.write(f"時間: {post[3]}")
    st.write(post[2])
    st.write("回覆: " + (post[4] if post[4] else "無"))
    reply = st.text_input(f"回覆 {post[0]}", key=f"reply_{post[0]}")
    if st.button(f"提交回覆 {post[0]}", key=f"submit_{post[0]}"):
        if reply:
            conn = sqlite3.connect("forum.db")
            c = conn.cursor()
            current_replies = post[4] or ""
            updated_replies = current_replies + "
- " + reply + " (" + datetime.now().strftime("%Y-%m-%d %H:%M") + ")"
            c.execute("UPDATE posts SET replies=? WHERE id=?", (updated_replies, post[0]))
            conn.commit()
            conn.close()
            st.success("回覆成功！")
            st.experimental_rerun()

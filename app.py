import streamlit as st
import sqlite3
from datetime import datetime

# Initialize database
conn = sqlite3.connect('forum.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, content TEXT, author TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT, author TEXT, date TEXT)''')
conn.commit()

# Streamlit App
st.title("Gay Spa 香港討論區")

# Sidebar: New Post
with st.sidebar:
    st.header("發新帖")
    title = st.text_input("標題 Title")
    content = st.text_area("內容 Content")
    author = st.text_input("作者 Author")
    if st.button("提交 Submit"):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO posts (title, content, author, date) VALUES (?, ?, ?, ?)", (title, content, author, date))
        conn.commit()
        st.success("帖子已發佈！")

# Main Page: Show Posts
posts = c.execute("SELECT * FROM posts ORDER BY date DESC").fetchall()
for post in posts:
    with st.expander(f"{post[1]} by {post[3]} on {post[4]}"):
        st.write(post[2])
        
        # Real-time Chat
        st.subheader("實時留言 Real-time Chat")
        messages = c.execute("SELECT * FROM messages WHERE post_id=? ORDER BY date", (post[0],)).fetchall()
        for msg in messages:
            st.write(f"{msg[3]} ({msg[4]}): {msg[2]}")
        
        # Send Message
        msg_author = st.text_input("你的名字 Your name", key=f"author_{post[0]}")
        msg_content = st.text_input("留言 Message", key=f"msg_{post[0]}")
        if st.button("發送 Send", key=f"send_{post[0]}"):
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO messages (post_id, content, author, date) VALUES (?, ?, ?, ?)", (post[0], msg_content, msg_author, date))
            conn.commit()
            st.rerun()

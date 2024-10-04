import streamlit as st
import json
import os

# 用户凭证文件路径
CREDENTIALS_FILE = "user_credentials.json"

# 读取用户凭证
def load_user_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

# 保存用户凭证
def save_user_credentials(credentials):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f)

# 用户凭证存储
USER_CREDENTIALS = load_user_credentials()

# 登录功能
def user_login():
    st.sidebar.title("用户登录")
    username = st.sidebar.text_input("用户名")
    password = st.sidebar.text_input("密码", type="password")
    if st.sidebar.button("登录"):
        if USER_CREDENTIALS.get(username) == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username  # 存储用户名
            st.sidebar.success(f"登录成功！{username}")
        else:
            st.sidebar.error("用户名或密码错误！")

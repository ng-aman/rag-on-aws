from streamlit_local_storage import LocalStorage
import streamlit as st
import os , uuid, json
from dotenv import load_dotenv
from rag_app_v1 import rag_app_v1
load_dotenv()
def LoggedIn_Clicked(userName,password):
    users = os.environ["USERS"]
    user_dict = json.loads(users)
    if userName in user_dict and user_dict[userName] == password:
        # if user_dict[userName] == password:
        localS = LocalStorage()
        session_id = str(uuid.uuid4())
        localS.setItem(itemKey="logs",itemValue=[session_id,userName])

    
def show_login_page():
    userName = st.text_input (label="Email", value="", placeholder="Enter your user name")
    password = st.text_input (label="Password", value="",placeholder="Enter password", type="password")
    st.button ("Login", on_click=LoggedIn_Clicked, args= (userName, password))

get_token = LocalStorage().getItem("logs")

try:
    if get_token is None:
        show_login_page()
    else:
        rag_app_v1()
except Exception as e:
    st.exception(e)
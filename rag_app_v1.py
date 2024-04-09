import json
import requests
import boto3
import os
from dotenv import load_dotenv
from upload_embeddings import main
from streamlit_local_storage import LocalStorage

import streamlit as st
from langchain_community.chat_message_histories.dynamodb import (
    DynamoDBChatMessageHistory,
)

load_dotenv()

boto3_session = boto3.Session(
    aws_access_key_id=os.environ["ACCESS_KEY"],
    aws_secret_access_key=os.environ["SECRET_KEY"],
    region_name=os.environ["REGION"],
)

table_name = "SessionTable"
dynamodb_client = boto3.client(
    "dynamodb",
    aws_access_key_id=os.environ["ACCESS_KEY"],
    aws_secret_access_key=os.environ["SECRET_KEY"],
    region_name=os.environ["REGION"],
)
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ["ACCESS_KEY"],
    aws_secret_access_key=os.environ["SECRET_KEY"],
    region_name=os.environ["REGION"],
)
table = dynamodb.Table(table_name)


def send_request_to_api_gateway(json_body):
    try:
        # Define the API Gateway endpoint URL
        api_url = os.environ["API_URL"]

        # Make a POST request to the API Gateway endpoint with the JSON body
        response_from_api = requests.post(api_url, json=json_body)
        response_data = response_from_api.json()
        return response_data
    except Exception as e:
        # Handle errors
        print("Error:", e)
        return {"error": "Internal server error"}


def get_sessions(table_name):
    response = dynamodb_client.scan(TableName=table_name)
    unique_session_ids = list(set(item["SessionId"]["S"] for item in response["Items"]))
    return unique_session_ids


def get_session_history(session_id, dynamodb_table="SessionTable"):
    history = DynamoDBChatMessageHistory(
        table_name=dynamodb_table, session_id=session_id, boto3_session=boto3_session
    )
    return history


# with st.sidebar:
#     st.title("RAG ChatBot")
#     st.subheader("With Memory :brain:")
#     main()
# sessions = get_sessions("SessionTable")
# st.sidebar.write("**Start New session**")
# new_session = st.sidebar.chat_input("New session name")
# seleceted_session = st.sidebar.selectbox("**Session Id**", sessions, index=None)

# users = os.environ["USERS"]

def get_chat_history(session):
    st.sidebar.write(f"current session:  **{session}**")
    if st.sidebar.button("logout"):
        LocalStorage().deleteItem("logs")
        st.session_state.clear() 
    if session:
        history = get_session_history(session_id=session)

        if history.messages == []:
            history.add_ai_message("How may I assist you today?")

        for msg in history.messages:
            st.chat_message(msg.type).write(msg.content)

    if prompt := st.chat_input():
        st.chat_message("human").write(prompt)
        # getting chat response from lambda
        payload = {"question": prompt, "session_id": session}
        response = send_request_to_api_gateway(payload)
        body = response["body"]
        st.chat_message("ai").write(body)


# create session state to store session ids in order to avoid sending none values to get_chat_history

def rag_app_v1():
    with st.sidebar:
        st.title("RAG ChatBot")
        st.subheader("With Memory :brain:")
        main()
    sessions = get_sessions("SessionTable")
    st.sidebar.write("**Start New session**")
    new_session = st.sidebar.chat_input("New session name")
    seleceted_session = st.sidebar.selectbox("**Session Id**", sessions, index=None)
    if "session" not in st.session_state:
        st.session_state["session"] = None

    if new_session:
        st.session_state["session"] = new_session
    elif seleceted_session:
        st.session_state["session"] = seleceted_session

    # calling get_chat_history

    get_chat_history(st.session_state["session"])

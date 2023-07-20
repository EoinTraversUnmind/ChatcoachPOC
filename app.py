import os
from uuid import uuid4 as generate_uuid
import openai
import streamlit as st
from dotenv import load_dotenv
import sqlalchemy as sa
import gspread

from src import connect_db, get_params_from_gsheets, log_session, log_chat
# Based on
# https://github.com/streamlit/llm-examples/blob/main/Chatbot.py



if "setup" not in st.session_state:
    # This is only run when the page first loads
    load_dotenv()
    st.session_state["OPENAI_KEY"] = os.getenv("OPENAI_KEY")
    st.session_state["db_conn"] = connect_db()
    possible_bot_params = get_params_from_gsheets()
    st.session_state["possible_bot_params"] = {p['pars_label']: p for p in possible_bot_params}
    st.session_state['uuid'] = generate_uuid()
    st.session_state['chat_step'] = 0
    st.session_state['started'] = False
    st.session_state["setup"] = True


def start_session():
    """`this is triggered once the big Start button in the sidebar is clicked, locking in the parameters.`"""
    bot_param_id = st.session_state["bot_param_id"]
    BOT_PARAMS = st.session_state['possible_bot_params'][bot_param_id]
    st.session_state['bot_params'] = BOT_PARAMS
    st.session_state["messages"] = [{"role": "system", "content": BOT_PARAMS["system_prompt"]}]
    if BOT_PARAMS["initial_message"]:
        st.session_state["messages"].append({"role": "assistant", "content": BOT_PARAMS["initial_message"]})
    st.session_state["started"] = True
    log_session(st.session_state)


with st.sidebar:
    # Which parameters to use?
    # These options are disabled once a conversation starts
    _options = st.session_state["possible_bot_params"].keys()
    # _options = [''] + list(_options)
    #is_disabled = st.session_state["chat_step"] > 0
    st.selectbox("Select parameter set", key="bot_param_id",
                 options = _options,
                 disabled = st.session_state["started"] == True)
    # on_change = reset_converation)
    st.text_input("(Optional) Enter a label for this conversation", key = "user_label",
                  disabled = st.session_state["started"] == True)
    st.button("Start", on_click = start_session,
              disabled = st.session_state["started"] == True)


## Start of the main app
st.title("💬 Unmind Career Coach Bot")

if st.session_state['started']:
    BOT_PARAMS = st.session_state['possible_bot_params'][st.session_state["bot_param_id"]]
else:
    # This shouldn't happen at present
    st.info("Choose your settings parameter set from the menu to the left to begin")
    st.stop()


#
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": BOT_PARAMS["system_prompt"]}]
    if BOT_PARAMS["initial_message"]:
        st.session_state["messages"].append({"role": "assistant", "content": BOT_PARAMS["initial_message"]})


# Show the conversation so far
for msg in st.session_state.messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(BOT_PARAMS["input_prompt"]):
    st.session_state["chat_step"] += 1
    st.session_state["input"] = prompt
    # TODO: Add loading indicator here
    openai.api_key = st.session_state["OPENAI_KEY"]
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = openai.ChatCompletion.create(model=BOT_PARAMS["gpt_model"], messages=st.session_state.messages)
    msg = response.choices[0].message
    print(msg)
    print(type(msg))
    st.session_state["output"] = msg['content']
    # msg = {"role" : "assistant", "content": "Hello!"}
    st.session_state["messages"].append(msg)
    log_chat(st.session_state)
    st.chat_message("assistant").write(msg["content"])

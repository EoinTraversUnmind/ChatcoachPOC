import os
from uuid import uuid4 as generate_uuid
import openai
import streamlit as st
from streamlit_star_rating import st_star_rating
from dotenv import load_dotenv
import sqlalchemy as sa
import gspread

from src import connect_db, get_params_from_gsheets, log_session, log_chat, log_feedback
# Based on
# https://github.com/streamlit/llm-examples/blob/main/Chatbot.py



if "setup" not in st.session_state:
    # This is only run when the page first loads
    load_dotenv()
    st.session_state["OPENAI_KEY"] = os.getenv("OPENAI_KEY")
    st.session_state["db_conn"] = connect_db()
    possible_personas = get_params_from_gsheets()
    st.session_state["possible_personas"] = {p['persona']: p for p in possible_personas}
    st.session_state['uuid'] = generate_uuid()
    st.session_state['chat_step'] = 0
    st.session_state['started'] = False
    st.session_state["setup"] = True


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

def start_session():
    """`this is triggered once the big Start button in the sidebar is clicked, locking in the parameters.`"""
    persona_id = st.session_state["persona_id"]
    PERSONA = st.session_state['possible_personas'][persona_id]
    st.session_state['persona'] = PERSONA
    st.session_state["messages"] = [{"role": "system", "content": PERSONA["system_prompt"]}]
    if PERSONA["initial_message"]:
        st.session_state["messages"].append({"role": "assistant", "content": PERSONA["initial_message"]})
    st.session_state["started"] = True
    log_session(st.session_state)

def save_feedback():
    # This goes at the top of the screen, don't know how to change it yet...
    st.write("[Feedback received]")
    log_feedback(st.session_state)
    st.session_state["feedback_text"] = ""


if check_password():

    with st.sidebar:
        # Which parameters to use?
        # These options are disabled once a conversation starts
        _options = st.session_state["possible_personas"].keys()
        st.title("Settings")
        st.selectbox("Select persona", key="persona_id",
                    options = _options,
                    disabled = st.session_state["started"] == True)
        st.text_input("(Optional) Enter a label for this conversation", key = "user_label",
                    disabled = st.session_state["started"] == True)
        st.button("Start", on_click = start_session,
                disabled = st.session_state["started"] == True)

        # Feeback
        st.write("\n-----\n")
        st.title("Feedback")
        st.write("Use the fields below at any time, as often as you like, to provide feedback")

        st_star_rating(label = "How is the chat going so far?",
                    maxValue = 5, defaultValue = 3, key = "feedback_rating", emoticons = True )
        st.text_input("Do you have any notes to add?", key = "feedback_text")
        st.button("Submit", on_click = save_feedback) # Doesn't do anything yet...


    ## Start of the main app
    st.title("💬 Unmind Career Coach Bot")

    if st.session_state['started']:
        PERSONA = st.session_state['possible_personas'][st.session_state["persona_id"]]
    else:
        # This shouldn't happen at present
        st.info("Choose your settings parameter set from the menu to the left to begin")
        st.stop()


    #
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": PERSONA["system_prompt"]}]
        if PERSONA["initial_message"]:
            st.session_state["messages"].append({"role": "assistant", "content": PERSONA["initial_message"]})


    # Show the conversation so far
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input(PERSONA["input_prompt"]):
        st.session_state["chat_step"] += 1
        st.session_state["input"] = prompt
        # TODO: Add loading indicator here
        openai.api_key = st.session_state["OPENAI_KEY"]
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        # Display loading indicator while we get response
        with st.spinner(''):
            response = openai.ChatCompletion.create(model=PERSONA["gpt_model"],
                                                    messages=st.session_state.messages)
            msg = response.choices[0].message
            st.session_state["output"] = msg['content']
        # msg = {"role" : "assistant", "content": "Hello!"}
        st.chat_message("assistant").write(msg["content"])
        st.session_state["messages"].append(msg)
        log_chat(st.session_state)

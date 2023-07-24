import os
from uuid import uuid4 as generate_uuid
import openai
import streamlit as st
from dotenv import load_dotenv
import sqlalchemy as sa
import gspread
import json

def check_password():
    """Require user to enter correct password (from .env) to continue.
    See https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
    """
    load_dotenv()
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("APP_PASSWORD"): # st.secrets["password"]:
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


def connect_db() -> sa.engine.base.Connection:
    """Connect to our postgres database"""
    load_dotenv()
    pars = {k: os.getenv(k)
            for k in ["DB_HOST", "DB_PORT", "DB_USERNAME", "DB_DATABASE", "DB_PASSWORD"]}
    db_url = sa.engine.URL.create(
        drivername="postgresql",
        username=pars["DB_USERNAME"],
        password=pars["DB_PASSWORD"],
        host=pars["DB_HOST"],
        port=pars["DB_PORT"],
        database=pars["DB_DATABASE"]
    )
    try:
        db_engine = sa.create_engine(db_url)
        db_conn = db_engine.connect()
    except:
        raise Exception("Couldn't connect to the database. VPN?")
        # print("Couldn't connect to the database. Are you running locally?")
        # db_conn = None
        # TODO: Set up schema here if it doesn't exist
    return db_conn

query_templates = {
    'session': 'insert into public.sessions (session_id, session_lbl, persona, parameters) values (:session_id, :session_lbl, :persona, :parameters)',
    'chat': "insert into public.chat_logs (session_id, persona, chat_step, input, output) values (:session_id, :persona, :chat_step, :input, :output)",
    'feedback': "insert into public.feedback (session_id, chat_step, rating, feedback_text) values (:session_id, :chat_step, :rating, :feedback_text)"
}

def run_query(db_conn: sa.engine.base.Connection,
              route: str, **kwargs):
    """Given a connection, and a key from `query_templates`, do the rest"""
    query = sa.sql.text(query_templates[route])
    print(query)
    return db_conn.execute(query, **kwargs)


def log_session(ss: st.runtime.state.session_state_proxy.SessionStateProxy):
    db_conn = ss['db_conn']
    run_query(db_conn, 'session',
              session_id = ss['uuid'],
              session_lbl = ss['user_label'],
              persona = ss['persona_id'],
              parameters = json.dumps(ss['persona']))

def log_chat(ss: st.runtime.state.session_state_proxy.SessionStateProxy):
    db_conn = ss['db_conn']
    run_query(db_conn, 'chat',
              session_id = ss['uuid'],
              persona = ss["persona_id"],
              chat_step = ss["chat_step"],
              input = ss["input"],
              output = ss["output"]
              )

def log_feedback(ss: st.runtime.state.session_state_proxy.SessionStateProxy):
    db_conn = ss['db_conn']
    run_query(db_conn, 'feedback',
              session_id = ss['uuid'],
              chat_step = ss['chat_step'],
              rating = ss['feedback_rating'],
              feedback_text = ss['feedback_text'])

def get_params_from_gsheets() -> list:
    """We have a gsheet with all our different possible chatbot configurations
    Load them so we can let the user choose one of them.
    """
    load_dotenv()
    credentials = {
        "type": "service_account",
        "project_id": os.getenv("GDRIVE_PROJECT_ID"),
        "private_key_id": os.getenv("GDRIVE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GDRIVE_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("GDRIVE_CLIENT_EMAIL"),
        "client_id": os.getenv("GDRIVE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("GDRIVE_X509_URL"),
        "universe_domain": "googleapis.com"
    }
    try:
        gc = gspread.service_account_from_dict(credentials)
        sheet_id = '1oqLGsZBXMy-9g92K1YnClieXiMC2Yud5YKmrquVYDKw'
        sheet = gc.open_by_key(sheet_id)
        return sheet.sheet1.get_all_records()
    except:
        raise(Exception("Couldn't connect to GSheets to access parameters"))



# POC Work Coach Chatbot


## Setup

Create a .env at the root, which will need the following variables filled:
```
OPENAI_KEY=
DB_HOST=
DB_PORT=
DB_USERNAME=
DB_DATABASE=
DB_PASSWORD=
GDRIVE_PROJECT_ID=
GDRIVE_PRIVATE_KEY_ID=
GDRIVE_PRIVATE_KEY=
GDRIVE_CLIENT_EMAIL=
GDRIVE_CLIENT_ID=
GDRIVE_X509_URL=
```

Create a file called `secrets.toml` inside `.streamlit/` with the contents like:
```
password = "{PASSWORD_GOES_HERE}"
```

## Running it



```bash
pip install -r requirements.txt
streamlit run app.py
# Optionally add --server.port 80, or whatever, at the end
# See https://docs.streamlit.io/library/advanced-features/configuration
```

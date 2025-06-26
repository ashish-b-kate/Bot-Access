import streamlit as st
import pandas as pd
import requests
import hashlib

# At the top of app.py
import streamlit as st

SHEET_ID = st.secrets["google_sheets"]["sheet_id"]
API_KEY = st.secrets["google_sheets"]["api_key"]
USERS_SHEET_NAME = "Users"       # Exact tab name (case-sensitive)
BOTS_SHEET_NAME = "Bots"         # Exact tab name (case-sensitive)

# --- Load Data from Google Sheets ---

def load_sheet(sheet_name):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet_name}?key={API_KEY}"
    response = requests.get(url).json()
    data = response.get("values", [])
    
    if not data:
        st.error("No data loaded! Check:")
        st.error(f"1. Sheet sharing permissions (must be 'Anyone with link can view')")
        st.error(f"2. Sheet/tab names are correct (case-sensitive)")
        return pd.DataFrame()
    
    headers = data[0]
    rows = data[1:]
    
    # Only validate Email column for Users sheet
    if sheet_name == "Users" and "Email" not in headers:
        st.error(f"Users sheet must contain 'Email' column! Found: {headers}")
        return pd.DataFrame()
    
    # Only validate BotID column for Bots sheet
    if sheet_name == "Bots" and "BotID" not in headers:
        st.error(f"Bots sheet must contain 'BotID' column! Found: {headers}")
        return pd.DataFrame()
    
    return pd.DataFrame(rows, columns=headers)

# --- Rest of your code (authentication, UI) remains the same ---
# (Copy the rest from the previous `app.py` example)


# Authentication

def authenticate_user(email, password, users_df):
    try:
        # Convert to lowercase for case-insensitive match
        email = email.strip().lower()
        users_df["Email"] = users_df["Email"].str.lower().str.strip()
        
        # Find user
        user = users_df[users_df["Email"] == email]
        
        if not user.empty:
            # Verify password (in real use, compare hashed passwords)
            if user["Password"].values[0] == password:
                return user
        return None
        
    except KeyError as e:
        st.error(f"Missing critical column in Users sheet: {e}")
        return None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

# Main App
def main():
    st.title("🔒 Employee Bot Access Portal")

    # Load data
    users_df = load_sheet("Users")
    bots_df = load_sheet("Bots")

    # Login
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user = authenticate_user(email, password, users_df)
            if user is not None:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Access Denied: Invalid credentials.")

    else:
        st.success(f"Welcome, {st.session_state.user['Email'].values[0]}!")
        allowed_bots = st.session_state.user["AllowedBots"].values[0].split(",")
        available_bots = bots_df[bots_df["BotID"].isin(allowed_bots)]

        selected_bot = st.selectbox("Choose a bot:", available_bots["BotName"])
        if st.button("Access Bot"):
            bot_url = available_bots[available_bots["BotName"] == selected_bot]["BotURL"].values[0]
            st.markdown(f"🔗 [Open {selected_bot}]({bot_url})", unsafe_allow_html=True)

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()
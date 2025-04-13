import streamlit as st
import sqlite3
import random
from datetime import datetime
import pandas as pd
import plotly.express as px

# --- Constants ---
NUM_SIDES = 6
DB_NAME = "dice_rolls.db"

# --- User Auth ---
valid_users = {
    "alice": "password123",
    "bob": "diceking",
    "admin": "adminpass"
}

def login():
    st.title("🔐 Dice Simulator Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username in valid_users and valid_users[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# --- Database Setup ---
def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rolls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            die1 INTEGER,
            die2 INTEGER,
            total INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def log_roll(username, die1, die2, total):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO rolls (timestamp, username, die1, die2, total) VALUES (?, ?, ?, ?, ?)",
              (timestamp, username, die1, die2, total))
    conn.commit()
    conn.close()

def fetch_user_rolls(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM rolls WHERE username = ? ORDER BY id DESC", (username,))
    data = c.fetchall()
    conn.close()
    return data

# --- Main App ---
def main():
    st.set_page_config(page_title="🎲 Dice Simulator", layout="centered")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    if not st.session_state.logged_in:
        login()
        return

    st.sidebar.success(f"✅ Logged in as: {st.session_state.user}")
    if st.sidebar.button("🚪 Logout"):
        logout()

    st.title("🎲 Dice Simulator with Stats & Filters")
    initialize_db()

    st.markdown("Click the button below to roll two dice and log the result.")

    if st.button("🎲 Roll Dice"):
        die1 = random.randint(1, NUM_SIDES)
        die2 = random.randint(1, NUM_SIDES)
        total = die1 + die2
        st.success(f"Die 1 = {die1}, Die 2 = {die2}, Total = {total}")
        log_roll(st.session_state.user, die1, die2, total)

    st.markdown("---")
    st.subheader("📅 Filter Rolls by Date Range")

    all_rolls = fetch_user_rolls(st.session_state.user)
    if all_rolls:
        df = pd.DataFrame(all_rolls, columns=["ID", "Timestamp", "Username", "Die 1", "Die 2", "Total"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])

        min_date = df["Timestamp"].min().date()
        max_date = df["Timestamp"].max().date()
        start_date, end_date = st.date_input("Select date range:", [min_date, max_date])

        filtered_df = df[
            (df["Timestamp"].dt.date >= start_date) &
            (df["Timestamp"].dt.date <= end_date)
        ]

        st.markdown("### 🎯 Filtered Statistics")
        if not filtered_df.empty:
            st.write(f"Total Rolls: {len(filtered_df)}")
            st.write(f"Average Total: {filtered_df['Total'].mean():.2f}")
            st.write(f"Highest Total: {filtered_df['Total'].max()}")

            st.markdown("### 📊 Total Roll Distribution")
            total_counts = filtered_df["Total"].value_counts().sort_index()
            st.bar_chart(total_counts)

            st.markdown("### 🧩 Die Value Distribution (Pie Chart)")
            die_values = pd.concat([filtered_df["Die 1"], filtered_df["Die 2"]])
            pie_chart = px.pie(
                names=die_values,
                title="Die Face Frequency",
                hole=0.4
            )
            st.plotly_chart(pie_chart, use_container_width=True)

            st.markdown("### 📁 Export Data")
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Filtered Rolls as CSV",
                data=csv,
                file_name='filtered_dice_rolls.csv',
                mime='text/csv'
            )

            st.markdown("### 📋 Filtered Roll History")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No rolls found in the selected date range.")
    else:
        st.warning("No rolls have been recorded yet.")

# Call the main function
if __name__ == "__main__":
    main()

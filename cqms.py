import streamlit as st
import pandas as pd
import mysql.connector
import hashlib
from datetime import datetime
import time
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# ----------------------------- PAGE CONFIG & STYLES -----------------------------
st.set_page_config(page_title="Client Query Management System", page_icon="💬", layout="wide")

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] { background: #f5f7fb !important; }
    header.stAppHeader { background-color: transparent !important; padding: 0 !important; margin: 0 !important; height: 0 !important; }
    section.main > div.block-container { padding-top: 0rem !important; margin-top: 0rem !important; }
    .login-card { background: #ffffff; border-radius: 16px; padding: 36px; width: 420px; margin: 60px auto; box-shadow: 0 12px 30px rgba(22,35,54,0.08); }
    .login-card input, .login-card select, .login-card textarea { max-width: 300px !important; width: 100% !important; margin: 0 auto !important; display: block !important; }
    .login-card .stTextInput, .login-card .stSelectbox, .login-card .stTextArea { max-width: 320px !important; margin: 0 auto !important; }
    .login-icon { width:72px; height:72px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin: 0 auto 14px auto;
        background: linear-gradient(135deg,#6b46ff 0%, #9f7aea 100%); box-shadow: 0 10px 25px rgba(107,70,255,0.12); font-size:28px; color: white; }
    .login-title { text-align:center; font-weight:700; font-size:20px; margin-bottom:4px; }
    .login-sub { text-align:center; color:#6b7280; margin-bottom:18px; }
    .stButton>button { background: linear-gradient(90deg,#6b46ff 0%,#9f7aea 100%) !important; color: white !important;
        border-radius: 10px !important; height:44px !important; font-weight:700 !important; border: none !important;
        box-shadow: 0 8px 18px rgba(99,102,241,0.12) !important; }
    .dashboard-header { margin-top: 12px; margin-bottom: 12px; }
    .small-muted { color:#6b7280; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- DATABASE / UTILS -----------------------------
def encrypt_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="02@Kavin07",
        database="client_queries",
        autocommit=True
    )

def add_user(user_id, password, role):
    conn = connect_db()
    cur = conn.cursor()
    enc = encrypt_password(password)
    cur.execute("INSERT INTO client_queries.login_details (user_id, password, role) VALUES (%s,%s,%s)", (user_id, enc, role))
    conn.commit()
    conn.close()

def check_user_exists(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM login_details WHERE user_id=%s", (user_id,))
    res = cur.fetchone()
    conn.close()
    return res is not None

def insert_client_query(user_id, email_id, mobile_number, query_heading, query_description):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO queries (user_id, email_id, mobile_number, query_heading, query_description, query_created_time, status, query_closed_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, email_id, mobile_number, query_heading, query_description, datetime.now(), "Open", None))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Error inserting query: {e}")
        return False

def get_all_queries(status_filter=None):
    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    if status_filter == "All":
        cur.execute("SELECT * FROM queries ORDER BY query_created_time DESC")
    else:
        cur.execute("SELECT * FROM queries WHERE status = %s ORDER BY query_created_time DESC", (status_filter,))
    rows = cur.fetchall()
    conn.close()
    return rows

def close_query(query_id):
    conn = connect_db()
    cur = conn.cursor()
    close_time = datetime.now()
    cur.execute("UPDATE queries SET status=%s, query_closed_time=%s WHERE query_id=%s", ("Closed", close_time, query_id))
    conn.commit()
    conn.close()
    return True

# ----------------------------- SESSION STATE -----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ----------------------------- LOGIN PAGE -----------------------------
if not st.session_state["logged_in"]:
    st.markdown("<div style='text-align:center;margin-top:24px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;margin-bottom:4px;'>Client Query Management Systems</h1>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-icon">🔒</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Welcome Back!</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Sign in to your account</div>', unsafe_allow_html=True)

        login_form = st.form(key="login_form")
        login_user = login_form.text_input("User ID", placeholder="Enter the user id", key="login_user_id", autocomplete="off")
        login_pwd = login_form.text_input("Password", type="password", placeholder="Enter the password", key="login_password", autocomplete="new-password")
        login_role = login_form.selectbox("Role", ["Select your role", "client", "support"], key="login_role")
        login_btn = login_form.form_submit_button("🚀 Login")

        st.markdown("<div style='text-align:center;margin:12px 0;color:#9ca3af;'>— OR —</div>", unsafe_allow_html=True)
        if st.button("✨ Create Account"):
            st.session_state["signup_needed"] = True

    if login_btn:
        if not login_user or not login_pwd or login_role == "Select your role":
            st.warning("⚠️ Please fill in all fields!")
        else:
            if check_user_exists(login_user):
                st.session_state["user_id"] = login_user
                st.session_state["role"] = login_role
                st.session_state["logged_in"] = True
                st.success(f"✅ Login successful as {login_role}")
                st.rerun()
            else:
                st.warning("User not found. Please sign up.")
                st.session_state["signup_needed"] = True

# ----------------------------- SIGNUP FORM -----------------------------
if ("signup_needed" in st.session_state and st.session_state["signup_needed"] and not st.session_state["logged_in"]):
    st.markdown("---")
    st.subheader("🆕 Quick Signup Form (create your account)")

    signup_form = st.form(key="signup_form")
    new_user = signup_form.text_input("User ID", placeholder="Choose a user ID", key="signup_user", autocomplete="off")
    new_pwd = signup_form.text_input("Password", type="password", placeholder="Create a password", key="signup_password", autocomplete="new-password")
    new_role = signup_form.selectbox("Role", ["Select your role", "client", "support"], key="signup_role")
    create_btn = signup_form.form_submit_button("✨ Create Account")
    if create_btn:
        if not new_user or not new_pwd or new_role == "Select your role":
            st.warning("⚠️ Please fill all fields!")
        else:
            try:
                add_user(new_user, new_pwd, new_role)
                st.success(f"🎉 Account created successfully for {new_user} as {new_role}")
                st.session_state["signup_needed"] = False
            except Exception as e:
                st.error(f"❌ Error creating account: {e}")

# ----------------------------- DASHBOARDS -----------------------------
else:
    with st.sidebar:
        if st.session_state.get("logged_in"):
            st.markdown(f"**👋 Logged in as:** `{st.session_state.get('user_id')}` ({st.session_state.get('role')})")
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ---------- CLIENT ----------
    if st.session_state.get("logged_in") and st.session_state.get("role") == "client":
        st.markdown("<div class='dashboard-header'><h2>💬 Client Query Submission Page</h2></div>", unsafe_allow_html=True)
        client_form = st.form(key='client_form')
        email = client_form.text_input("Email ID", placeholder="Enter your email")
        mobile = client_form.text_input("Mobile Number", placeholder="Enter your mobile number")
        query_heading = client_form.text_input("Query Heading", placeholder="Enter query title")
        query_description = client_form.text_area("Query Description", placeholder="Describe your issue in detail")
        submit_query = client_form.form_submit_button("Submit Query")
        if submit_query:
            if not email or not mobile or not query_heading or not query_description:
                st.warning("⚠️ Please fill all fields!")
            else:
                ok = insert_client_query(st.session_state["user_id"], email, mobile, query_heading, query_description)
                if ok:
                    st.success("✅ Query submitted successfully! Your query status is 'Open'.")

    # ---------- SUPPORT ----------
    if st.session_state.get("logged_in") and st.session_state.get("role") == "support":
        st.markdown("<div class='dashboard-header'><h2>🛠️ Support Team Dashboard</h2></div>", unsafe_allow_html=True)

        status_filter = st.selectbox("Filter queries by status", ["All", "Open", "Closed"])
        queries = get_all_queries(status_filter)

        if not queries:
            st.info("No queries found.")
        else:
            st.markdown("### 📋 Query List")
            df = pd.DataFrame(queries)

            # 🧠 Step 1: Ensure proper datetime conversion for EDA
            df["query_created_time"] = pd.to_datetime(df["query_created_time"], errors="coerce")
            df["query_closed_time"] = pd.to_datetime(df["query_closed_time"], errors="coerce")
            df["created_date"] = df["query_created_time"].dt.date

            st.dataframe(df, use_container_width=True)

            # 🧩 Step 2: EDA Visualization Section
            st.markdown("## 📊 Query Analytics Overview")

            # 1️⃣ Queries Over Time
            queries_over_time = df.groupby("created_date").size().reset_index(name="count")
            if not queries_over_time.empty:
                fig_time = px.line(queries_over_time, x="created_date", y="count", markers=True,
                                   title="📅 Queries Created Over Time")
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("No data available for Queries Over Time chart.")

            # 2️⃣ Status Distribution
            status_count = df["status"].value_counts().reset_index()
            status_count.columns = ["status", "count"]
            if not status_count.empty:
                fig_status = px.pie(status_count, names="status", values="count",
                                    title="🟢 Query Status Distribution")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No data available for Status Distribution chart.")

            # 3️⃣ Average Resolution Time
            df["resolution_time_days"] = (df["query_closed_time"] - df["query_created_time"]).dt.total_seconds() / (3600 * 24)
            resolution_data = df[df["status"] == "Closed"].groupby("user_id")["resolution_time_days"].mean().reset_index()

            if not resolution_data.empty:
                fig_resolution = px.bar(resolution_data, x="user_id", y="resolution_time_days",
                                        title="⏱️ Average Query Resolution Time (per User)", text_auto=".2f")
                st.plotly_chart(fig_resolution, use_container_width=True)
            else:
                st.info("No closed queries yet for resolution time analysis.")

            # ✅ Query Close section stays as before
            open_queries = [q for q in queries if q["status"] == "Open"]
            if open_queries:
                st.markdown("### ✅ Close a Query")
                query_options = {f"{q['query_id']} - {q['query_heading']}": q['query_id'] for q in open_queries}
                selected_query = st.selectbox("Select Query to Close", list(query_options.keys()))

                if st.button("Close Selected Query"):
                    query_id = query_options[selected_query]
                    query_heading = selected_query.split(" - ", 1)[1]
                    try:
                        close_query(query_id)
                        st.session_state["last_closed_message"] = f"✅ Query #{query_id} – {query_heading} closed successfully!"
                        st.success(st.session_state["last_closed_message"])
                        time.sleep(3)
                        del st.session_state["last_closed_message"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error closing query: {e}")

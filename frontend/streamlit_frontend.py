import streamlit as st
import requests
from datetime import datetime

# ============================================
# CONFIGURATION — update this after deploying backend on Render
# ============================================
API_BASE_URL = "http://localhost:8000"

ROLES = {0: "Admin", 1: "Staff", 2: "User"}
ACCESS_LEVELS = {0: "Admin Only", 1: "Admin & Staff", 2: "Public (All Users)"}


# ============================================
# SESSION STATE
# ============================================
def init_session():
    defaults = {"token": None, "user": None, "current_session_id": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ============================================
# API HELPERS
# ============================================
def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_post(endpoint, json_data=None, data=None, files=None, use_auth=True):
    try:
        return requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=json_data, data=data, files=files,
            headers=headers() if use_auth else {}
        )
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None

def api_get(endpoint, params=None):
    try:
        return requests.get(f"{API_BASE_URL}{endpoint}", headers=headers(), params=params)
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None

def api_delete(endpoint):
    try:
        return requests.delete(f"{API_BASE_URL}{endpoint}", headers=headers())
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None


# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    st.title("🧠 DocuMind")
    st.subheader("Document Management System")
    st.divider()

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            resp = api_post("/auth/login", data={"username": email, "password": password}, use_auth=False)
            if resp and resp.status_code == 200:
                st.session_state.token = resp.json()["access_token"]
                me = api_get("/auth/me")
                if me and me.status_code == 200:
                    st.session_state.user = me.json()
                st.success("✅ Logged in!")
                st.rerun()
            elif resp:
                st.error(f"❌ {resp.json().get('detail', 'Login failed')}")

    with tab2:
        with st.form("register_form"):
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Register as User", use_container_width=True)

        if submitted:
            resp = api_post("/auth/register", json_data={"email": reg_email, "password": reg_password, "role": 2}, use_auth=False)
            if resp and resp.status_code == 200:
                st.success("✅ Registered! You can now log in.")
            elif resp:
                st.error(f"❌ {resp.json().get('detail', 'Registration failed')}")


# ============================================
# SIDEBAR
# ============================================
def sidebar():
    with st.sidebar:
        user = st.session_state.user
        st.markdown(f"### 👤 {user['email']}")
        st.markdown(f"**Role:** `{ROLES.get(user['role'], '?')}`")
        st.divider()

        pages = ["💬 Chat"]
        if user["role"] in [0, 1]:
            pages.append("📄 Documents")
        if user["role"] == 0:
            pages += ["👥 User Management", "📊 Admin Dashboard"]

        page = st.radio("Navigate", pages, label_visibility="collapsed")
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            for key in ["token", "user", "current_session_id"]:
                st.session_state[key] = None
            st.rerun()

    return page


# ============================================
# CHAT PAGE
# ============================================
def chat_page():
    st.title("💬 Chat with Documents")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Sessions")
        if st.button("➕ New Session", use_container_width=True):
            resp = api_post("/chat/session", json_data={})
            if resp and resp.status_code == 200:
                st.session_state.current_session_id = resp.json()["id"]
                st.rerun()

        sessions_resp = api_get("/chat/sessions")
        if sessions_resp and sessions_resp.status_code == 200:
            for s in sessions_resp.json():
                created = datetime.fromisoformat(s["created_at"]).strftime("%b %d %H:%M")
                is_active = st.session_state.current_session_id == s["id"]
                btn_type = "primary" if is_active else "secondary"

                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(f"#{s['id']} · {created}", key=f"s_{s['id']}", type=btn_type, use_container_width=True):
                        st.session_state.current_session_id = s["id"]
                        st.rerun()
                with c2:
                    if st.button("🗑", key=f"d_{s['id']}"):
                        api_delete(f"/chat/session/{s['id']}")
                        if st.session_state.current_session_id == s["id"]:
                            st.session_state.current_session_id = None
                        st.rerun()

    with col2:
        if not st.session_state.current_session_id:
            st.info("👈 Create or select a chat session to begin.")
            return

        st.subheader(f"Session #{st.session_state.current_session_id}")

        history_resp = api_get(f"/chat/session/{st.session_state.current_session_id}/history")
        if history_resp and history_resp.status_code == 200:
            for msg in history_resp.json():
                with st.chat_message("user" if msg["role"] == 0 else "assistant"):
                    st.write(msg["context"])

        user_input = st.chat_input("Ask a question about your documents...")
        if user_input:
            resp = api_post(
                f"/chat/session/{st.session_state.current_session_id}/message",
                json_data={"content": user_input}
            )
            if resp and resp.status_code == 200:
                st.rerun()
            elif resp:
                st.error(f"❌ {resp.json().get('detail', 'Error')}")


# ============================================
# DOCUMENTS PAGE
# ============================================
def documents_page():
    st.title("📄 Document Management")
    user = st.session_state.user

    tab1, tab2 = st.tabs(["📋 All Documents", "⬆️ Upload"])

    with tab1:
        resp = api_get("/doc/all_docs")
        if resp and resp.status_code == 200:
            data = resp.json()
            st.markdown(f"**Total:** {data['total']} documents")
            for doc in data["list_documents"]:
                with st.expander(f"📄 {doc['filename']} — {ACCESS_LEVELS.get(doc['access_level'], '?')}"):
                    st.write(f"**ID:** {doc['id']}")
                    st.write(f"**Access:** {ACCESS_LEVELS.get(doc['access_level'], '?')}")
                    st.write(f"**Uploaded:** {doc['created_at']}")
                    if user["role"] == 0:
                        if st.button(f"🗑 Delete", key=f"del_{doc['id']}"):
                            dr = api_delete(f"/doc/delete/{doc['id']}")
                            if dr and dr.status_code == 200:
                                st.success("Deleted!")
                                st.rerun()
        elif resp and resp.status_code == 404:
            st.info("No documents uploaded yet.")

    with tab2:
        st.subheader("Upload New Document")
        with st.form("upload_form"):
            uploaded_file = st.file_uploader("Choose a file (.pdf or .txt)", type=["pdf", "txt"])
            level_options = {"Public (All Users)": 2, "Admin & Staff": 1}
            if user["role"] == 0:
                level_options["Admin Only"] = 0
            label = st.selectbox("Who can access this document?", list(level_options.keys()))
            submitted = st.form_submit_button("Upload", use_container_width=True)

        if submitted and uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            resp = api_post("/doc/upload", data={"access_level": level_options[label]}, files=files)
            if resp and resp.status_code == 200:
                st.success(f"✅ '{uploaded_file.name}' uploaded!")
                st.rerun()
            elif resp:
                st.error(f"❌ {resp.json().get('detail', 'Upload failed')}")


# ============================================
# USER MANAGEMENT PAGE (ADMIN)
# ============================================
def user_management_page():
    st.title("👥 User Management")

    tab1, tab2, tab3 = st.tabs(["📋 All Users", "➕ Create Staff", "➕ Create Admin"])

    with tab1:
        resp = api_get("/auth/users", params={"limit": 100})
        if resp and resp.status_code == 200:
            for u in resp.json():
                icon = "🔴" if u["is_deleted"] else "🟢"
                with st.expander(f"{icon} {u['email']} — {ROLES.get(u['role'], '?')}"):
                    st.write(f"**ID:** {u['id']} | **Role:** {ROLES.get(u['role'])} | **Status:** {'Deactivated' if u['is_deleted'] else 'Active'}")
                    st.write(f"**Created:** {u['created_at']}")
                    if not u["is_deleted"] and u["id"] != st.session_state.user["id"]:
                        if st.button(f"🗑 Deactivate", key=f"du_{u['id']}"):
                            dr = api_delete(f"/auth/users/{u['id']}")
                            if dr and dr.status_code == 200:
                                st.success("User deactivated!")
                                st.rerun()

    with tab2:
        with st.form("create_staff"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Create Staff", use_container_width=True):
                resp = api_post("/auth/admin/create-staff", json_data={"email": email, "password": password, "role": 1})
                if resp and resp.status_code == 200:
                    st.success(f"✅ Staff '{email}' created!")
                elif resp:
                    st.error(resp.json().get("detail", "Failed"))

    with tab3:
        with st.form("create_admin"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Create Admin", use_container_width=True):
                resp = api_post("/auth/admin/create-admin", json_data={"email": email, "password": password, "role": 0})
                if resp and resp.status_code == 200:
                    st.success(f"✅ Admin '{email}' created!")
                elif resp:
                    st.error(resp.json().get("detail", "Failed"))


# ============================================
# ADMIN DASHBOARD
# ============================================
def admin_dashboard_page():
    st.title("📊 Admin Dashboard")

    resp = api_get("/chat/admin/all-sessions")
    if resp and resp.status_code == 200:
        data = resp.json()
        st.subheader(f"All Users ({len(data)} total)")
        for u in data:
            with st.expander(f"👤 {u['email']} ({ROLES.get(u['role'])}) — {u['session_count']} sessions"):
                if u["sessions"]:
                    for s in u["sessions"]:
                        created = datetime.fromisoformat(str(s["created_at"])).strftime("%b %d %H:%M")
                        st.write(f"• Session #{s['id']} | {created} | {s['message_count']} messages")
                else:
                    st.write("No sessions yet.")


# ============================================
# MAIN
# ============================================
def main():
    st.set_page_config(
        page_title="DocuMind",
        page_icon="🧠",
        layout="wide"
    )

    if not st.session_state.token:
        login_page()
        return

    page = sidebar()

    if page == "💬 Chat":
        chat_page()
    elif page == "📄 Documents":
        documents_page()
    elif page == "👥 User Management":
        user_management_page()
    elif page == "📊 Admin Dashboard":
        admin_dashboard_page()


if __name__ == "__main__":
    main()

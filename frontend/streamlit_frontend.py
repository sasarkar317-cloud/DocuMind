import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, List
import json

# ============================================
# CONFIGURATION
# ============================================
API_BASE_URL = "https://documind-czq5.onrender.com"

# Role mappings
ROLES = {
    0: "Admin",
    1: "Staff", 
    2: "User"
}

ACCESS_LEVELS = {
    0: "Admin Only",
    1: "Admin & Staff",
    2: "Public (All Users)"
}

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
def init_session_state():
    """Initialize session state variables"""
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_chat_session' not in st.session_state:
        st.session_state.current_chat_session = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'show_error_details' not in st.session_state:
        st.session_state.show_error_details = False

# Initialize session state immediately when module loads
init_session_state()

# ============================================
# ERROR DISPLAY FUNCTIONS
# ============================================
def display_error(response: requests.Response, context: str = ""):
    """Display detailed error information from API response"""
    status_code = response.status_code
    
    # Try to parse error detail from response
    try:
        error_data = response.json()
        error_detail = error_data.get('detail', 'Unknown error')
    except:
        error_detail = response.text or "Unknown error"
    
    # Map status codes to user-friendly messages and icons
    error_types = {
        400: ("⚠️", "Bad Request", "warning"),
        401: ("🔒", "Unauthorized", "error"),
        403: ("🚫", "Forbidden", "error"),
        404: ("🔍", "Not Found", "info"),
        422: ("❌", "Validation Error", "warning"),
        500: ("💥", "Server Error", "error"),
    }
    
    icon, title, msg_type = error_types.get(status_code, ("❌", "Error", "error"))
    
    # Display error based on type
    if msg_type == "error":
        st.error(f"{icon} **{title}** ({status_code}): {error_detail}")
    elif msg_type == "warning":
        st.warning(f"{icon} **{title}** ({status_code}): {error_detail}")
    else:
        st.info(f"{icon} **{title}** ({status_code}): {error_detail}")
    
    # Show detailed error info in expander
    if st.session_state.show_error_details:
        with st.expander("🔍 Error Details", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Request Info:**")
                st.code(f"Method: {response.request.method}\nURL: {response.url}\nStatus: {status_code}")
            
            with col2:
                st.write("**Response Headers:**")
                headers_str = "\n".join([f"{k}: {v}" for k, v in response.headers.items()])
                st.code(headers_str, language="text")
            
            if context:
                st.write(f"**Context:** {context}")
            
            st.write("**Full Response:**")
            try:
                st.json(response.json())
            except:
                st.code(response.text)

def show_success(message: str, icon: str = "✅"):
    """Display success message with animation"""
    st.success(f"{icon} {message}")

# ============================================
# API HELPER FUNCTIONS
# ============================================
def get_headers() -> Dict[str, str]:
    """Get headers with authentication token"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def api_request(method: str, endpoint: str, show_errors: bool = True, context: str = "", **kwargs) -> Optional[Dict]:
    """Make API request with comprehensive error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, **kwargs)
        
        # Success responses
        if response.status_code in [200, 201]:
            return response.json()
        
        # Handle specific error cases
        if response.status_code == 401:
            if show_errors:
                st.error("🔒 **Session Expired**: Your session has expired. Please login again.")
            logout()
            return None
        
        elif response.status_code == 403:
            if show_errors:
                try:
                    detail = response.json().get('detail', 'Access forbidden')
                    st.error(f"🚫 **Access Denied**: {detail}")
                except:
                    st.error("🚫 **Access Denied**: You don't have permission to perform this action.")
        
        elif response.status_code == 404:
            if show_errors:
                try:
                    detail = response.json().get('detail', 'Resource not found')
                    st.warning(f"🔍 **Not Found**: {detail}")
                except:
                    st.warning("🔍 **Not Found**: The requested resource was not found.")
        
        elif response.status_code == 400:
            if show_errors:
                try:
                    detail = response.json().get('detail', 'Bad request')
                    st.warning(f"⚠️ **Invalid Request**: {detail}")
                except:
                    st.warning("⚠️ **Invalid Request**: The request was invalid.")
        
        elif response.status_code == 422:
            if show_errors:
                try:
                    error_data = response.json()
                    detail = error_data.get('detail', 'Validation error')
                    st.warning(f"❌ **Validation Error**: {detail}")
                    
                    # Show validation details if available
                    if isinstance(detail, list):
                        with st.expander("Validation Details"):
                            for error in detail:
                                st.write(f"• **{error.get('loc', [])}**: {error.get('msg', '')}")
                except:
                    st.warning("❌ **Validation Error**: The data provided was invalid.")
        
        else:
            # Generic error handling
            if show_errors:
                try:
                    detail = response.json().get('detail', 'An error occurred')
                    st.error(f"💥 **Error ({response.status_code})**: {detail}")
                except:
                    st.error(f"💥 **Error ({response.status_code})**: An unexpected error occurred.")
        
        # Display detailed error if enabled
        if show_errors and st.session_state.show_error_details:
            display_error(response, context)
        
        return None
        
    except requests.exceptions.ConnectionError:
        if show_errors:
            st.error("🔌 **Connection Error**: Cannot connect to the server. Please ensure the backend is running on " + API_BASE_URL)
        return None
    
    except requests.exceptions.Timeout:
        if show_errors:
            st.error("⏱️ **Timeout Error**: The request took too long. Please try again.")
        return None
    
    except Exception as e:
        if show_errors:
            st.error(f"❌ **Unexpected Error**: {str(e)}")
            if st.session_state.show_error_details:
                with st.expander("Error Traceback"):
                    st.exception(e)
        return None

# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================
def login(email: str, password: str) -> bool:
    """Login user and store token"""
    data = {"username": email, "password": password}
    response = requests.post(f"{API_BASE_URL}/auth/login", data=data)
    
    if response.status_code == 200:
        result = response.json()
        st.session_state.token = result['access_token']
        
        # Get user details
        user_data = api_request("GET", "/auth/me", headers=get_headers(), show_errors=False)
        if user_data:
            st.session_state.user = user_data
            return True
    else:
        # Display error
        display_error(response, "Login attempt")
    
    return False

def register(email: str, password: str) -> bool:
    """Register new user"""
    data = {"email": email, "password": password, "role": 2}
    response = requests.post(f"{API_BASE_URL}/auth/register", json=data)
    
    if response.status_code in [200, 201]:
        return True
    else:
        display_error(response, "Registration attempt")
    
    return False

def logout():
    """Logout user and clear session"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.current_chat_session = None
    st.session_state.chat_messages = []
    st.session_state.page = 'login'
    st.rerun()

# ============================================
# DOCUMENT FUNCTIONS
# ============================================
def upload_document(file, access_level: int) -> bool:
    """Upload document to server"""
    files = {"file": (file.name, file, file.type)}
    data = {"access_level": access_level}
    
    try:
        url = f"{API_BASE_URL}/doc/upload"
        response = requests.post(url, files=files, data=data, headers=get_headers())
        
        if response.status_code == 200:
            return True
        else:
            display_error(response, f"Uploading document: {file.name}")
            return False
    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")
        return False

def get_documents() -> Optional[List[Dict]]:
    """Get all documents"""
    response = api_request("GET", "/doc/all_docs", headers=get_headers(), context="Fetching documents list")
    if response:
        return response.get('list_documents', [])
    return None

def delete_document(doc_id: int) -> bool:
    """Delete document"""
    response = api_request("DELETE", f"/doc/delete/{doc_id}", headers=get_headers(), context=f"Deleting document ID: {doc_id}")
    return response is not None

# ============================================
# CHAT FUNCTIONS
# ============================================
def create_chat_session() -> Optional[Dict]:
    """Create new chat session"""
    return api_request("POST", "/chat/session", headers=get_headers(), context="Creating new chat session")

def send_message(session_id: int, message: str) -> Optional[Dict]:
    """Send message in chat session"""
    data = {"content": message}
    return api_request("POST", f"/chat/session/{session_id}/message", 
                      json=data, headers=get_headers(), context=f"Sending message to session {session_id}")

def get_chat_sessions() -> Optional[List[Dict]]:
    """Get user's chat sessions"""
    return api_request("GET", "/chat/sessions", headers=get_headers(), 
                      show_errors=False, context="Fetching chat sessions")

def get_chat_history(session_id: int) -> Optional[List[Dict]]:
    """Get chat history for a session"""
    return api_request("GET", f"/chat/session/{session_id}/history", 
                      headers=get_headers(), show_errors=False, context=f"Fetching history for session {session_id}")

def delete_chat_session(session_id: int) -> bool:
    """Delete chat session"""
    response = api_request("DELETE", f"/chat/session/{session_id}", 
                          headers=get_headers(), context=f"Deleting chat session {session_id}")
    return response is not None

# ============================================
# ADMIN FUNCTIONS
# ============================================
def get_all_users() -> Optional[List[Dict]]:
    """Get all users (Admin only)"""
    return api_request("GET", "/auth/users", headers=get_headers(), context="Fetching all users")

def delete_user(user_id: int) -> bool:
    """Delete user (Admin only)"""
    response = api_request("DELETE", f"/auth/users/{user_id}", 
                          headers=get_headers(), context=f"Deleting user ID: {user_id}")
    return response is not None

def create_staff(email: str, password: str) -> bool:
    """Create staff user (Admin only)"""
    data = {"email": email, "password": password, "role": 1}
    response = api_request("POST", "/auth/admin/create-staff", 
                          json=data, headers=get_headers(), context=f"Creating staff user: {email}")
    return response is not None

def create_admin(email: str, password: str) -> bool:
    """Create admin user (Admin only)"""
    data = {"email": email, "password": password, "role": 0}
    response = api_request("POST", "/auth/admin/create-admin", 
                          json=data, headers=get_headers(), context=f"Creating admin user: {email}")
    return response is not None

def get_all_sessions() -> Optional[List[Dict]]:
    """Get all chat sessions (Admin only)"""
    return api_request("GET", "/chat/admin/all-sessions", headers=get_headers(), context="Fetching all chat sessions")

# ============================================
# UI PAGES
# ============================================
def login_page():
    """Login and registration page"""
    st.title("📚 DocuMind")
    st.caption("Intelligent Document Management System")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        st.subheader("Welcome Back!")
        
        email = st.text_input("📧 Email Address", key="login_email", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password", key="login_password", placeholder="Enter your password")
        
        if st.button("🚀 Sign In", type="primary", use_container_width=True):
            if email and password:
                with st.spinner("Authenticating..."):
                    if login(email, password):
                        st.success("✅ Welcome back!")
                        st.balloons()
                        st.rerun()
            else:
                st.warning("⚠️ Please enter your credentials")
    
    with tab2:
        st.subheader("Create Account")
        st.info("👤 New accounts are created with User role")
        
        reg_email = st.text_input("📧 Email Address", key="reg_email", placeholder="you@example.com")
        reg_password = st.text_input("🔒 Password", type="password", key="reg_password", placeholder="Create a password")
        reg_password2 = st.text_input("🔒 Confirm Password", type="password", key="reg_password2", placeholder="Confirm your password")
        
        if st.button("✨ Create Account", type="primary", use_container_width=True):
            if reg_email and reg_password and reg_password2:
                if reg_password == reg_password2:
                    with st.spinner("Creating your account..."):
                        if register(reg_email, reg_password):
                            st.success("✅ Account created! Please sign in.")
                            st.balloons()
                else:
                    st.error("❌ Passwords don't match")
            else:
                st.warning("⚠️ Please fill all fields")

def chat_page():
    """Chat interface with RAG"""
    st.title("💬 AI Assistant")
    st.caption("Ask questions about your documents")
    
    st.divider()
    
    with st.sidebar:
        st.subheader("💭 Conversations")
        
        if st.button("✨ New Chat", use_container_width=True, type="primary"):
            session = create_chat_session()
            if session:
                st.session_state.current_chat_session = session['id']
                st.session_state.chat_messages = []
                show_success("Chat created!")
                st.rerun()
        
        st.divider()
        
        sessions = get_chat_sessions()
        if sessions:
            st.caption(f"{len(sessions)} conversation(s)")
            
            for session in sessions:
                session_date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                is_active = st.session_state.current_chat_session == session['id']
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    button_type = "primary" if is_active else "secondary"
                    button_label = f"{'🟢' if is_active else '⚪'} {session_date.strftime('%b %d, %H:%M')}"
                    if st.button(button_label, key=f"session_{session['id']}", use_container_width=True, type=button_type):
                        st.session_state.current_chat_session = session['id']
                        history = get_chat_history(session['id'])
                        st.session_state.chat_messages = history if history else []
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"delete_{session['id']}"):
                        if delete_chat_session(session['id']):
                            if st.session_state.current_chat_session == session['id']:
                                st.session_state.current_chat_session = None
                                st.session_state.chat_messages = []
                            show_success("Deleted!")
                            st.rerun()
    
    if st.session_state.current_chat_session:
        # Display chat messages
        for msg in st.session_state.chat_messages:
            role = "user" if msg['role'] == 0 else "assistant"
            with st.chat_message(role):
                st.write(msg['context'])
        
        # Chat input
        if prompt := st.chat_input("💭 Ask me anything..."):
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.spinner("🤔 Thinking..."):
                response = send_message(st.session_state.current_chat_session, prompt)
                
                if response:
                    history = get_chat_history(st.session_state.current_chat_session)
                    st.session_state.chat_messages = history if history else []
                    st.rerun()
    else:
        st.info("🤖 Start a conversation to get AI-powered answers from your documents")
        
        st.subheader("Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("📄 **Document Analysis**")
            st.caption("Extract insights and information")
        
        with col2:
            st.write("🔍 **Smart Search**")
            st.caption("Find answers instantly")
        
        with col3:
            st.write("💡 **AI Insights**")
            st.caption("Intelligent recommendations")

def documents_page():
    """Document management page"""
    st.title("📚 Document Library")
    st.caption("Manage your documents and files")
    
    st.divider()
    
    user_role = st.session_state.user['role']
    
    # Upload section (only for Admin and Staff)
    if user_role in [0, 1]:
        st.subheader("📤 Upload Document")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'txt'],
                help="Upload PDF or TXT documents"
            )
        
        with col2:
            access_options = {
                2: "🌐 Public",
                1: "👥 Staff",
                0: "🔒 Admin Only"
            }
            
            if user_role == 1:
                del access_options[0]
            
            access_level = st.selectbox(
                "Access Level",
                options=list(access_options.keys()),
                format_func=lambda x: access_options[x]
            )
        
        if uploaded_file:
            if st.button("⬆️ Upload Document", type="primary", use_container_width=True):
                with st.spinner("🔄 Processing..."):
                    if upload_document(uploaded_file, access_level):
                        show_success(f"{uploaded_file.name} uploaded!")
                        st.balloons()
                        st.rerun()
        
        st.divider()
    
    # Documents list
    st.subheader("📋 Your Documents")
    
    documents = get_documents()
    
    if documents:
        # Filter out deleted documents for display
        active_documents = [doc for doc in documents if not doc['is_deleted']]
        
        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 Total Documents", len(active_documents))
        with col2:
            # Count by access level
            public_docs = sum(1 for d in active_documents if d['access_level'] == 2)
            st.metric("🌐 Public Documents", public_docs)
        
        st.divider()
        
        # Document list
        for doc in active_documents:
            with st.expander(f"📄 {doc['filename']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Access:** {ACCESS_LEVELS.get(doc['access_level'], 'Unknown')}")
                    upload_date = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
                    st.write(f"**Uploaded:** {upload_date.strftime('%b %d, %Y')}")
                
                with col2:
                    st.write(f"**ID:** #{doc['id']}")
                    st.write(f"**Status:** ✅ Active")
                
                with col3:
                    # Only admins can delete documents
                    if user_role == 0:
                        if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}", type="secondary"):
                            if delete_document(doc['id']):
                                show_success("Document deleted!")
                                st.rerun()
    else:
        st.info("📭 No documents yet")

def admin_page():
    """Admin dashboard"""
    st.title("⚙️ Admin Dashboard")
    st.caption("Manage users and view analytics")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "➕ Create Staff", "👑 Create Admin", "📊 Sessions"])
    
    with tab1:
        st.subheader("User Management")
        
        users = get_all_users()
        
        if users:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Total Users", len(users))
            with col2:
                admins = sum(1 for u in users if u['role'] == 0)
                st.metric("👑 Admins", admins)
            with col3:
                staff = sum(1 for u in users if u['role'] == 1)
                st.metric("👔 Staff", staff)
            with col4:
                regular = sum(1 for u in users if u['role'] == 2)
                st.metric("👤 Users", regular)
            
            st.divider()
            
            # User list
            for user in users:
                with st.expander(f"👤 {user['email']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**User ID:** #{user['id']}")
                        st.write(f"**Role:** {ROLES.get(user['role'], 'Unknown')}")
                    
                    with col2:
                        created = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                        st.write(f"**Joined:** {created.strftime('%b %d, %Y')}")
                        status = "✅ Active" if not user['is_deleted'] else "🗑️ Deleted"
                        st.write(f"**Status:** {status}")
                    
                    with col3:
                        if not user['is_deleted'] and user['id'] != st.session_state.user['id']:
                            if st.button("🗑️ Delete", key=f"del_user_{user['id']}", type="secondary"):
                                if delete_user(user['id']):
                                    show_success("User deleted!")
                                    st.rerun()
        else:
            st.info("👥 No users found")
    
    with tab2:
        st.subheader("👔 Create Staff User")
        st.info("Staff users can upload and manage documents (except Admin-only documents)")
        
        staff_email = st.text_input("📧 Email Address", key="staff_email", placeholder="staff@example.com")
        staff_password = st.text_input("🔒 Password", type="password", key="staff_password", placeholder="Create a password")
        staff_password2 = st.text_input("🔒 Confirm Password", type="password", key="staff_password2", placeholder="Confirm password")
        
        if st.button("✨ Create Staff User", type="primary", use_container_width=True):
            if staff_email and staff_password and staff_password2:
                if staff_password == staff_password2:
                    if create_staff(staff_email, staff_password):
                        show_success("Staff user created successfully!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Passwords don't match")
            else:
                st.warning("⚠️ Please fill all fields")
    
    with tab3:
        st.subheader("👑 Create Admin User")
        st.warning("⚠️ Admin users have full system access. Use with caution!")
        
        admin_email = st.text_input("📧 Email Address", key="admin_email", placeholder="admin@example.com")
        admin_password = st.text_input("🔒 Password", type="password", key="admin_password", placeholder="Create a password")
        admin_password2 = st.text_input("🔒 Confirm Password", type="password", key="admin_password2", placeholder="Confirm password")
        
        if st.button("✨ Create Admin User", type="primary", use_container_width=True):
            if admin_email and admin_password and admin_password2:
                if admin_password == admin_password2:
                    if create_admin(admin_email, admin_password):
                        show_success("Admin user created successfully!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Passwords don't match")
            else:
                st.warning("⚠️ Please fill all fields")
    
    with tab4:
        st.subheader("💬 All Chat Sessions")
        
        all_sessions = get_all_sessions()
        
        if all_sessions:
            total_sessions = sum(user['session_count'] for user in all_sessions)
            total_messages = sum(
                session['message_count']
                for user_data in all_sessions
                for session in user_data['sessions']
            )
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Active Users", len(all_sessions))
            with col2:
                st.metric("💬 Total Sessions", total_sessions)
            with col3:
                st.metric("💭 Total Messages", total_messages)
            with col4:
                avg = total_messages // total_sessions if total_sessions > 0 else 0
                st.metric("📈 Avg/Session", avg)
            
            st.divider()
            
            # Session details by user
            for user_data in all_sessions:
                with st.expander(f"👤 {user_data['email']} • {user_data['session_count']} session(s)", expanded=False):
                    st.write(f"**Role:** {ROLES.get(user_data['role'], 'Unknown')}")
                    
                    if user_data['sessions']:
                        for session in user_data['sessions']:
                            created = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**💬 Session #{session['id']}** - {created.strftime('%b %d, %Y %H:%M')}")
                                st.caption(f"📊 {session['message_count']} messages")
                            
                            with col2:
                                # Admin can delete any session
                                if st.button("🗑️", key=f"admin_del_session_{session['id']}", help="Delete this session"):
                                    if delete_chat_session(session['id']):
                                        show_success(f"Session #{session['id']} deleted!")
                                        st.rerun()
                            
                            # Show message history
                            if session['message_count'] > 0:
                                if st.checkbox(f"Show messages", key=f"show_history_{session['id']}", value=False):
                                    chat_history = get_chat_history(session['id'])
                                    
                                    if chat_history:
                                        for idx, msg in enumerate(chat_history):
                                            msg_time = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
                                            role_icon = "👤" if msg['role'] == 0 else "🤖"
                                            role_name = "User" if msg['role'] == 0 else "AI"
                                            
                                            st.write(f"**{role_icon} {role_name}** - {msg_time.strftime('%H:%M:%S')}")
                                            
                                            content = msg['context']
                                            if len(content) > 300:
                                                show_full = st.checkbox(
                                                    "Show full message", 
                                                    key=f"show_msg_{session['id']}_{idx}",
                                                    value=False
                                                )
                                                display = content if show_full else content[:300] + "..."
                                            else:
                                                display = content
                                            
                                            st.code(display, language="text")
                            
                            st.divider()
        else:
            st.info("📊 No chat session data available")

# ============================================
# MAIN APP
# ============================================
def main():
    st.set_page_config(
        page_title="DocuMind - AI Document Management",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded" if st.session_state.token else "collapsed"
    )
    
    init_session_state()
    
    if not st.session_state.token:
        login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📚 DocuMind")
        st.caption("AI-Powered DMS")
        
        st.divider()
        
        user = st.session_state.user
        st.write(f"**👤 {user['email']}**")
        st.caption(f"Role: {ROLES.get(user['role'], 'Unknown')}")
        
        st.divider()
        
        # Developer mode toggle
        st.session_state.show_error_details = st.checkbox(
            "🔧 Developer Mode", 
            value=st.session_state.show_error_details,
            help="Show detailed error information for debugging"
        )
        
        st.divider()
        
        st.subheader("Navigation")
        
        # Navigation buttons
        pages = {"💬 AI Assistant": "chat"}
        
        if user['role'] in [0, 1]:
            pages["📚 Documents"] = "documents"
        
        if user['role'] == 0:
            pages["⚙️ Admin"] = "admin"
        
        for page_name, page_key in pages.items():
            button_type = "primary" if st.session_state.page == page_key else "secondary"
            if st.button(page_name, use_container_width=True, type=button_type):
                st.session_state.page = page_key
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            logout()
    
    # Render the selected page
    if st.session_state.page == "chat":
        chat_page()
    elif st.session_state.page == "documents":
        documents_page()
    elif st.session_state.page == "admin":
        admin_page()

if __name__ == "__main__":
    main()

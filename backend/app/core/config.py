from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# SECURITY
# =========================
SECRET_KEY = os.getenv("SECRET_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# =========================
# INITIAL USERS
# =========================
INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD")

INITIAL_STAFF_EMAIL = os.getenv("INITIAL_STAFF_EMAIL")
INITIAL_STAFF_PASSWORD = os.getenv("INITIAL_STAFF_PASSWORD")

INITIAL_USER_EMAIL = os.getenv("INITIAL_USER_EMAIL")
INITIAL_USER_PASSWORD = os.getenv("INITIAL_USER_PASSWORD")

# =========================
# DATABASE (SQLite)
# =========================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dms.db")

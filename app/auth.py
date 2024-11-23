from flask import session, request
from flask_jwt_extended import verify_jwt_in_request
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os

auth = HTTPBasicAuth()
load_dotenv()

CREDENTIALS = {
    "admin": os.getenv("ADMIN_PASSWORD", "default-admin-password"),
    "dotnet_user": os.getenv("DOTNET_USER_PASSWORD", "default-dotnet-password")
}

@auth.verify_password
def verify_password(username, password):
    print(f"Debug: Username={username}, Password={password}")
    print(f"Debug: CREDENTIALS={CREDENTIALS}")
    if username in CREDENTIALS and CREDENTIALS[username] == password:
        return username
    return None

def authenticate_request():
    if request.path.startswith('/api/'):
        if 'Authorization' in request.headers:
            try:
                verify_jwt_in_request()
                return
            except Exception as e:
                return f"JWT Error: {str(e)}", 401  # Return error as a string
        elif session.get('admin_logged_in'):
            return
        else:
            return "Unauthorized", 401  # Return plain string for unauthorized access
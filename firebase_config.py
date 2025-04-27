# firebase_config.py
import firebase_admin
from firebase_admin import credentials, storage, initialize_app
import pyrebase
import os
import streamlit as st
import json

# Check if the app is running on Streamlit Cloud
if os.getenv("RUNNING_IN_STREAMLIT_CLOUD"):
    cred=credentials.Certificate(st.secrets["firebase"])
else:
    cred = credentials.Certificate(r"C:\Users\vedan\Downloads\travelplanner-43fb2-firebase-adminsdk-fbsvc-33bf021161.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'your-project-id.appspot.com'
})

# Initialize Pyrebase (for client operations)
firebase_config = {
    "apiKey": "AIzaSyA79hwte9OM-uD3wXS8m_F46mqJBMuBrJg",
    "authDomain": "travelplanner-43fb2.firebaseapp.com",
    "databaseURL": "https://travelplanner-43fb2.firebaseio.com",
    "projectId": "travelplanner-43fb2",
    "storageBucket": "travelplanner-43fb2.firebasestorage.app",
    "messagingSenderId": "537409361764",
    "appId": "1:537409361764:web:6f5627863a54a23f600c71"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
storage = firebase.storage()

def upload_file(file_path, destination_path):
    try:
        storage.child(destination_path).put(file_path)
        url = storage.child(destination_path).get_url(None)
        return url
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def download_file(cloud_path, local_path):
    try:
        storage.child(cloud_path).download(local_path)
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def authenticate_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def create_user(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return user
    except Exception as e:
        print(f"User creation error: {e}")
        return None
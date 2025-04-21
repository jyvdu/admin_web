import firebase_admin
from firebase_admin import credentials, db
import streamlit as st
import json

def initialize_firebase():
    print("Initializing Firebase with URL: https://research-58228-default-rtdb.asia-southeast1.firebasedatabase.app/")
    if not firebase_admin._apps:
        # Use Streamlit secrets for deployment
        try:
            # Try to use Streamlit secrets
            service_account_info = st.secrets["firebase"]
            cred = credentials.Certificate(service_account_info)
        except:
            cred = credentials.Certificate("serviceAccountKey.json")
            
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://research-58228-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
    return firebase_admin.get_app()
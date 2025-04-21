import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    print("Initializing Firebase with URL: https://research-58228-default-rtdb.asia-southeast1.firebasedatabase.app/")
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://research-58228-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
    return firebase_admin.get_app()
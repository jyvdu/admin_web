import streamlit as st
import base64
import os
import firebase_admin
from firebase_admin import credentials, db

# --- Firebase Initialization Function ---
def initialize_firebase():
    """Initialize Firebase with appropriate error handling and flexibility for deployments"""
    try:
        if not firebase_admin._apps:
            # Try to use Streamlit secrets for cloud deployment
            try:
                service_account_info = st.secrets["firebase"]
                cred = credentials.Certificate(service_account_info)
                print("Using Firebase credentials from Streamlit secrets")
            except Exception as e:
                # Fall back to file for local development
                print(f"Falling back to serviceAccountKey.json: {str(e)}")
                cred = credentials.Certificate("serviceAccountKey.json")
                
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://research-58228-default-rtdb.asia-southeast1.firebasedatabase.app/'
            })
            print("Firebase initialized successfully")
        return firebase_admin.get_app()
    except Exception as e:
        st.error(f"Firebase initialization error: {str(e)}")
        st.info("Try adding your serviceAccountKey.json to the same directory as this app, or set up secrets in Streamlit Cloud.")
        return None

# --- Page Configuration ---
st.set_page_config(
    page_title="Document Viewer App",
    page_icon="🔍",
    layout="wide"
)

# --- Styling ---
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
        }
        .app-header {
            text-align: center;
            padding: 1.5rem 0;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 2rem;
        }
        .search-section {
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .document-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
        }
        .document-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .document-title {
            font-weight: bold;
            font-size: 1.1rem;
        }
        .document-meta {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #e0e0e0;
            font-size: 0.8rem;
            color: #666;
        }
    </style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if 'found_user' not in st.session_state:
    st.session_state.found_user = None
    
if 'searched_email' not in st.session_state:
    st.session_state.searched_email = ""

if 'view_pdf' not in st.session_state:
    st.session_state.view_pdf = {}

# --- App Header ---
st.markdown('<div class="app-header">', unsafe_allow_html=True)
st.title("Bio-Immigration Document Viewer 🔍")
st.markdown("Access user documents by email address")
st.markdown('</div>', unsafe_allow_html=True)

# --- Firebase Initialization ---
app = initialize_firebase()

if not app:
    st.warning("⚠️ Firebase connection issue. Please check your configuration and try again.")
    st.stop()

# Try to connect to database
try:
    db_ref = db.reference('/', app=app)
    db_ref.get()  # Test connection
except Exception as e:
    st.error(f"Failed to connect to Firebase database: {str(e)}")
    st.stop()

# --- Search Section ---
st.markdown("### Search User Documents")

with st.container():
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_email = st.text_input("Enter user email address")
    
    with col2:
        search_btn = st.button("Search")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Search Logic ---
if search_btn and search_email:
    with st.spinner("Searching..."):
        st.session_state.searched_email = search_email
        
        # Search for user with this email
        users_ref = db.reference('users', app=app)
        users = users_ref.get() or {}
        
        found_user_id = None
        found_user_data = None
        
        for user_id, user_data in users.items():
            if user_data.get('email') == search_email:
                found_user_id = user_id
                found_user_data = user_data
                st.session_state.found_user = {
                    'id': user_id,
                    'data': user_data
                }
                break
        
        if found_user_data:
            st.success(f"Found user: {search_email}")
            
            # Display documents if they exist
            if 'documents' in found_user_data and found_user_data['documents']:
                st.markdown("### User Documents")
                
                # Display each document
                for doc_id, doc in found_user_data['documents'].items():
                    if 'filename' not in doc or 'description' not in doc:
                        continue
                    
                    st.markdown(f'<div class="document-card">', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="document-header">', unsafe_allow_html=True)
                    st.markdown(f'<span class="document-title">📄 {doc["description"]}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown(
                        f'<div class="document-meta">Filename: {doc["filename"]} | '
                        f'Uploaded: {doc.get("upload_date", "Unknown")}</div>', 
                        unsafe_allow_html=True
                    )
                    
                    # Add view and download options
                    if 'file_data' in doc:
                        try:
                            # Decode the base64 data
                            pdf_bytes = base64.b64decode(doc['file_data'])
                            
                            col1, col2 = st.columns(2)
                            
                            # Download button
                            with col1:
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_bytes,
                                    file_name=doc['filename'],
                                    mime="application/pdf"
                                )
                            
                            # View button
                            with col2:
                                view_button = st.button("View PDF", key=f"view_{doc_id}")
                                if view_button:
                                    if doc_id in st.session_state.view_pdf:
                                        st.session_state.view_pdf[doc_id] = not st.session_state.view_pdf[doc_id]
                                    else:
                                        st.session_state.view_pdf[doc_id] = True
                            
                            # Display PDF if view button was clicked
                            if doc_id in st.session_state.view_pdf and st.session_state.view_pdf[doc_id]:
                                st.markdown("#### PDF Preview")
                                # Display PDF using iframe
                                base64_pdf = doc['file_data']
                                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                                st.markdown(pdf_display, unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.error(f"Error processing PDF: {str(e)}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info(f"User {search_email} has no uploaded documents.")
        else:
            st.error(f"No user found with email: {search_email}")

# --- Display previously searched user if exists in session state ---
elif 'found_user' in st.session_state and st.session_state.found_user:
    found_user_data = st.session_state.found_user['data']
    search_email = st.session_state.searched_email
    
    st.success(f"Found user: {search_email}")
    
    # Display documents if they exist
    if 'documents' in found_user_data and found_user_data['documents']:
        st.markdown("### User Documents")
        
        # Display each document
        for doc_id, doc in found_user_data['documents'].items():
            if 'filename' not in doc or 'description' not in doc:
                continue
            
            st.markdown(f'<div class="document-card">', unsafe_allow_html=True)
            
            st.markdown(f'<div class="document-header">', unsafe_allow_html=True)
            st.markdown(f'<span class="document-title">📄 {doc["description"]}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown(
                f'<div class="document-meta">Filename: {doc["filename"]} | '
                f'Uploaded: {doc.get("upload_date", "Unknown")}</div>', 
                unsafe_allow_html=True
            )
            
            # Add view and download options
            if 'file_data' in doc:
                try:
                    # Decode the base64 data
                    pdf_bytes = base64.b64decode(doc['file_data'])
                    
                    col1, col2 = st.columns(2)
                    
                    # Download button
                    with col1:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_bytes,
                            file_name=doc['filename'],
                            mime="application/pdf"
                        )
                    
                    # View button
                    with col2:
                        view_button = st.button("View PDF", key=f"view_{doc_id}")
                        if view_button:
                            if doc_id in st.session_state.view_pdf:
                                st.session_state.view_pdf[doc_id] = not st.session_state.view_pdf[doc_id]
                            else:
                                st.session_state.view_pdf[doc_id] = True
                    
                    # Display PDF if view button was clicked
                    if doc_id in st.session_state.view_pdf and st.session_state.view_pdf[doc_id]:
                        st.markdown("#### PDF Preview")
                        # Display PDF using iframe
                        base64_pdf = doc['file_data']
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info(f"User {search_email} has no uploaded documents.")

# --- Footer ---
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("Bio-Immigration Document Viewer | Admin Access Only")
st.markdown('</div>', unsafe_allow_html=True)
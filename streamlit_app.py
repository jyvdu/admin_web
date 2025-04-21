import streamlit as st
import base64
import os
import json
import time
from datetime import datetime
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
    page_title="Bio-Immigration Document Viewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
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
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        .search-section {
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .document-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .document-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .document-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .document-title {
            font-weight: bold;
            font-size: 1.1rem;
            color: #1E3A8A;
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
        .user-info {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .stButton button {
            width: 100%;
        }
        .pdf-viewer {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
        }
        .alert {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .alert-info {
            background-color: #e8f4fd;
            border-left: 5px solid #2196F3;
        }
        .alert-success {
            background-color: #e8f5e9;
            border-left: 5px solid #4CAF50;
        }
        .alert-warning {
            background-color: #fff8e1;
            border-left: 5px solid #FFC107;
        }
    </style>
""", unsafe_allow_html=True)

# --- Initialize session state variables ---
if 'found_user' not in st.session_state:
    st.session_state.found_user = None
    
if 'searched_email' not in st.session_state:
    st.session_state.searched_email = ""
    
if 'view_pdf' not in st.session_state:
    st.session_state.view_pdf = {}
    
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# --- App Header ---
st.markdown('<div class="app-header">', unsafe_allow_html=True)
st.title("Bio-Immigration Document Viewer 🔍")
st.markdown("Access and manage user documents securely")
st.markdown('</div>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("Admin Controls")
    st.markdown("---")
    
    # Refresh data button
    if st.button("🔄 Refresh Data"):
        st.session_state.last_refresh = time.time()
        st.session_state.found_user = None
        st.experimental_rerun()
    
    # Show last refresh time
    st.markdown(f"Last refreshed: {datetime.fromtimestamp(st.session_state.last_refresh).strftime('%H:%M:%S')}")
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    # Clear search results
    if st.button("🗑️ Clear Results"):
        st.session_state.found_user = None
        st.session_state.searched_email = ""
        st.session_state.view_pdf = {}
        st.experimental_rerun()
    
    st.markdown("---")
    st.info("This is an admin-only interface. All actions are logged for security purposes.")

# --- Firebase Initialization ---
app = initialize_firebase()

if not app:
    st.warning("⚠️ Firebase connection issue. Please check your configuration and try again.")
    
    # Provide troubleshooting tips
    with st.expander("Troubleshooting Tips"):
        st.markdown("""
        1. **Check your serviceAccountKey.json file:**
           - Make sure it exists in the same directory as your app
           - Verify it's valid and not expired
           
        2. **For Streamlit Cloud deployment:**
           - Add your Firebase credentials to Streamlit secrets
           - Format: `firebase = { "type": "service_account", ... }` (paste contents of serviceAccountKey.json)
           
        3. **Firebase permissions:**
           - Ensure the service account has appropriate read permissions
           
        4. **Try generating a new key:**
           - Go to Firebase console > Project settings > Service accounts
           - Generate a new private key
        """)
    st.stop()

# Try to connect to database
try:
    # Test the database connection
    db_ref = db.reference('/', app=app)
    # Try a simple read operation to verify connection
    db_ref.get()
    st.sidebar.success("✅ Connected to Firebase")
except Exception as e:
    st.error(f"Failed to connect to Firebase database: {str(e)}")
    st.stop()

# --- Search Section ---
st.markdown("### Search User Documents")

with st.container():
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_email = st.text_input("Enter user email address", value=st.session_state.searched_email)
    
    with col2:
        search_btn = st.button("🔍 Search")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Search Logic ---
if search_btn and search_email:
    with st.spinner("Searching for user..."):
        st.session_state.searched_email = search_email
        
        # Search for user with this email
        users_ref = db.reference('users', app=app)
        
        try:
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
                st.success(f"✅ Found user: {search_email}")
            else:
                st.error(f"❌ No user found with email: {search_email}")
                
                # Suggest similar emails as a fallback
                similar_emails = []
                for _, user_data in users.items():
                    email = user_data.get('email', '')
                    if email and search_email.split('@')[0] in email:
                        similar_emails.append(email)
                
                if similar_emails:
                    st.markdown('<div class="alert alert-info">', unsafe_allow_html=True)
                    st.markdown("Did you mean one of these emails?")
                    for email in similar_emails[:3]:  # Show up to 3 suggestions
                        if st.button(f"📧 {email}", key=f"suggest_{email}"):
                            st.session_state.searched_email = email
                            st.experimental_rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error retrieving user data: {str(e)}")
            st.session_state.found_user = None

# --- Display User Data ---
if 'found_user' in st.session_state and st.session_state.found_user:
    found_user_data = st.session_state.found_user['data']
    search_email = st.session_state.searched_email
    
    # Display user info (excluding password and document data)
    with st.expander("User Information", expanded=True):
        st.markdown('<div class="user-info">', unsafe_allow_html=True)
        
        # Create two columns for user info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Information")
            st.markdown(f"**Full Name:** {found_user_data.get('first_name', '')} {found_user_data.get('last_name', '')}")
            st.markdown(f"**Email:** {found_user_data.get('email', '')}")
            st.markdown(f"**Phone:** {found_user_data.get('phone', 'Not provided')}")
        
        with col2:
            st.markdown("#### Account Details")
            st.markdown(f"**User ID:** {st.session_state.found_user['id']}")
            st.markdown(f"**Account Created:** {found_user_data.get('created_at', 'Unknown')}")
            st.markdown(f"**Last Login:** {found_user_data.get('last_login', 'Unknown')}")
        
        # Additional user fields if available
        if any(key in found_user_data for key in ['address', 'city', 'state', 'country']):
            st.markdown("#### Address Information")
            address_parts = []
            if found_user_data.get('address'): address_parts.append(found_user_data.get('address'))
            if found_user_data.get('city'): address_parts.append(found_user_data.get('city'))
            if found_user_data.get('state'): address_parts.append(found_user_data.get('state'))
            if found_user_data.get('postal_code'): address_parts.append(found_user_data.get('postal_code'))
            if found_user_data.get('country'): address_parts.append(found_user_data.get('country'))
            
            if address_parts:
                st.markdown(f"**Address:** {', '.join(address_parts)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display documents if they exist
    if 'documents' in found_user_data and found_user_data['documents']:
        st.markdown("### User Documents")
        
        # Organize documents by category if possible
        documents = found_user_data['documents']
        doc_categories = {}
        
        for doc_id, doc in documents.items():
            if 'filename' not in doc or 'description' not in doc:
                continue
                
            category = doc.get('category', 'Uncategorized')
            if category not in doc_categories:
                doc_categories[category] = []
            
            doc_categories[category].append((doc_id, doc))
        
        # Display documents by category using tabs
        if len(doc_categories) > 1:
            tabs = st.tabs(list(doc_categories.keys()))
            
            for i, (category, docs) in enumerate(doc_categories.items()):
                with tabs[i]:
                    for doc_id, doc in docs:
                        display_document(doc_id, doc)
        else:
            # Just display all documents without tabs
            for doc_id, doc in documents.items():
                if 'filename' not in doc or 'description' not in doc:
                    continue
                display_document(doc_id, doc)
    else:
        st.markdown('<div class="alert alert-warning">', unsafe_allow_html=True)
        st.markdown(f"User {search_email} has no uploaded documents.")
        st.markdown('</div>', unsafe_allow_html=True)


# --- Document Display Function ---
def display_document(doc_id, doc):
    """Display a single document card with viewing options"""
    st.markdown(f'<div class="document-card">', unsafe_allow_html=True)
    
    st.markdown(f'<div class="document-header">', unsafe_allow_html=True)
    st.markdown(f'<span class="document-title">📄 {doc["description"]}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Document metadata
    upload_date = doc.get('upload_date', 'Unknown')
    file_size = "Unknown"
    if 'file_data' in doc:
        # Calculate approximate file size in KB
        try:
            size_bytes = len(base64.b64decode(doc['file_data']))
            file_size = f"{size_bytes/1024:.1f} KB"
        except:
            pass
    
    st.markdown(
        f'<div class="document-meta">Filename: {doc["filename"]} | '
        f'Size: {file_size} | '
        f'Uploaded: {upload_date}</div>', 
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
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=doc['filename'],
                    mime="application/pdf"
                )
            
            # View button
            with col2:
                view_button = st.button("👁️ View PDF", key=f"view_{doc_id}")
                if view_button:
                    if doc_id in st.session_state.view_pdf:
                        st.session_state.view_pdf[doc_id] = not st.session_state.view_pdf[doc_id]
                    else:
                        st.session_state.view_pdf[doc_id] = True
            
            # Display PDF if view button was clicked
            if doc_id in st.session_state.view_pdf and st.session_state.view_pdf[doc_id]:
                st.markdown('<div class="pdf-viewer">', unsafe_allow_html=True)
                st.markdown("#### PDF Preview")
                # Display PDF using iframe
                base64_pdf = doc['file_data']
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- Footer ---
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("Bio-Immigration Document Viewer | Admin Access Only")
st.markdown(f"Current session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown('</div>', unsafe_allow_html=True)
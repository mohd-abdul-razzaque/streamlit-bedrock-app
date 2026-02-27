import streamlit as st
import boto3
import hashlib
from datetime import datetime
import json
import subprocess
import os
import re
import uuid

# Load AWS credentials from Streamlit secrets or environment
def get_boto3_session():
    """Create boto3 session with credentials from secrets or environment"""
    try:
        # Try to get credentials from Streamlit secrets
        if 'AWS_ACCESS_KEY_ID' in st.secrets:
            session = boto3.Session(
                aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'],
                region_name=st.secrets.get('AWS_DEFAULT_REGION', 'ap-south-1')
            )
        else:
            # Fall back to environment variables or IAM role
            session = boto3.Session(region_name='ap-south-1')
        return session
    except Exception as e:
        st.error(f"AWS Configuration Error: {str(e)}")
        return None

# DynamoDB setup
try:
    session = get_boto3_session()
    if session:
        dynamodb = session.resource('dynamodb')
        users_table = dynamodb.Table('user_login_details')
        queries_table = dynamodb.Table('demo_agent_history')
    else:
        st.error("Failed to initialize AWS session")
        st.stop()
except Exception as e:
    st.error(f"DynamoDB Error: {str(e)}")
    st.stop()

# Bedrock AgentCore endpoint
AGENTCORE_ENDPOINT = "arn:aws:bedrock-agentcore:ap-south-1:423781074828:runtime/test1-HBDXfJ46Xa"
AGENTCORE_URL = "https://bedrock-agentcore.ap-south-1.amazonaws.com/runtime/invoke"

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def user_exists(email: str) -> bool:
    """Check if user exists in DynamoDB"""
    try:
        response = users_table.get_item(Key={'email': email})
        return 'Item' in response
    except Exception as e:
        st.error(f"Error checking user: {str(e)}")
        return False

def create_user(email: str, password: str, name: str) -> bool:
    """Create new user in DynamoDB"""
    try:
        users_table.put_item(
            Item={
                'email': email,
                'password': hash_password(password),
                'name': name,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False

def authenticate_user(email: str, password: str) -> dict:
    """Authenticate user and return user details"""
    try:
        response = users_table.get_item(Key={'email': email})
        if 'Item' not in response:
            return None
        
        user = response['Item']
        if verify_password(password, user['password']):
            return user
        return None
    except Exception as e:
        st.error(f"Error authenticating user: {str(e)}")
        return None

def invoke_agentcore(query: str) -> str:
    try:
        # Primary attempt with extended timeout
        result = subprocess.run(
            ["agentcore", "invoke", json.dumps({"prompt": query})],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(__file__)
        )
        output = (result.stdout + result.stderr).strip()

        if not output:
            return "No response from agent"

        # Clean box-drawing borders and extract meaningful lines
        def clean_line(s: str) -> str:
            s = s.strip()
            if not s:
                return ""
            # Remove leading/trailing box drawing chars and pipes
            s = re.sub(r'^[\s\|\u2500-\u257F]+', '', s)
            s = re.sub(r'[\s\|\u2500-\u257F]+$', '', s)
            return s.strip()

        lines = []
        for raw in output.split('\n'):
            cleaned = clean_line(raw)
            if not cleaned:
                continue
            # Skip known non-content headers/metadata
            skip_prefixes = (
                'Invoke information', 'Warning', '⚠️',
                'Session:', 'Request ID:', 'ARN:', 'Logs:', 'GenAI Dashboard:'
            )
            if cleaned.startswith(skip_prefixes):
                continue
            lines.append(cleaned)

        # Prefer explicit "Response:" content if present
        if lines:
            for i, line in enumerate(lines):
                if line.lower().startswith('response:'):
                    content = line.split(':', 1)[1].strip()
                    if content:
                        return content
                    # If the content is on the next line
                    if i + 1 < len(lines):
                        return lines[i + 1]
            # Otherwise, return the last meaningful line
            return lines[-1]
        return output
    except FileNotFoundError:
        return "AgentCore not installed"
    except subprocess.TimeoutExpired:
        # Single retry with a longer timeout
        try:
            retry = subprocess.run(
                ["agentcore", "invoke", json.dumps({"prompt": query})],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=os.path.dirname(__file__)
            )
            output = (retry.stdout + retry.stderr).strip()
            if not output:
                return "No response from agent"

            def clean_line_retry(s: str) -> str:
                s = s.strip()
                if not s:
                    return ""
                s = re.sub(r'^[\s\|\u2500-\u257F]+', '', s)
                s = re.sub(r'[\s\|\u2500-\u257F]+$', '', s)
                return s.strip()

            lines = []
            for raw in output.split('\n'):
                cleaned = clean_line_retry(raw)
                if not cleaned:
                    continue
                if cleaned.startswith(('Invoke information', 'Warning', '⚠️', 'Session:', 'Request ID:', 'ARN:', 'Logs:', 'GenAI Dashboard:')):
                    continue
                lines.append(cleaned)

            if lines:
                for i, line in enumerate(lines):
                    if line.lower().startswith('response:'):
                        content = line.split(':', 1)[1].strip()
                        if content:
                            return content
                        if i + 1 < len(lines):
                            return lines[i + 1]
                return lines[-1]
            return output
        except subprocess.TimeoutExpired:
            return "Agent timeout. Please verify the AgentCore container is running and responsive."
        except Exception as e:
            return f"Error after retry: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Page configuration
st.set_page_config(page_title="Agent Query System", layout="wide", initial_sidebar_state="expanded")

# Custom CSS styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #0066cc;
        --secondary-color: #00d4ff;
        --success-color: #00cc66;
        --danger-color: #ff3333;
    }
    
    /* Header styling */
    h1 {
        color: #0066cc;
        font-size: 2.5em;
        font-weight: 700;
        margin-bottom: 10px;
        background: linear-gradient(135deg, #0066cc 0%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #0066cc;
        font-size: 1.8em;
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        font-size: 16px;
    }
    
    .stTextArea textarea:focus {
        border-color: #0066cc;
        box-shadow: 0 0 10px rgba(0, 102, 204, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #0066cc 0%, #00d4ff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 102, 204, 0.3);
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 10px;
        font-size: 14px;
    }
    
    .stTextInput input:focus {
        border-color: #0066cc;
        box-shadow: 0 0 10px rgba(0, 102, 204, 0.3);
    }
    
    /* Response box styling */
    .response-box {
        background: linear-gradient(135deg, #f0f7ff 0%, #e6f2ff 100%);
        border-left: 5px solid #0066cc;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1);
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: #e6f9f0 !important;
        border-radius: 8px !important;
    }
    
    /* Error message styling */
    .stError {
        background-color: #ffe6e6 !important;
        border-radius: 8px !important;
    }
    
    /* Warning message styling */
    .stWarning {
        background-color: #fff8e6 !important;
        border-radius: 8px !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f7ff 0%, #e8f0ff 100%);
    }
    
    /* Radio button styling */
    .stRadio > label {
        font-weight: 600;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for processing
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Sidebar for authentication
with st.sidebar:
    st.title("Authentication")
    
    if not st.session_state.authenticated:
        auth_choice = st.radio("Choose action:", ["Login", "Sign Up"])
        
        if auth_choice == "Login":
            st.subheader("🔓 Login")
            st.markdown("---")
            login_email = st.text_input("📧 Email", key="login_email", placeholder="your@email.com")
            login_password = st.text_input("🔑 Password", type="password", key="login_password", placeholder="••••••••")
            
            st.markdown("---")
            if st.button("✨ Login", key="login_btn", use_container_width=True):
                user = authenticate_user(login_email, login_password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.session_id = f"streamlit-{user['email']}-{uuid.uuid4()}"
                    st.success(f"🎉 Welcome {user['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password")
        
        else:  # Sign Up
            st.subheader("📝 Create Account")
            st.markdown("---")
            signup_name = st.text_input("👤 Full Name", key="signup_name", placeholder="John Doe")
            signup_email = st.text_input("📧 Email", key="signup_email", placeholder="your@email.com")
            signup_password = st.text_input("🔑 Password", type="password", key="signup_password", placeholder="••••••••")
            signup_confirm = st.text_input("🔐 Confirm Password", type="password", key="signup_confirm", placeholder="••••••••")
            
            st.markdown("---")
            if st.button("✨ Create Account", key="signup_btn", use_container_width=True):
                if not signup_name or not signup_email or not signup_password:
                    st.error("❌ All fields are required")
                elif signup_password != signup_confirm:
                    st.error("❌ Passwords do not match")
                elif user_exists(signup_email):
                    st.error("❌ Email already registered")
                elif create_user(signup_email, signup_password, signup_name):
                    st.success("✅ Account created successfully! Please login.")
                    st.rerun()
                else:
                    st.error("❌ Error creating account")
    
    else:
        st.subheader(f"👤 {st.session_state.user['name']}")
        st.text(st.session_state.user['email'])
        
        if st.button("Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

# Main content
if st.session_state.authenticated:
    # Header with user info
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🤖 Agent Query System")
    with col2:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", key="logout_btn_top"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    
    st.divider()
    
    # Welcome message
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #e6f2ff 0%, #f0f7ff 100%); 
                padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 16px; color: #0066cc;"><strong>Welcome, {st.session_state.user['name']}!</strong></p>
        <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">Ask me anything about your data</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("💬 Ask a Question")
    user_query = st.text_area("Enter your question:", height=120, placeholder="e.g., How many customers are there?", disabled=st.session_state.is_processing)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        send_btn = st.button("🚀 Send Query", key="send_query_btn", use_container_width=True, disabled=st.session_state.is_processing)
    
    if send_btn:
        if user_query.strip():
            st.session_state.is_processing = True
    
    if st.session_state.is_processing:
        if user_query.strip():
            with st.spinner("🔄 Processing your query..."):
                response = invoke_agentcore(user_query)
                st.session_state.is_processing = False
                
                # Pretty format the response
                st.markdown("""
                <div class="response-box">
                    <h3 style="margin-top: 0; color: #0066cc;">✨ Response</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.success("✅ Response received!")
                st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 8px; 
                            border-left: 5px solid #00cc66; margin: 15px 0; 
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);">
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin: 0;">
                        {response}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Store in history
                try:
                    queries_table.put_item(
                        Item={
                            'query_id': f"{st.session_state.user['email']}-{datetime.utcnow().timestamp()}",
                            'user_email': st.session_state.user['email'],
                            'question': user_query,
                            'answer': response,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )
                except Exception as e:
                    st.warning(f"⚠️ Could not save to history: {str(e)}")
        else:
            st.warning("⚠️ Please enter a question before sending")
            st.session_state.is_processing = False

else:
    # Login/Signup page styling
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(135deg, #0066cc 0%, #00d4ff 100%); 
                      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                      background-clip: text; font-size: 3em; margin: 0;">
                🤖 Agent Query System
            </h1>
            <p style="font-size: 18px; color: #666; margin-top: 10px;">
                Intelligent data queries powered by AWS Bedrock
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <p style="font-size: 16px; color: #333; line-height: 1.6;">
                <strong>Get started by logging in or creating a new account</strong><br>
                <span style="color: #666; font-size: 14px;">Use the sidebar to access authentication</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

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

# AgentCore configuration is handled by local CLI and .bedrock_agentcore.yaml

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

        # Return complete output without filtering
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

            # Return complete output without filtering
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
  h1, h2 { color: #0066cc; }
  .stTextArea textarea, .stTextInput input { border-radius: 8px; }
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
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_btn"):
                user = authenticate_user(login_email, login_password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.session_id = f"streamlit-{user['email']}-{uuid.uuid4()}"
                    st.rerun()
                else:
                    st.error("Invalid email or password")
        else:
            signup_name = st.text_input("Full Name", key="signup_name")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            if st.button("Create Account", key="signup_btn"):
                if not signup_name or not signup_email or not signup_password:
                    st.error("All fields are required")
                elif signup_password != signup_confirm:
                    st.error("Passwords do not match")
                elif user_exists(signup_email):
                    st.error("Email already registered")
                elif create_user(signup_email, signup_password, signup_name):
                    st.success("Account created. Please login.")
                    st.rerun()
                else:
                    st.error("Error creating account")
    else:
        st.subheader(st.session_state.user['name'])
        st.text(st.session_state.user['email'])
        if st.button("Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

# Main content
if st.session_state.authenticated:
    st.title("🤖 Agent Query System")
    if st.button("🚪 Logout", key="logout_btn_top"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()
    
    st.divider()
    
    # Welcome message
    st.info(f"Welcome, {st.session_state.user['name']}! Ask me anything about your data.")
    
    st.subheader("💬 Ask a Question")
    user_query = st.text_area("Enter your question:", height=120, placeholder="e.g., How many customers are there?", disabled=st.session_state.is_processing)
    
    send_btn = st.button("🚀 Send Query", key="send_query_btn", disabled=st.session_state.is_processing)
    
    if send_btn:
        if user_query.strip():
            st.session_state.is_processing = True
    
    if st.session_state.is_processing:
        if user_query.strip():
            with st.spinner("🔄 Processing your query..."):
                response = invoke_agentcore(user_query)
                st.session_state.is_processing = False
                
                st.success("✅ Response received!")
                st.write(response)
                
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

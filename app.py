def setup_drive_folders(self) -> bool:
        """Create necessary folders in Google Drive with domain-based organization"""
        try:
            if not self.drive_service:
                self.add_log("❌ Drive service not initialized", 'error')
                return False
            
            self.add_log("📁 Setting up domain-based Drive folder structure", 'info')
            
            # Check if main folder already exists
            query = "name='VLSI Resume Scanner' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            
            if results.get('files'):
                parent_folder = results['files'][0]
                parent_folder_id = parent_folder['id']
                self.add_log(f"✅ Found existing parent folder: {parent_folder['name']}", 'success')
            else:
                # Create parent folder
                parent_metadata = {
                    'name': 'VLSI Resume Scanner',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                parent_folder = self.drive_service.files().create(body=parent_metadata, fields='id').execute()
                parent_folder_id = parent_folder.get('id')
                self.add_log("✅ Created parent folder: VLSI Resume Scanner", 'success')
            
            # Create/find main resumes folder
            resume_query = f"name='Resumes by Domain' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            resume_results = self.drive_service.files().list(q=resume_query, fields="files(id, name)").execute()
            
            if resume_results.get('files'):
                self.resume_folder_id = resume_results['files'][0]['id']
                self.add_log("✅ Found existing 'Resumes by Domain' folder", 'success')
            else:
                resume_metadata = {
                    'name': 'Resumes by Domain',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                resume_folder = self.drive_service.files().create(body=resume_metadata, fields='id').execute()
                self.resume_folder_id = resume_folder.get('id')
                self.add_log("✅ Created 'Resumes by Domain' folder", 'success')
            
            # Create domain-specific subfolders
            domain_descriptions = {
                'Physical Design': '🏗️ Place & Route, Floorplanning, STA, Power Analysis',
                'Design Verification': '🔍 UVM, SystemVerilog, Testbenches, Coverage',
                'DFT': '🧪 ATPG, BIST, Scan Chains, Test Compression',
                'RTL Design': '⚡ Verilog, SystemVerilog, Logic Design, Synthesis',
                'Analog Design': '📡 OpAmps, ADC/DAC, PLL, Mixed Signal',
                'FPGA': '🔧 Xilinx, Altera, Vivado, Quartus',
                'Silicon Validation': '🔬 Post-Silicon, ATE, Lab Validation',
                'Mixed Signal': '⚖️ High-Speed, SerDes, Signal Integrity',
                'General VLSI': '🎯 General VLSI/ASIC Experience',
                'Unknown Domain': '❓ Unclassified Technical Resumes'
            }
            
            for domain_name, description in domain_descriptions.items():
                folder_query = f"name='{domain_name}' and parents in '{self.resume_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                folder_results = self.drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
                
                if folder_results.get('files'):
                    folder_id = folder_results['files'][0]['id']
                    self.domain_folders[domain_name] = folder_id
                    self.add_log(f"✅ Found existing folder: {domain_name}", 'success')
                else:
                    folder_metadata = {
                        'name': domain_name,
                        'parents': [self.resume_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder',
                        'description': description
                    }
                    folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
                    folder_id = folder.get('id')
                    self.domain_folders[domain_name] = folder_id
                    self.add_log(f"✅ Created domain folder: {domain_name}", 'success')
                    
                    # Create experience-based subfolders within each domain
                    experience_levels = ['Fresher (0-2 years)', 'Mid-Level (2-5 years)', 'Senior (5-8 years)', 'Experienced (8+ years)']
                    for exp_level in experience_levels:
                        exp_metadata = {
                            'name': exp_level,
                            'parents': [folder_id],
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                        self.drive_service.files().create(body=exp_metadata, fields='id').execute()
                        self.add_log(f"✅ Created experience subfolder: {domain_name}/{exp_level}", 'info')
            
            # Create processed emails folder
            processed_query = f"name='Processed Emails' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            processed_results = self.drive_service.files().list(q=processed_query, fields="files(id, name)").execute()
            
            if processed_results.get('files'):
                self.processed_folder_id = processed_results['files'][0]['id']
                self.add_log("✅ Found existing Processed Emails folder", 'success')
            else:
                processed_metadata = {
                    'name': 'Processed Emails',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re
import base64
import time
import tempfile

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session

# Try to import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

# Try to import PDF processing
try:
    import PyPDF2
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    try:
        import pdfplumber
        PDF_PROCESSING_AVAILABLE = True
    except ImportError:
        PDF_PROCESSING_AVAILABLE = False

# Try to import DOC processing
try:
    import docx
    from docx import Document
    DOCX_PROCESSING_AVAILABLE = True
except ImportError:
    DOCX_PROCESSING_AVAILABLE = False

try:
    import python_docx2txt
    DOC_PROCESSING_AVAILABLE = True
except ImportError:
    DOC_PROCESSING_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vlsi-scanner-secret-key-2024')

# Configuration
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

# Enhanced logging
logging.basicConfig(level=logging.INFO)

class VLSIResumeScanner:
    def __init__(self):
        self.credentials = None
        self.gmail_service = None
        self.drive_service = None
        self.logs = []
        self.max_logs = 1000
        self.stats = {
            'total_emails': 0,
            'resumes_found': 0,
            'last_scan_time': None,
            'processing_errors': 0
        }
        self.resume_folder_id = None
        self.processed_folder_id = None
        self.high_score_folder_id = None
        self.medium_score_folder_id = None
        self.low_score_folder_id = None
        self.domain_folders = {
            'Physical Design': None,
            'Design Verification': None, 
            'DFT': None,
            'RTL Design': None,
            'Analog Design': None,
            'FPGA': None,
            'Silicon Validation': None,
            'Mixed Signal': None,
            'General VLSI': None,
            'Unknown Domain': None
        }
        # Experience level tracking
        self.experience_levels = ['Fresher (0-2 years)', 'Mid-Level (2-5 years)', 'Senior (5+ years)', 'Experienced (8+ years)']
        # User management
        self.current_user_email = None
        self.user_credentials = {}  # Store multiple user credentials
        
    def add_log(self, message: str, level: str = 'info'):
        """Add a log entry with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        # Keep only recent logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Also log to console
        if level == 'error':
            logging.error(f"[{timestamp}] {message}")
        elif level == 'warning':
            logging.warning(f"[{timestamp}] {message}")
        else:
            logging.info(f"[{timestamp}] {message}")

    def authenticate_google_apis(self, user_email: str = None) -> bool:
        """Authenticate with Google APIs using environment variables or credentials.json"""
        try:
            creds = None
            
            # Try to load existing token for specific user
            if user_email:
                token_file = f'token_{user_email.replace("@", "_").replace(".", "_")}.json'
                if os.path.exists(token_file):
                    try:
                        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
                        self.add_log(f"🔐 Loaded existing token for {user_email}", 'info')
                    except Exception as e:
                        self.add_log(f"⚠️ Could not load token for {user_email}: {e}", 'warning')
            else:
                # Try default token
                if os.path.exists('token.json'):
                    try:
                        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                        self.add_log("🔐 Loaded existing authentication token", 'info')
                    except Exception as e:
                        self.add_log(f"⚠️ Could not load existing token: {e}", 'warning')
            
            # If there are no (valid) credentials available
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        self.add_log("🔄 Refreshed expired token", 'info')
                    except Exception as e:
                        self.add_log(f"❌ Token refresh failed: {e}", 'error')
                        creds = None
                
                if not creds:
                    return self._run_oauth_flow(user_email)
            
            # Test the credentials and set current user
            self.credentials = creds
            if self._test_credentials():
                # Get user email from credentials
                if self.gmail_service:
                    try:
                        profile = self.gmail_service.users().getProfile(userId='me').execute()
                        self.current_user_email = profile.get('emailAddress')
                        self.user_credentials[self.current_user_email] = creds
                        self.add_log(f"✅ Authenticated as: {self.current_user_email}", 'success')
                    except Exception as e:
                        self.add_log(f"⚠️ Could not get user profile: {e}", 'warning')
                return True
            else:
                return False
            
        except Exception as e:
            self.add_log(f"❌ Authentication failed: {e}", 'error')
            return False

    def _run_oauth_flow(self, user_email: str = None) -> bool:
        """Run OAuth flow for new authentication"""
        try:
            # Try environment variables first
            client_id = os.environ.get('GOOGLE_CLIENT_ID')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            project_id = os.environ.get('GOOGLE_PROJECT_ID')
            
            credentials_dict = None
            
            if client_id and client_secret and project_id:
                self.add_log("📋 No credentials.json found, trying environment variables", 'info')
                credentials_dict = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
                self.add_log("✅ Created credentials from environment variables", 'success')
            elif os.path.exists('credentials.json'):
                with open('credentials.json', 'r') as f:
                    credentials_dict = json.load(f)
                self.add_log("✅ Found credentials.json file", 'info')
            else:
                self.add_log("❌ No credentials found. Set environment variables or upload credentials.json", 'error')
                return False
            
            # Check if it's a desktop application credentials
            if 'installed' in credentials_dict:
                self.add_log("✅ Found OAuth desktop credentials", 'success')
            elif 'web' in credentials_dict:
                self.add_log("⚠️ Web credentials found, converting to desktop format", 'warning')
                # Convert web to desktop format
                web_creds = credentials_dict['web']
                credentials_dict = {
                    "installed": {
                        "client_id": web_creds['client_id'],
                        "client_secret": web_creds['client_secret'],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
            else:
                self.add_log("❌ Invalid credentials format", 'error')
                return False
            
            self.add_log("🔐 Starting new OAuth flow", 'info')
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_config(
                credentials_dict, 
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            # Store OAuth flow for later use with manual code entry
            self._oauth_flow = flow
            
            # Generate auth URL with account selection
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='select_account',  # Forces account selection
                include_granted_scopes='true'
            )
            
            self.add_log("🌐 OAuth authorization required", 'info')
            self.add_log(f"📋 Authorization URL: {auth_url}", 'info')
            self.add_log("1️⃣ Copy the URL above and open in browser", 'info')
            self.add_log("2️⃣ Select your Gmail account or login with team member's account", 'info')
            self.add_log("3️⃣ Complete Google authorization", 'info')
            self.add_log("4️⃣ Copy the authorization code", 'info')
            self.add_log("5️⃣ Enter it in the form below", 'info')
            if user_email:
                self.add_log(f"👤 Authenticating for user: {user_email}", 'info')
            
            return False  # Indicates manual intervention needed
            
        except Exception as e:
            self.add_log(f"❌ OAuth flow failed: {e}", 'error')
            return False

    def _test_credentials(self) -> bool:
        """Test the credentials by making API calls"""
        try:
            self.add_log("🧪 Testing Gmail API access", 'info')
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            
            # Test Gmail access
            result = self.gmail_service.users().getProfile(userId='me').execute()
            email = result.get('emailAddress', 'Unknown')
            self.add_log(f"✅ Gmail access confirmed for: {email}", 'success')
            
            self.add_log("🧪 Testing Drive API access", 'info')
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            
            # Test Drive access
            about = self.drive_service.about().get(fields='user').execute()
            drive_email = about.get('user', {}).get('emailAddress', 'Unknown')
            self.add_log(f"✅ Drive access confirmed for: {drive_email}", 'success')
            
            # Save credentials for next run
            with open('token.json', 'w') as token:
                token.write(self.credentials.to_json())
            self.add_log("💾 Saved authentication token", 'success')
            
            return True
            
        except Exception as e:
            self.add_log(f"❌ Credential test failed: {e}", 'error')
            return False

    def setup_drive_folders(self) -> bool:
        """Create necessary folders in Google Drive with score-based organization"""
        try:
            if not self.drive_service:
                self.add_log("❌ Drive service not initialized", 'error')
                return False
            
            self.add_log("📁 Setting up enhanced Drive folder structure", 'info')
            
            # Check if main folder already exists
            query = "name='VLSI Resume Scanner' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            
            if results.get('files'):
                parent_folder = results['files'][0]
                parent_folder_id = parent_folder['id']
                self.add_log(f"✅ Found existing parent folder: {parent_folder['name']}", 'success')
            else:
                # Create parent folder
                parent_metadata = {
                    'name': 'VLSI Resume Scanner',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                parent_folder = self.drive_service.files().create(body=parent_metadata, fields='id').execute()
                parent_folder_id = parent_folder.get('id')
                self.add_log("✅ Created parent folder: VLSI Resume Scanner", 'success')
            
            # Create/find main resumes folder
            resume_query = f"name='Resumes' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            resume_results = self.drive_service.files().list(q=resume_query, fields="files(id, name)").execute()
            
            if resume_results.get('files'):
                self.resume_folder_id = resume_results['files'][0]['id']
                self.add_log("✅ Found existing Resumes folder", 'success')
            else:
                resume_metadata = {
                    'name': 'Resumes',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                resume_folder = self.drive_service.files().create(body=resume_metadata, fields='id').execute()
                self.resume_folder_id = resume_folder.get('id')
                self.add_log("✅ Created Resumes folder", 'success')
            
            # Create score-based subfolders
            score_folders = {
                'High Priority (Score 0.7+)': 'high_score_folder_id',
                'Medium Priority (Score 0.4-0.7)': 'medium_score_folder_id', 
                'Low Priority (Score 0.1-0.4)': 'low_score_folder_id'
            }
            
            for folder_name, attr_name in score_folders.items():
                folder_query = f"name='{folder_name}' and parents in '{self.resume_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                folder_results = self.drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
                
                if folder_results.get('files'):
                    folder_id = folder_results['files'][0]['id']
                    setattr(self, attr_name, folder_id)
                    self.add_log(f"✅ Found existing folder: {folder_name}", 'success')
                else:
                    folder_metadata = {
                        'name': folder_name,
                        'parents': [self.resume_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
                    folder_id = folder.get('id')
                    setattr(self, attr_name, folder_id)
                    self.add_log(f"✅ Created folder: {folder_name}", 'success')
            
            # Create processed emails folder
            processed_query = f"name='Processed Emails' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            processed_results = self.drive_service.files().list(q=processed_query, fields="files(id, name)").execute()
            
            if processed_results.get('files'):
                self.processed_folder_id = processed_results['files'][0]['id']
                self.add_log("✅ Found existing Processed Emails folder", 'success')
            else:
                processed_metadata = {
                    'name': 'Processed Emails',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                processed_folder = self.drive_service.files().create(body=processed_metadata, fields='id').execute()
                self.processed_folder_id = processed_folder.get('id')
                self.add_log("✅ Created Processed Emails folder", 'success')
            
            # Create summary document
            self._create_summary_document(parent_folder_id)
            
            return True
            
        except Exception as e:
            self.add_log(f"❌ Drive folder setup failed: {e}", 'error')
            return False

    def scan_emails(self, max_results: int = None) -> Dict[str, Any]:
        """Scan Gmail for resume attachments"""
        try:
            if not self.gmail_service:
                self.add_log("❌ Gmail service not initialized", 'error')
                return {'success': False, 'error': 'Gmail service not available'}
            
            self.add_log(f"🔍 Starting Gmail scan (max: {max_results or 'unlimited'})", 'info')
            
            # Search for emails with PDF or DOC attachments
            query = 'has:attachment (filename:pdf OR filename:doc OR filename:docx)'
            if max_results:
                query += f' newer_than:30d'  # Limit to last 30 days for quick scans
            
            messages = []
            page_token = None
            
            while True:
                result = self.gmail_service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(100, max_results or 100),
                    pageToken=page_token
                ).execute()
                
                messages.extend(result.get('messages', []))
                page_token = result.get('nextPageToken')
                
                if not page_token or (max_results and len(messages) >= max_results):
                    break
            
            if max_results:
                messages = messages[:max_results]
            
            self.add_log(f"📧 Found {len(messages)} emails with PDF/DOC attachments", 'info')
            
            resumes_found = 0
            processed_count = 0
            
            for i, message in enumerate(messages, 1):
                try:
                    self.add_log(f"📨 Processing email {i}/{len(messages)}", 'info')
                    result = self.process_email(message['id'])
                    
                    if result.get('has_resume'):
                        resumes_found += 1
                        
                    processed_count += 1
                    
                    # Add a small delay to avoid rate limiting
                    if i % 10 == 0:
                        time.sleep(1)
                        
                except Exception as e:
                    self.add_log(f"❌ Error processing email {i}: {e}", 'error')
                    self.stats['processing_errors'] += 1
                    continue
            
            # Update stats
            self.stats['total_emails'] = processed_count
            self.stats['resumes_found'] = resumes_found
            self.stats['last_scan_time'] = datetime.now().isoformat()
            
            self.add_log(f"✅ Scan completed: {processed_count} emails processed, {resumes_found} resumes found", 'success')
            
            return {
                'success': True,
                'processed': processed_count,
                'resumes_found': resumes_found,
                'stats': self.stats
            }
            
        except Exception as e:
            self.add_log(f"❌ Email scan failed: {e}", 'error')
            return {'success': False, 'error': str(e)}

    def process_email(self, message_id: str) -> Dict[str, Any]:
        """Process a single email for resume attachments"""
        try:
            # Get email details
            message = self.gmail_service.users().messages().get(userId='me', id=message_id).execute()
            
            # Extract email metadata
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Check for attachments (PDF, DOC, DOCX)
            attachments = []
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    filename = part.get('filename', '').lower()
                    if filename and (filename.endswith('.pdf') or filename.endswith('.doc') or filename.endswith('.docx')):
                        if 'body' in part and 'attachmentId' in part['body']:
                            attachments.append({
                                'filename': part['filename'],
                                'attachment_id': part['body']['attachmentId'],
                                'size': part['body'].get('size', 0),
                                'type': 'pdf' if filename.endswith('.pdf') else 'doc'
                            })
            
            has_resume = False
            processed_attachments = []
            
            for attachment in attachments:
                try:
                    # Download attachment
                    att = self.gmail_service.users().messages().attachments().get(
                        userId='me',
                        messageId=message_id,
                        id=attachment['attachment_id']
                    ).execute()
                    
                    data = base64.urlsafe_b64decode(att['data'])
                    
                    # Process based on file type
                    if attachment['type'] == 'pdf':
                        analysis_result = self.analyze_pdf_content(data, attachment['filename'])
                    else:  # DOC/DOCX
                        analysis_result = self.analyze_doc_content(data, attachment['filename'])
                    
                    if analysis_result and analysis_result.get('is_resume', False):
                        has_resume = True
                        
                        # Save to Drive with domain categorization
                        drive_file_id = self.save_to_drive(
                            data,
                            attachment['filename'],
                            {
                                'subject': subject,
                                'sender': sender,
                                'date': date_header,
                                'resume_score': analysis_result.get('resume_score', 0),
                                'domain': analysis_result.get('domain', 'Unknown Domain'),
                                'domain_score': analysis_result.get('domain_score', 0),
                                'analysis_result': analysis_result
                            }
                        )
                        
                        processed_attachments.append({
                            'filename': attachment['filename'],
                            'resume_score': analysis_result.get('resume_score', 0),
                            'domain': analysis_result.get('domain', 'Unknown Domain'),
                            'domain_score': analysis_result.get('domain_score', 0),
                            'drive_file_id': drive_file_id
                        })
                        
                        self.add_log(f"✅ Resume found: {attachment['filename']} | Domain: {analysis_result.get('domain', 'Unknown')} | Score: {analysis_result.get('resume_score', 0):.2f}", 'success')
                    
                except Exception as e:
                    self.add_log(f"❌ Error processing attachment {attachment['filename']}: {e}", 'error')
                    continue
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date_header,
                'has_resume': has_resume,
                'attachments': processed_attachments
            }
            
        except Exception as e:
            self.add_log(f"❌ Error processing email {message_id}: {e}", 'error')
            return {'message_id': message_id, 'error': str(e)}

    def analyze_doc_content(self, doc_data: bytes, filename: str) -> float:
        """Analyze DOC/DOCX content to determine if it's likely a resume"""
        try:
            text = ""
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.docx' if filename.lower().endswith('.docx') else '.doc', delete=False) as temp_file:
                temp_file.write(doc_data)
                temp_file_path = temp_file.name
            
            try:
                if filename.lower().endswith('.docx'):
                    # Process DOCX files
                    if DOCX_PROCESSING_AVAILABLE:
                        try:
                            doc = Document(temp_file_path)
                            for paragraph in doc.paragraphs:
                                text += paragraph.text + "\n"
                            self.add_log(f"📄 Extracted text from DOCX: {filename}", 'info')
                        except Exception as e:
                            self.add_log(f"❌ DOCX extraction failed for {filename}: {e}", 'error')
                            return 0.0
                    else:
                        self.add_log("⚠️ DOCX processing not available, install python-docx", 'warning')
                        return 0.5  # Default moderate score
                
                else:
                    # Process DOC files
                    if DOC_PROCESSING_AVAILABLE:
                        try:
                            import docx2txt
                            text = docx2txt.process(temp_file_path)
                            self.add_log(f"📄 Extracted text from DOC: {filename}", 'info')
                        except Exception as e:
                            self.add_log(f"❌ DOC extraction failed for {filename}: {e}", 'error')
                            return 0.0
                    else:
                        self.add_log("⚠️ DOC processing not available, install docx2txt", 'warning')
                        return 0.5  # Default moderate score
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
            if not text:
                self.add_log(f"⚠️ No text extracted from {filename}", 'warning')
                return 0.0
            
            # Use the same resume analysis logic as PDF
            return self._analyze_resume_text(text, filename)
            
        except Exception as e:
            self.add_log(f"❌ Error analyzing DOC {filename}: {e}", 'error')
            return {
                'resume_score': 0.0,
                'domain': 'Unknown Domain', 
                'domain_score': 0.0,
                'is_resume': False
            }
    def _analyze_resume_text(self, text: str, filename: str) -> float:
        """Analyze text content to determine if it's likely a resume"""
        try:
            
            # Convert to lowercase for analysis
            text_lower = text.lower()
            
            # Resume indicators with weights
            indicators = {
                # Strong indicators
                'experience': 2.0,
                'education': 2.0,
                'skills': 2.0,
                'resume': 3.0,
                'cv': 3.0,
                'curriculum vitae': 3.0,
                
                # Professional terms
                'work experience': 1.5,
                'professional experience': 1.5,
                'employment history': 1.5,
                'career objective': 1.5,
                'objective': 1.0,
                'summary': 1.0,
                
                # Education terms
                'bachelor': 1.5,
                'master': 1.5,
                'degree': 1.5,
                'university': 1.0,
                'college': 1.0,
                'graduated': 1.0,
                
                # VLSI/Tech specific
                'vlsi': 2.5,
                'asic': 2.0,
                'fpga': 2.0,
                'verilog': 2.0,
                'systemverilog': 2.0,
                'design verification': 2.0,
                'rtl': 2.0,
                'synthesis': 1.5,
                'physical design': 1.5,
                'dft': 1.5,
                
                # Contact information
                'email': 1.0,
                'phone': 1.0,
                'address': 1.0,
                'linkedin': 1.0,
                
                # Professional skills
                'programming': 1.0,
                'software': 1.0,
                'hardware': 1.0,
                'project': 1.0,
                'projects': 1.0,
            }
            
            score = 0.0
            matches = []
            
            for term, weight in indicators.items():
                if term in text_lower:
                    score += weight
                    matches.append(term)
            
            # Normalize score (rough normalization)
            max_possible_score = sum(indicators.values())
            normalized_score = min(score / max_possible_score * 2, 1.0)  # Cap at 1.0
            
            if matches:
                self.add_log(f"📄 Resume indicators found in {filename}: {', '.join(matches[:5])} (score: {normalized_score:.2f})", 'info')
            
            return normalized_score
            
        except Exception as e:
            self.add_log(f"❌ Error analyzing PDF {filename}: {e}", 'error')
            return 0.0

    def extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text from PDF data"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_data)
                temp_file_path = temp_file.name
            
            text = ""
            
            try:
                # Try pdfplumber first (better for complex layouts)
                import pdfplumber
                with pdfplumber.open(temp_file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
            except ImportError:
                # Fallback to PyPDF2
                try:
                    import PyPDF2
                    with open(temp_file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                            
                except ImportError:
                    self.add_log("❌ No PDF processing library available", 'error')
                    return ""
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return text.strip()
            
        except Exception as e:
            self.add_log(f"❌ PDF text extraction failed: {e}", 'error')
            return ""

    def _create_summary_document(self, parent_folder_id: str):
        """Create a summary document to track scanning results"""
        try:
            # Check if summary document already exists
            summary_query = f"name='Resume Scanning Summary' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.document' and trashed=false"
            summary_results = self.drive_service.files().list(q=summary_query, fields="files(id, name)").execute()
            
            if not summary_results.get('files'):
                # Create summary document
                summary_metadata = {
                    'name': 'Resume Scanning Summary',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.document'
                }
                summary_doc = self.drive_service.files().create(body=summary_metadata, fields='id').execute()
                self.add_log("✅ Created Resume Scanning Summary document", 'success')
            else:
                self.add_log("✅ Found existing Resume Scanning Summary document", 'success')
                
        except Exception as e:
            self.add_log(f"⚠️ Could not create summary document: {e}", 'warning')

    def save_to_drive(self, file_data: bytes, filename: str, metadata: Dict) -> Optional[str]:
        """Save file to Google Drive with domain and experience-based organization"""
        try:
            if not self.drive_service:
                self.add_log("❌ Drive service not available", 'error')
                return None
            
            # Get domain and experience info from analysis
            domain = metadata.get('domain', 'Unknown Domain')
            resume_score = metadata.get('resume_score', 0)
            experience_info = metadata.get('experience_info', {})
            experience_level = experience_info.get('level', 'Unknown')
            experience_years = experience_info.get('years', 0)
            
            # Get domain folder ID
            domain_folder_id = self.domain_folders.get(domain)
            if not domain_folder_id:
                self.add_log(f"⚠️ Domain folder not found for {domain}, using Unknown Domain", 'warning')
                domain_folder_id = self.domain_folders.get('Unknown Domain', self.resume_folder_id)
            
            # Find experience subfolder
            exp_folder_query = f"name='{experience_level}' and parents in '{domain_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            exp_folder_results = self.drive_service.files().list(q=exp_folder_query, fields="files(id, name)").execute()
            
            if exp_folder_results.get('files'):
                target_folder_id = exp_folder_results['files'][0]['id']
            else:
                # Create experience subfolder if it doesn't exist
                exp_metadata = {
                    'name': experience_level,
                    'parents': [domain_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                exp_folder_obj = self.drive_service.files().create(body=exp_metadata, fields='id').execute()
                target_folder_id = exp_folder_obj.get('id')
                self.add_log(f"✅ Created experience subfolder: {domain}/{experience_level}", 'info')
            
            # Create enhanced file metadata
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_extension = filename.split('.')[-1].lower()
            clean_filename = filename.replace(f'.{file_extension}', '')
            
            # Enhanced filename with domain and experience
            domain_abbrev = {
                'Physical Design': 'PD',
                'Design Verification': 'DV', 
                'DFT': 'DFT',
                'RTL Design': 'RTL',
                'Analog Design': 'ANA',
                'FPGA': 'FPGA',
                'Silicon Validation': 'SiVal',
                'Mixed Signal': 'MS',
                'General VLSI': 'VLSI',
                'Unknown Domain': 'UNK'
            }.get(domain, 'UNK')
            
            exp_abbrev = {
                'Fresher (0-2 years)': 'FR',
                'Mid-Level (2-5 years)': 'ML',
                'Senior (5-8 years)': 'SR',
                'Experienced (8+ years)': 'EX'
            }.get(experience_level, 'UK')
            
            new_filename = f"[{domain_abbrev}_{exp_abbrev}_{experience_years}Y] {timestamp}_{clean_filename}.{file_extension}"
            
            # Get domain-specific matches for description
            analysis_result = metadata.get('analysis_result', {})
            domain_matches = analysis_result.get('domain_matches', {}).get(domain, [])
            top_keywords = ', '.join(domain_matches[:5]) if domain_matches else 'No specific keywords found'
            experience_evidence = ', '.join(experience_info.get('evidence', ['Not specified'])[:3])
            
            file_metadata = {
                'name': new_filename,
                'parents': [target_folder_id],
                'description': f"""🎯 VLSI Resume Scanner Analysis Report

📧 Email Details:
   • From: {metadata.get('sender', 'Unknown')}
   • Subject: {metadata.get('subject', 'No subject')}
   • Date: {metadata.get('date', 'Unknown')}

🔍 Analysis Results:
   • Domain: {domain}
   • Domain Score: {metadata.get('domain_score', 0):.3f}
   • Resume Quality Score: {resume_score:.3f}
   • Top Keywords: {top_keywords}

💼 Experience Analysis:
   • Experience Level: {experience_level}
   • Estimated Years: {experience_years}
   • Evidence: {experience_evidence}

📁 Filing Information:
   • Auto-filed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
   • Location: {domain} > {experience_level}
   • File Type: {file_extension.upper()}

🤖 Generated by VLSI Resume Scanner v2.1
   Smart domain and experience-based candidate categorization."""
            }
            
            # Determine MIME type
            mime_types = {
                'pdf': 'application/pdf',
                'doc': 'application/msword', 
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            
            # Create a temporary file for upload
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                # Upload file
                from googleapiclient.http import MediaFileUpload
                media = MediaFileUpload(temp_file_path, mimetype=mime_type)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                file_id = file.get('id')
                self.add_log(f"💾 Saved to Drive: {domain}/{experience_level} - {filename} (Resume: {resume_score:.2f}, Exp: {experience_years}Y)", 'success')
                
                return file_id
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
        except Exception as e:
            self.add_log(f"❌ Drive save failed for {filename}: {e}", 'error')
            return None: bytes, filename: str, metadata: Dict) -> Optional[str]:
        """Save file to Google Drive with domain-based organization"""
        try:
            if not self.drive_service:
                self.add_log("❌ Drive service not available", 'error')
                return None
            
            # Get domain and scores from analysis
            domain = metadata.get('domain', 'Unknown Domain')
            resume_score = metadata.get('resume_score', 0)
            domain_score = metadata.get('domain_score', 0)
            
            # Get domain folder ID
            domain_folder_id = self.domain_folders.get(domain)
            if not domain_folder_id:
                self.add_log(f"⚠️ Domain folder not found for {domain}, using Unknown Domain", 'warning')
                domain_folder_id = self.domain_folders.get('Unknown Domain', self.resume_folder_id)
            
            # Determine priority subfolder based on resume score
            if resume_score >= 0.7:
                priority_folder = "High Priority (0.7+)"
                priority_label = "HIGH"
            elif resume_score >= 0.4:
                priority_folder = "Medium Priority (0.4-0.7)"
                priority_label = "MEDIUM"
            elif resume_score >= 0.1:
                priority_folder = "Low Priority (0.1-0.4)"
                priority_label = "LOW"
            else:
                priority_folder = None
                priority_label = "UNKNOWN"
            
            # Find or create priority subfolder
            target_folder_id = domain_folder_id
            if priority_folder:
                priority_query = f"name='{priority_folder}' and parents in '{domain_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                priority_results = self.drive_service.files().list(q=priority_query, fields="files(id, name)").execute()
                
                if priority_results.get('files'):
                    target_folder_id = priority_results['files'][0]['id']
                else:
                    # Create priority subfolder if it doesn't exist
                    priority_metadata = {
                        'name': priority_folder,
                        'parents': [domain_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    priority_folder_obj = self.drive_service.files().create(body=priority_metadata, fields='id').execute()
                    target_folder_id = priority_folder_obj.get('id')
                    self.add_log(f"✅ Created priority subfolder: {domain}/{priority_folder}", 'info')
            
            # Create enhanced file metadata
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_extension = filename.split('.')[-1].lower()
            clean_filename = filename.replace(f'.{file_extension}', '')
            
            # Enhanced filename with domain and priority
            domain_abbrev = {
                'Physical Design': 'PD',
                'Design Verification': 'DV', 
                'DFT': 'DFT',
                'RTL Design': 'RTL',
                'Analog Design': 'ANA',
                'FPGA': 'FPGA',
                'Silicon Validation': 'SiVal',
                'Mixed Signal': 'MS',
                'General VLSI': 'VLSI',
                'Unknown Domain': 'UNK'
            }.get(domain, 'UNK')
            
            new_filename = f"[{domain_abbrev}_{priority_label}] {timestamp}_{clean_filename}.{file_extension}"
            
            # Get domain-specific matches for description
            analysis_result = metadata.get('analysis_result', {})
            domain_matches = analysis_result.get('domain_matches', {}).get(domain, [])
            top_keywords = ', '.join(domain_matches[:5]) if domain_matches else 'No specific keywords found'
            
            file_metadata = {
                'name': new_filename,
                'parents': [target_folder_id],
                'description': f"""🎯 VLSI Resume Scanner Analysis Report

📧 Email Details:
   • From: {metadata.get('sender', 'Unknown')}
   • Subject: {metadata.get('subject', 'No subject')}
   • Date: {metadata.get('date', 'Unknown')}

🔍 Analysis Results:
   • Domain: {domain}
   • Domain Score: {domain_score:.3f}
   • Resume Score: {resume_score:.3f}
   • Priority: {priority_label}
   • Top Keywords: {top_keywords}

📁 Filing Information:
   • Auto-filed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
   • Location: {domain} > {priority_folder or 'Main Folder'}
   • File Type: {file_extension.upper()}

🤖 Generated by VLSI Resume Scanner v2.0
   Intelligent domain classification for efficient candidate screening."""
            }
            
            # Determine MIME type
            mime_types = {
                'pdf': 'application/pdf',
                'doc': 'application/msword', 
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            
            # Create a temporary file for upload
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                # Upload file
                from googleapiclient.http import MediaFileUpload
                media = MediaFileUpload(temp_file_path, mimetype=mime_type)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                file_id = file.get('id')
                self.add_log(f"💾 Saved to Drive: {domain}/{priority_folder or 'Main'} - {filename} (Resume: {resume_score:.2f}, Domain: {domain_score:.2f})", 'success')
                
                return file_id
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
        except Exception as e:
            self.add_log(f"❌ Drive save failed for {filename}: {e}", 'error')
            return None

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'google_apis_available': GOOGLE_APIS_AVAILABLE,
            'pdf_processing_available': PDF_PROCESSING_AVAILABLE,
            'docx_processing_available': DOCX_PROCESSING_AVAILABLE,
            'doc_processing_available': DOC_PROCESSING_AVAILABLE,
            'credentials_file_exists': os.path.exists('credentials.json'),
            'token_file_exists': os.path.exists('token.json'),
            'gmail_service_active': self.gmail_service is not None,
            'drive_service_active': self.drive_service is not None,
            'env_client_id': bool(os.environ.get('GOOGLE_CLIENT_ID')),
            'env_client_secret': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
            'env_project_id': bool(os.environ.get('GOOGLE_PROJECT_ID')),
            'client_id_preview': os.environ.get('GOOGLE_CLIENT_ID', '')[:20] + '...' if os.environ.get('GOOGLE_CLIENT_ID') else None,
            'project_id_value': os.environ.get('GOOGLE_PROJECT_ID'),
            'domain_folders_setup': all(folder_id is not None for folder_id in self.domain_folders.values()),
            'supported_formats': ['PDF', 'DOC', 'DOCX'],
            'supported_domains': list(self.domain_folders.keys()),
            'main_folders_ready': all([
                self.resume_folder_id,
                self.processed_folder_id
            ]),
            'stats': self.stats,
            'recent_logs': self.logs[-10:] if self.logs else []
        }

# Initialize scanner
scanner = VLSIResumeScanner()

def admin_required(f):
    """Decorator to require admin authentication"""
    def wrapper(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    """Main dashboard"""
    template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VLSI Resume Scanner</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; padding: 20px; color: #333;
            }
            .container { 
                max-width: 1200px; margin: 0 auto; 
                background: white; border-radius: 15px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
                overflow: hidden; 
            }
            .header {
                background: linear-gradient(135deg, #4a90e2 0%, #7b68ee 100%);
                color: white; padding: 30px; text-align: center;
            }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .header p { font-size: 1.1em; opacity: 0.9; }
            .content { padding: 30px; }
            .auth-section {
                background: #f8f9fa; border-radius: 10px; 
                padding: 20px; margin-bottom: 30px; text-align: center;
            }
            .controls { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px; margin-bottom: 30px; 
            }
            .controls button {
                padding: 15px 20px; border: none; border-radius: 8px;
                font-size: 1em; font-weight: bold; cursor: pointer;
                transition: all 0.3s ease; color: white;
            }
            .controls button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
            .controls button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
            .status-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px; margin-bottom: 30px;
            }
            .status-card {
                background: #f8f9fa; border-radius: 10px; padding: 20px;
                border-left: 4px solid #4a90e2;
            }
            .status-card h3 { color: #4a90e2; margin-bottom: 15px; }
            .status-item { 
                display: flex; justify-content: space-between; 
                margin-bottom: 8px; padding: 5px 0;
            }
            .status-value.success { color: #28a745; font-weight: bold; }
            .status-value.error { color: #dc3545; font-weight: bold; }
            .status-value.warning { color: #ffc107; font-weight: bold; }
            .logs-section {
                background: #1e1e1e; border-radius: 10px; padding: 20px;
                max-height: 400px; overflow-y: auto;
            }
            .log-entry {
                margin-bottom: 8px; font-family: 'Consolas', monospace; 
                font-size: 0.9em; padding: 5px; border-radius: 3px;
            }
            .log-entry.info { color: #61dafb; }
            .log-entry.success { color: #4ade80; }
            .log-entry.warning { color: #fbbf24; }
            .log-entry.error { color: #f87171; }
            .input-group {
                display: flex; gap: 10px; margin-bottom: 20px;
            }
            .input-group input {
                flex: 1; padding: 10px; border: 1px solid #ddd;
                border-radius: 5px; font-size: 1em;
            }
            .input-group button {
                padding: 10px 20px; background: #4a90e2; color: white;
                border: none; border-radius: 5px; cursor: pointer;
            }
            .stats-overview {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px; margin-bottom: 20px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 10px; text-align: center;
            }
            .stat-number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
            .stat-label { font-size: 0.9em; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 VLSI Resume Scanner</h1>
                <p>Automated Gmail Resume Detection & Analysis System</p>
            </div>
            
            <div class="content">
                <div id="auth-section" class="auth-section">
                    <div class="input-group">
                        <input type="password" id="admin-password" placeholder="Enter admin password">
                        <button onclick="authenticate()">🔐 Login</button>
                    </div>
                    <p>Enter admin password to access the scanner controls</p>
                </div>

                <div id="main-content" style="display: none;">
                    <div class="stats-overview">
                        <div class="stat-card">
                            <div class="stat-number" id="total-emails">-</div>
                            <div class="stat-label">Emails Scanned</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="resumes-found">-</div>
                            <div class="stat-label">Resumes Found</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="last-scan">Never</div>
                            <div class="stat-label">Last Scan</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="errors-count">-</div>
                            <div class="stat-label">Processing Errors</div>
                        </div>
                    </div>

                    <div class="controls">
                        <button onclick="setupGmail()" style="background: #17a2b8;">🔧 Setup Gmail Integration</button>
                        <button onclick="scanGmail()" style="background: #007bff;">📧 Full Gmail Scan</button>
                        <button onclick="quickScan()" style="background: #28a745;">⚡ Quick Scan (Last 50)</button>
                        <button onclick="testSystem()" style="background: #6c757d;">🔍 Test System</button>
                        <button onclick="showUserManager()" style="background: #fd7e14;">👥 Manage Team Access</button>
                    </div>

                    <div id="user-manager" style="display: none; background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #1976d2; margin: 0 0 15px 0;">👥 Team Member Authentication</h3>
                        <p style="color: #1976d2; margin: 0 0 15px 0;">
                            Team members can authenticate with their own Gmail accounts for personalized access.
                        </p>
                        <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 15px;">
                            <input type="email" id="user-email-input" placeholder="team-member@gmail.com" 
                                   style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <button onclick="authenticateUser()" style="padding: 10px 20px; background: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                Add Team Member
                            </button>
                        </div>
                        <div id="authenticated-users" style="background: white; border-radius: 4px; padding: 10px;">
                            <strong>Authenticated Users:</strong>
                            <div id="user-list">Loading...</div>
                        </div>
                        <button onclick="hideUserManager()" style="margin-top: 10px; padding: 8px 16px; background: #666; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Close
                        </button>
                    </div>

                    <div id="oauth-input" style="display: none; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #856404; margin: 0 0 15px 0;">🔑 OAuth Authorization Required</h3>
                        <p style="color: #856404; margin: 0 0 15px 0;">
                            Click the authorization URL in the logs above, complete Google authorization, then enter the code you receive:
                        </p>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="text" id="oauth-code-input" placeholder="4/1AUJR-x7uuwO5w4uilFkKhvWFzrd99..." 
                                   style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;">
                            <button onclick="submitOAuthCode()" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                Submit Code
                            </button>
                        </div>
                    </div>

                    <div class="status-grid">
                        <div class="status-card">
                            <h3>🔧 System Status</h3>
                            <div id="system-status">Loading...</div>
                        </div>
                        
                        <div class="status-card">
                            <h3>🔑 Authentication</h3>
                            <div id="auth-status">Loading...</div>
                        </div>
                        
                        <div class="status-card">
                            <h3>📊 Statistics</h3>
                            <div id="stats-details">Loading...</div>
                        </div>
                    </div>

                    <div class="status-card">
                        <h3>📋 Activity Logs</h3>
                        <div class="logs-section" id="logs-container">
                            <div class="log-entry info">System initialized. Waiting for commands...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        let isAdmin = false;
        let logCount = 0;

        function authenticate() {
            const password = document.getElementById('admin-password').value;
            
            fetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    isAdmin = true;
                    document.getElementById('auth-section').style.display = 'none';
                    document.getElementById('main-content').style.display = 'block';
                    loadSystemStatus();
                    startLogPolling();
                } else {
                    alert('Invalid password');
                }
            });
        }

        function setupGmail() {
            if (!isAdmin) return;
            addLogToDisplay('🔧 Starting Gmail API setup...', 'info');
            
            fetch('/api/setup-gmail', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        addLogToDisplay('✅ ' + data.message, 'success');
                        hideOAuthInput();
                    } else {
                        addLogToDisplay('❌ ' + data.message, 'error');
                        // Check if OAuth authorization is needed
                        if (data.message.includes('authentication failed')) {
                            setTimeout(showOAuthInput, 1000);
                        }
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ Setup failed: ' + e.message, 'error');
                });
        }

        function showOAuthInput() {
            document.getElementById('oauth-input').style.display = 'block';
        }

        function hideOAuthInput() {
            document.getElementById('oauth-input').style.display = 'none';
            document.getElementById('oauth-code-input').value = '';
        }

        function showUserManager() {
            document.getElementById('user-manager').style.display = 'block';
            loadAuthenticatedUsers();
        }

        function hideUserManager() {
            document.getElementById('user-manager').style.display = 'none';
        }

        function authenticateUser() {
            const email = document.getElementById('user-email-input').value.trim();
            
            if (!email) {
                addLogToDisplay('❌ Please enter a valid email address', 'error');
                return;
            }
            
            if (!email.includes('@')) {
                addLogToDisplay('❌ Please enter a valid email address', 'error');
                return;
            }
            
            addLogToDisplay(`🔐 Starting authentication for ${email}...`, 'info');
            
            fetch('/api/setup-gmail', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: email })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLogToDisplay('✅ ' + data.message, 'success');
                    hideOAuthInput();
                    hideUserManager();
                } else {
                    addLogToDisplay('❌ ' + data.message, 'error');
                    if (data.message.includes('authentication failed')) {
                        setTimeout(showOAuthInput, 1000);
                    }
                }
            })
            .catch(e => {
                addLogToDisplay('❌ Authentication failed: ' + e.message, 'error');
            });
        }

        function submitOAuthCode() {
            const code = document.getElementById('oauth-code-input').value.trim();
            
            if (!code) {
                addLogToDisplay('❌ Please enter the authorization code', 'error');
                return;
            }
            
            addLogToDisplay('🔄 Submitting authorization code...', 'info');
            
            fetch('/api/oauth-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLogToDisplay('✅ ' + data.message, 'success');
                    hideOAuthInput();
                } else {
                    addLogToDisplay('❌ ' + data.message, 'error');
                }
            })
            .catch(e => {
                addLogToDisplay('❌ Code submission failed: ' + e.message, 'error');
            });
        }

        function scanGmail() {
            if (!isAdmin) return;
            addLogToDisplay('📧 Starting full Gmail scan...', 'info');
            
            fetch('/api/scan-gmail', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        addLogToDisplay(`✅ Scan completed: ${data.processed} emails processed, ${data.resumes_found} resumes found`, 'success');
                        updateStats(data.stats);
                    } else {
                        addLogToDisplay('❌ ' + data.error, 'error');
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ Scan failed: ' + e.message, 'error');
                });
        }

        function quickScan() {
            if (!isAdmin) return;
            addLogToDisplay('⚡ Starting quick scan (last 50 emails)...', 'info');
            
            fetch('/api/quick-scan', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        addLogToDisplay(`✅ Quick scan completed: ${data.processed} emails processed, ${data.resumes_found} resumes found`, 'success');
                        updateStats(data.stats);
                    } else {
                        addLogToDisplay('❌ ' + data.error, 'error');
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ Quick scan failed: ' + e.message, 'error');
                });
        }

        function testSystem() {
            if (!isAdmin) return;
            addLogToDisplay('🔍 Running system test...', 'info');
            
            fetch('/api/test-system', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    addLogToDisplay('📊 System test results: ' + JSON.stringify(data, null, 2), 'info');
                    loadSystemStatus();
                })
                .catch(e => {
                    addLogToDisplay('❌ System test failed: ' + e.message, 'error');
                });
        }

        function loadSystemStatus() {
            if (!isAdmin) return;
            
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    updateSystemStatus(data);
                    updateStats(data.stats);
                })
                .catch(e => {
                    console.error('Failed to load status:', e);
                });
        }

        function updateSystemStatus(data) {
            const systemStatus = document.getElementById('system-status');
            const authStatus = document.getElementById('auth-status');
            const statsDetails = document.getElementById('stats-details');
            
            systemStatus.innerHTML = `
                <div class="status-item">
                    <span>Google APIs:</span>
                    <span class="status-value ${data.google_apis_available ? 'success' : 'error'}">
                        ${data.google_apis_available ? '✅ Available' : '❌ Missing'}
                    </span>
                </div>
                <div class="status-item">
                    <span>PDF Processing:</span>
                    <span class="status-value ${data.pdf_processing_available ? 'success' : 'error'}">
                        ${data.pdf_processing_available ? '✅ Available' : '❌ Missing'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Environment Variables:</span>
                    <span class="status-value ${data.env_client_id && data.env_client_secret ? 'success' : 'error'}">
                        ${data.env_client_id && data.env_client_secret ? '✅ Set' : '❌ Missing'}
                    </span>
                </div>
            `;
            
            authStatus.innerHTML = `
                <div class="status-item">
                    <span>Gmail Service:</span>
                    <span class="status-value ${data.gmail_service_active ? 'success' : 'error'}">
                        ${data.gmail_service_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Drive Service:</span>
                    <span class="status-value ${data.drive_service_active ? 'success' : 'error'}">
                        ${data.drive_service_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Token File:</span>
                    <span class="status-value ${data.token_file_exists ? 'success' : 'warning'}">
                        ${data.token_file_exists ? '✅ Exists' : '⚠️ Missing'}
                    </span>
                </div>
            `;
            
            if (data.client_id_preview) {
                authStatus.innerHTML += `
                    <div class="status-item">
                        <span>Client ID:</span>
                        <span class="status-value success">${data.client_id_preview}</span>
                    </div>
                `;
            }
        }

        function updateStats(stats) {
            if (stats) {
                document.getElementById('total-emails').textContent = stats.total_emails || 0;
                document.getElementById('resumes-found').textContent = stats.resumes_found || 0;
                document.getElementById('errors-count').textContent = stats.processing_errors || 0;
                
                if (stats.last_scan_time) {
                    const lastScan = new Date(stats.last_scan_time).toLocaleString();
                    document.getElementById('last-scan').textContent = lastScan;
                }
            }
        }

        function addLogToDisplay(message, level = 'info') {
            const logsContainer = document.getElementById('logs-container');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${level}`;
            logEntry.textContent = `[${timestamp}] ${message}`;
            
            logsContainer.appendChild(logEntry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
            
            // Keep only last 100 log entries
            while (logsContainer.children.length > 100) {
                logsContainer.removeChild(logsContainer.firstChild);
            }
        }

        function startLogPolling() {
            setInterval(() => {
                if (isAdmin) {
                    fetch('/api/logs')
                        .then(r => r.json())
                        .then(logs => {
                            const logsContainer = document.getElementById('logs-container');
                            
                            // Only show new logs
                            const newLogs = logs.slice(logCount);
                            newLogs.forEach(log => {
                                const logEntry = document.createElement('div');
                                logEntry.className = `log-entry ${log.level}`;
                                logEntry.textContent = `[${log.timestamp}] ${log.message}`;
                                logsContainer.appendChild(logEntry);
                            });
                            
                            logCount = logs.length;
                            logsContainer.scrollTop = logsContainer.scrollHeight;
                            
                            // Keep only last 100 log entries
                            while (logsContainer.children.length > 100) {
                                logsContainer.removeChild(logsContainer.firstChild);
                            }
                        })
                        .catch(e => console.error('Log polling failed:', e));
                }
            }, 2000);
        }
        </script>
    </body>
    </html>
    '''
    return render_template_string(template)

@app.route('/api/auth', methods=['POST'])
def api_auth():
    """Admin authentication"""
    data = request.get_json()
    password = data.get('password', '')
    
    if password == ADMIN_PASSWORD:
        session['admin_authenticated'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/api/setup-gmail', methods=['POST'])
@admin_required
def api_setup_gmail():
    """Setup Gmail API authentication"""
    try:
        data = request.get_json() or {}
        user_email = data.get('user_email')
        
        if user_email:
            scanner.add_log(f"Starting Gmail API setup for {user_email}...", 'info')
        else:
            scanner.add_log("Starting Gmail API setup...", 'info')
        
        # Check if Google APIs are available
        if not GOOGLE_APIS_AVAILABLE:
            error_msg = "Google API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-api-python-client"
            scanner.add_log(error_msg, 'error')
            return jsonify({'status': 'error', 'message': error_msg})
        
        # Check environment variables first
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        project_id = os.environ.get('GOOGLE_PROJECT_ID')
        
        scanner.add_log("🔍 Checking authentication method...", 'info')
        
        if client_id and client_secret and project_id:
            scanner.add_log("✅ Found environment variables for authentication", 'success')
            scanner.add_log(f"📋 Using Project ID: {project_id}", 'info')
            scanner.add_log(f"📋 Using Client ID: {client_id[:20]}...", 'info')
        elif os.path.exists('credentials.json'):
            scanner.add_log("✅ Found credentials.json file", 'info')
        else:
            error_msg = "No authentication method found. Set environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID) or upload credentials.json"
            scanner.add_log(error_msg, 'error')
            return jsonify({'status': 'error', 'message': error_msg})
        
        # Try to authenticate
        if scanner.authenticate_google_apis(user_email):
            if scanner.setup_drive_folders():
                scanner.add_log("✅ Gmail and Drive setup completed successfully", 'success')
                return jsonify({'status': 'success', 'message': 'Gmail integration setup completed'})
            else:
                error_msg = "Drive folder setup failed. Check permissions."
                scanner.add_log(error_msg, 'error')
                return jsonify({'status': 'error', 'message': error_msg})
        else:
            error_msg = "Gmail authentication failed. Check credentials and permissions."
            scanner.add_log(error_msg, 'error')
            return jsonify({'status': 'error', 'message': error_msg})
            
    except Exception as e:
        error_msg = f"Setup failed with exception: {str(e)}"
        scanner.add_log(error_msg, 'error')
        return jsonify({'status': 'error', 'message': error_msg})

@app.route('/api/users')
@admin_required
def api_users():
    """Get list of authenticated users"""
    try:
        users = list(scanner.user_credentials.keys())
        if scanner.current_user_email and scanner.current_user_email not in users:
            users.append(scanner.current_user_email)
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/oauth-code', methods=['POST'])
@admin_required
def api_oauth_code():
    """Submit OAuth authorization code"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'})
            
        auth_code = data.get('code', '').strip()
        
        if not auth_code:
            scanner.add_log("❌ No authorization code provided", 'error')
            return jsonify({'status': 'error', 'message': 'Authorization code is required'})
        
        scanner.add_log(f"📋 Received authorization code: {auth_code[:10]}...", 'info')
        
        # Check if we have an OAuth flow stored
        if not hasattr(scanner, '_oauth_flow') or not scanner._oauth_flow:
            scanner.add_log("❌ No OAuth flow found. Please restart Gmail setup.", 'error')
            return jsonify({'status': 'error', 'message': 'OAuth flow not found. Please click "Setup Gmail Integration" again.'})
        
        try:
            scanner.add_log("🔄 Exchanging authorization code for tokens...", 'info')
            
            # Exchange code for credentials using the stored OAuth flow
            scanner._oauth_flow.fetch_token(code=auth_code)
            creds = scanner._oauth_flow.credentials
            
            scanner.add_log("✅ Successfully obtained OAuth tokens", 'success')
            
            # Save credentials for next run with user-specific filename
            try:
                # Get user email from new credentials
                temp_gmail_service = build('gmail', 'v1', credentials=creds)
                profile = temp_gmail_service.users().getProfile(userId='me').execute()
                user_email = profile.get('emailAddress')
                
                # Save with user-specific filename
                if user_email:
                    token_filename = f'token_{user_email.replace("@", "_").replace(".", "_")}.json'
                    with open(token_filename, 'w') as token:
                        token.write(creds.to_json())
                    scanner.add_log(f"💾 Saved authentication token for {user_email}", 'success')
                    
                    # Also save as default token for backward compatibility
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                else:
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                    scanner.add_log("💾 Saved authentication token", 'success')
            except Exception as e:
                scanner.add_log(f"⚠️ Warning: Could not save token: {e}", 'warning')
            
            # Initialize Google services
            try:
                scanner.credentials = creds
                scanner.add_log("🔧 Initializing Gmail service", 'info')
                
                if GOOGLE_APIS_AVAILABLE:
                    scanner.gmail_service = build('gmail', 'v1', credentials=creds)
                    
                    scanner.add_log("🔧 Initializing Drive service", 'info')
                    scanner.drive_service = build('drive', 'v3', credentials=creds)
                    
                    # Test Gmail access
                    scanner.add_log("🧪 Testing Gmail access", 'info')
                    result = scanner.gmail_service.users().getProfile(userId='me').execute()
                    email = result.get('emailAddress', 'Unknown')
                    scanner.add_log(f"✅ Gmail access confirmed for: {email}", 'success')
                    
                    # Test Drive access
                    scanner.add_log("🧪 Testing Drive access", 'info')
                    about = scanner.drive_service.about().get(fields='user').execute()
                    drive_email = about.get('user', {}).get('emailAddress', 'Unknown')
                    scanner.add_log(f"✅ Drive access confirmed for: {drive_email}", 'success')
                    
                    # Setup Drive folders
                    if scanner.setup_drive_folders():
                        scanner.add_log("✅ OAuth authentication completed successfully", 'success')
                        scanner.add_log("✅ Gmail and Drive setup completed successfully", 'success')
                        
                        # Clean up OAuth flow
                        scanner._oauth_flow = None
                        
                        return jsonify({'status': 'success', 'message': 'OAuth authentication completed successfully'})
                    else:
                        scanner.add_log("❌ Drive folder setup failed", 'error')
                        return jsonify({'status': 'error', 'message': 'Drive folder setup failed'})
                else:
                    scanner.add_log("❌ Google APIs not available", 'error')
                    return jsonify({'status': 'error', 'message': 'Google APIs not available'})
                
            except Exception as e:
                scanner.add_log(f"❌ Service initialization failed: {e}", 'error')
                return jsonify({'status': 'error', 'message': f'Service initialization failed: {str(e)}'})
            
        except Exception as e:
            scanner.add_log(f"❌ Failed to exchange authorization code: {e}", 'error')
            
            # Provide helpful error messages
            error_str = str(e).lower()
            if "invalid_grant" in error_str:
                scanner.add_log("💡 The authorization code may have expired or been used already", 'warning')
                scanner.add_log("🔄 Please try the Gmail setup process again", 'info')
            elif "redirect_uri_mismatch" in error_str:
                scanner.add_log("💡 Redirect URI mismatch. Check OAuth client configuration", 'warning')
            
            return jsonify({'status': 'error', 'message': f'Failed to exchange authorization code: {str(e)}'})
        
    except Exception as e:
        scanner.add_log(f"❌ OAuth code submission failed: {e}", 'error')
        return jsonify({'status': 'error', 'message': f'OAuth submission failed: {str(e)}'})

@app.route('/api/scan-gmail', methods=['POST'])
@admin_required
def api_scan_gmail():
    """Full Gmail scan"""
    result = scanner.scan_emails()
    return jsonify(result)

@app.route('/api/quick-scan', methods=['POST'])
@admin_required
def api_quick_scan():
    """Quick Gmail scan (last 50 emails)"""
    result = scanner.scan_emails(max_results=50)
    return jsonify(result)

@app.route('/api/test-system', methods=['POST'])
@admin_required
def api_test_system():
    """Test system components"""
    status = scanner.get_system_status()
    scanner.add_log("System test results: " + json.dumps(status, indent=2), 'info')
    return jsonify(status)

@app.route('/api/status')
@admin_required
def api_status():
    """Get system status"""
    return jsonify(scanner.get_system_status())

@app.route('/api/logs')
@admin_required
def api_logs():
    """Get recent logs"""
    return jsonify(scanner.logs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

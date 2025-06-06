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

    def authenticate_google_apis(self) -> bool:
        """Authenticate with Google APIs using environment variables or credentials.json"""
        try:
            creds = None
            
            # Try to load existing token
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
                    return self._run_oauth_flow()
            
            # Test the credentials
            self.credentials = creds
            return self._test_credentials()
            
        except Exception as e:
            self.add_log(f"❌ Authentication failed: {e}", 'error')
            return False

    def _run_oauth_flow(self) -> bool:
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
            
            # Generate auth URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='consent',
                include_granted_scopes='true'
            )
            
            self.add_log("🌐 OAuth authorization required", 'info')
            self.add_log(f"📋 Authorization URL: {auth_url}", 'info')
            self.add_log("1️⃣ Copy the URL above and open in browser", 'info')
            self.add_log("2️⃣ Complete Google authorization", 'info')
            self.add_log("3️⃣ Copy the authorization code", 'info')
            self.add_log("4️⃣ Enter it in the form below", 'info')
            
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
        """Create necessary folders in Google Drive"""
        try:
            if not self.drive_service:
                self.add_log("❌ Drive service not initialized", 'error')
                return False
            
            self.add_log("📁 Setting up Drive folders", 'info')
            
            # Check if folders already exist
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
            
            # Create/find resumes subfolder
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
                self.add_log("✅ Created Resumes subfolder", 'success')
            
            # Create/find processed emails subfolder
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
                self.add_log("✅ Created Processed Emails subfolder", 'success')
            
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
            
            # Search for emails with PDF attachments
            query = 'has:attachment filename:pdf'
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
            
            self.add_log(f"📧 Found {len(messages)} emails with PDF attachments", 'info')
            
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
            
            # Check for attachments
            attachments = []
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part.get('filename') and part.get('filename').lower().endswith('.pdf'):
                        if 'body' in part and 'attachmentId' in part['body']:
                            attachments.append({
                                'filename': part['filename'],
                                'attachment_id': part['body']['attachmentId'],
                                'size': part['body'].get('size', 0)
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
                    
                    # Process PDF
                    resume_score = self.analyze_pdf_content(data, attachment['filename'])
                    
                    if resume_score and resume_score > 0.3:  # Threshold for considering it a resume
                        has_resume = True
                        
                        # Save to Drive
                        drive_file_id = self.save_to_drive(
                            data,
                            attachment['filename'],
                            {
                                'subject': subject,
                                'sender': sender,
                                'date': date_header,
                                'score': resume_score
                            }
                        )
                        
                        processed_attachments.append({
                            'filename': attachment['filename'],
                            'score': resume_score,
                            'drive_file_id': drive_file_id
                        })
                        
                        self.add_log(f"✅ Resume found: {attachment['filename']} (score: {resume_score:.2f})", 'success')
                    
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

    def analyze_pdf_content(self, pdf_data: bytes, filename: str) -> float:
        """Analyze PDF content to determine if it's likely a resume"""
        try:
            if not PDF_PROCESSING_AVAILABLE:
                self.add_log("⚠️ PDF processing not available, assuming it's a resume", 'warning')
                return 0.5  # Default moderate score
            
            text = self.extract_text_from_pdf(pdf_data)
            if not text:
                return 0.0
            
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

    def save_to_drive(self, file_data: bytes, filename: str, metadata: Dict) -> Optional[str]:
        """Save file to Google Drive with metadata"""
        try:
            if not self.drive_service or not self.resume_folder_id:
                self.add_log("❌ Drive service or folder not available", 'error')
                return None
            
            # Create file metadata
            file_metadata = {
                'name': f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
                'parents': [self.resume_folder_id],
                'description': f"Resume from: {metadata.get('sender', 'Unknown')}\nSubject: {metadata.get('subject', 'No subject')}\nScore: {metadata.get('score', 'Unknown')}"
            }
            
            # Create a temporary file for upload
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                # Upload file
                from googleapiclient.http import MediaFileUpload
                media = MediaFileUpload(temp_file_path, mimetype='application/pdf')
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                file_id = file.get('id')
                self.add_log(f"💾 Saved to Drive: {filename} (ID: {file_id})", 'success')
                
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
            'credentials_file_exists': os.path.exists('credentials.json'),
            'token_file_exists': os.path.exists('token.json'),
            'gmail_service_active': self.gmail_service is not None,
            'drive_service_active': self.drive_service is not None,
            'env_client_id': bool(os.environ.get('GOOGLE_CLIENT_ID')),
            'env_client_secret': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
            'env_project_id': bool(os.environ.get('GOOGLE_PROJECT_ID')),
            'client_id_preview': os.environ.get('GOOGLE_CLIENT_ID', '')[:20] + '...' if os.environ.get('GOOGLE_CLIENT_ID') else None,
            'project_id_value': os.environ.get('GOOGLE_PROJECT_ID'),
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
        if scanner.authenticate_google_apis():
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
            
            # Save credentials for next run
            try:
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

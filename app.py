#!/usr/bin/env python3
"""
VLSI Resume Analytics Dashboard - Real Gmail Integration
Scans Gmail for resumes and categorizes them to Google Drive
"""

import os
import json
import hashlib
import time
import threading
import base64
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, session, redirect, url_for, render_template_string
from functools import wraps

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    import google.auth
    from google.oauth2.credentials import Credentials
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    print("Google API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-api-python-client")

# PDF/Word processing imports
try:
    import PyPDF2
    import docx
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False
    print("PDF/Word processing libraries not installed. Install with: pip install PyPDF2 python-docx")

# Configuration
PORT = int(os.environ.get('PORT', 8080))
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'vlsi2025')
SECRET_KEY = os.environ.get('SECRET_KEY', 'vlsi-team-secret-2025')

# Google API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

app = Flask(__name__)
app.secret_key = SECRET_KEY

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

class VLSIGmailScanner:
    def __init__(self):
        self.gmail_service = None
        self.drive_service = None
        self.main_folder_id = None
        self.domain_folder_ids = {}
        self.is_running = False
        self.scan_status = "System ready - Click 'Setup Gmail' to start"
        self.logs = []
        self.next_scan_time = datetime.now() + timedelta(hours=2)
        self.credentials = None
        
        # VLSI Domain Keywords for categorization
        self.domain_keywords = {
            'RTL_Design': [
                'rtl', 'verilog', 'vhdl', 'systemverilog', 'digital design', 'logic design',
                'synthesis', 'fpga', 'asic', 'soc', 'microarchitecture', 'cpu design',
                'quartus', 'vivado', 'synopsys design compiler', 'hdl'
            ],
            'Design_Verification': [
                'verification', 'testbench', 'uvm', 'ovm', 'coverage', 'assertion',
                'formal verification', 'simulation', 'questa', 'vcs', 'ncsim',
                'xcelium', 'constrained random', 'functional coverage', 'dv engineer'
            ],
            'DFT_Design_for_Test': [
                'dft', 'design for test', 'scan', 'atpg', 'bist', 'boundary scan',
                'test pattern', 'manufacturing test', 'tetramax', 'fastscan',
                'dft compiler', 'test insertion'
            ],
            'STA_Timing_Analysis': [
                'sta', 'static timing analysis', 'timing analysis', 'timing closure',
                'primetime', 'setup time', 'hold time', 'clock domain crossing',
                'timing constraints', 'sdf', 'liberty', 'delay calculation'
            ],
            'Physical_Design': [
                'physical design', 'place and route', 'layout', 'floorplan',
                'routing', 'innovus', 'encounter', 'icc2', 'fusion compiler',
                'calibre', 'physical verification', 'drc', 'lvs', 'antenna'
            ],
            'Power_Verification': [
                'power analysis', 'low power', 'upf', 'cpf', 'power optimization',
                'ir drop', 'power grid', 'em analysis', 'power intent', 'voltus',
                'power verification', 'dynamic power', 'static power'
            ],
            'Analog_Design': [
                'analog design', 'mixed signal', 'ams', 'spice', 'layout',
                'adc', 'dac', 'pll', 'rf design', 'cadence virtuoso',
                'hspice', 'spectre', 'circuit design'
            ]
        }
        
        # Initialize data
        self.processed_resumes = {}
        self.stats = self.initialize_stats()
        
        # Start auto-scanner if credentials exist
        if os.path.exists('credentials.json'):
            self.add_log("Found credentials.json - Ready for Gmail setup", 'info')
        else:
            self.add_log("No credentials.json found - Upload your Google credentials", 'warning')
    
    def add_log(self, message, level='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'level': level
        }
        self.logs.append(log_entry)
        
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        
        print(f"[{timestamp}] {level.upper()}: {message}")
    
    def initialize_stats(self):
        return {
            'total_processed': 0,
            'total_duplicates': 0,
            'total_high_priority': 0,
            'today_processed': 0,
            'success_rate': 0.0,
            'avg_processing_time': 0.0,
            'total_scans_today': 0,
            'domain_stats': {domain.replace('_', ' '): 0 for domain in self.domain_keywords.keys()},
            'experience_stats': {
                'Fresher (0-1 Years)': 0,
                'Junior (2-3 Years)': 0,
                'Mid (4-6 Years)': 0,
                'Senior (7-10 Years)': 0,
                'Expert (10+ Years)': 0
            },
            'priority_distribution': {'High Priority': 0, 'Medium Priority': 0, 'Low Priority': 0},
            'recent_activity': []
        }
    
    def create_credentials_from_env(self):
        """Create credentials from environment variables (secure approach)"""
        try:
            # Get credentials from environment variables
            client_id = os.environ.get('GOOGLE_CLIENT_ID')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            project_id = os.environ.get('GOOGLE_PROJECT_ID')
            
            if not all([client_id, client_secret, project_id]):
                missing = []
                if not client_id: missing.append('GOOGLE_CLIENT_ID')
                if not client_secret: missing.append('GOOGLE_CLIENT_SECRET')
                if not project_id: missing.append('GOOGLE_PROJECT_ID')
                
                self.add_log(f"❌ Missing environment variables: {', '.join(missing)}", 'error')
                self.add_log("📋 Set these in Railway environment variables:", 'info')
                self.add_log("   GOOGLE_CLIENT_ID = your-client-id.apps.googleusercontent.com", 'info')
                self.add_log("   GOOGLE_CLIENT_SECRET = GOCSPX-your-secret", 'info')
                self.add_log("   GOOGLE_PROJECT_ID = your-project-id", 'info')
                return False
            
            # Create credentials dictionary
            creds_data = {
                "installed": {
                    "client_id": client_id,
                    "project_id": project_id,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": client_secret,
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            # Create temporary credentials file
            with open('temp_credentials.json', 'w') as f:
                json.dump(creds_data, f)
            
            self.add_log("✅ Created credentials from environment variables", 'success')
            return True
            
        except Exception as e:
            self.add_log(f"❌ Error creating credentials from env: {e}", 'error')
            return False

    def authenticate_google_apis(self):
        """Authenticate with Google APIs with detailed error logging"""
        if not GOOGLE_APIS_AVAILABLE:
            self.add_log("Google API libraries not installed", 'error')
            return False
        
        try:
            # First try to create credentials from environment variables
            if not os.path.exists('credentials.json'):
                self.add_log("📋 No credentials.json found, trying environment variables", 'info')
                if not self.create_credentials_from_env():
                    return False
                credentials_file = 'temp_credentials.json'
            else:
                credentials_file = 'credentials.json'
                self.add_log("✅ Found credentials.json file", 'info')
            
            # Try to read and validate credentials
            try:
                with open(credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    
                # Check if it's the right type of credentials
                if 'installed' in creds_data:
                    self.add_log("✅ Found OAuth desktop credentials", 'info')
                elif 'web' in creds_data:
                    self.add_log("✅ Found OAuth web credentials", 'info')
                elif 'type' in creds_data and creds_data['type'] == 'service_account':
                    self.add_log("✅ Found service account credentials", 'info')
                    return self.authenticate_service_account()
                else:
                    self.add_log("❌ Invalid credentials format", 'error')
                    return False
                    
            except json.JSONDecodeError as e:
                self.add_log(f"❌ Credentials file is not valid JSON: {e}", 'error')
                return False
            except Exception as e:
                self.add_log(f"❌ Error reading credentials file: {e}", 'error')
                return False
            
            creds = None
            
            # Load existing token
            if os.path.exists('token.json'):
                try:
                    self.add_log("🔍 Loading existing token.json", 'info')
                    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                    
                    if creds.valid:
                        self.add_log("✅ Existing token is valid", 'success')
                    else:
                        self.add_log("⚠️ Existing token needs refresh", 'warning')
                        
                except Exception as e:
                    self.add_log(f"⚠️ Error loading token.json: {e}", 'warning')
                    # Remove corrupted token file
                    try:
                        os.remove('token.json')
                        self.add_log("🗑️ Removed corrupted token.json", 'info')
                    except:
                        pass
                    creds = None
            
            # If no valid credentials, need manual setup
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        self.add_log("🔄 Attempting to refresh expired token", 'info')
                        creds.refresh(Request())
                        self.add_log("✅ Successfully refreshed token", 'success')
                    except Exception as e:
                        self.add_log(f"❌ Failed to refresh token: {e}", 'error')
                        creds = None
                
                if not creds:
                    self.add_log("🔐 Starting new OAuth flow", 'info')
                    
                    try:
                        # Create OAuth flow
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # For manual code entry
                        
                        # Generate authorization URL
                        auth_url, _ = flow.authorization_url(
                            access_type='offline',
                            prompt='consent',
                            include_granted_scopes='true'
                        )
                        
                        self.add_log("🌐 OAuth authorization required", 'warning')
                        self.add_log(f"📋 Authorization URL: {auth_url}", 'info')
                        self.add_log("1️⃣ Copy the URL above and open in browser", 'info')
                        self.add_log("2️⃣ Complete Google authorization", 'info')
                        self.add_log("3️⃣ Copy the authorization code", 'info')
                        self.add_log("4️⃣ Enter it in the form below", 'info')
                        
                        # Store the flow for later use
                        self._oauth_flow = flow
                        self.scan_status = "⏳ Waiting for OAuth authorization - Check logs for URL"
                        
                        return False  # Will complete setup when user provides auth code
                        
                    except Exception as e:
                        self.add_log(f"❌ OAuth flow setup failed: {e}", 'error')
                        self.add_log(f"🔍 Error details: {type(e).__name__}", 'error')
                        return False
                
                # Save credentials for next run
                if creds and creds.valid:
                    try:
                        with open('token.json', 'w') as token:
                            token.write(creds.to_json())
                        self.add_log("💾 Saved authentication token", 'success')
                    except Exception as e:
                        self.add_log(f"⚠️ Warning: Could not save token: {e}", 'warning')
            
            # Test the credentials by initializing services
            try:
                self.credentials = creds
                self.add_log("🔧 Initializing Gmail service", 'info')
                self.gmail_service = build('gmail', 'v1', credentials=creds)
                
                self.add_log("🔧 Initializing Drive service", 'info')
                self.drive_service = build('drive', 'v3', credentials=creds)
                
                # Test Gmail access
                self.add_log("🧪 Testing Gmail access", 'info')
                result = self.gmail_service.users().getProfile(userId='me').execute()
                email = result.get('emailAddress', 'Unknown')
                self.add_log(f"✅ Gmail access confirmed for: {email}", 'success')
                
                # Test Drive access
                self.add_log("🧪 Testing Drive access", 'info')
                about = self.drive_service.about().get(fields='user').execute()
                drive_email = about.get('user', {}).get('emailAddress', 'Unknown')
                self.add_log(f"✅ Drive access confirmed for: {drive_email}", 'success')
                
                # Clean up temporary file
                if os.path.exists('temp_credentials.json'):
                    os.remove('temp_credentials.json')
                
                return True
                
            except Exception as e:
                self.add_log(f"❌ Service initialization failed: {e}", 'error')
                self.add_log(f"🔍 Error type: {type(e).__name__}", 'error')
                
                # Check for common permission issues
                if "insufficient permissions" in str(e).lower():
                    self.add_log("💡 This may be a permission issue. Ensure you've enabled Gmail and Drive APIs", 'warning')
                elif "quota" in str(e).lower():
                    self.add_log("💡 API quota exceeded. Check your Google Cloud Console quotas", 'warning')
                elif "credentials" in str(e).lower():
                    self.add_log("💡 Credentials issue. Try regenerating your OAuth credentials", 'warning')
                
                return False
            
        except Exception as e:
            self.add_log(f"❌ Authentication failed with exception: {str(e)}", 'error')
            self.add_log(f"🔍 Exception type: {type(e).__name__}", 'error')
            
            # Provide helpful troubleshooting info
            self.add_log("🛠️ Troubleshooting steps:", 'info')
            self.add_log("1. Set environment variables in Railway", 'info')
            self.add_log("2. Check Gmail API and Drive API are enabled", 'info')
            self.add_log("3. Ensure OAuth consent screen is configured", 'info')
            
            return False
    
    def authenticate_service_account(self):
        """Alternative authentication using service account (better for cloud)"""
        try:
            from google.oauth2 import service_account
            
            self.add_log("🔧 Using service account authentication", 'info')
            
            creds = service_account.Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES)
            
            # For service accounts, we need to enable domain-wide delegation
            # and impersonate a user account
            self.add_log("⚠️ Service account requires domain-wide delegation setup", 'warning')
            self.add_log("📋 See: https://developers.google.com/identity/protocols/oauth2/service-account", 'info')
            
            return False  # Service account setup is more complex
            
        except Exception as e:
            self.add_log(f"❌ Service account authentication failed: {e}", 'error')
            return False
    
    def setup_drive_folders(self):
        """Create organized folder structure in Google Drive"""
        try:
            # Create main VLSI Resumes folder
            main_folder_metadata = {
                'name': 'VLSI_Resume_Analytics',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            main_folder = self.drive_service.files().create(body=main_folder_metadata).execute()
            self.main_folder_id = main_folder.get('id')
            
            # Create domain-specific subfolders
            for domain in self.domain_keywords.keys():
                folder_metadata = {
                    'name': domain,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.main_folder_id]
                }
                folder = self.drive_service.files().create(body=folder_metadata).execute()
                self.domain_folder_ids[domain] = folder.get('id')
            
            self.add_log(f"✅ Created Google Drive folder structure with {len(self.domain_keywords)} domain folders", 'success')
            return True
            
        except Exception as e:
            self.add_log(f"❌ Failed to create Drive folders: {str(e)}", 'error')
            return False
    
    def scan_gmail_for_resumes(self, scan_type="incremental"):
        """Scan Gmail for resume attachments"""
        if not self.gmail_service:
            self.add_log("Gmail service not authenticated", 'error')
            return
        
        try:
            self.is_running = True
            self.scan_status = f"Scanning Gmail for resume attachments..."
            self.add_log(f"🔍 Starting {scan_type} Gmail scan", 'info')
            
            # Search query for emails with resume attachments
            search_queries = [
                'has:attachment (resume OR cv OR "curriculum vitae") filetype:pdf',
                'has:attachment (resume OR cv) filetype:doc',
                'has:attachment (resume OR cv) filetype:docx',
                'subject:(application OR resume OR cv OR "job application")',
                'has:attachment vlsi OR verification OR rtl OR dft OR "physical design"'
            ]
            
            processed_count = 0
            new_resumes = 0
            
            for query in search_queries:
                try:
                    # Limit results for incremental scan
                    max_results = 10 if scan_type == "incremental" else 50
                    
                    result = self.gmail_service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=max_results
                    ).execute()
                    
                    messages = result.get('messages', [])
                    self.add_log(f"📧 Found {len(messages)} emails matching query: {query[:50]}...", 'info')
                    
                    for message in messages:
                        try:
                            processed = self.process_email_message(message['id'])
                            if processed:
                                new_resumes += 1
                            processed_count += 1
                            
                            # Add small delay to avoid API limits
                            time.sleep(0.1)
                            
                        except Exception as e:
                            self.add_log(f"⚠️ Error processing message: {str(e)}", 'warning')
                            continue
                    
                except Exception as e:
                    self.add_log(f"⚠️ Error with search query: {str(e)}", 'warning')
                    continue
            
            # Update statistics
            self.stats['total_processed'] += new_resumes
            self.stats['today_processed'] += new_resumes
            self.stats['total_scans_today'] += 1
            
            self.scan_status = f"✅ Scan completed: {new_resumes} new resumes found and categorized"
            self.add_log(f"🎉 Gmail scan completed - {new_resumes} new resumes processed from {processed_count} emails", 'success')
            
        except Exception as e:
            self.scan_status = f"❌ Scan failed: {str(e)}"
            self.add_log(f"❌ Gmail scan failed: {str(e)}", 'error')
        finally:
            self.is_running = False
    
    def process_email_message(self, message_id):
        """Process individual email message for resume attachments"""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract sender and subject
            headers = message['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            
            # Process attachments
            return self.process_email_attachments(message, sender, subject)
            
        except Exception as e:
            self.add_log(f"Error processing message {message_id}: {str(e)}", 'error')
            return False
    
    def process_email_attachments(self, message, sender, subject):
        """Extract and process resume attachments"""
        processed_any = False
        
        def process_parts(parts, sender, subject):
            nonlocal processed_any
            for part in parts:
                if part.get('parts'):
                    process_parts(part['parts'], sender, subject)
                elif part.get('body', {}).get('attachmentId'):
                    filename = part.get('filename', 'unknown')
                    
                    # Check if it's a resume file
                    if self.is_resume_file(filename, subject):
                        try:
                            # Download attachment
                            attachment = self.gmail_service.users().messages().attachments().get(
                                userId='me',
                                messageId=message['id'],
                                id=part['body']['attachmentId']
                            ).execute()
                            
                            file_data = base64.urlsafe_b64decode(attachment['data'])
                            
                            # Process the resume
                            if self.process_resume_file(file_data, filename, sender, subject):
                                processed_any = True
                                
                        except Exception as e:
                            self.add_log(f"Error processing attachment {filename}: {str(e)}", 'error')
        
        # Process message parts
        payload = message.get('payload', {})
        if payload.get('parts'):
            process_parts(payload['parts'], sender, subject)
        
        return processed_any
    
    def is_resume_file(self, filename, subject):
        """Check if file is likely a resume"""
        resume_keywords = ['resume', 'cv', 'curriculum', 'vitae']
        file_extensions = ['.pdf', '.doc', '.docx']
        
        filename_lower = filename.lower()
        subject_lower = subject.lower()
        
        # Check filename and extension
        has_resume_keyword = any(keyword in filename_lower or keyword in subject_lower for keyword in resume_keywords)
        has_valid_extension = any(filename_lower.endswith(ext) for ext in file_extensions)
        
        return has_resume_keyword and has_valid_extension
    
    def process_resume_file(self, file_data, filename, sender, subject):
        """Process resume file and categorize by VLSI domain"""
        try:
            # Generate unique fingerprint
            fingerprint = hashlib.md5(file_data).hexdigest()
            
            # Check for duplicates
            if fingerprint in self.processed_resumes:
                self.add_log(f"⚠️ Duplicate resume detected: {filename}", 'warning')
                self.stats['total_duplicates'] += 1
                return False
            
            # Extract text content
            text_content = self.extract_text_from_file(file_data, filename)
            if not text_content:
                self.add_log(f"⚠️ Could not extract text from {filename}", 'warning')
                return False
            
            # Analyze VLSI domain and experience
            domain = self.categorize_vlsi_domain(text_content)
            experience_level = self.extract_experience_level(text_content)
            confidence = self.calculate_confidence_score(text_content, domain)
            priority = self.determine_priority(experience_level, confidence)
            
            # Save to appropriate Google Drive folder
            drive_file_id = self.save_to_drive_folder(file_data, filename, domain, sender)
            
            # Store processed resume data
            resume_data = {
                'fingerprint': fingerprint,
                'filename': filename,
                'sender': sender,
                'subject': subject,
                'domain': domain,
                'experience_level': experience_level,
                'confidence_score': confidence,
                'priority': priority,
                'drive_file_id': drive_file_id,
                'processed_date': datetime.now().isoformat(),
                'file_size': len(file_data)
            }
            
            self.processed_resumes[fingerprint] = resume_data
            
            # Update statistics
            self.stats['domain_stats'][domain.replace('_', ' ')] += 1
            self.stats['experience_stats'][experience_level] += 1
            self.stats['priority_distribution'][f'{priority} Priority'] += 1
            
            # Add to recent activity
            self.stats['recent_activity'].insert(0, {
                'sender': sender.split('<')[0].strip() if '<' in sender else sender,
                'filename': filename,
                'domain': domain.replace('_', ' '),
                'experience': experience_level,
                'confidence': confidence,
                'priority': priority,
                'date': datetime.now().isoformat()
            })
            
            # Keep only last 20 activities
            self.stats['recent_activity'] = self.stats['recent_activity'][:20]
            
            self.add_log(f"✅ Processed: {filename} → {domain} ({confidence:.1f}% confidence)", 'success')
            return True
            
        except Exception as e:
            self.add_log(f"❌ Error processing resume {filename}: {str(e)}", 'error')
            return False
    
    def extract_text_from_file(self, file_data, filename):
        """Extract text content from PDF or Word file"""
        if not PDF_PROCESSING_AVAILABLE:
            return "PDF processing not available"
        
        try:
            if filename.lower().endswith('.pdf'):
                # Extract from PDF
                import io
                pdf_file = io.BytesIO(file_data)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
                
            elif filename.lower().endswith(('.doc', '.docx')):
                # Extract from Word document
                import io
                doc_file = io.BytesIO(file_data)
                doc = docx.Document(doc_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
        except Exception as e:
            self.add_log(f"Text extraction error for {filename}: {str(e)}", 'error')
        
        return ""
    
    def categorize_vlsi_domain(self, text):
        """Categorize resume into VLSI domain based on keywords"""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            domain_scores[domain] = score
        
        # Return domain with highest score, or RTL_Design as default
        best_domain = max(domain_scores, key=domain_scores.get)
        return best_domain if domain_scores[best_domain] > 0 else 'RTL_Design'
    
    def extract_experience_level(self, text):
        """Extract experience level from resume text"""
        text_lower = text.lower()
        
        # Look for experience patterns
        experience_patterns = [
            (r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', lambda m: int(m.group(1))),
            (r'experience\s*(?:of\s*)?(\d+)\+?\s*years?', lambda m: int(m.group(1))),
            (r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)', lambda m: int(m.group(1)))
        ]
        
        years = 0
        for pattern, extractor in experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                years = max(years, max(int(match) for match in matches))
        
        # Categorize by years
        if years == 0:
            return 'Fresher (0-1 Years)'
        elif years <= 3:
            return 'Junior (2-3 Years)'
        elif years <= 6:
            return 'Mid (4-6 Years)'
        elif years <= 10:
            return 'Senior (7-10 Years)'
        else:
            return 'Expert (10+ Years)'
    
    def calculate_confidence_score(self, text, domain):
        """Calculate confidence score for domain classification"""
        text_lower = text.lower()
        keywords = self.domain_keywords.get(domain, [])
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        # Calculate confidence as percentage
        max_possible = len(keywords)
        confidence = min((matches / max_possible) * 100, 95) if max_possible > 0 else 50
        
        return max(confidence, 30)  # Minimum 30% confidence
    
    def determine_priority(self, experience_level, confidence):
        """Determine candidate priority"""
        if confidence >= 80 and 'Senior' in experience_level or 'Expert' in experience_level:
            return 'High'
        elif confidence >= 60 and 'Mid' in experience_level:
            return 'Medium'
        else:
            return 'Low'
    
    def save_to_drive_folder(self, file_data, filename, domain, sender):
        """Save resume file to appropriate Google Drive folder"""
        try:
            # Ensure folders exist
            if not self.domain_folder_ids:
                self.setup_drive_folders()
            
            folder_id = self.domain_folder_ids.get(domain, self.main_folder_id)
            
            # Create unique filename with sender info
            sender_name = sender.split('<')[0].strip().replace(' ', '_') if '<' in sender else 'Unknown'
            unique_filename = f"{sender_name}_{filename}"
            
            # Upload file
            import io
            media = MediaIoBaseUpload(io.BytesIO(file_data), 
                                    mimetype='application/octet-stream')
            
            file_metadata = {
                'name': unique_filename,
                'parents': [folder_id]
            }
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            self.add_log(f"Error saving to Drive: {str(e)}", 'error')
            return None
    
    def get_dashboard_data(self):
        """Get dashboard data"""
        return {
            **self.stats,
            'system_status': 'SCANNING' if self.is_running else ('READY' if self.gmail_service else 'SETUP REQUIRED'),
            'scan_status': self.scan_status,
            'logs': self.logs[-25:],
            'next_scan_time': self.next_scan_time.isoformat(),
            'google_authenticated': bool(self.gmail_service),
            'drive_folders_created': bool(self.domain_folder_ids),
            'credentials_available': os.path.exists('credentials.json')
        }

# Initialize scanner
scanner = VLSIGmailScanner()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['role'] = 'admin'
            session['username'] = username
            scanner.add_log(f"Admin login: {username}", 'info')
            return redirect(url_for('dashboard'))
        elif username and password:
            session['logged_in'] = True
            session['role'] = 'viewer'
            session['username'] = username
            scanner.add_log(f"Viewer login: {username}", 'info')
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid credentials")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    scanner.add_log(f"User logout: {username}", 'info')
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def dashboard():
    role = session.get('role', 'viewer')
    username = session.get('username', 'User')
    return render_template_string(DASHBOARD_TEMPLATE, role=role, username=username)

@app.route('/api/stats')
@require_auth
def api_stats():
    return jsonify(scanner.get_dashboard_data())

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
                        
                        # Clean up temporary file
                        if os.path.exists('temp_credentials.json'):
                            os.remove('temp_credentials.json')
                        
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

@app.route('/api/scan/full', methods=['POST'])
@admin_required
def api_full_scan():
    """Start full Gmail scan"""
    if not scanner.gmail_service:
        return jsonify({'status': 'error', 'message': 'Gmail not authenticated. Run setup first.'})
    
    threading.Thread(target=scanner.scan_gmail_for_resumes, args=("full",), daemon=True).start()
    scanner.add_log("Full Gmail scan initiated by admin", 'info')
    return jsonify({'status': 'Full Gmail scan started'})

@app.route('/api/scan/incremental', methods=['POST'])
@admin_required
def api_incremental_scan():
    """Start incremental Gmail scan"""
    if not scanner.gmail_service:
        return jsonify({'status': 'error', 'message': 'Gmail not authenticated. Run setup first.'})
    
    threading.Thread(target=scanner.scan_gmail_for_resumes, args=("incremental",), daemon=True).start()
    scanner.add_log("Quick Gmail scan initiated by admin", 'info')
    return jsonify({'status': 'Quick Gmail scan started'})

@app.route('/api/oauth-code', methods=['POST'])
@admin_required
def api_oauth_code():
    """Handle OAuth authorization code manually"""
    try:
        data = request.get_json()
        auth_code = data.get('code', '').strip()
        
        if not auth_code:
            return jsonify({'status': 'error', 'message': 'Authorization code is required'})
        
        if not hasattr(scanner, '_oauth_flow'):
            return jsonify({'status': 'error', 'message': 'OAuth flow not initialized. Run setup first.'})
        
        scanner.add_log(f"Processing OAuth authorization code...", 'info')
        
        # Exchange code for credentials
        scanner._oauth_flow.fetch_token(code=auth_code)
        creds = scanner._oauth_flow.credentials
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        # Initialize services
        scanner.credentials = creds
        scanner.gmail_service = build('gmail', 'v1', credentials=creds)
        scanner.drive_service = build('drive', 'v3', credentials=creds)
        
        scanner.add_log("✅ OAuth authentication completed successfully", 'success')
        
        # Clean up
        delattr(scanner, '_oauth_flow')
        
        # Setup drive folders
        if scanner.setup_drive_folders():
            return jsonify({'status': 'success', 'message': 'OAuth authentication and Drive setup completed'})
        else:
            return jsonify({'status': 'partial', 'message': 'OAuth completed but Drive setup failed'})
            
    except Exception as e:
        error_msg = f"OAuth code processing failed: {str(e)}"
        scanner.add_log(error_msg, 'error')
        return jsonify({'status': 'error', 'message': error_msg})

@app.route('/api/test-system', methods=['POST'])
@admin_required
def api_test_system():
    """Test system requirements"""
    status = {
        'google_apis_available': GOOGLE_APIS_AVAILABLE,
        'pdf_processing_available': PDF_PROCESSING_AVAILABLE,
        'credentials_file_exists': os.path.exists('credentials.json'),
        'token_file_exists': os.path.exists('token.json'),
        'gmail_service_active': bool(scanner.gmail_service),
        'drive_service_active': bool(scanner.drive_service),
        # Check environment variables
        'env_client_id': bool(os.environ.get('GOOGLE_CLIENT_ID')),
        'env_client_secret': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
        'env_project_id': bool(os.environ.get('GOOGLE_PROJECT_ID')),
        'client_id_preview': os.environ.get('GOOGLE_CLIENT_ID', '')[:20] + '...' if os.environ.get('GOOGLE_CLIENT_ID') else 'Not set',
        'project_id_value': os.environ.get('GOOGLE_PROJECT_ID', 'Not set')
    }
    
    scanner.add_log(f"System test results: {status}", 'info')
    
    # Log environment variable status
    if status['env_client_id'] and status['env_client_secret'] and status['env_project_id']:
        scanner.add_log("✅ All environment variables are set", 'success')
    else:
        scanner.add_log("❌ Missing environment variables", 'error')
        if not status['env_client_id']:
            scanner.add_log("❌ GOOGLE_CLIENT_ID not set", 'error')
        if not status['env_client_secret']:
            scanner.add_log("❌ GOOGLE_CLIENT_SECRET not set", 'error')
        if not status['env_project_id']:
            scanner.add_log("❌ GOOGLE_PROJECT_ID not set", 'error')
    
    return jsonify({'status': 'success', 'system_status': status})

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'gmail_authenticated': bool(scanner.gmail_service),
        'drive_authenticated': bool(scanner.drive_service)
    })

# Templates (keeping them concise for space)
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>VLSI Gmail Scanner - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
        .container { background: rgba(255,255,255,0.95); border-radius: 20px; padding: 40px; max-width: 400px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        h1 { background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; }
        input { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        input:focus { outline: none; border-color: #667eea; }
        .btn { width: 100%; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 15px; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .error { color: #f44336; text-align: center; margin-bottom: 20px; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 VLSI Gmail Scanner</h1>
        <div class="info">
            <strong>Real Gmail Integration</strong><br>
            Scans your Gmail for resumes and categorizes them automatically to Google Drive folders
        </div>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Username:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>VLSI Gmail Scanner Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; color: #333; }
        .header { background: rgba(255,255,255,0.95); padding: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header h1 { background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        
        .setup-banner { background: linear-gradient(135deg, #ff6b6b, #feca57); color: white; padding: 20px; border-radius: 15px; margin-bottom: 25px; text-align: center; }
        .setup-banner.ready { background: linear-gradient(135deg, #5f27cd, #00d2d3); }
        
        .status-bar { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 25px; }
        .stat-card { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; text-align: center; transition: transform 0.3s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; font-size: 0.9rem; }
        
        .controls { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 25px; margin-bottom: 25px; }
        .btn-group { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }
        .btn { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; margin: 5px; transition: all 0.3s; }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .btn.setup { background: linear-gradient(135deg, #5f27cd, #00d2d3); }
        .btn.danger { background: linear-gradient(135deg, #ff6b6b, #feca57); }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 25px; }
        .card { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 25px; }
        .chart-container { height: 300px; margin: 15px 0; }
        .logs { background: #1a1a1a; color: #0f0; border-radius: 10px; padding: 15px; height: 300px; overflow-y: auto; font-family: monospace; font-size: 0.85rem; }
        .activity-item { padding: 12px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .priority-badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
        .priority-badge.high { background: #ffebee; color: #c62828; }
        .priority-badge.medium { background: #fff3e0; color: #ef6c00; }
        .priority-badge.low { background: #e8f5e8; color: #2e7d32; }
        .logout-btn { background: #f44336; color: white; padding: 8px 16px; border: none; border-radius: 20px; text-decoration: none; }
        
        .drive-folders { background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0; }
        .folder-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #eee; }
        
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } .header { flex-direction: column; gap: 15px; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>📧 VLSI Gmail Scanner</h1>
        <div>
            <span>{{ username }} ({{ role.upper() }})</span>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>

    <div class="container">
        <div id="setup-banner" class="setup-banner">
            <h3>🔧 Gmail Integration Setup Required</h3>
            <p>Click "Setup Gmail" to authenticate and start scanning your Gmail for VLSI resumes</p>
        </div>

        <div class="status-bar">
            <div>
                <strong id="system-status">System Status: LOADING</strong>
                <div>Gmail: <span id="gmail-status">Not Connected</span> | Drive: <span id="drive-status">Not Connected</span></div>
            </div>
            <div id="current-time"></div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-processed">0</div>
                <div class="stat-label">Resumes Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-duplicates">0</div>
                <div class="stat-label">Duplicates Filtered</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="high-priority">0</div>
                <div class="stat-label">High Priority Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="today-processed">0</div>
                <div class="stat-label">Processed Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-scans">0</div>
                <div class="stat-label">Scans Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="folders-created">0</div>
                <div class="stat-label">Drive Folders</div>
            </div>
        </div>

        {% if role == 'admin' %}
        <div class="controls">
            <h3>🎮 Gmail Scanner Controls</h3>
            <div class="btn-group">
                <button class="btn setup" onclick="setupGmail()" id="setup-btn">🔧 Setup Gmail Integration</button>
                <button class="btn" onclick="testSystem()" id="test-btn">🔍 Test System</button>
                <button class="btn" onclick="checkGoogleSetup()" id="google-check-btn">☁️ Check Google Setup</button>
                <button class="btn" onclick="runFullScan()" id="full-scan-btn" disabled>📧 Full Gmail Scan</button>
                <button class="btn" onclick="runQuickScan()" id="quick-scan-btn" disabled>⚡ Quick Scan (New Emails)</button>
                <button class="btn" onclick="refreshData()">🔄 Refresh Dashboard</button>
                <button class="btn danger" onclick="viewDriveFolders()">📁 View Drive Folders</button>
            </div>
            <div id="scan-status" style="margin-top: 15px; padding: 15px; background: #f0f0f0; border-radius: 8px; border-left: 4px solid #667eea;">
                System ready - Setup Gmail integration to begin scanning
            </div>
            
            <div style="margin-top: 10px; padding: 10px; background: #e3f2fd; border-radius: 8px; font-size: 0.9rem;">
                <strong>Admin Debug Info:</strong><br>
                Role: {{ role }} | Username: {{ username }}<br>
                If you don't see the "Setup Gmail Integration" button above, please refresh the page.
            </div>
            
            <!-- OAuth Code Input (hidden by default) -->
            <div id="oauth-input" style="display: none; margin-top: 15px; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <h4>🔑 OAuth Authorization Required</h4>
                <p>Click the authorization URL in the logs above, then enter the code you receive:</p>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <input type="text" id="auth-code" placeholder="Enter authorization code here" style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <button class="btn" onclick="submitOAuthCode()">Submit Code</button>
                </div>
            </div>
            
            <div class="drive-folders" id="drive-folders" style="display: none;">
                <h4>📁 Google Drive Folder Structure</h4>
                <div id="folder-list">Loading...</div>
            </div>
        </div>
        {% endif %}

        <div class="grid">
            <div class="card">
                <h3>📊 VLSI Domain Classification</h3>
                <div class="chart-container">
                    <canvas id="domainChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>⏰ Experience Level Distribution</h3>
                <div class="chart-container">
                    <canvas id="experienceChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>🏆 Priority Classification</h3>
                <div class="chart-container">
                    <canvas id="priorityChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>🕒 Recent Gmail Processing</h3>
                <div id="activity-feed" style="max-height: 300px; overflow-y: auto;">
                    <div style="text-align: center; padding: 40px; color: #666;">
                        No resumes processed yet. Run a Gmail scan to see activity.
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>📋 System & Gmail Logs</h3>
                <div class="logs" id="logs">Starting VLSI Gmail Scanner...</div>
            </div>

            <div class="card">
                <h3>📈 Processing Statistics</h3>
                <div style="padding: 20px;">
                    <div style="margin-bottom: 15px;">
                        <strong>Gmail Scan Performance</strong>
                        <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">
                            <div>Average Processing Time: <span id="avg-time">-</span></div>
                            <div>Success Rate: <span id="success-rate">-</span></div>
                            <div>Last Scan: <span id="last-scan">Never</span></div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong>Google Drive Integration</strong>
                        <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">
                            <div>Main Folder: <span id="main-folder">Not Created</span></div>
                            <div>Domain Folders: <span id="domain-folders">0/7 Created</span></div>
                            <div>Files Uploaded: <span id="files-uploaded">0</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let charts = {};
        const isAdmin = '{{ role }}' === 'admin';

        function initCharts() {
            const domainLabels = ['RTL Design', 'Design Verification', 'DFT Design for Test', 'STA Timing Analysis', 'Physical Design', 'Power Verification', 'Analog Design'];
            
            charts.domain = new Chart(document.getElementById('domainChart'), {
                type: 'doughnut',
                data: { 
                    labels: domainLabels, 
                    datasets: [{ 
                        data: [0,0,0,0,0,0,0], 
                        backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'] 
                    }] 
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            charts.experience = new Chart(document.getElementById('experienceChart'), {
                type: 'bar',
                data: { 
                    labels: ['Fresher', 'Junior', 'Mid-Level', 'Senior', 'Expert'], 
                    datasets: [{ 
                        data: [0,0,0,0,0], 
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }] 
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
            });

            charts.priority = new Chart(document.getElementById('priorityChart'), {
                type: 'pie',
                data: { 
                    labels: ['High Priority', 'Medium Priority', 'Low Priority'], 
                    datasets: [{ 
                        data: [0,0,0], 
                        backgroundColor: ['#FF6B6B', '#FFEAA7', '#96CEB4'] 
                    }] 
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        function updateClock() {
            document.getElementById('current-time').textContent = new Date().toLocaleString();
        }

        function loadData() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    // Update stats
                    document.getElementById('total-processed').textContent = data.total_processed || 0;
                    document.getElementById('total-duplicates').textContent = data.total_duplicates || 0;
                    document.getElementById('high-priority').textContent = data.total_high_priority || 0;
                    document.getElementById('today-processed').textContent = data.today_processed || 0;
                    document.getElementById('total-scans').textContent = data.total_scans_today || 0;
                    document.getElementById('folders-created').textContent = data.drive_folders_created ? '7' : '0';
                    
                    // Update system status
                    document.getElementById('system-status').textContent = 'System Status: ' + data.system_status;
                    document.getElementById('gmail-status').textContent = data.google_authenticated ? '✅ Connected' : '❌ Not Connected';
                    document.getElementById('drive-status').textContent = data.drive_folders_created ? '✅ Folders Ready' : '❌ Not Setup';
                    
                    // Update setup banner
                    const banner = document.getElementById('setup-banner');
                    if (data.google_authenticated && data.drive_folders_created) {
                        banner.className = 'setup-banner ready';
                        banner.innerHTML = '<h3>✅ Gmail Integration Active</h3><p>Scanning Gmail for VLSI resumes and auto-categorizing to Google Drive</p>';
                    } else if (data.credentials_available) {
                        banner.innerHTML = '<h3>🔧 Gmail Setup Available</h3><p>Credentials detected. Click "Setup Gmail" to authenticate and create Drive folders</p>';
                    } else {
                        banner.innerHTML = '<h3>📥 Upload Google Credentials</h3><p>Download credentials.json from Google Cloud Console and upload to enable Gmail scanning</p>';
                    }
                    
                    // Enable/disable buttons
                    if (isAdmin) {
                        const authenticated = data.google_authenticated;
                        document.getElementById('full-scan-btn').disabled = !authenticated;
                        document.getElementById('quick-scan-btn').disabled = !authenticated;
                        document.getElementById('setup-btn').textContent = authenticated ? '✅ Gmail Connected' : '🔧 Setup Gmail Integration';
                    }

                    // Update charts
                    if (charts.domain && data.domain_stats) {
                        charts.domain.data.datasets[0].data = Object.values(data.domain_stats);
                        charts.domain.update();
                    }

                    if (charts.experience && data.experience_stats) {
                        charts.experience.data.datasets[0].data = Object.values(data.experience_stats);
                        charts.experience.update();
                    }

                    if (charts.priority && data.priority_distribution) {
                        charts.priority.data.datasets[0].data = Object.values(data.priority_distribution);
                        charts.priority.update();
                    }

                    // Update activity feed
                    if (data.recent_activity && data.recent_activity.length > 0) {
                        document.getElementById('activity-feed').innerHTML = data.recent_activity.map(activity => `
                            <div class="activity-item">
                                <div>
                                    <strong>${activity.sender}</strong><br>
                                    <small>${activity.filename} → ${activity.domain}</small><br>
                                    <small>${activity.experience} | ${activity.confidence.toFixed(1)}% confidence</small>
                                </div>
                                <span class="priority-badge ${activity.priority.toLowerCase()}">${activity.priority}</span>
                            </div>
                        `).join('');
                    }

                    // Update logs
                    if (data.logs && data.logs.length > 0) {
                        const logs = document.getElementById('logs');
                        logs.innerHTML = data.logs.map(log => {
                            const colors = { error: '#ff6b6b', success: '#4caf50', warning: '#ffd43b', info: '#0f0' };
                            return `<div style="color: ${colors[log.level] || '#0f0'}">[${log.timestamp}] ${log.message}</div>`;
                        }).join('');
                        logs.scrollTop = logs.scrollHeight;
                    }

                    // Update scan status
                    if (isAdmin && data.scan_status) {
                        document.getElementById('scan-status').innerHTML = data.scan_status;
                    }

                    // Update statistics
                    document.getElementById('avg-time').textContent = data.avg_processing_time ? data.avg_processing_time.toFixed(1) + 's' : '-';
                    document.getElementById('success-rate').textContent = data.success_rate ? data.success_rate.toFixed(1) + '%' : '-';
                    document.getElementById('files-uploaded').textContent = data.total_processed || 0;
                })
                .catch(e => {
                    console.error('Failed to load data:', e);
                    addLogToDisplay('Failed to connect to backend: ' + e.message, 'error');
                });
        }

        function addLogToDisplay(message, type = 'info') {
            const logs = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            const colors = { error: '#ff6b6b', success: '#4caf50', warning: '#ffd43b', info: '#0f0' };
            logs.innerHTML += `<div style="color: ${colors[type]}">[${timestamp}] ${message}</div>`;
            logs.scrollTop = logs.scrollHeight;
        }

        function checkGoogleSetup() {
            if (!isAdmin) return;
            addLogToDisplay('☁️ Checking Google Cloud Console setup...', 'info');
            addLogToDisplay('', 'info');
            addLogToDisplay('📋 Google Cloud Console Setup Checklist:', 'info');
            addLogToDisplay('1️⃣ Go to: https://console.cloud.google.com/', 'info');
            addLogToDisplay('2️⃣ Create/Select a project', 'info');
            addLogToDisplay('3️⃣ Enable APIs:', 'info');
            addLogToDisplay('   - Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com', 'info');
            addLogToDisplay('   - Google Drive API: https://console.cloud.google.com/apis/library/drive.googleapis.com', 'info');
            addLogToDisplay('4️⃣ Configure OAuth consent screen:', 'info');
            addLogToDisplay('   - Go to: APIs & Services > OAuth consent screen', 'info');
            addLogToDisplay('   - Add your email to test users', 'info');
            addLogToDisplay('   - Add scopes: Gmail readonly, Drive file access', 'info');
            addLogToDisplay('5️⃣ Create credentials:', 'info');
            addLogToDisplay('   - Go to: APIs & Services > Credentials', 'info');
            addLogToDisplay('   - Create OAuth 2.0 Client ID (Desktop Application)', 'info');
            addLogToDisplay('   - Download as credentials.json', 'info');
            addLogToDisplay('6️⃣ Upload credentials.json to your Railway deployment', 'info');
            addLogToDisplay('', 'info');
            addLogToDisplay('💡 Common Issues:', 'warning');
            addLogToDisplay('❌ "Access blocked" → Add email to test users in OAuth consent', 'warning');
            addLogToDisplay('❌ "API not enabled" → Enable Gmail & Drive APIs', 'warning');
            addLogToDisplay('❌ "Invalid credentials" → Re-download credentials.json', 'warning');
            addLogToDisplay('❌ "Insufficient permissions" → Check scopes in OAuth consent', 'warning');
        }

        function submitOAuthCode() {
            const code = document.getElementById('auth-code').value.trim();
            if (!code) {
                addLogToDisplay('❌ Please enter the authorization code', 'error');
                return;
            }
            
            addLogToDisplay('🔑 Submitting OAuth authorization code...', 'info');
            
            fetch('/api/oauth-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLogToDisplay('✅ OAuth authentication completed!', 'success');
                    document.getElementById('oauth-input').style.display = 'none';
                    loadData(); // Refresh dashboard
                } else {
                    addLogToDisplay('❌ OAuth failed: ' + data.message, 'error');
                }
            })
            .catch(e => {
                addLogToDisplay('❌ OAuth submission failed: ' + e.message, 'error');
            });
        }

        function testSystem() {
            if (!isAdmin) return;
            addLogToDisplay('🔍 Testing system requirements...', 'info');
            
            fetch('/api/test-system', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    addLogToDisplay('📋 System Test Results:', 'info');
                    const status = data.system_status;
                    
                    addLogToDisplay(`📦 Google APIs Available: ${status.google_apis_available ? '✅' : '❌'}`, status.google_apis_available ? 'success' : 'error');
                    addLogToDisplay(`📄 PDF Processing Available: ${status.pdf_processing_available ? '✅' : '❌'}`, status.pdf_processing_available ? 'success' : 'error');
                    
                    // Environment Variables Check
                    addLogToDisplay('', 'info');
                    addLogToDisplay('🔐 Environment Variables:', 'info');
                    addLogToDisplay(`   GOOGLE_CLIENT_ID: ${status.env_client_id ? '✅ Set' : '❌ Missing'}`, status.env_client_id ? 'success' : 'error');
                    addLogToDisplay(`   GOOGLE_CLIENT_SECRET: ${status.env_client_secret ? '✅ Set' : '❌ Missing'}`, status.env_client_secret ? 'success' : 'error');
                    addLogToDisplay(`   GOOGLE_PROJECT_ID: ${status.env_project_id ? '✅ Set' : '❌ Missing'}`, status.env_project_id ? 'success' : 'error');
                    
                    if (status.client_id_preview !== 'Not set') {
                        addLogToDisplay(`   Client ID Preview: ${status.client_id_preview}`, 'info');
                    }
                    if (status.project_id_value !== 'Not set') {
                        addLogToDisplay(`   Project ID: ${status.project_id_value}`, 'info');
                    }
                    
                    // File Status
                    addLogToDisplay('', 'info');
                    addLogToDisplay('📁 Files:', 'info');
                    addLogToDisplay(`🔑 Credentials File: ${status.credentials_file_exists ? '✅ Found' : '❌ Missing (Using env vars)'}`, status.credentials_file_exists ? 'success' : 'warning');
                    addLogToDisplay(`🎫 Token File: ${status.token_file_exists ? '✅ Found' : '⚠️ Not created yet'}`, status.token_file_exists ? 'success' : 'warning');
                    
                    // Services
                    addLogToDisplay('', 'info');
                    addLogToDisplay('🔗 Services:', 'info');
                    addLogToDisplay(`📧 Gmail Service: ${status.gmail_service_active ? '✅ Active' : '❌ Not connected'}`, status.gmail_service_active ? 'success' : 'error');
                    addLogToDisplay(`💾 Drive Service: ${status.drive_service_active ? '✅ Active' : '❌ Not connected'}`, status.drive_service_active ? 'success' : 'error');
                    
                    // Provide next steps
                    addLogToDisplay('', 'info');
                    addLogToDisplay('📋 Next Steps:', 'info');
                    
                    if (!status.google_apis_available) {
                        addLogToDisplay('❗ Install Google APIs: pip install google-auth google-auth-oauthlib google-api-python-client', 'warning');
                    }
                    
                    if (!status.env_client_id || !status.env_client_secret || !status.env_project_id) {
                        addLogToDisplay('❗ Set missing environment variables in Railway dashboard', 'warning');
                        addLogToDisplay('   Go to: Railway Project → Variables tab', 'info');
                    } else if (!status.gmail_service_active) {
                        addLogToDisplay('▶️ Environment variables are set! Try "Setup Gmail Integration"', 'success');
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ System test failed: ' + e.message, 'error');
                });
        }

        function setupGmail() {
            if (!isAdmin) return;
            addLogToDisplay('Starting Gmail integration setup...', 'info');
            
            // Disable button during setup
            const setupBtn = document.getElementById('setup-btn');
            setupBtn.disabled = true;
            setupBtn.textContent = '🔄 Setting up...';
            
            fetch('/api/setup-gmail', { method: 'POST' })
                .then(response => {
                    addLogToDisplay(`Setup response status: ${response.status}`, 'info');
                    return response.json();
                })
                .then(data => {
                    addLogToDisplay(`Setup response: ${JSON.stringify(data)}`, 'info');
                    
                    if (data.status === 'success') {
                        addLogToDisplay('✅ Gmail integration setup completed', 'success');
                        setupBtn.textContent = '✅ Gmail Connected';
                        loadData(); // Refresh to show updated status
                    } else {
                        addLogToDisplay('❌ Setup failed: ' + data.message, 'error');
                        
                        // If OAuth is required, show the input form
                        if (data.message.includes('OAuth') || data.message.includes('authorization')) {
                            document.getElementById('oauth-input').style.display = 'block';
                            addLogToDisplay('👆 Please complete OAuth authorization above', 'warning');
                        }
                        
                        setupBtn.disabled = false;
                        setupBtn.textContent = '🔧 Retry Setup';
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ Setup request failed: ' + e.message, 'error');
                    addLogToDisplay('This might be due to missing credentials.json file', 'warning');
                    setupBtn.disabled = false;
                    setupBtn.textContent = '🔧 Retry Setup';
                });
        }

        function runFullScan() {
            if (!isAdmin) return;
            addLogToDisplay('🔍 Starting full Gmail scan for resumes...', 'info');
            
            fetch('/api/scan/full', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.status.includes('error')) {
                        addLogToDisplay('❌ ' + data.message, 'error');
                    } else {
                        addLogToDisplay('🔄 ' + data.status, 'success');
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ Scan request failed: ' + e.message, 'error');
                });
        }

        function runQuickScan() {
            if (!isAdmin) return;
            addLogToDisplay('⚡ Starting quick Gmail scan for new resumes...', 'info');
            
            fetch('/api/scan/incremental', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.status.includes('error')) {
                        addLogToDisplay('❌ ' + data.message, 'error');
                    } else {
                        addLogToDisplay('⚡ ' + data.status, 'success');
                    }
                })
                .catch(e => {
                    addLogToDisplay('❌ Scan request failed: ' + e.message, 'error');
                });
        }

        function viewDriveFolders() {
            const foldersDiv = document.getElementById('drive-folders');
            foldersDiv.style.display = foldersDiv.style.display === 'none' ? 'block' : 'none';
            
            if (foldersDiv.style.display === 'block') {
                const domains = ['RTL_Design', 'Design_Verification', 'DFT_Design_for_Test', 'STA_Timing_Analysis', 'Physical_Design', 'Power_Verification', 'Analog_Design'];
                document.getElementById('folder-list').innerHTML = domains.map(domain => 
                    `<div class="folder-item">
                        <span>📁 ${domain.replace(/_/g, ' ')}</span>
                        <span style="color: #4caf50;">✓ Created</span>
                    </div>`
                ).join('');
            }
        }

        function refreshData() {
            addLogToDisplay('🔄 Refreshing dashboard data...', 'info');
            loadData();
        }

        // Initialize everything
        window.addEventListener('load', () => {
            initCharts();
            loadData();
            updateClock();
            
            // Set up auto-refresh every 30 seconds
            setInterval(loadData, 30000);
            setInterval(updateClock, 1000);
            
            addLogToDisplay('🚀 VLSI Gmail Scanner Dashboard initialized', 'success');
            addLogToDisplay('📧 Ready to scan Gmail for VLSI resumes', 'info');
        });
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    print(f"🚀 Starting VLSI Gmail Scanner on port {PORT}")
    print("📧 Real Gmail Integration - Scans Gmail and categorizes to Google Drive")
    scanner.add_log("VLSI Gmail Scanner started", 'success')
    app.run(host='0.0.0.0', port=PORT, debug=False)

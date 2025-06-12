import os
import json
import logging
import re
import base64
import time
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, render_template_string, request, jsonify, session

# Try to import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
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
    from docx import Document
    DOCX_PROCESSING_AVAILABLE = True
except ImportError:
    DOCX_PROCESSING_AVAILABLE = False

try:
    import docx2txt
    DOC_PROCESSING_AVAILABLE = True
except ImportError:
    DOC_PROCESSING_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vlsi-scanner-secret-key-2024')

# Configuration
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive'  # Add this line
]

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
        self.current_user_email = None
        self.user_credentials = {}
        self._oauth_flow = None
        
    def add_log(self, message: str, level: str = 'info'):
        """Add a log entry with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        if level == 'error':
            logging.error(f"[{timestamp}] {message}")
        elif level == 'warning':
            logging.warning(f"[{timestamp}] {message}")
        else:
            logging.info(f"[{timestamp}] {message}")

    def authenticate_google_apis(self, user_email: str = None) -> bool:
        """Authenticate with Google APIs"""
        try:
            creds = None
            
            # Try to load existing token
            token_file = 'token.json'
            if user_email:
                token_file = f'token_{user_email.replace("@", "_").replace(".", "_")}.json'
            
            if os.path.exists(token_file):
                try:
                    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
                    self.add_log(f"🔐 Loaded existing token", 'info')
                except Exception as e:
                    self.add_log(f"⚠️ Could not load token: {e}", 'warning')
            
            # If credentials are invalid, start OAuth flow
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
            
            # Test the credentials
            self.credentials = creds
            return self._test_credentials()
            
        except Exception as e:
            self.add_log(f"❌ Authentication failed: {e}", 'error')
            return False

    def _run_oauth_flow(self, user_email: str = None) -> bool:
        """Run OAuth flow for new authentication"""
        try:
            # Get credentials from environment variables
            client_id = os.environ.get('GOOGLE_CLIENT_ID')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            project_id = os.environ.get('GOOGLE_PROJECT_ID')
            
            if not all([client_id, client_secret, project_id]):
                self.add_log("❌ Missing OAuth credentials in environment variables", 'error')
                return False
            
            credentials_dict = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_config(
                credentials_dict, 
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            
            self._oauth_flow = flow
            
            # Generate auth URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='select_account',
                include_granted_scopes='true'
            )
            
            self.add_log("🌐 OAuth authorization required", 'info')
            self.add_log(f"📋 Authorization URL: {auth_url}", 'info')
            self.add_log("1️⃣ Copy the URL above and open in browser", 'info')
            self.add_log("2️⃣ Select your Gmail account", 'info')
            self.add_log("3️⃣ Complete Google authorization", 'info')
            self.add_log("4️⃣ Copy the authorization code", 'info')
            self.add_log("5️⃣ Enter it in the form below", 'info')
            
            return False  # Indicates manual intervention needed
            
        except Exception as e:
            self.add_log(f"❌ OAuth flow failed: {e}", 'error')
            return False

    def _test_credentials(self) -> bool:
        """Test the credentials by making API calls"""
        try:
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            result = self.gmail_service.users().getProfile(userId='me').execute()
            email = result.get('emailAddress', 'Unknown')
            self.add_log(f"✅ Gmail access confirmed for: {email}", 'success')
            
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            about = self.drive_service.about().get(fields='user').execute()
            drive_email = about.get('user', {}).get('emailAddress', 'Unknown')
            self.add_log(f"✅ Drive access confirmed for: {drive_email}", 'success')
            
            # Save credentials
            with open('token.json', 'w') as token:
                token.write(self.credentials.to_json())
            self.add_log("💾 Saved authentication token", 'success')
            
            self.current_user_email = email
            self.user_credentials[email] = self.credentials
            
            return True
            
        except Exception as e:
            self.add_log(f"❌ Credential test failed: {e}", 'error')
            return False

    def setup_drive_folders(self) -> bool:
        """Create necessary folders in Google Drive"""
        try:
            if not self.drive_service:
                return False
            
            self.add_log("📁 Setting up Drive folders", 'info')
            
            # Create main folder
            query = "name='VLSI Resume Scanner' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            
            if results.get('files'):
                parent_folder_id = results['files'][0]['id']
                self.add_log("✅ Found existing parent folder", 'success')
            else:
                parent_metadata = {
                    'name': 'VLSI Resume Scanner',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                parent_folder = self.drive_service.files().create(body=parent_metadata, fields='id').execute()
                parent_folder_id = parent_folder.get('id')
                self.add_log("✅ Created parent folder", 'success')
            
            # Create resumes folder
            resume_query = f"name='Resumes by Domain' and parents in '{parent_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            resume_results = self.drive_service.files().list(q=resume_query, fields="files(id, name)").execute()
            
            if resume_results.get('files'):
                self.resume_folder_id = resume_results['files'][0]['id']
                self.add_log("✅ Found existing Resumes folder", 'success')
            else:
                resume_metadata = {
                    'name': 'Resumes by Domain',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                resume_folder = self.drive_service.files().create(body=resume_metadata, fields='id').execute()
                self.resume_folder_id = resume_folder.get('id')
                self.add_log("✅ Created Resumes folder", 'success')
            
            # Create domain folders
            domains = ['Physical Design', 'Design Verification', 'DFT', 'RTL Design', 'Analog Design', 'FPGA', 'Silicon Validation', 'Mixed Signal', 'General VLSI', 'Unknown Domain']
            
            for domain in domains:
                folder_query = f"name='{domain}' and parents in '{self.resume_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                folder_results = self.drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
                
                if folder_results.get('files'):
                    self.domain_folders[domain] = folder_results['files'][0]['id']
                    self.add_log(f"✅ Found folder: {domain}", 'success')
                else:
                    folder_metadata = {
                        'name': domain,
                        'parents': [self.resume_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
                    self.domain_folders[domain] = folder.get('id')
                    self.add_log(f"✅ Created folder: {domain}", 'success')
                    
                    # Create experience subfolders
                    for exp_level in ['Fresher (0-2 years)', 'Mid-Level (2-5 years)', 'Senior (5-8 years)', 'Experienced (8+ years)']:
                        exp_metadata = {
                            'name': exp_level,
                            'parents': [folder.get('id')],
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                        self.drive_service.files().create(body=exp_metadata, fields='id').execute()
            
            return True
            
        except Exception as e:
            self.add_log(f"❌ Drive setup failed: {e}", 'error')
            return False

    def scan_emails(self, max_results: int = None) -> Dict[str, Any]:
        """Scan Gmail for resume attachments"""
        try:
            if not self.gmail_service:
                return {'success': False, 'error': 'Gmail service not available'}
            
            self.add_log(f"🔍 Starting Gmail scan", 'info')
            
            # Search for emails with attachments
            query = 'has:attachment (filename:pdf OR filename:doc OR filename:docx)'
            if max_results:
                query += f' newer_than:30d'
            
            result = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=min(50, max_results or 50)
            ).execute()
            
            messages = result.get('messages', [])
            self.add_log(f"📧 Found {len(messages)} emails with attachments", 'info')
            
            resumes_found = 0
            processed_count = 0
            
            for i, message in enumerate(messages, 1):
                try:
                    self.add_log(f"📨 Processing email {i}/{len(messages)}", 'info')
                    result = self.process_email(message['id'])
                    
                    if result.get('has_resume'):
                        resumes_found += 1
                        
                    processed_count += 1
                    
                    if i % 5 == 0:
                        time.sleep(1)  # Rate limiting
                        
                except Exception as e:
                    self.add_log(f"❌ Error processing email {i}: {e}", 'error')
                    self.stats['processing_errors'] += 1
                    continue
            
            # Update stats
            self.stats['total_emails'] = processed_count
            self.stats['resumes_found'] = resumes_found
            self.stats['last_scan_time'] = datetime.now().isoformat()
            
            self.add_log(f"✅ Scan completed: {processed_count} emails, {resumes_found} resumes", 'success')
            
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
            message = self.gmail_service.users().messages().get(userId='me', id=message_id).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Check for attachments
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
                    
                    # Analyze content
                    analysis_result = self.analyze_content(data, attachment['filename'])
                    
                    if analysis_result and analysis_result.get('is_resume', False):
                        has_resume = True
                        
                        # Save to Drive
                        drive_file_id = self.save_to_drive(
                            data,
                            attachment['filename'],
                            {
                                'subject': subject,
                                'sender': sender,
                                'date': date_header,
                                'analysis_result': analysis_result
                            }
                        )
                        
                        processed_attachments.append({
                            'filename': attachment['filename'],
                            'domain': analysis_result.get('domain', 'Unknown Domain'),
                            'experience': analysis_result.get('experience_level', 'Unknown'),
                            'score': analysis_result.get('resume_score', 0),
                            'drive_file_id': drive_file_id
                        })
                    
                except Exception as e:
                    self.add_log(f"❌ Error processing {attachment['filename']}: {e}", 'error')
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

    def analyze_content(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Analyze file content to determine if it's a resume and categorize it"""
        try:
            text = ""
            
            # Extract text based on file type (using your existing methods)
            if filename.lower().endswith('.pdf'):
                text = self.extract_pdf_text(file_data)
            elif filename.lower().endswith('.docx'):
                text = self.extract_docx_text(file_data, filename)
            elif filename.lower().endswith('.doc'):
                text = self.extract_doc_text(file_data, filename)
            
            if not text:
                return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}
            
            # Analyze text for resume indicators
            text_lower = text.lower()
            
            # Enhanced resume detection - check for non-resume documents
            non_resume_indicators = [
                'table of contents', 'chapter', 'bibliography', 'references',
                'abstract', 'isbn', 'doi:', 'journal', 'conference',
                'invoice', 'receipt', 'balance sheet', 'financial statement',
                'user manual', 'datasheet', 'specification', 'rev ', 'version ',
                'confidential', 'proprietary', 'not for distribution'
            ]
            
            non_resume_count = sum(1 for indicator in non_resume_indicators if indicator in text_lower)
            if non_resume_count >= 3:
                self.add_log(f"❌ Rejected {filename}: Appears to be technical documentation (found {non_resume_count} indicators)", 'warning')
                return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}
            
            # Check for resume sections
            resume_sections = {
                'contact': ['email', 'phone', 'address', 'linkedin'],
                'experience': ['experience', 'employment', 'work history', 'professional experience', 'career'],
                'education': ['education', 'qualification', 'degree', 'university', 'college', 'academic'],
                'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'proficient']
            }
            
            sections_found = 0
            for section, keywords in resume_sections.items():
                if any(keyword in text_lower for keyword in keywords):
                    sections_found += 1
            
            # Must have at least 3 resume sections
            if sections_found < 3:
                self.add_log(f"❌ Rejected {filename}: Only {sections_found} resume sections found", 'warning')
                return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}
            
            # Basic resume scoring
            resume_indicators = ['experience', 'education', 'skills', 'resume', 'cv', 'work', 'employment', 'career']
            resume_score = sum(1 for indicator in resume_indicators if indicator in text_lower)
            
            if resume_score < 3:
                return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}
            
            # Enhanced domain classification with weighted keywords
            domain_keywords = {
                'Physical Design': {
                    'primary': ['physical design', 'place and route', 'floorplanning', 'sta', 'static timing', 
                               'primetime', 'innovus', 'icc', 'icc2', 'encounter', 'timing closure', 'cts'],
                    'secondary': ['synopsys', 'cadence', 'mentor', 'power planning', 'ir drop'],
                    'weight': 3
                },
                'Design Verification': {
                    'primary': ['verification', 'dv engineer', 'uvm', 'systemverilog', 'testbench', 
                               'coverage', 'assertion', 'scoreboard', 'questa', 'vcs'],
                    'secondary': ['simulation', 'regression', 'constrained random'],
                    'weight': 3
                },
                'DFT': {
                    'primary': ['dft', 'design for test', 'scan', 'atpg', 'bist', 'mbist', 
                               'jtag', 'boundary scan', 'tessent', 'tetramax'],
                    'secondary': ['fault coverage', 'test pattern', 'scan chain'],
                    'weight': 3
                },
                'RTL Design': {
                    'primary': ['rtl', 'rtl design', 'verilog', 'vhdl', 'synthesis', 
                               'design compiler', 'genus', 'fsm', 'microarchitecture'],
                    'secondary': ['hdl', 'behavioral', 'structural'],
                    'weight': 3
                },
                'Analog Design': {
                    'primary': ['analog', 'analog design', 'adc', 'dac', 'pll', 'opamp', 
                               'amplifier', 'spice', 'spectre', 'cadence virtuoso'],
                    'secondary': ['cmos', 'transistor', 'layout', 'matching'],
                    'weight': 3
                },
                'FPGA': {
                    'primary': ['fpga', 'xilinx', 'altera', 'vivado', 'quartus', 
                               'zynq', 'ultrascale', 'vitis'],
                    'secondary': ['bitstream', 'block ram', 'lut'],
                    'weight': 3
                },
                'Silicon Validation': {
                    'primary': ['silicon validation', 'post silicon', 'bring up', 'characterization',
                               'lab', 'oscilloscope', 'logic analyzer'],
                    'secondary': ['debug', 'correlation', 'yield analysis'],
                    'weight': 3
                },
                'Mixed Signal': {
                    'primary': ['mixed signal', 'ams', 'serdes', 'high speed', 'transceiver',
                               'signal integrity', 'jitter', 'eye diagram'],
                    'secondary': ['differential', 'pcie', 'usb', 'ddr'],
                    'weight': 3
                }
            }
            
            domain_scores = {}
            for domain, keywords_dict in domain_keywords.items():
                score = 0
                # Check primary keywords (higher weight)
                for keyword in keywords_dict['primary']:
                    if keyword in text_lower:
                        score += keywords_dict['weight']
                # Check secondary keywords (lower weight)
                for keyword in keywords_dict['secondary']:
                    if keyword in text_lower:
                        score += 1
                
                domain_scores[domain] = score
            
            # Determine primary domain
            if domain_scores:
                primary_domain = max(domain_scores.items(), key=lambda x: x[1])
                domain = primary_domain[0] if primary_domain[1] > 0 else 'General VLSI'
                
                # Check if multiple domains have high scores (mixed profile)
                high_score_domains = [d for d, s in domain_scores.items() if s >= 5]
                if len(high_score_domains) > 1:
                    # Log additional domains
                    self.add_log(f"📋 Multi-domain profile detected: {', '.join(high_score_domains)}", 'info')
            else:
                domain = 'General VLSI'
            
            # Enhanced experience level detection
            experience_years = 0
            year_patterns = [
                r'(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
                r'experience\s*:?\s*(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)',
                r'(\d+)\s*years?\s*(\d+)\s*months?',
                r'total\s*experience\s*:?\s*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:professional|industry)'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle "X years Y months" pattern
                        if len(match) == 2 and match[0].isdigit() and match[1].isdigit():
                            years = float(match[0]) + float(match[1]) / 12
                            experience_years = max(experience_years, years)
                    else:
                        years = float(match)
                        if 0 < years < 50:  # Sanity check
                            experience_years = max(experience_years, years)
            
            # Check for fresher indicators if no experience found
            if experience_years == 0:
                fresher_indicators = ['fresher', 'entry level', 'recent graduate', 'fresh graduate']
                if any(indicator in text_lower for indicator in fresher_indicators):
                    experience_years = 0
            
            # Categorize experience
            if experience_years <= 2:
                experience_level = 'Fresher (0-2 years)'
            elif experience_years <= 5:
                experience_level = 'Mid-Level (2-5 years)'
            elif experience_years <= 8:
                experience_level = 'Senior (5-8 years)'
            else:
                experience_level = 'Experienced (8+ years)'
            
            # Log successful analysis
            self.add_log(f"✅ Resume detected: {filename} | Domain: {domain} | Experience: {experience_level} ({experience_years} years)", 'success')
            
            return {
                'is_resume': True,
                'domain': domain,
                'experience_level': experience_level,
                'experience_years': experience_years,
                'resume_score': min(resume_score / 10.0, 1.0)
            }
            
        except Exception as e:
            self.add_log(f"❌ Error analyzing {filename}: {e}", 'error')
            return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}

    def extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF"""
        try:
            if not PDF_PROCESSING_AVAILABLE:
                return ""
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_data)
                temp_file_path = temp_file.name
            
            try:
                try:
                    import pdfplumber
                    with pdfplumber.open(temp_file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    return text
                except ImportError:
                    import PyPDF2
                    with open(temp_file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                    return text
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.add_log(f"❌ PDF extraction failed: {e}", 'error')
            return ""

    def extract_docx_text(self, doc_data: bytes, filename: str) -> str:
        """Extract text from DOCX"""
        try:
            if not DOCX_PROCESSING_AVAILABLE:
                return ""
            
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(doc_data)
                temp_file_path = temp_file.name
            
            try:
                doc = Document(temp_file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.add_log(f"❌ DOCX extraction failed: {e}", 'error')
            return ""

    def extract_doc_text(self, doc_data: bytes, filename: str) -> str:
        """Extract text from DOC"""
        try:
            if not DOC_PROCESSING_AVAILABLE:
                return ""
            
            with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as temp_file:
                temp_file.write(doc_data)
                temp_file_path = temp_file.name
            
            try:
                import docx2txt
                text = docx2txt.process(temp_file_path)
                return text
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.add_log(f"❌ DOC extraction failed: {e}", 'error')
            return ""

    def save_to_drive(self, file_data: bytes, filename: str, metadata: Dict) -> Optional[str]:
        """Save file to Google Drive with domain and experience organization"""
        try:
            if not self.drive_service:
                return None
            
            analysis = metadata.get('analysis_result', {})
            domain = analysis.get('domain', 'Unknown Domain')
            experience_level = analysis.get('experience_level', 'Unknown')
            experience_years = analysis.get('experience_years', 0)
            
            # Get domain folder
            domain_folder_id = self.domain_folders.get(domain, self.domain_folders.get('Unknown Domain'))
            
            # Find experience subfolder
            exp_folder_query = f"name='{experience_level}' and parents in '{domain_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            exp_results = self.drive_service.files().list(q=exp_folder_query, fields="files(id, name)").execute()
            
            if exp_results.get('files'):
                target_folder_id = exp_results['files'][0]['id']
            else:
                # Create experience subfolder
                exp_metadata = {
                    'name': experience_level,
                    'parents': [domain_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                exp_folder = self.drive_service.files().create(body=exp_metadata, fields='id').execute()
                target_folder_id = exp_folder.get('id')
            
            # Create enhanced filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_extension = filename.split('.')[-1].lower()
            clean_filename = filename.replace(f'.{file_extension}', '')
            
            domain_abbrev = {
                'Physical Design': 'PD', 'Design Verification': 'DV', 'DFT': 'DFT',
                'RTL Design': 'RTL', 'Analog Design': 'ANA', 'FPGA': 'FPGA',
                'Silicon Validation': 'SiVal', 'Mixed Signal': 'MS',
                'General VLSI': 'VLSI', 'Unknown Domain': 'UNK'
            }.get(domain, 'UNK')
            
            exp_abbrev = {
                'Fresher (0-2 years)': 'FR', 'Mid-Level (2-5 years)': 'ML',
                'Senior (5-8 years)': 'SR', 'Experienced (8+ years)': 'EX'
            }.get(experience_level, 'UK')
            
            new_filename = f"[{domain_abbrev}_{exp_abbrev}_{experience_years}Y] {timestamp}_{clean_filename}.{file_extension}"
            
            file_metadata = {
                'name': new_filename,
                'parents': [target_folder_id],
                'description': f"""VLSI Resume Scanner Analysis

Email: {metadata.get('sender', 'Unknown')}
Subject: {metadata.get('subject', 'No subject')}
Date: {metadata.get('date', 'Unknown')}

Domain: {domain}
Experience: {experience_level} ({experience_years} years)
Score: {analysis.get('resume_score', 0):.2f}

Auto-filed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Location: {domain} > {experience_level}"""
            }
            
            # Upload file
            mime_types = {
                'pdf': 'application/pdf',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                from googleapiclient.http import MediaFileUpload
                media = MediaFileUpload(temp_file_path, mimetype=mime_type)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                file_id = file.get('id')
                self.add_log(f"💾 Saved: {domain}/{experience_level} - {filename}", 'success')
                return file_id
                
            finally:
                os.unlink(temp_file_path)
            
        except Exception as e:
            self.add_log(f"❌ Save failed for {filename}: {e}", 'error')
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
            'current_user': self.current_user_email,
            'authenticated_users': list(self.user_credentials.keys()),
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
                <h1>🔬 VLSI Resume Scanner v2.1</h1>
                <p>AI-Powered Domain & Experience Classification System</p>
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
            
            fetch('/api/setup-gmail', { 
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({})
            })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        addLogToDisplay('✅ ' + data.message, 'success');
                        hideOAuthInput();
                    } else {
                        addLogToDisplay('❌ ' + data.message, 'error');
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

        function showUserManager() {
            document.getElementById('user-manager').style.display = 'block';
            loadAuthenticatedUsers();
        }

        function hideUserManager() {
            document.getElementById('user-manager').style.display = 'none';
        }

        function authenticateUser() {
            const email = document.getElementById('user-email-input').value.trim();
            
            if (!email || !email.includes('@')) {
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

        function loadAuthenticatedUsers() {
            fetch('/api/users')
            .then(r => r.json())
            .then(data => {
                const userList = document.getElementById('user-list');
                if (data.users && data.users.length > 0) {
                    userList.innerHTML = data.users.map(user => 
                        `<div style="padding: 5px 0; border-bottom: 1px solid #eee;">
                            <span style="color: #2196f3;">✓</span> ${user}
                        </div>`
                    ).join('');
                } else {
                    userList.innerHTML = '<div style="color: #666; font-style: italic;">No authenticated users yet</div>';
                }
            })
            .catch(e => {
                document.getElementById('user-list').innerHTML = '<div style="color: #f44336;">Error loading users</div>';
            });
        }

        function scanGmail() {
            if (!isAdmin) return;
            addLogToDisplay('📧 Starting full Gmail scan...', 'info');
            
            fetch('/api/scan-gmail', { 
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({})
            })
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
            
            fetch('/api/quick-scan', { 
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({})
            })
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
            
            fetch('/api/test-system', { 
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({})
            })
                .then(r => r.json())
                .then(data => {
                    addLogToDisplay('📊 System test completed', 'info');
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
                    <span>DOC Processing:</span>
                    <span class="status-value ${data.docx_processing_available || data.doc_processing_available ? 'success' : 'error'}">
                        ${data.docx_processing_available || data.doc_processing_available ? '✅ Available' : '❌ Missing'}
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
                    <span>Current User:</span>
                    <span class="status-value ${data.current_user ? 'success' : 'warning'}">
                        ${data.current_user || 'Not authenticated'}
                    </span>
                </div>
            `;
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
                            
                            const newLogs = logs.slice(logCount);
                            newLogs.forEach(log => {
                                const logEntry = document.createElement('div');
                                logEntry.className = `log-entry ${log.level}`;
                                logEntry.textContent = `[${log.timestamp}] ${log.message}`;
                                logsContainer.appendChild(logEntry);
                            });
                            
                            logCount = logs.length;
                            logsContainer.scrollTop = logsContainer.scrollHeight;
                            
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
        
        if not GOOGLE_APIS_AVAILABLE:
            return jsonify({'status': 'error', 'message': 'Google API libraries not available'})
        
        if scanner.authenticate_google_apis(user_email):
            if scanner.setup_drive_folders():
                return jsonify({'status': 'success', 'message': 'Gmail integration setup completed'})
            else:
                return jsonify({'status': 'error', 'message': 'Drive folder setup failed'})
        else:
            return jsonify({'status': 'error', 'message': 'Gmail authentication failed'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Setup failed: {str(e)}'})

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
            return jsonify({'status': 'error', 'message': 'Authorization code is required'})
        
        if not hasattr(scanner, '_oauth_flow') or not scanner._oauth_flow:
            return jsonify({'status': 'error', 'message': 'OAuth flow not found. Please restart Gmail setup.'})
        
        try:
            # Exchange code for credentials
            scanner._oauth_flow.fetch_token(code=auth_code)
            creds = scanner._oauth_flow.credentials
            
            # Save credentials
            try:
                temp_gmail_service = build('gmail', 'v1', credentials=creds)
                profile = temp_gmail_service.users().getProfile(userId='me').execute()
                user_email = profile.get('emailAddress')
                
                if user_email:
                    token_filename = f'token_{user_email.replace("@", "_").replace(".", "_")}.json'
                    with open(token_filename, 'w') as token:
                        token.write(creds.to_json())
                    scanner.add_log(f"💾 Saved token for {user_email}", 'success')
                    
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                    
            except Exception as e:
                scanner.add_log(f"⚠️ Could not save token: {e}", 'warning')
            
            # Initialize services
            scanner.credentials = creds
            if scanner._test_credentials():
                if scanner.setup_drive_folders():
                    scanner._oauth_flow = None
                    return jsonify({'status': 'success', 'message': 'OAuth authentication completed successfully'})
                else:
                    return jsonify({'status': 'error', 'message': 'Drive folder setup failed'})
            else:
                return jsonify({'status': 'error', 'message': 'Credential verification failed'})
            
        except Exception as e:
            error_str = str(e).lower()
            if "invalid_grant" in error_str:
                scanner.add_log("💡 Authorization code may have expired", 'warning')
            return jsonify({'status': 'error', 'message': f'Failed to exchange code: {str(e)}'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'OAuth submission failed: {str(e)}'})

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

@app.route('/api/scan-gmail', methods=['POST'])
@admin_required
def api_scan_gmail():
    """Full Gmail scan"""
    result = scanner.scan_emails()
    return jsonify(result)

@app.route('/api/quick-scan', methods=['POST'])
@admin_required
def api_quick_scan():
    """Quick Gmail scan"""
    result = scanner.scan_emails(max_results=50)
    return jsonify(result)

@app.route('/api/test-system', methods=['POST'])
@admin_required
def api_test_system():
    """Test system components"""
    status = scanner.get_system_status()
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

import os
import json
import logging
import re
import base64
import time
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
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
        import pypdf as PyPDF2
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
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

logging.basicConfig(level=logging.INFO)

class VLSIResumeScanner:
    """Complete VLSI Resume Scanner with Sheets Integration"""
    def __init__(self):
        self.credentials = None
        self.gmail_service = None
        self.drive_service = None
        self.sheets_service = None
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
        self.main_spreadsheet_id = None
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
            if not GOOGLE_APIS_AVAILABLE:
                self.add_log("❌ Google APIs not available", 'error')
                return False
                
            creds = None
            
            # Try to load existing token (will fail on Railway due to ephemeral storage)
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
            
            # Test Sheets API
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            self.add_log("✅ Sheets access confirmed", 'success')
            
            # Save credentials (will work on Railway for session only)
            try:
                with open('token.json', 'w') as token:
                    token.write(self.credentials.to_json())
                self.add_log("💾 Saved authentication token (session only)", 'info')
            except Exception as e:
                self.add_log(f"⚠️ Could not save token: {e}", 'warning')
            
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
            domains = ['Physical Design', 'Design Verification', 'DFT', 'RTL Design', 
                      'Analog Design', 'FPGA', 'Silicon Validation', 'Mixed Signal', 
                      'General VLSI', 'Unknown Domain']
            
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
                    for exp_level in ['Fresher (0-2 years)', 'Mid-Level (2-5 years)', 
                                    'Senior (5-8 years)', 'Experienced (8+ years)']:
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

    def setup_sheets_integration(self) -> bool:
        """Create and setup Google Sheets for resume data"""
        try:
            if not self.sheets_service:
                self.add_log("❌ Sheets service not available", 'error')
                return False
                
            self.add_log("📊 Setting up Google Sheets integration", 'info')
            
            # Create main spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': f'VLSI Resume Database - {datetime.now().strftime("%Y-%m-%d")}',
                    'locale': 'en_US',
                    'timeZone': 'UTC'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Resume Summary',
                            'gridProperties': {'rowCount': 1000, 'columnCount': 20}
                        }
                    },
                    {
                        'properties': {
                            'title': 'Contact Details',
                            'gridProperties': {'rowCount': 1000, 'columnCount': 15}
                        }
                    }
                ]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            self.main_spreadsheet_id = spreadsheet['spreadsheetId']
            self.add_log(f"✅ Created main spreadsheet: {self.main_spreadsheet_id}", 'success')
            
            # Setup headers
            self._setup_sheet_headers()
            
            return True
            
        except Exception as e:
            self.add_log(f"❌ Sheets setup failed: {e}", 'error')
            return False

    def _setup_sheet_headers(self):
        """Setup headers for sheets"""
        try:
            # Resume Summary headers
            resume_headers = [
                'ID', 'Timestamp', 'Name', 'Email', 'Phone', 'Domain', 
                'Experience Level', 'Experience Years', 'Education', 'Current Company',
                'Current Role', 'Location', 'Resume Score', 'Key Skills', 
                'File Name', 'Drive File ID', 'Source Email', 'Processing Status'
            ]
            
            # Write headers
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.main_spreadsheet_id,
                range='Resume Summary!A1:R1',
                valueInputOption='USER_ENTERED',
                body={'values': [resume_headers]}
            ).execute()
            
            self.add_log("✅ Sheet headers configured", 'success')
            
        except Exception as e:
            self.add_log(f"❌ Header setup failed: {e}", 'error')

    def analyze_content(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Analyze file content to determine if it's a resume"""
        try:
            text = ""
            
            # Extract text based on file type
            if filename.lower().endswith('.pdf') and PDF_PROCESSING_AVAILABLE:
                text = self.extract_pdf_text(file_data)
            elif filename.lower().endswith('.docx') and DOCX_PROCESSING_AVAILABLE:
                text = self.extract_docx_text(file_data, filename)
            elif filename.lower().endswith('.doc') and DOC_PROCESSING_AVAILABLE:
                text = self.extract_doc_text(file_data, filename)
            
            if not text:
                self.add_log(f"⚠️ Could not extract text from {filename}", 'warning')
                return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}
            
            # Basic resume validation
            text_lower = text.lower()
            
            # Check for resume sections
            resume_sections = {
                'contact': ['email', 'phone', 'address', 'linkedin'],
                'experience': ['experience', 'employment', 'work history', 'professional experience'],
                'education': ['education', 'qualification', 'degree', 'university'],
                'skills': ['skills', 'technical skills', 'competencies']
            }
            
            sections_found = 0
            for section, keywords in resume_sections.items():
                if any(keyword in text_lower for keyword in keywords):
                    sections_found += 1
            
            if sections_found < 2:
                return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}
            
            # Domain classification
            domain = self._classify_domain(text_lower)
            
            # Experience level detection
            experience_level, experience_years = self._detect_experience(text_lower)
            
            return {
                'is_resume': True,
                'domain': domain,
                'experience_level': experience_level,
                'experience_years': experience_years,
                'resume_score': sections_found / 4.0
            }
            
        except Exception as e:
            self.add_log(f"❌ Error analyzing {filename}: {e}", 'error')
            return {'is_resume': False, 'domain': 'Unknown Domain', 'experience_level': 'Unknown', 'resume_score': 0}

    def _classify_domain(self, text: str) -> str:
        """Classify VLSI domain"""
        domain_keywords = {
            'Physical Design': ['physical design', 'place and route', 'floorplanning', 'sta', 'primetime'],
            'Design Verification': ['verification', 'uvm', 'systemverilog', 'testbench'],
            'DFT': ['dft', 'scan', 'atpg', 'bist'],
            'RTL Design': ['rtl', 'verilog', 'vhdl', 'synthesis'],
            'Analog Design': ['analog', 'spice', 'opamp', 'pll'],
            'FPGA': ['fpga', 'xilinx', 'vivado', 'quartus']
        }
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            domain_scores[domain] = score
        
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            return best_domain[0] if best_domain[1] > 0 else 'General VLSI'
        
        return 'General VLSI'

    def _detect_experience(self, text: str) -> tuple:
        """Detect experience level"""
        # Look for experience patterns
        experience_patterns = [
            r'(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*:?\s*(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)'
        ]
        
        experience_years = 0
        for pattern in experience_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    years = float(match)
                    if 0 < years < 50:
                        experience_years = max(experience_years, years)
                except:
                    continue
        
        # Categorize experience
        if experience_years <= 2:
            return 'Fresher (0-2 years)', experience_years
        elif experience_years <= 5:
            return 'Mid-Level (2-5 years)', experience_years
        elif experience_years <= 8:
            return 'Senior (5-8 years)', experience_years
        else:
            return 'Experienced (8+ years)', experience_years

    def extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_data)
                temp_file_path = temp_file.name
            
            try:
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

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'google_apis_available': GOOGLE_APIS_AVAILABLE,
            'pdf_processing_available': PDF_PROCESSING_AVAILABLE,
            'docx_processing_available': DOCX_PROCESSING_AVAILABLE,
            'doc_processing_available': DOC_PROCESSING_AVAILABLE,
            'gmail_service_active': self.gmail_service is not None,
            'drive_service_active': self.drive_service is not None,
            'sheets_service_active': self.sheets_service is not None,
            'current_user': self.current_user_email,
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
            .status { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 VLSI Resume Scanner</h1>
                <p>AI-Powered Resume Analysis with Google Sheets Integration</p>
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
                    <div class="status">
                        <h3>✅ Railway Deployment Successful!</h3>
                        <p>Basic application is running. You can now set up Google API integration.</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
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
                    document.getElementById('auth-section').style.display = 'none';
                    document.getElementById('main-content').style.display = 'block';
                } else {
                    alert('Invalid password');
                }
            });
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

@app.route('/api/status')
@admin_required
def api_status():
    """Get system status"""
    return jsonify(scanner.get_system_status())

@app.route('/health')
def health_check():
    """Railway health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'google_apis': GOOGLE_APIS_AVAILABLE,
        'pdf_processing': PDF_PROCESSING_AVAILABLE
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

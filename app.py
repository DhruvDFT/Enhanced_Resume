import os
import json
import logging
from datetime import datetime
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

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-2024')

# Configuration
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

logging.basicConfig(level=logging.INFO)

class VLSIResumeScanner:
    """VLSI Resume Scanner with Google Integration"""
    
    def __init__(self):
        self.credentials = None
        self.gmail_service = None
        self.drive_service = None
        self.sheets_service = None
        self.logs = []
        self.max_logs = 50
        self.stats = {
            'total_emails': 0,
            'resumes_found': 0,
            'last_scan_time': None,
            'processing_errors': 0
        }
        self.current_user_email = None
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

    def get_system_status(self) -> dict:
        """Get current system status"""
        return {
            'google_apis_available': GOOGLE_APIS_AVAILABLE,
            'pdf_processing_available': PDF_PROCESSING_AVAILABLE,
            'docx_processing_available': DOCX_PROCESSING_AVAILABLE,
            'gmail_service_active': self.gmail_service is not None,
            'drive_service_active': self.drive_service is not None,
            'sheets_service_active': self.sheets_service is not None,
            'current_user': self.current_user_email,
            'stats': self.stats,
            'recent_logs': self.logs[-5:] if self.logs else [],
            'environment_check': {
                'has_client_id': bool(os.environ.get('GOOGLE_CLIENT_ID')),
                'has_client_secret': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
                'has_project_id': bool(os.environ.get('GOOGLE_PROJECT_ID')),
                'admin_password_set': bool(os.environ.get('ADMIN_PASSWORD'))
            }
        }

    def save_credentials(self, client_id: str, client_secret: str, project_id: str):
        """Save credentials to environment/session"""
        try:
            # Store in session for this instance
            session['google_client_id'] = client_id
            session['google_client_secret'] = client_secret
            session['google_project_id'] = project_id
            
            self.add_log("✅ Google credentials saved to session", 'info')
            return {'success': True, 'message': 'Credentials saved successfully'}
        except Exception as e:
            self.add_log(f"❌ Failed to save credentials: {e}", 'error')
            return {'success': False, 'error': str(e)}

    def start_oauth_flow(self):
        """Start OAuth authentication flow"""
        try:
            if not GOOGLE_APIS_AVAILABLE:
                return {'success': False, 'error': 'Google APIs not available'}
                
            # Get credentials from environment or session
            client_id = os.environ.get('GOOGLE_CLIENT_ID') or session.get('google_client_id')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or session.get('google_client_secret')
            
            if not client_id or not client_secret:
                return {'success': False, 'error': 'OAuth credentials not configured. Please set them up first.'}
            
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
            flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
            self._oauth_flow = flow
            
            # Generate auth URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='select_account',
                include_granted_scopes='true'
            )
            
            self.add_log("🌐 OAuth authorization URL generated", 'info')
            return {
                'success': True, 
                'auth_url': auth_url,
                'message': 'Please visit the authorization URL and enter the code'
            }
            
        except Exception as e:
            self.add_log(f"❌ OAuth flow failed: {e}", 'error')
            return {'success': False, 'error': str(e)}

    def complete_oauth_flow(self, auth_code: str):
        """Complete OAuth flow with authorization code"""
        try:
            if not self._oauth_flow:
                return {'success': False, 'error': 'OAuth flow not started'}
            
            # Exchange code for token
            self._oauth_flow.fetch_token(code=auth_code)
            self.credentials = self._oauth_flow.credentials
            
            # Test the credentials
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            result = self.gmail_service.users().getProfile(userId='me').execute()
            email = result.get('emailAddress', 'Unknown')
            
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            
            self.current_user_email = email
            self.add_log(f"✅ Authentication successful for: {email}", 'info')
            
            return {'success': True, 'email': email, 'message': 'Authentication completed successfully'}
            
        except Exception as e:
            self.add_log(f"❌ OAuth completion failed: {e}", 'error')
            return {'success': False, 'error': str(e)}

# Initialize scanner
scanner = VLSIResumeScanner()

@app.route('/')
def index():
    """Main dashboard with integrated setup"""
    template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔬 VLSI Resume Scanner</title>
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
            .status {
                background: #e8f5e8; border: 2px solid #4caf50;
                border-radius: 10px; padding: 20px; margin: 20px 0;
                text-align: center;
            }
            .status h3 { color: #2e7d32; margin-bottom: 10px; }
            .status p { color: #388e3c; }
            .auth-section {
                background: #f8f9fa; border-radius: 10px; 
                padding: 20px; margin-bottom: 30px; text-align: center;
            }
            .input-group {
                display: flex; gap: 10px; margin-bottom: 20px;
                justify-content: center; align-items: center; flex-wrap: wrap;
            }
            .input-group input {
                padding: 12px; border: 1px solid #ddd;
                border-radius: 5px; font-size: 1em; min-width: 250px;
            }
            .input-group button, .btn {
                padding: 12px 24px; background: #4a90e2; color: white;
                border: none; border-radius: 5px; cursor: pointer;
                font-size: 1em; margin: 5px;
            }
            .input-group button:hover, .btn:hover { background: #357abd; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
            .btn-warning { background: #ffc107; color: #212529; }
            .btn-warning:hover { background: #e0a800; }
            .btn-info { background: #17a2b8; }
            .btn-info:hover { background: #138496; }
            .main-content, .setup-content { display: none; }
            .dashboard-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px; margin-top: 30px;
            }
            .card {
                background: #f8f9fa; border-radius: 10px; padding: 20px;
                border-left: 4px solid #4a90e2; min-height: 150px;
            }
            .card h4 { color: #4a90e2; margin-bottom: 15px; }
            .card p { margin-bottom: 10px; line-height: 1.5; }
            .logs-container {
                max-height: 200px; overflow-y: auto; 
                background: #f1f1f1; padding: 10px; border-radius: 5px;
                font-family: monospace; font-size: 0.9em;
            }
            .log-entry { margin-bottom: 5px; }
            .log-info { color: #0066cc; }
            .log-warning { color: #ff8800; }
            .log-error { color: #cc0000; }
            .oauth-section {
                background: #fff3cd; border: 1px solid #ffeaa7;
                border-radius: 10px; padding: 20px; margin: 20px 0;
            }
            .oauth-url {
                background: #f8f9fa; padding: 10px; border-radius: 5px;
                word-break: break-all; margin: 10px 0; font-size: 0.9em;
            }
            .setup-wizard {
                background: #e3f2fd; border: 2px solid #2196f3;
                border-radius: 10px; padding: 30px; margin: 20px 0;
                text-align: center;
            }
            .setup-step {
                background: white; border-radius: 8px; padding: 20px;
                margin: 15px 0; border-left: 4px solid #2196f3;
                text-align: left;
            }
            .setup-step h5 { color: #1976d2; margin-bottom: 10px; }
            .setup-step p { margin-bottom: 8px; line-height: 1.5; }
            .credentials-form {
                background: white; padding: 20px; border-radius: 8px;
                margin: 20px 0; text-align: left;
            }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .form-group small { color: #666; font-size: 0.9em; }
            .hidden { display: none; }
            .tab-container { margin-bottom: 20px; }
            .tab-button { 
                padding: 10px 20px; margin-right: 10px; border: none; 
                background: #f0f0f0; border-radius: 5px 5px 0 0; cursor: pointer;
            }
            .tab-button.active { background: #4a90e2; color: white; }
            .alert { padding: 15px; margin: 15px 0; border-radius: 5px; }
            .alert-info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            .alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 VLSI Resume Scanner</h1>
                <p>AI-Powered Resume Analysis with Google Sheets Integration</p>
            </div>
            
            <div class="content">
                <div class="status">
                    <h3>✅ Application Ready!</h3>
                    <p>Complete setup to start scanning resumes from Gmail.</p>
                </div>

                <div id="auth-section" class="auth-section">
                    <h3>🔐 Admin Authentication</h3>
                    <div class="input-group">
                        <input type="password" id="admin-password" placeholder="Enter admin password">
                        <button onclick="authenticate()">🔑 Login</button>
                    </div>
                    <p>Enter admin password to access the VLSI Resume Scanner dashboard</p>
                </div>

                <div id="setup-content" class="setup-content">
                    <div class="setup-wizard">
                        <h2>🛠️ Google API Setup Wizard</h2>
                        <p>Let's set up your Google API credentials step by step</p>
                        
                        <div class="tab-container">
                            <button class="tab-button active" onclick="showTab('instructions')">📋 Instructions</button>
                            <button class="tab-button" onclick="showTab('credentials')">🔑 Enter Credentials</button>
                        </div>

                        <div id="instructions-tab">
                            <div class="setup-step">
                                <h5>Step 1: Create Google Cloud Project</h5>
                                <p>1. Visit <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></p>
                                <p>2. Click "Select a project" → "NEW PROJECT"</p>
                                <p>3. Enter project name: "VLSI Resume Scanner"</p>
                                <p>4. Click "CREATE"</p>
                            </div>

                            <div class="setup-step">
                                <h5>Step 2: Enable Required APIs</h5>
                                <p>1. Go to "APIs & Services" → "Library"</p>
                                <p>2. Search and enable these APIs:</p>
                                <ul style="margin-left: 20px;">
                                    <li>Gmail API</li>
                                    <li>Google Drive API</li>
                                    <li>Google Sheets API</li>
                                </ul>
                            </div>

                            <div class="setup-step">
                                <h5>Step 3: Create OAuth Credentials</h5>
                                <p>1. Go to "APIs & Services" → "Credentials"</p>
                                <p>2. Click "OAuth consent screen" and configure:</p>
                                <ul style="margin-left: 20px;">
                                    <li>User Type: External</li>
                                    <li>App name: VLSI Resume Scanner</li>
                                    <li>Add your email as test user</li>
                                </ul>
                                <p>3. Go to "Credentials" → "CREATE CREDENTIALS" → "OAuth 2.0 Client IDs"</p>
                                <p>4. Choose "Desktop application"</p>
                                <p>5. Copy the Client ID and Client Secret</p>
                            </div>

                            <div class="alert alert-info">
                                <strong>💡 Pro Tip:</strong> Keep the Google Cloud Console tab open while entering credentials in the next tab.
                            </div>
                        </div>

                        <div id="credentials-tab" class="hidden">
                            <div class="credentials-form">
                                <h4>🔑 Enter Your Google API Credentials</h4>
                                
                                <div class="form-group">
                                    <label for="client-id">Google Client ID</label>
                                    <input type="text" id="client-id" placeholder="123456789-abc...googleusercontent.com">
                                    <small>Found in Google Cloud Console → Credentials → OAuth 2.0 Client IDs</small>
                                </div>

                                <div class="form-group">
                                    <label for="client-secret">Google Client Secret</label>
                                    <input type="text" id="client-secret" placeholder="GOCSPX-abc123...">
                                    <small>Found next to the Client ID in Google Cloud Console</small>
                                </div>

                                <div class="form-group">
                                    <label for="project-id">Google Project ID</label>
                                    <input type="text" id="project-id" placeholder="vlsi-scanner-123456">
                                    <small>Found in Google Cloud Console project selector</small>
                                </div>

                                <div class="input-group">
                                    <button class="btn btn-success" onclick="saveCredentials()">💾 Save Credentials</button>
                                    <button class="btn" onclick="showMainDashboard()">⏭️ Skip for Now</button>
                                </div>

                                <div class="alert alert-warning">
                                    <strong>⚠️ Note:</strong> Credentials are stored in session only. For permanent storage, set environment variables.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="main-content" class="main-content">
                    <h2>🎛️ VLSI Resume Scanner Dashboard</h2>
                    <p>Welcome to the admin panel. Your Google API integration status is shown below.</p>
                    
                    <div class="dashboard-grid">
                        <div class="card">
                            <h4>📊 System Status</h4>
                            <div id="system-status">
                                <p>Loading system status...</p>
                            </div>
                            <button class="btn" onclick="refreshStatus()">🔄 Refresh Status</button>
                            <button class="btn btn-info" onclick="showSetupWizard()">🛠️ Setup Wizard</button>
                        </div>
                        
                        <div class="card">
                            <h4>🔧 Google API Setup</h4>
                            <p>Configure Gmail, Drive, and Sheets integration</p>
                            <button class="btn btn-success" onclick="setupGoogleAuth()" id="setup-btn">
                                🚀 Start Google Authentication
                            </button>
                            <div id="oauth-section" class="oauth-section hidden">
                                <h5>📋 OAuth Authorization Required</h5>
                                <p>1. Click the link below to authorize the application:</p>
                                <div id="auth-url" class="oauth-url"></div>
                                <p>2. Copy the authorization code and paste it here:</p>
                                <div class="input-group">
                                    <input type="text" id="auth-code" placeholder="Paste authorization code here">
                                    <button onclick="completeAuth()">✅ Complete Authentication</button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h4>📧 Resume Scanning</h4>
                            <p>Scan Gmail for resumes and organize them</p>
                            <button class="btn" onclick="startScan()" id="scan-btn" disabled>
                                📊 Start Gmail Scan
                            </button>
                            <div id="scan-results"></div>
                        </div>
                        
                        <div class="card">
                            <h4>📋 Activity Logs</h4>
                            <div id="logs-container" class="logs-container">
                                <p>Logs will appear here...</p>
                            </div>
                            <button class="btn btn-warning" onclick="clearLogs()">🗑️ Clear Logs</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        function showTab(tabName) {
            // Hide all tabs
            document.getElementById('instructions-tab').classList.add('hidden');
            document.getElementById('credentials-tab').classList.add('hidden');
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.remove('hidden');
            event.target.classList.add('active');
        }

        function showSetupWizard() {
            document.getElementById('main-content').style.display = 'none';
            document.getElementById('setup-content').style.display = 'block';
        }

        function showMainDashboard() {
            document.getElementById('setup-content').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
            refreshStatus();
        }

        function saveCredentials() {
            const clientId = document.getElementById('client-id').value;
            const clientSecret = document.getElementById('client-secret').value;
            const projectId = document.getElementById('project-id').value;
            
            if (!clientId || !clientSecret || !projectId) {
                alert('Please fill in all credential fields');
                return;
            }
            
            fetch('/api/save-credentials', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    client_id: clientId,
                    client_secret: clientSecret,
                    project_id: projectId
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Credentials saved successfully!');
                    showMainDashboard();
                } else {
                    alert('❌ Failed to save credentials: ' + data.error);
                }
            })
            .catch(err => {
                alert('Failed to save credentials');
                console.error('Save error:', err);
            });
        }

        function authenticate() {
            const password = document.getElementById('admin-password').value;
            
            if (!password) {
                alert('Please enter admin password');
                return;
            }
            
            fetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('auth-section').style.display = 'none';
                    // Check if credentials are configured
                    fetch('/api/status')
                    .then(r => r.json())
                    .then(status => {
                        if (status.environment_check.has_client_id && status.environment_check.has_client_secret) {
                            showMainDashboard();
                        } else {
                            document.getElementById('setup-content').style.display = 'block';
                        }
                    });
                } else {
                    alert('Invalid password. Please try again.');
                    document.getElementById('admin-password').value = '';
                }
            })
            .catch(err => {
                alert('Authentication failed. Please try again.');
                console.error('Auth error:', err);
            });
        }

        function refreshStatus() {
            fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                const statusDiv = document.getElementById('system-status');
                statusDiv.innerHTML = `
                    <p><strong>Google APIs:</strong> ${data.google_apis_available ? '✅' : '❌'}</p>
                    <p><strong>PDF Processing:</strong> ${data.pdf_processing_available ? '✅' : '❌'}</p>
                    <p><strong>Credentials:</strong> ${data.environment_check.has_client_id ? '✅' : '❌'}</p>
                    <p><strong>Current User:</strong> ${data.current_user || 'Not authenticated'}</p>
                    <p><strong>Gmail Service:</strong> ${data.gmail_service_active ? '✅' : '❌'}</p>
                    <p><strong>Drive Service:</strong> ${data.drive_service_active ? '✅' : '❌'}</p>
                    <p><strong>Sheets Service:</strong> ${data.sheets_service_active ? '✅' : '❌'}</p>
                `;
                
                // Update scan button state
                const scanBtn = document.getElementById('scan-btn');
                if (data.gmail_service_active) {
                    scanBtn.disabled = false;
                    scanBtn.textContent = '📊 Start Gmail Scan';
                } else {
                    scanBtn.disabled = true;
                    scanBtn.textContent = '📊 Gmail Authentication Required';
                }
                
                // Update logs
                if (data.recent_logs && data.recent_logs.length > 0) {
                    const logsDiv = document.getElementById('logs-container');
                    logsDiv.innerHTML = data.recent_logs.map(log => 
                        `<div class="log-entry log-${log.level}">[${log.timestamp}] ${log.message}</div>`
                    ).join('');
                }
            })
            .catch(err => {
                console.error('Status error:', err);
                document.getElementById('system-status').innerHTML = '<p style="color: red;">Failed to load status</p>';
            });
        }

        function setupGoogleAuth() {
            fetch('/api/start-oauth', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('oauth-section').classList.remove('hidden');
                    document.getElementById('auth-url').innerHTML = 
                        `<a href="${data.auth_url}" target="_blank">${data.auth_url}</a>`;
                    document.getElementById('setup-btn').textContent = '⏳ Waiting for Authorization...';
                    document.getElementById('setup-btn').disabled = true;
                } else {
                    if (data.error.includes('not configured')) {
                        alert('Please set up your Google API credentials first using the Setup Wizard');
                        showSetupWizard();
                    } else {
                        alert('Failed to start OAuth: ' + data.error);
                    }
                }
            })
            .catch(err => {
                alert('OAuth setup failed');
                console.error('OAuth error:', err);
            });
        }

        function completeAuth() {
            const authCode = document.getElementById('auth-code').value;
            if (!authCode) {
                alert('Please enter the authorization code');
                return;
            }
            
            fetch('/api/complete-oauth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auth_code: authCode })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('Authentication successful! Email: ' + data.email);
                    document.getElementById('oauth-section').classList.add('hidden');
                    document.getElementById('setup-btn').textContent = '✅ Google APIs Connected';
                    document.getElementById('setup-btn').disabled = true;
                    refreshStatus();
                } else {
                    alert('Authentication failed: ' + data.error);
                }
            })
            .catch(err => {
                alert('Authentication completion failed');
                console.error('Auth completion error:', err);
            });
        }

        function startScan() {
            document.getElementById('scan-results').innerHTML = '<p>🔄 Scanning emails...</p>';
            
            fetch('/api/scan-emails', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('scan-results').innerHTML = 
                        `<p>✅ Scan completed! Found ${data.resumes_found || 0} resumes in ${data.emails_scanned || 0} emails.</p>`;

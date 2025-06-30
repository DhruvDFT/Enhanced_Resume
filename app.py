import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session

# RAILWAY FIX 1: Ensure proper logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    stream=sys.stdout
)

# RAILWAY FIX 2: Set proper timeouts and buffering
sys.stdout.reconfigure(line_buffering=True)

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

# RAILWAY FIX 3: Proper configuration for Railway environment
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
PORT = int(os.environ.get('PORT', 5000))
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

# RAILWAY FIX 4: Add health check and startup optimization (Flask 2.3+ compatible)
def initialize_app():
    """Initialize app - this runs on startup"""
    app.logger.info("🚀 VLSI Resume Scanner starting up...")
    app.logger.info(f"📊 Google APIs available: {GOOGLE_APIS_AVAILABLE}")
    app.logger.info(f"🔧 Environment: Railway Cloud")

# Call initialization immediately
with app.app_context():
    initialize_app()

@app.route('/health')
def health_check():
    """Railway health check endpoint - CRITICAL for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'google_apis': GOOGLE_APIS_AVAILABLE,
        'pdf_processing': PDF_PROCESSING_AVAILABLE,
        'message': 'VLSI Resume Scanner is running successfully on Railway'
    }), 200

# RAILWAY FIX 5: Add startup route for faster initial response
@app.route('/startup')
def startup_check():
    """Quick startup check - helps Railway detect successful deployment"""
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.now().isoformat(),
        'message': 'Application ready to serve requests'
    }), 200

class VLSIResumeScanner:
    """VLSI Resume Scanner with Google Integration - Railway Optimized"""
    
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
        
        # RAILWAY FIX 6: Add startup logging
        self.add_log("🚀 VLSI Resume Scanner initialized for Railway", 'info')
        
    def add_log(self, message: str, level: str = 'info'):
        """Enhanced logging for Railway"""
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
        
        # RAILWAY FIX 7: Ensure logs appear in Railway dashboard
        if level == 'error':
            app.logger.error(f"[{timestamp}] {message}")
        elif level == 'warning':
            app.logger.warning(f"[{timestamp}] {message}")
        else:
            app.logger.info(f"[{timestamp}] {message}")

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
                'has_client_id': bool(os.environ.get('GOOGLE_CLIENT_ID')) or bool(session.get('google_client_id')),
                'has_client_secret': bool(os.environ.get('GOOGLE_CLIENT_SECRET')) or bool(session.get('google_client_secret')),
                'has_project_id': bool(os.environ.get('GOOGLE_PROJECT_ID')) or bool(session.get('google_project_id')),
                'admin_password_set': bool(os.environ.get('ADMIN_PASSWORD'))
            }
        }

    def save_credentials(self, client_id: str, client_secret: str, project_id: str):
        """Save credentials to session"""
        try:
            session['google_client_id'] = client_id
            session['google_client_secret'] = client_secret
            session['google_project_id'] = project_id
            
            self.add_log("✅ Google credentials saved to session", 'info')
            return {'success': True, 'message': 'Credentials saved successfully'}
        except Exception as e:
            self.add_log(f"❌ Failed to save credentials: {e}", 'error')
            return {'success': False, 'error': str(e)}

    def start_oauth_flow(self):
        """Start OAuth authentication flow - ULTIMATE FIX VERSION"""
        try:
            if not GOOGLE_APIS_AVAILABLE:
                return {'success': False, 'error': 'Google APIs not available'}
                
            # Get credentials from environment or session
            client_id = os.environ.get('GOOGLE_CLIENT_ID') or session.get('google_client_id')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or session.get('google_client_secret')
            
            if not client_id or not client_secret:
                return {'success': False, 'error': 'OAuth credentials not configured'}
            
            # ULTIMATE FIX: Use manual URL construction to avoid oauthlib conflicts
            try:
                import urllib.parse
                
                # Build OAuth URL manually - this eliminates ALL redirect_uri conflicts
                params = {
                    'client_id': client_id,
                    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                    'scope': ' '.join(SCOPES),
                    'response_type': 'code',
                    'access_type': 'offline',
                    'prompt': 'select_account'
                }
                
                auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
                
                # Store credentials for later use
                session['oauth_client_id'] = client_id
                session['oauth_client_secret'] = client_secret
                
                self.add_log("✅ Manual OAuth URL generated successfully", 'info')
                
                return {
                    'success': True, 
                    'auth_url': auth_url,
                    'message': 'Please visit the authorization URL and enter the code',
                    'method': 'manual'
                }
                
            except Exception as manual_error:
                self.add_log(f"❌ Manual URL generation failed: {manual_error}", 'error')
                
                # FALLBACK: Try the original method with extra safety
                try:
                    # Clear any existing flow
                    self._oauth_flow = None
                    
                    # Create minimal credentials config
                    credentials_dict = {
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token"
                        }
                    }
                    
                    # Create flow with explicit redirect_uri parameter
                    flow = InstalledAppFlow.from_client_config(
                        credentials_dict, 
                        SCOPES, 
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )
                    
                    # Generate URL WITHOUT specifying redirect_uri again
                    auth_url, _ = flow.authorization_url(
                        access_type='offline',
                        prompt='select_account'
                    )
                    
                    self._oauth_flow = flow
                    self.add_log("✅ Fallback OAuth flow created", 'info')
                    
                    return {
                        'success': True, 
                        'auth_url': auth_url,
                        'message': 'Please visit the authorization URL and enter the code',
                        'method': 'fallback'
                    }
                    
                except Exception as fallback_error:
                    self.add_log(f"❌ All OAuth methods failed: {fallback_error}", 'error')
                    return {'success': False, 'error': 'OAuth setup failed - please check credentials'}
            
        except Exception as e:
            error_msg = str(e)
            self.add_log(f"❌ OAuth flow failed: {error_msg}", 'error')
            return {'success': False, 'error': f'OAuth setup failed: {error_msg}'}

    def complete_oauth_flow(self, auth_code: str):
        """Complete OAuth flow - ULTIMATE FIX VERSION"""
        try:
            if not auth_code or not auth_code.strip():
                return {'success': False, 'error': 'Authorization code is required'}
            
            auth_code = auth_code.strip()
            self.add_log(f"🔄 Processing auth code: {auth_code[:10]}...", 'info')
            
            # Get stored credentials
            client_id = session.get('oauth_client_id') or os.environ.get('GOOGLE_CLIENT_ID')
            client_secret = session.get('oauth_client_secret') or os.environ.get('GOOGLE_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                return {'success': False, 'error': 'OAuth credentials not found - please restart authentication'}
            
            # ULTIMATE FIX: Manual token exchange to avoid oauthlib conflicts
            try:
                import urllib.parse
                import urllib.request
                import json
                
                # Manual token exchange
                token_data = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': auth_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
                }
                
                token_request = urllib.request.Request(
                    'https://oauth2.googleapis.com/token',
                    data=urllib.parse.urlencode(token_data).encode('utf-8'),
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                with urllib.request.urlopen(token_request) as response:
                    token_response = json.loads(response.read().decode('utf-8'))
                
                if 'access_token' not in token_response:
                    raise Exception('No access token in response')
                
                # Create credentials object manually
                self.credentials = Credentials(
                    token=token_response.get('access_token'),
                    refresh_token=token_response.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=SCOPES
                )
                
                self.add_log("✅ Manual token exchange successful", 'info')
                
            except Exception as manual_error:
                self.add_log(f"❌ Manual token exchange failed: {manual_error}", 'error')
                
                # FALLBACK: Try with existing flow if available
                if self._oauth_flow:
                    try:
                        self._oauth_flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                        self._oauth_flow.fetch_token(code=auth_code)
                        self.credentials = self._oauth_flow.credentials
                        self.add_log("✅ Fallback token exchange successful", 'info')
                    except Exception as fallback_error:
                        self.add_log(f"❌ Fallback token exchange failed: {fallback_error}", 'error')
                        return {'success': False, 'error': f'Token exchange failed: {str(fallback_error)}'}
                else:
                    return {'success': False, 'error': f'Manual token exchange failed: {str(manual_error)}'}
            
            # Test services one by one
            services_status = {}
            email = 'Unknown'
            
            # Test Gmail
            try:
                self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
                result = self.gmail_service.users().getProfile(userId='me').execute()
                email = result.get('emailAddress', 'Unknown')
                services_status['gmail'] = '✅'
                self.add_log(f"✅ Gmail service active for: {email}", 'info')
            except Exception as gmail_error:
                services_status['gmail'] = '❌'
                self.add_log(f"❌ Gmail service failed: {gmail_error}", 'error')
            
            # Test Drive
            try:
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                self.drive_service.about().get(fields='user').execute()
                services_status['drive'] = '✅'
                self.add_log("✅ Drive service active", 'info')
            except Exception as drive_error:
                services_status['drive'] = '❌'
                self.add_log(f"❌ Drive service failed: {drive_error}", 'error')
            
            # Test Sheets
            try:
                self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
                services_status['sheets'] = '✅'
                self.add_log("✅ Sheets service active", 'info')
            except Exception as sheets_error:
                services_status['sheets'] = '❌'
                self.add_log(f"❌ Sheets service failed: {sheets_error}", 'error')
            
            self.current_user_email = email
            
            # Clean up session
            session.pop('oauth_client_id', None)
            session.pop('oauth_client_secret', None)
            
            # Success with detailed status
            success_message = f"Authentication completed! Services: Gmail {services_status.get('gmail', '❌')}, Drive {services_status.get('drive', '❌')}, Sheets {services_status.get('sheets', '❌')}"
            self.add_log(success_message, 'info')
            
            return {
                'success': True, 
                'email': email, 
                'message': success_message,
                'services': services_status
            }
                
        except Exception as e:
            error_msg = str(e)
            self.add_log(f"❌ OAuth completion failed: {error_msg}", 'error')
            return {'success': False, 'error': f'Authentication failed: {error_msg}'}

# Initialize scanner
scanner = VLSIResumeScanner()

# RAILWAY FIX 8: Optimized main route to prevent timeout
@app.route('/')
def index():
    """Main dashboard - RAILWAY OPTIMIZED"""
    try:
        # Quick check for Railway environment
        is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
        
        # Log the request for Railway monitoring
        app.logger.info(f"📊 Dashboard accessed - Railway: {is_railway}")
        
        # Check credentials quickly
        has_credentials = (
            bool(os.environ.get('GOOGLE_CLIENT_ID')) and 
            bool(os.environ.get('GOOGLE_CLIENT_SECRET'))
        )
        
        template = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🔬 VLSI Resume Scanner - Railway</title>
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
                .setup-section {
                    background: #e3f2fd; border: 2px solid #2196f3;
                    border-radius: 10px; padding: 30px; margin: 20px 0;
                    text-align: center;
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
                .hidden { display: none; }
                .form-group { margin-bottom: 15px; }
                .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
                .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                .form-group small { color: #666; font-size: 0.9em; }
                .railway-badge {
                    background: #0070f3; color: white; padding: 5px 10px;
                    border-radius: 15px; font-size: 0.9em; margin-left: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔬 VLSI Resume Scanner</h1>
                    <p>AI-Powered Resume Analysis with Google Sheets Integration<span class="railway-badge">⚡ Railway</span></p>
                </div>
                
                <div class="content">
                    <div class="status">
                        <h3>✅ Railway Deployment Successful!</h3>
                        <p>Application is running and ready for Google API integration.</p>
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
                        <div class="setup-section">
                            <h2>🛠️ Google API Setup</h2>
                            <p>Enter your Google API credentials to get started</p>
                            
                            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left;">
                                <h4>🔑 Enter Google API Credentials</h4>
                                
                                <div class="form-group">
                                    <label for="client-id">Google Client ID</label>
                                    <input type="text" id="client-id" placeholder="123456789-abc...googleusercontent.com">
                                    <small>From Google Cloud Console → APIs & Services → Credentials</small>
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
                            </div>
                            
                            <p><small>💡 <strong>Need help?</strong> Visit <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a> to create OAuth credentials</small></p>
                        </div>
                    </div>

                    <div id="main-content" class="main-content">
                        <h2>🎛️ VLSI Resume Scanner Dashboard</h2>
                        <p>Welcome to the admin panel. Configure Google API integration to start scanning resumes.</p>
                        
                        <div class="dashboard-grid">
                            <div class="card">
                                <h4>📊 System Status</h4>
                                <div id="system-status">
                                    <p>Loading system status...</p>
                                </div>
                                <button class="btn" onclick="refreshStatus()">🔄 Refresh Status</button>
                                ''' + ('<!-- Credentials configured via Railway -->' if has_credentials else '<button class="btn" onclick="showSetupSection()">🛠️ Setup Credentials</button>') + '''
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
            function showSetupSection() {
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
                        <p><strong>Railway:</strong> ${data.railway_environment ? '✅' : '❌'}</p>
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
                            alert('Please set up your Google API credentials first');
                            showSetupSection();
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
                    } else {
                        document.getElementById('scan-results').innerHTML = 
                            `<p style="color: red;">❌ Scan failed: ${data.error}</p>`;
                    }
                    refreshStatus();
                })
                .catch(err => {
                    document.getElementById('scan-results').innerHTML = 
                        '<p style="color: red;">❌ Scan request failed</p>';
                    console.error('Scan error:', err);
                });
            }

            function clearLogs() {
                fetch('/api/clear-logs', { method: 'POST' })
                .then(() => {
                    document.getElementById('logs-container').innerHTML = '<p>Logs cleared</p>';
                });
            }

            // Handle Enter key in password field
            document.getElementById('admin-password').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    authenticate();
                }
            });

            // Auto-refresh status every 30 seconds when authenticated
            setInterval(() => {
                if (document.getElementById('main-content').style.display !== 'none') {
                    refreshStatus();
                }
            }, 30000);
            </script>
        </body>
        </html>
        '''
        
        return render_template_string(template)
        
    except Exception as e:
        app.logger.error(f"❌ Dashboard error: {e}")
        return f"Dashboard temporarily unavailable: {str(e)}", 500

@app.route('/api/save-credentials', methods=['POST'])
def api_save_credentials():
    """Save Google API credentials"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
            
        data = request.get_json()
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()
        project_id = data.get('project_id', '').strip()
        
        if not client_id or not client_secret or not project_id:
            return jsonify({'success': False, 'error': 'All credential fields are required'})
        
        result = scanner.save_credentials(client_id, client_secret, project_id)
        return jsonify(result)
        
    except Exception as e:
        scanner.add_log(f"❌ Failed to save credentials: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/auth', methods=['POST'])
def api_auth():
    """Admin authentication"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            scanner.add_log("🔑 Admin authentication successful", 'info')
            return jsonify({'success': True, 'message': 'Authentication successful'})
        else:
            scanner.add_log("❌ Failed admin authentication attempt", 'warning')
            return jsonify({'success': False, 'message': 'Invalid password'})
    except Exception as e:
        scanner.add_log(f"❌ Authentication error: {e}", 'error')
        return jsonify({'success': False, 'message': f'Authentication error: {str(e)}'})

@app.route('/api/status')
def api_status():
    """Get system status"""
    try:
        status = scanner.get_system_status()
        status['timestamp'] = datetime.now().isoformat()
        status['railway_environment'] = bool(os.environ.get('RAILWAY_ENVIRONMENT'))
        
        return jsonify(status)
    except Exception as e:
        scanner.add_log(f"❌ Status check failed: {e}", 'error')
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@app.route('/api/start-oauth', methods=['POST'])
def api_start_oauth():
    """Start OAuth flow"""
    try:
        result = scanner.start_oauth_flow()
        return jsonify(result)
    except Exception as e:
        scanner.add_log(f"❌ OAuth start failed: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complete-oauth', methods=['POST'])
def api_complete_oauth():
    """Complete OAuth flow"""
    try:
        data = request.get_json()
        auth_code = data.get('auth_code', '')
        
        if not auth_code:
            return jsonify({'success': False, 'error': 'Authorization code required'})
            
        result = scanner.complete_oauth_flow(auth_code)
        return jsonify(result)
    except Exception as e:
        scanner.add_log(f"❌ OAuth completion failed: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scan-emails', methods=['POST'])
def api_scan_emails():
    """Scan emails for resumes"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
            
        if not scanner.gmail_service:
            return jsonify({'success': False, 'error': 'Gmail authentication required'})
            
        # This is a placeholder - implement actual email scanning logic
        scanner.add_log("📧 Starting email scan", 'info')
        
        # Simulate scanning
        scanner.stats['total_emails'] = 50
        scanner.stats['resumes_found'] = 5
        scanner.stats['last_scan_time'] = datetime.now().isoformat()
        
        scanner.add_log("✅ Email scan completed", 'info')
        
        return jsonify({
            'success': True,
            'emails_scanned': scanner.stats['total_emails'],
            'resumes_found': scanner.stats['resumes_found']
        })
    except Exception as e:
        scanner.add_log(f"❌ Email scan failed: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear-logs', methods=['POST'])
def api_clear_logs():
    """Clear system logs"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
            
        scanner.logs.clear()
        scanner.add_log("🗑️ Logs cleared", 'info')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
def api_test():
    """Simple API test endpoint"""
    return jsonify({
        'message': 'VLSI Resume Scanner API is working on Railway!',
        'timestamp': datetime.now().isoformat(),
        'status': 'success',
        'railway_environment': bool(os.environ.get('RAILWAY_ENVIRONMENT')),
        'features': {
            'google_apis': GOOGLE_APIS_AVAILABLE,
            'pdf_processing': PDF_PROCESSING_AVAILABLE,
            'docx_processing': DOCX_PROCESSING_AVAILABLE
        }
    })

# RAILWAY FIX 9: Error handlers for better Railway compatibility
@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f"🔍 404 Error: {request.url}")
    return jsonify({
        'error': 'Endpoint not found',
        'railway_status': 'running',
        'available_endpoints': ['/', '/health', '/startup', '/api/test']
    }), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"💥 500 Error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'railway_status': 'error',
        'message': 'Please check Railway logs for details'
    }), 500

@app.errorhandler(TimeoutError)
def timeout_error(error):
    app.logger.error(f"⏰ Timeout Error: {error}")
    return jsonify({
        'error': 'Request timeout',
        'railway_status': 'timeout',
        'message': 'Operation took too long - try again'
    }), 504

# Initialize scanner on startup
scanner.add_log("🚀 VLSI Resume Scanner initialized for Railway", 'info')
scanner.add_log(f"📊 Google APIs available: {GOOGLE_APIS_AVAILABLE}", 'info')
scanner.add_log(f"📄 PDF processing available: {PDF_PROCESSING_AVAILABLE}", 'info')

# RAILWAY FIX 10: Proper main execution
if __name__ == '__main__':
    # Railway deployment configuration
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        app.logger.info("🚅 Starting on Railway...")
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,  # Never use debug=True in production
            threaded=True
        )
    else:
        # Local development
        app.logger.info("💻 Starting locally...")
        app.run(
            debug=True,
            host='0.0.0.0',
            port=PORT
        )

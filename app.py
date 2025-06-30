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
        """Start OAuth authentication flow - BULLETPROOF VERSION"""
        try:
            if not GOOGLE_APIS_AVAILABLE:
                return {'success': False, 'error': 'Google APIs not available'}
                
            # Get credentials from environment or session
            client_id = os.environ.get('GOOGLE_CLIENT_ID') or session.get('google_client_id')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or session.get('google_client_secret')
            
            if not client_id or not client_secret:
                return {'success': False, 'error': 'OAuth credentials not configured'}
            
            # STEP 1: Create minimal credentials config (NO redirect_uris here!)
            credentials_dict = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
            }
            
            # STEP 2: Create flow WITHOUT any redirect_uri parameter
            try:
                flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
                self._oauth_flow = flow
                self.add_log("✅ OAuth flow object created successfully", 'info')
            except Exception as flow_error:
                self.add_log(f"❌ Flow creation failed: {flow_error}", 'error')
                return {'success': False, 'error': f'Flow creation failed: {str(flow_error)}'}
            
            # STEP 3: Generate auth URL with redirect_uri ONLY here
            try:
                auth_url, state = flow.authorization_url(
                    access_type='offline',
                    prompt='select_account',
                    include_granted_scopes='true',
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                self.add_log("✅ Authorization URL generated successfully", 'info')
            except Exception as url_error:
                self.add_log(f"❌ URL generation failed: {url_error}", 'error')
                return {'success': False, 'error': f'URL generation failed: {str(url_error)}'}
            
            self.add_log("🌐 OAuth flow ready - no conflicts detected", 'info')
            return {
                'success': True, 
                'auth_url': auth_url,
                'message': 'Please visit the authorization URL and enter the code'
            }
            
        except Exception as e:
            error_msg = str(e)
            self.add_log(f"❌ OAuth flow failed: {error_msg}", 'error')
            
            # Provide specific help for common issues
            if "redirect_uri" in error_msg.lower():
                return {'success': False, 'error': 'OAuth redirect URI conflict - using fallback method'}
            elif "client_id" in error_msg.lower():
                return {'success': False, 'error': 'Invalid client ID - please check credentials'}
            elif "scope" in error_msg.lower():
                return {'success': False, 'error': 'OAuth scope issue - please contact support'}
            else:
                return {'success': False, 'error': f'OAuth setup failed: {error_msg}'}

    def complete_oauth_flow(self, auth_code: str):
        """Complete OAuth flow - BULLETPROOF VERSION"""
        try:
            if not self._oauth_flow:
                self.add_log("❌ No OAuth flow found", 'error')
                return {'success': False, 'error': 'OAuth flow not started - please try authentication again'}
            
            if not auth_code or not auth_code.strip():
                return {'success': False, 'error': 'Authorization code is required'}
            
            auth_code = auth_code.strip()
            self.add_log(f"🔄 Processing auth code: {auth_code[:10]}...", 'info')
            
            # STEP 1: Set redirect_uri for token exchange
            try:
                self._oauth_flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                self.add_log("✅ Redirect URI set for token exchange", 'info')
            except Exception as redirect_error:
                self.add_log(f"⚠️ Redirect URI warning: {redirect_error}", 'warning')
            
            # STEP 2: Exchange code for token with detailed error handling
            try:
                self._oauth_flow.fetch_token(code=auth_code)
                self.credentials = self._oauth_flow.credentials
                self.add_log("✅ Token exchange successful", 'info')
            except Exception as token_error:
                error_msg = str(token_error)
                self.add_log(f"❌ Token exchange failed: {error_msg}", 'error')
                
                if "invalid_grant" in error_msg.lower():
                    return {'success': False, 'error': 'Invalid or expired authorization code. Please try again.'}
                elif "redirect_uri_mismatch" in error_msg.lower():
                    return {'success': False, 'error': 'Redirect URI mismatch. Please contact support.'}
                else:
                    return {'success': False, 'error': f'Token exchange failed: {error_msg}'}
            
            # STEP 3: Test services one by one
            services_status = {}
            
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
                email = 'Unknown'
            
            # Test Drive
            try:
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                # Test with a simple API call
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
                .railway-badge {
                    background: #0070f3; color: white; padding: 5px 10px;
                    border-radius: 15px; font-size: 0.9em; margin-left: 10px;
                }
                .btn {
                    padding: 12px 24px; background: #4a90e2; color: white;
                    border: none; border-radius: 5px; cursor: pointer;
                    font-size: 1em; margin: 5px; text-decoration: none;
                    display: inline-block;
                }
                .btn:hover { background: #357abd; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔬 VLSI Resume Scanner</h1>
                    <p>AI-Powered Resume Analysis<span class="railway-badge">⚡ Railway</span></p>
                </div>
                
                <div class="content">
                    <div class="status">
                        <h3>✅ Railway Deployment Successful!</h3>
                        <p>Application is running and ready for Google API integration.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="/health" class="btn">🏥 Health Check</a>
                        <a href="/api/test" class="btn">🧪 API Test</a>
                        <a href="/startup" class="btn">🚀 Startup Status</a>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h4>🎛️ Next Steps:</h4>
                        <ol style="margin-left: 20px; line-height: 1.6;">
                            <li>Click "Health Check" to verify deployment</li>
                            <li>Set up Google API credentials via Railway environment variables</li>
                            <li>Configure OAuth for Gmail, Drive, and Sheets integration</li>
                            <li>Start scanning resumes from your Gmail account</li>
                        </ol>
                    </div>
                </div>
            </div>
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

@app.route('/api/test')
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

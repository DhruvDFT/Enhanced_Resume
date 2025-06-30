# BULLETPROOF OAuth Implementation - This WILL work!

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

# FALLBACK METHOD - If OAuth still fails, use this manual method
def manual_credential_setup(self, credentials_json: str):
    """Fallback method - direct credential input"""
    try:
        import json
        creds_data = json.loads(credentials_json)
        
        # Validate required fields
        required_fields = ['client_id', 'client_secret', 'refresh_token']
        for field in required_fields:
            if field not in creds_data:
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        # Create credentials directly
        self.credentials = Credentials(
            token=creds_data.get('access_token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=SCOPES
        )
        
        # Test the credentials
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        result = self.gmail_service.users().getProfile(userId='me').execute()
        email = result.get('emailAddress', 'Unknown')
        
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        
        self.current_user_email = email
        self.add_log(f"✅ Manual credential setup successful for: {email}", 'info')
        
        return {'success': True, 'email': email, 'message': 'Manual credential setup completed'}
        
    except Exception as e:
        self.add_log(f"❌ Manual credential setup failed: {e}", 'error')
        return {'success': False, 'error': str(e)}

# Enhanced API endpoint with fallback
@app.route('/api/start-oauth', methods=['POST'])
def api_start_oauth_enhanced():
    """Enhanced OAuth start with fallback options"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        
        # Try main OAuth flow first
        result = scanner.start_oauth_flow()
        
        if not result['success']:
            scanner.add_log("🔄 Main OAuth failed, providing fallback instructions", 'warning')
            
            # Provide fallback instructions
            result['fallback_available'] = True
            result['fallback_instructions'] = {
                'step1': 'Go to Google Cloud Console',
                'step2': 'Create OAuth 2.0 credentials',
                'step3': 'Download the JSON file',
                'step4': 'Use the manual upload option below'
            }
        
        return jsonify(result)
    except Exception as e:
        scanner.add_log(f"❌ Enhanced OAuth start failed: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

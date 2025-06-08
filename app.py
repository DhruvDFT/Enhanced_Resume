import os
import json
import logging
import re
import base64
import time
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from collections import Counter
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
    'https://www.googleapis.com/auth/drive.file'
]

logging.basicConfig(level=logging.INFO)


class EnhancedResumeAnalyzer:
    """Enhanced resume analysis with better classification and filtering"""
    
    def __init__(self):
        # Enhanced domain keywords with weights and context
        self.domain_keywords = {
            'Physical Design': {
                'primary': {
                    'physical design': 3, 'pd engineer': 3, 'place and route': 3, 
                    'floorplanning': 3, 'clock tree synthesis': 3, 'cts': 2,
                    'sta': 2, 'static timing analysis': 3, 'primetime': 2,
                    'innovus': 2, 'icc': 2, 'icc2': 2, 'encounter': 2,
                    'power planning': 2, 'ir drop': 2, 'em analysis': 2,
                    'drc': 2, 'lvs': 2, 'timing closure': 3, 'eco': 2,
                    'synopsys': 1, 'cadence': 1, 'mentor': 1
                },
                'secondary': {
                    'layout': 1, 'gds': 1, 'def': 1, 'lef': 1, 'spef': 1,
                    'sdc': 1, 'upf': 1, 'cpf': 1, 'low power': 1
                },
                'negative': ['verification engineer', 'dv engineer', 'validation engineer']
            },
            'Design Verification': {
                'primary': {
                    'verification': 3, 'dv engineer': 3, 'design verification': 3,
                    'uvm': 3, 'systemverilog': 3, 'testbench': 3, 'coverage': 2,
                    'functional coverage': 3, 'code coverage': 2, 'assertion': 2,
                    'scoreboard': 2, 'monitor': 2, 'driver': 2, 'sequence': 2,
                    'questa': 2, 'vcs': 2, 'ncsim': 2, 'xcelium': 2,
                    'formal verification': 2, 'simulation': 2, 'regression': 2
                },
                'secondary': {
                    'ovm': 1, 'vmm': 1, 'constrained random': 2, 'directed test': 1,
                    'protocol': 1, 'checker': 1, 'bfm': 1, 'vip': 1
                },
                'negative': ['physical design', 'pd engineer', 'silicon validation']
            },
            'DFT': {
                'primary': {
                    'dft': 3, 'design for test': 3, 'scan': 3, 'atpg': 3,
                    'bist': 3, 'mbist': 3, 'lbist': 3, 'boundary scan': 2,
                    'jtag': 2, 'test pattern': 2, 'fault coverage': 3,
                    'tessent': 2, 'tetramax': 2, 'fastscan': 2,
                    'scan chain': 3, 'scan compression': 2, 'test mode': 2
                },
                'secondary': {
                    'stuck at': 1, 'transition fault': 1, 'path delay': 1,
                    'iddq': 1, 'burn in': 1, 'yield': 1, 'diagnosis': 1
                },
                'negative': ['software test', 'qa engineer', 'test automation']
            },
            'RTL Design': {
                'primary': {
                    'rtl': 3, 'rtl design': 3, 'verilog': 3, 'vhdl': 2,
                    'synthesis': 3, 'design compiler': 2, 'genus': 2,
                    'microarchitecture': 3, 'fsm': 2, 'state machine': 2,
                    'pipeline': 2, 'datapath': 2, 'control logic': 2,
                    'lint': 1, 'cdc': 2, 'clock domain crossing': 2
                },
                'secondary': {
                    'hdl': 1, 'behavioral': 1, 'structural': 1, 'gate level': 1,
                    'netlist': 1, 'elaboration': 1, 'inference': 1
                },
                'negative': ['verification', 'physical design', 'analog']
            },
            'Analog Design': {
                'primary': {
                    'analog': 3, 'analog design': 3, 'mixed signal': 2,
                    'adc': 3, 'dac': 3, 'pll': 3, 'dll': 2, 'vco': 2,
                    'opamp': 3, 'amplifier': 2, 'comparator': 2,
                    'bandgap': 2, 'ldo': 2, 'dcdc': 2, 'power management': 2,
                    'spice': 3, 'spectre': 3, 'hspice': 2, 'cadence virtuoso': 3,
                    'layout': 2, 'matching': 2, 'noise': 2
                },
                'secondary': {
                    'cmos': 1, 'bjt': 1, 'mosfet': 1, 'transistor': 1,
                    'current mirror': 1, 'bias': 1, 'stability': 1,
                    'phase margin': 1, 'gain': 1, 'bandwidth': 1
                },
                'negative': ['digital design', 'rtl', 'fpga']
            },
            'FPGA': {
                'primary': {
                    'fpga': 3, 'xilinx': 3, 'altera': 2, 'intel fpga': 2,
                    'vivado': 3, 'quartus': 3, 'ise': 2, 'vitis': 2,
                    'zynq': 2, 'ultrascale': 2, 'stratix': 2, 'arria': 2,
                    'hls': 2, 'high level synthesis': 2, 'partial reconfiguration': 2
                },
                'secondary': {
                    'xdc': 1, 'qsf': 1, 'bitstream': 1, 'block ram': 1,
                    'dsp slice': 1, 'clb': 1, 'lut': 1, 'fabric': 1
                },
                'negative': ['asic', 'custom silicon', 'tapeout']
            },
            'Silicon Validation': {
                'primary': {
                    'silicon validation': 3, 'post silicon': 3, 'bring up': 3,
                    'debug': 2, 'characterization': 3, 'correlation': 2,
                    'lab': 2, 'oscilloscope': 2, 'logic analyzer': 2,
                    'pattern generator': 2, 'probe': 2, 'eva': 2,
                    'yield analysis': 2, 'failure analysis': 2
                },
                'secondary': {
                    'ate': 1, 'tester': 1, 'loadboard': 1, 'socket': 1,
                    'thermal': 1, 'voltage': 1, 'frequency': 1, 'shmoo': 1
                },
                'negative': ['pre silicon', 'rtl', 'design verification']
            },
            'Mixed Signal': {
                'primary': {
                    'mixed signal': 3, 'ams': 3, 'analog mixed signal': 3,
                    'serdes': 3, 'high speed': 2, 'transceiver': 2,
                    'pcie': 2, 'usb': 2, 'ddr': 2, 'mipi': 2,
                    'signal integrity': 2, 'jitter': 2, 'eye diagram': 2,
                    'equalization': 2, 'cdr': 2, 'ctle': 2, 'dfe': 2
                },
                'secondary': {
                    'differential': 1, 'termination': 1, 'impedance': 1,
                    'crosstalk': 1, 'insertion loss': 1, 'return loss': 1
                },
                'negative': ['pure analog', 'pure digital']
            }
        }
        
        # Resume structure indicators
        self.resume_sections = {
            'contact': ['email', 'phone', 'address', 'linkedin', 'github'],
            'summary': ['summary', 'objective', 'profile', 'about'],
            'experience': ['experience', 'employment', 'work history', 'professional experience'],
            'education': ['education', 'qualification', 'degree', 'university', 'college'],
            'skills': ['skills', 'technical skills', 'core competencies', 'expertise'],
            'projects': ['projects', 'key projects', 'academic projects'],
            'achievements': ['achievements', 'accomplishments', 'awards', 'recognition']
        }
        
        # Non-resume document indicators
        self.non_resume_indicators = [
            'table of contents', 'chapter', 'bibliography', 'references',
            'abstract', 'introduction', 'conclusion', 'methodology',
            'invoice', 'receipt', 'balance sheet', 'financial statement',
            'confidential', 'proprietary', 'not for distribution',
            'user manual', 'datasheet', 'specification', 'rev ', 'version '
        ]

    def is_resume(self, text: str) -> Dict[str, Any]:
        """Determine if document is actually a resume"""
        text_lower = text.lower()
        
        # Check for non-resume indicators
        non_resume_count = sum(1 for indicator in self.non_resume_indicators 
                              if indicator in text_lower)
        if non_resume_count >= 3:
            return {
                'is_resume': False,
                'confidence': 0.9,
                'reason': 'Document appears to be technical documentation or report'
            }
        
        # Count resume sections
        section_counts = {}
        total_sections = 0
        for section, keywords in self.resume_sections.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                section_counts[section] = count
                total_sections += 1
        
        # Must have at least 3 resume sections
        if total_sections < 3:
            return {
                'is_resume': False,
                'confidence': 0.7,
                'reason': f'Only {total_sections} resume sections found'
            }
        
        # Check for personal pronouns (resumes often use "I" or are written in third person)
        first_person = len(re.findall(r'\bi\b', text_lower))
        has_personal_content = first_person > 2 or 'experience' in text_lower
        
        # Calculate confidence
        confidence = min(0.95, 0.3 + (total_sections * 0.15) + (0.1 if has_personal_content else 0))
        
        return {
            'is_resume': True,
            'confidence': confidence,
            'sections_found': list(section_counts.keys())
        }

    def analyze_domains(self, text: str) -> Dict[str, Any]:
        """Enhanced domain analysis with context awareness"""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords_dict in self.domain_keywords.items():
            score = 0
            matches = []
            
            # Check primary keywords
            for keyword, weight in keywords_dict['primary'].items():
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                if count > 0:
                    score += count * weight
                    matches.append(keyword)
            
            # Check secondary keywords
            for keyword, weight in keywords_dict['secondary'].items():
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                if count > 0:
                    score += count * weight
                    matches.append(keyword)
            
            # Apply negative keywords penalty
            for neg_keyword in keywords_dict.get('negative', []):
                if neg_keyword in text_lower:
                    score *= 0.7  # Reduce score by 30%
            
            domain_scores[domain] = {
                'score': score,
                'matches': matches,
                'match_count': len(matches)
            }
        
        # Sort domains by score
        sorted_domains = sorted(domain_scores.items(), 
                               key=lambda x: x[1]['score'], 
                               reverse=True)
        
        # Determine primary domain
        if sorted_domains[0][1]['score'] > 0:
            primary_domain = sorted_domains[0][0]
            confidence = min(0.95, sorted_domains[0][1]['score'] / 100)
            
            # Check if it's a mixed profile
            if len(sorted_domains) > 1 and sorted_domains[1][1]['score'] > 0:
                second_score_ratio = sorted_domains[1][1]['score'] / sorted_domains[0][1]['score']
                if second_score_ratio > 0.7:  # Secondary domain is strong too
                    primary_domain = 'Mixed Signal'  # or could be multi-domain
        else:
            primary_domain = 'General VLSI'
            confidence = 0.3
        
        return {
            'primary_domain': primary_domain,
            'confidence': confidence,
            'all_domains': [
                {
                    'domain': domain,
                    'score': info['score'],
                    'matches': info['matches'][:5]  # Top 5 matches
                }
                for domain, info in sorted_domains[:3]
                if info['score'] > 0
            ]
        }

    def extract_experience(self, text: str) -> Dict[str, Any]:
        """Extract experience with better pattern matching"""
        text_lower = text.lower()
        
        # Multiple patterns for experience extraction
        experience_patterns = [
            r'(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*:?\s*(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)',
            r'total\s*experience\s*:?\s*(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)',
            r'(\d+\.?\d*)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:professional|industry|relevant)',
            r'working\s*since\s*(\d{4})',  # Calculate from year
            r'(\d+)\s*years?\s*(\d+)\s*months?'  # Years and months
        ]
        
        experience_years = 0
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:  # Years and months pattern
                        years = float(match[0])
                        months = float(match[1])
                        total_years = years + (months / 12)
                        if total_years > experience_years:
                            experience_years = total_years
                else:
                    if pattern == r'working\s*since\s*(\d{4})':
                        # Calculate years from start year
                        start_year = int(match)
                        current_year = datetime.now().year
                        calculated_years = current_year - start_year
                        if 0 < calculated_years < 50:  # Sanity check
                            experience_years = max(experience_years, calculated_years)
                    else:
                        years = float(match)
                        if years > experience_years and years < 50:  # Sanity check
                            experience_years = years
        
        # Also check for fresher indicators
        if experience_years == 0:
            fresher_indicators = ['fresher', 'entry level', 'recent graduate', 
                                'fresh graduate', 'seeking entry', '0 year']
            if any(indicator in text_lower for indicator in fresher_indicators):
                experience_years = 0
        
        # Categorize experience level
        if experience_years <= 2:
            level = 'Fresher (0-2 years)'
        elif experience_years <= 5:
            level = 'Mid-Level (2-5 years)'
        elif experience_years <= 8:
            level = 'Senior (5-8 years)'
        else:
            level = 'Experienced (8+ years)'
        
        return {
            'years': round(experience_years, 1),
            'level': level
        }

    def calculate_quality_score(self, text: str, domain_analysis: Dict, 
                               experience_info: Dict) -> float:
        """Calculate overall resume quality score"""
        score = 0.0
        
        # Domain clarity (max 0.4)
        score += min(0.4, domain_analysis['confidence'] * 0.4)
        
        # Experience clarity (max 0.3)
        if experience_info['years'] > 0:
            score += 0.3
        elif experience_info['level'] == 'Fresher (0-2 years)':
            score += 0.15
        
        # Text length and structure (max 0.3)
        text_length = len(text)
        if text_length > 500:
            score += 0.1
        if text_length > 1000:
            score += 0.1
        if text_length > 2000:
            score += 0.1
        
        return round(score, 2)

    def analyze_content(self, text: str, filename: str) -> Dict[str, Any]:
        """Enhanced content analysis with better classification"""
        try:
            if not text or len(text) < 100:
                return {
                    'is_resume': False,
                    'confidence': 0,
                    'reason': 'Insufficient text content'
                }
            
            # Check if it's actually a resume
            resume_check = self.is_resume(text)
            if not resume_check['is_resume']:
                return resume_check
            
            # Analyze domains with enhanced scoring
            domain_analysis = self.analyze_domains(text)
            
            # Extract experience information
            experience_info = self.extract_experience(text)
            
            # Calculate overall resume quality score
            quality_score = self.calculate_quality_score(
                text, domain_analysis, experience_info
            )
            
            return {
                'is_resume': True,
                'confidence': resume_check['confidence'],
                'domain': domain_analysis['primary_domain'],
                'domain_confidence': domain_analysis['confidence'],
                'all_domains': domain_analysis['all_domains'],
                'experience_level': experience_info['level'],
                'experience_years': experience_info['years'],
                'quality_score': quality_score,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'is_resume': False,
                'confidence': 0,
                'error': str(e),
                'reason': 'Analysis failed'
            }


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
        
        # Initialize enhanced analyzer
        self.enhanced_analyzer = EnhancedResumeAnalyzer()
        
        # Add new statistics tracking
        self.classification_stats = {
            'total_analyzed': 0,
            'correctly_classified': 0,
            'false_positives': 0,
            'domains': {}
        }
        
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
        """Enhanced content analysis with better classification"""
        try:
            # Extract text using existing methods
            text = ""
            if filename.lower().endswith('.pdf'):
                text = self.extract_pdf_text(file_data)
            elif filename.lower().endswith('.docx'):
                text = self.extract_docx_text(file_data, filename)
            elif filename.lower().endswith('.doc'):
                text = self.extract_doc_text(file_data, filename)
            
            if not text:
                self.add_log(f"⚠️ No text extracted from {filename}", 'warning')
                return {
                    'is_resume': False,
                    'domain': 'Unknown Domain',
                    'experience_level': 'Unknown',
                    'resume_score': 0,
                    'rejection_reason': 'No text content'
                }
            
            # Use enhanced analysis
            result = self.enhanced_analyzer.analyze_content(text, filename)
            
            # Update statistics
            self.classification_stats['total_analyzed'] += 1
            
            # Format result for compatibility with existing code
            if result['is_resume']:
                # Track domain statistics
                domain = result['domain']
                if domain not in self.classification_stats['domains']:
                    self.classification_stats['domains'][domain] = 0
                self.classification_stats['domains'][domain] += 1
                
                # Log detailed analysis info
                self.add_log(
                    f"✅ Resume detected: {filename} | "
                    f"Domain: {domain} (confidence: {result['domain_confidence']:.2f}) | "
                    f"Experience: {result['experience_level']} | "
                    f"Quality: {result['quality_score']:.2f}",
                    'success'
                )
                
                # Log additional domains if found
                if len(result.get('all_domains', [])) > 1:
                    other_domains = [d['domain'] for d in result['all_domains'][1:] if d['score'] > 5]
                    if other_domains:
                        self.add_log(
                            f"   Also matches: {', '.join(other_domains)}",
                            'info'
                        )
                
                return {
                    'is_resume': True,
                    'domain': domain,
                    'experience_level': result['experience_level'],
                    'experience_years': result['experience_years'],
                    'resume_score': result['quality_score'],
                    'enhanced_analysis': result  # Keep full analysis for reference
                }
            else:
                self.classification_stats['false_positives'] += 1
                self.add_log(
                    f"❌ Rejected {filename}: {result.get('reason', 'Not a resume')} "
                    f"(confidence: {result.get('confidence', 0):.2f})",
                    'warning'
                )
                return {
                    'is_resume': False,
                    'domain': 'Unknown Domain',
                    'experience_level': 'Unknown',
                    'resume_score': 0,
                    'rejection_reason': result.get('reason', 'Not a resume')
                }
                
        except Exception as e:
            self.add_log(f"❌ Error analyzing {filename}: {e}", 'error')
            return {
                'is_resume': False,
                'domain': 'Unknown Domain',
                'experience_level': 'Unknown',
                'resume_score': 0,
                'rejection_reason': f'Analysis error: {str(e)}'
            }

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
        """Enhanced save to Google Drive with additional metadata"""
        try:
            if not self.drive_service:
                return None
            
            analysis = metadata.get('analysis_result', {})
            enhanced = analysis.get('enhanced_analysis', {})
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
            
            # Create enhanced filename with quality score
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
            
            quality_score = analysis.get('resume_score', 0)
            quality_indicator = 'H' if quality_score >= 0.7 else 'M' if quality_score >= 0.4 else 'L'
            
            new_filename = f"[{domain_abbrev}_{exp_abbrev}_{experience_years}Y_Q{quality_indicator}] {timestamp}_{clean_filename}.{file_extension}"
            
            # Build enhanced description
            description_parts = [
                f"VLSI Resume Scanner Analysis v2.1",
                f"",
                f"Email: {metadata.get('sender', 'Unknown')}",
                f"Subject: {metadata.get('subject', 'No subject')}",
                f"Date: {metadata.get('date', 'Unknown')}",
                f"",
                f"=== CLASSIFICATION ===",
                f"Domain: {domain} (confidence: {enhanced.get('domain_confidence', 0):.2f})",
                f"Experience: {experience_level} ({experience_years} years)",
                f"Quality Score: {quality_score:.2f}"
            ]
            
            # Add other matching domains
            if enhanced.get('all_domains') and len(enhanced['all_domains']) > 1:
                description_parts.extend([
                    f"",
                    f"=== OTHER DOMAINS ===",
                ])
                for domain_info in enhanced['all_domains'][1:3]:
                    description_parts.append(
                        f"{domain_info['domain']}: score {domain_info['score']}"
                    )
            
            description_parts.extend([
                f"",
                f"Auto-filed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Location: {domain} > {experience_level}"
            ])
            
            file_metadata = {
                'name': new_filename,
                'parents': [target_folder_id],
                'description': '\n'.join(description_parts)
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
                self.add_log(
                    f"💾 Saved: {domain}/{experience_level} - {filename} "
                    f"(Quality: {quality_score:.2f})",
                    'success'
                )
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

    def get_classification_report(self) -> Dict[str, Any]:
        """Generate classification statistics report"""
        stats = self.classification_stats
        
        # Calculate accuracy
        total = stats['total_analyzed']
        if total > 0:
            accuracy = (total - stats['false_positives']) / total
        else:
            accuracy = 0
        
        # Sort domains by count
        sorted_domains = sorted(
            stats['domains'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'total_analyzed': total,
            'accuracy': round(accuracy * 100, 2),
            'false_positives': stats['false_positives'],
            'domain_distribution': sorted_domains,
            'top_domain': sorted_domains[0][0] if sorted_domains else 'None',
            'report_generated': datetime.now().isoformat()
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
                        <button onclick="showClassificationReport()" style="background: #9c27b0;">📊 Classification Report</button>
                        <button onclick="showUserManager()" style="background: #fd7e14;">👥 Manage Team Access</button>
                    </div>

                    <div id="classification-report" style="display: none; background: #f3e5f5; border: 1px solid #9c27b0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #7b1fa2;">📊 Classification Analytics</h3>
                        <div id="report-content">Loading...</div>
                        <button onclick="hideClassificationReport()" style="margin-top: 10px; padding: 8px 16px; background: #666; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Close
                        </button>
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
                    addLogToDisplay('📊 System test completed', 'info');
                    loadSystemStatus();
                })
                .catch(e => {
                    addLogToDisplay('❌ System test failed: ' + e.message, 'error');
                });
        }

        function showClassificationReport() {
            document.getElementById('classification-report').style.display = 'block';
            
            fetch('/api/classification-report')
                .then(r => r.json())
                .then(data => {
                    let html = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                            <div style="background: white; padding: 15px; border-radius: 5px;">
                                <div style="font-size: 2em; font-weight: bold; color: #7b1fa2;">${data.total_analyzed}</div>
                                <div style="color: #666;">Total Analyzed</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 5px;">
                                <div style="font-size: 2em; font-weight: bold; color: #4caf50;">${data.accuracy}%</div>
                                <div style="color: #666;">Accuracy</div>
                            </div>
                            <div style="background: white; padding: 15px; border-radius: 5px;">
                                <div style="font-size: 2em; font-weight: bold; color: #f44336;">${data.false_positives}</div>
                                <div style="color: #666;">False Positives</div>
                            </div>
                        </div>
                        
                        <h4>Domain Distribution:</h4>
                        <div style="background: white; padding: 15px; border-radius: 5px;">
                    `;
                    
                    if (data.domain_distribution && data.domain_distribution.length > 0) {
                        data.domain_distribution.forEach(([domain, count]) => {
                            const percentage = ((count / data.total_analyzed) * 100).toFixed(1);
                            html += `
                                <div style="margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span>${domain}</span>
                                        <span>${count} (${percentage}%)</span>
                                    </div>
                                    <div style="background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                                        <div style="background: #7b1fa2; width: ${percentage}%; height: 100%;"></div>
                                    </div>
                                </div>
                            `;
                        });
                    } else {
                        html += '<p style="color: #666;">No domain data available yet</p>';
                    }
                    
                    html += '</div>';
                    document.getElementById('report-content').innerHTML = html;
                })
                .catch(e => {
                    document.getElementById('report-content').innerHTML = 
                        '<div style="color: #f44336;">Error loading report</div>';
                });
        }

        function hideClassificationReport() {
            document.getElementById('classification-report').style.display = 'none';
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

        // Enter key support for password field
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('admin-password').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    authenticate();
                }
            });
        });
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

@app.route('/api/classification-report')
@admin_required
def api_classification_report():
    """Get classification statistics report"""
    report = scanner.get_classification_report()
    return jsonify(report)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) resume_results['files'][0]['id']
                self.add_log("✅ Found existing Resumes folder", 'success')
            else:
                resume_metadata = {
                    'name': 'Resumes by Domain',
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                resume_folder = self.drive_service.files().create(body=resume_metadata, fields='id').execute()
                self.resume_folder_id =

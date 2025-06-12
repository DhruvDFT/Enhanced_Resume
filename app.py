# GOOGLE SHEETS INTEGRATION EXTENSION
# Add this to your existing app.py

import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Update SCOPES to include Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'  # Add this line
]

class EnhancedVLSIResumeScanner(VLSIResumeScanner):
    def __init__(self):
        super().__init__()
        self.sheets_service = None
        self.resume_sheet_id = None
        self.contact_sheet_id = None
        self.skills_sheet_id = None
        self.main_spreadsheet_id = None
        
    def _test_credentials(self) -> bool:
        """Test credentials including Sheets API"""
        try:
            # Test Gmail and Drive (existing code)
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
            # Simple test call
            self.sheets_service.spreadsheets().get(spreadsheetId='test').execute()
            
        except Exception as e:
            if "not found" in str(e).lower():
                # This is expected for the test spreadsheet
                self.add_log(f"✅ Sheets access confirmed", 'success')
            else:
                self.add_log(f"❌ Sheets API test failed: {e}", 'error')
                return False
            
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(self.credentials.to_json())
        self.add_log("💾 Saved authentication token", 'success')
        
        self.current_user_email = email
        self.user_credentials[email] = self.credentials
        
        return True

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
                    },
                    {
                        'properties': {
                            'title': 'Skills Matrix',
                            'gridProperties': {'rowCount': 1000, 'columnCount': 25}
                        }
                    },
                    {
                        'properties': {
                            'title': 'Experience Details',
                            'gridProperties': {'rowCount': 1000, 'columnCount': 20}
                        }
                    }
                ]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            self.main_spreadsheet_id = spreadsheet['spreadsheetId']
            self.add_log(f"✅ Created main spreadsheet: {self.main_spreadsheet_id}", 'success')
            
            # Setup headers for each sheet
            self._setup_sheet_headers()
            
            # Move spreadsheet to VLSI Resume Scanner folder
            self._move_spreadsheet_to_folder()
            
            return True
            
        except Exception as e:
            self.add_log(f"❌ Sheets setup failed: {e}", 'error')
            return False

    def _setup_sheet_headers(self):
        """Setup headers for all sheets"""
        try:
            # Resume Summary headers
            resume_headers = [
                'ID', 'Timestamp', 'Name', 'Email', 'Phone', 'Domain', 
                'Experience Level', 'Experience Years', 'Education', 'Current Company',
                'Current Role', 'Location', 'Resume Score', 'Key Skills', 
                'Certifications', 'Projects', 'File Name', 'Drive File ID', 
                'Source Email', 'Processing Status'
            ]
            
            # Contact Details headers
            contact_headers = [
                'ID', 'Name', 'Primary Email', 'Secondary Email', 'Phone 1', 
                'Phone 2', 'LinkedIn', 'GitHub', 'Portfolio', 'Address',
                'City', 'State', 'Country', 'Postal Code', 'Last Updated'
            ]
            
            # Skills Matrix headers
            skills_headers = [
                'ID', 'Name', 'Domain', 'Programming Languages', 'Tools & Software',
                'Methodologies', 'Protocols', 'Operating Systems', 'Databases',
                'Cloud Platforms', 'Certifications', 'Years in Domain',
                'Physical Design Skills', 'Verification Skills', 'DFT Skills',
                'RTL Skills', 'Analog Skills', 'FPGA Skills', 'Silicon Val Skills',
                'Mixed Signal Skills', 'Management Skills', 'Other Skills',
                'Skill Level', 'Last Updated'
            ]
            
            # Experience Details headers
            experience_headers = [
                'ID', 'Name', 'Company', 'Role', 'Start Date', 'End Date',
                'Duration', 'Description', 'Key Achievements', 'Technologies Used',
                'Domain Focus', 'Team Size', 'Reporting Manager', 'Employment Type',
                'Location', 'Salary Range', 'Industry', 'Company Size',
                'Notable Projects', 'Last Updated'
            ]
            
            # Batch update all headers
            requests = []
            
            # Resume Summary headers
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': 0,  # Resume Summary sheet
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': len(resume_headers)
                    },
                    'rows': [{
                        'values': [{'userEnteredValue': {'stringValue': header}} for header in resume_headers]
                    }],
                    'fields': 'userEnteredValue'
                }
            })
            
            # Contact Details headers  
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': self._get_sheet_id('Contact Details'),
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': len(contact_headers)
                    },
                    'rows': [{
                        'values': [{'userEnteredValue': {'stringValue': header}} for header in contact_headers]
                    }],
                    'fields': 'userEnteredValue'
                }
            })
            
            # Skills Matrix headers
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': self._get_sheet_id('Skills Matrix'),
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': len(skills_headers)
                    },
                    'rows': [{
                        'values': [{'userEnteredValue': {'stringValue': header}} for header in skills_headers]
                    }],
                    'fields': 'userEnteredValue'
                }
            })
            
            # Experience Details headers
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': self._get_sheet_id('Experience Details'),
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': len(experience_headers)
                    },
                    'rows': [{
                        'values': [{'userEnteredValue': {'stringValue': header}} for header in experience_headers]
                    }],
                    'fields': 'userEnteredValue'
                }
            })
            
            # Apply formatting
            requests.extend(self._get_formatting_requests())
            
            # Execute batch update
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.main_spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            self.add_log("✅ Sheet headers configured", 'success')
            
        except Exception as e:
            self.add_log(f"❌ Header setup failed: {e}", 'error')

    def _get_sheet_id(self, sheet_name: str) -> int:
        """Get sheet ID by name"""
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.main_spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            return 0
        except:
            return 0

    def _get_formatting_requests(self) -> List[Dict]:
        """Get formatting requests for headers"""
        return [
            # Bold headers and freeze rows
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True},
                            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {'frozenRowCount': 1}
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }
        ]

    def _move_spreadsheet_to_folder(self):
        """Move spreadsheet to VLSI Resume Scanner folder"""
        try:
            if self.resume_folder_id:
                self.drive_service.files().update(
                    fileId=self.main_spreadsheet_id,
                    addParents=self.resume_folder_id,
                    fields='id,parents'
                ).execute()
                self.add_log("📁 Moved spreadsheet to resume folder", 'success')
        except Exception as e:
            self.add_log(f"⚠️ Could not move spreadsheet: {e}", 'warning')

    def enhanced_analyze_content(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Enhanced content analysis with detailed parsing"""
        try:
            text = ""
            
            # Extract text (existing code)
            if filename.lower().endswith('.pdf'):
                text = self.extract_pdf_text(file_data)
            elif filename.lower().endswith('.docx'):
                text = self.extract_docx_text(file_data, filename)
            elif filename.lower().endswith('.doc'):
                text = self.extract_doc_text(file_data, filename)
            
            if not text:
                return {'is_resume': False}
            
            # Basic resume validation (existing code)
            basic_analysis = super().analyze_content(file_data, filename)
            if not basic_analysis.get('is_resume', False):
                return basic_analysis
            
            # Enhanced parsing
            parsed_data = self._parse_resume_details(text, filename)
            
            # Merge basic analysis with detailed parsing
            result = {**basic_analysis, **parsed_data}
            
            return result
            
        except Exception as e:
            self.add_log(f"❌ Enhanced analysis failed for {filename}: {e}", 'error')
            return {'is_resume': False}

    def _parse_resume_details(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse detailed information from resume text"""
        text_lower = text.lower()
        lines = text.split('\n')
        
        parsed_data = {
            'name': self._extract_name(text, lines),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'location': self._extract_location(text),
            'linkedin': self._extract_linkedin(text),
            'github': self._extract_github(text),
            'education': self._extract_education(text),
            'current_company': self._extract_current_company(text),
            'current_role': self._extract_current_role(text),
            'skills': self._extract_skills(text),
            'certifications': self._extract_certifications(text),
            'projects': self._extract_projects(text),
            'experience_details': self._extract_experience_details(text),
            'programming_languages': self._extract_programming_languages(text),
            'tools_software': self._extract_tools_software(text)
        }
        
        return parsed_data

    def _extract_name(self, text: str, lines: List[str]) -> str:
        """Extract candidate name"""
        try:
            # Look for name patterns in first few lines
            for i, line in enumerate(lines[:5]):
                line = line.strip()
                if len(line) > 2 and len(line) < 50:
                    # Skip common headers
                    skip_patterns = ['resume', 'cv', 'curriculum vitae', 'profile', 'email', 'phone', '@']
                    if not any(pattern in line.lower() for pattern in skip_patterns):
                        # Check if it looks like a name (2-4 words, mostly alphabetic)
                        words = line.split()
                        if 2 <= len(words) <= 4 and all(word.replace('-', '').replace("'", '').isalpha() for word in words):
                            return line.title()
            
            # Fallback: look for name patterns
            name_patterns = [
                r'name\s*:?\s*([a-zA-Z\s\-\']+)',
                r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).strip().title()
                    
            return "Not Found"
        except:
            return "Not Found"

    def _extract_email(self, text: str) -> str:
        """Extract email address"""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            return emails[0] if emails else "Not Found"
        except:
            return "Not Found"

    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        try:
            phone_patterns = [
                r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'(\+\d{1,3}[-.\s]?)?\d{10}',
                r'(\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(0).strip()
            return "Not Found"
        except:
            return "Not Found"

    def _extract_location(self, text: str) -> str:
        """Extract location/address"""
        try:
            location_patterns = [
                r'(?:address|location|based in|residing in)\s*:?\s*([^,\n]+(?:,\s*[^,\n]+)*)',
                r'([A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5})',
                r'([A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+)'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return "Not Found"
        except:
            return "Not Found"

    def _extract_linkedin(self, text: str) -> str:
        """Extract LinkedIn profile"""
        try:
            linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/pub/)([A-Za-z0-9\-]+)'
            match = re.search(linkedin_pattern, text, re.IGNORECASE)
            return f"linkedin.com/in/{match.group(1)}" if match else "Not Found"
        except:
            return "Not Found"

    def _extract_github(self, text: str) -> str:
        """Extract GitHub profile"""
        try:
            github_pattern = r'(?:github\.com/)([A-Za-z0-9\-]+)'
            match = re.search(github_pattern, text, re.IGNORECASE)
            return f"github.com/{match.group(1)}" if match else "Not Found"
        except:
            return "Not Found"

    def _extract_education(self, text: str) -> str:
        """Extract education details"""
        try:
            education_keywords = ['education', 'qualification', 'academic', 'degree', 'university', 'college']
            lines = text.split('\n')
            
            education_section = []
            in_education_section = False
            
            for line in lines:
                line_lower = line.lower().strip()
                
                # Check if we're entering education section
                if any(keyword in line_lower for keyword in education_keywords) and len(line_lower) < 30:
                    in_education_section = True
                    continue
                
                # Check if we're leaving education section
                if in_education_section and any(keyword in line_lower for keyword in ['experience', 'work', 'employment', 'skills', 'projects']):
                    break
                
                # Collect education lines
                if in_education_section and line.strip() and len(line.strip()) > 5:
                    education_section.append(line.strip())
                    if len(education_section) >= 3:  # Limit to prevent overly long text
                        break
            
            return ' | '.join(education_section) if education_section else "Not Found"
        except:
            return "Not Found"

    def _extract_current_company(self, text: str) -> str:
        """Extract current company"""
        try:
            # Look for recent/current employment patterns
            company_patterns = [
                r'(?:currently|present|current)[\s\w]*(?:at|with)\s+([A-Za-z\s&,.-]+?)(?:\s*[\n|,])',
                r'(\w+(?:\s+\w+)*)\s*(?:\(|\|)\s*(?:current|present|now)',
                r'(?:working at|employed at|at)\s+([A-Za-z\s&,.-]+?)(?:\s*[\n|,])'
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    if len(company) > 2 and len(company) < 50:
                        return company
            
            return "Not Found"
        except:
            return "Not Found"

    def _extract_current_role(self, text: str) -> str:
        """Extract current role/position"""
        try:
            role_patterns = [
                r'(?:current role|current position|currently)\s*:?\s*([^,\n]+)',
                r'(?:working as|employed as)\s+([^,\n]+)',
                r'(\w+\s+engineer|\w+\s+designer|\w+\s+architect|\w+\s+manager)'
            ]
            
            for pattern in role_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    role = match.group(1).strip()
                    if len(role) > 5 and len(role) < 50:
                        return role.title()
            
            return "Not Found"
        except:
            return "Not Found"

    def _extract_skills(self, text: str) -> str:
        """Extract technical skills"""
        try:
            # VLSI-specific skills
            vlsi_skills = [
                'verilog', 'vhdl', 'systemverilog', 'synthesis', 'sta', 'primetime',
                'innovus', 'encounter', 'icc', 'icc2', 'design compiler', 'genus',
                'uvm', 'testbench', 'coverage', 'assertion', 'questa', 'vcs',
                'dft', 'scan', 'atpg', 'bist', 'mbist', 'tetramax', 'tessent',
                'fpga', 'xilinx', 'altera', 'vivado', 'quartus', 'zynq',
                'spice', 'spectre', 'cadence', 'mentor', 'synopsys',
                'physical design', 'place and route', 'floorplanning', 'cts'
            ]
            
            found_skills = []
            text_lower = text.lower()
            
            for skill in vlsi_skills:
                if skill in text_lower:
                    found_skills.append(skill.upper())
            
            return ', '.join(found_skills) if found_skills else "Not Found"
        except:
            return "Not Found"

    def _extract_programming_languages(self, text: str) -> str:
        """Extract programming languages"""
        try:
            languages = ['python', 'c++', 'c', 'java', 'perl', 'tcl', 'shell', 'bash', 'matlab', 'r']
            found_languages = []
            text_lower = text.lower()
            
            for lang in languages:
                if lang in text_lower:
                    found_languages.append(lang.title())
            
            return ', '.join(found_languages) if found_languages else "Not Found"
        except:
            return "Not Found"

    def _extract_tools_software(self, text: str) -> str:
        """Extract tools and software"""
        try:
            tools = [
                'cadence', 'synopsys', 'mentor', 'xilinx', 'altera', 'intel',
                'vivado', 'quartus', 'modelsim', 'questa', 'vcs', 'ncsim',
                'primetime', 'innovus', 'encounter', 'icc', 'design compiler'
            ]
            
            found_tools = []
            text_lower = text.lower()
            
            for tool in tools:
                if tool in text_lower:
                    found_tools.append(tool.title())
            
            return ', '.join(found_tools) if found_tools else "Not Found"
        except:
            return "Not Found"

    def _extract_certifications(self, text: str) -> str:
        """Extract certifications"""
        try:
            cert_patterns = [
                r'(?:certification|certified|certificate)\s*:?\s*([^,\n]+)',
                r'(?:pmp|ccna|aws|azure|google cloud|oracle)(?:\s+certified)?'
            ]
            
            certifications = []
            for pattern in cert_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                certifications.extend(matches)
            
            return ', '.join(certifications) if certifications else "Not Found"
        except:
            return "Not Found"

    def _extract_projects(self, text: str) -> str:
        """Extract project information"""
        try:
            project_keywords = ['project', 'projects worked', 'key projects', 'notable projects']
            lines = text.split('\n')
            
            projects = []
            in_project_section = False
            
            for line in lines:
                line_lower = line.lower().strip()
                
                if any(keyword in line_lower for keyword in project_keywords) and len(line_lower) < 30:
                    in_project_section = True
                    continue
                
                if in_project_section and any(keyword in line_lower for keyword in ['experience', 'education', 'skills']):
                    break
                
                if in_project_section and line.strip() and len(line.strip()) > 10:
                    projects.append(line.strip())
                    if len(projects) >= 2:  # Limit to prevent overly long text
                        break
            
            return ' | '.join(projects) if projects else "Not Found"
        except:
            return "Not Found"

    def _extract_experience_details(self, text: str) -> List[Dict]:
        """Extract detailed experience information"""
        try:
            # This is a simplified version - can be enhanced further
            experience_patterns = [
                r'(\d{4})\s*[-–]\s*(?:(\d{4})|(?:present|current))\s*:?\s*([^,\n]+?)(?:\s*at\s*)?([^,\n]+)',
                r'([A-Za-z\s&,.-]+?)\s*(?:\(|\|)\s*(\d{4})\s*[-–]\s*(?:(\d{4})|(?:present|current))'
            ]
            
            experiences = []
            for pattern in experience_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 3:
                        experiences.append({
                            'start_year': match[0] if match[0].isdigit() else '',
                            'end_year': match[1] if len(match) > 1 and match[1].isdigit() else 'Present',
                            'role': match[2] if len(match) > 2 else '',
                            'company': match[3] if len(match) > 3 else ''
                        })
            
            return experiences
        except:
            return []

    def write_to_sheets(self, resume_data: Dict[str, Any], email_metadata: Dict[str, Any]) -> bool:
        """Write parsed resume data to Google Sheets"""
        try:
            if not self.sheets_service or not self.main_spreadsheet_id:
                self.add_log("❌ Sheets service not available", 'error')
                return False
            
            # Generate unique ID
            resume_id = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare Resume Summary data
            resume_row = [
                resume_id,
                timestamp,
                resume_data.get('name', 'Not Found'),
                resume_data.get('email', 'Not Found'),
                resume_data.get('phone', 'Not Found'),
                resume_data.get('domain', 'Unknown Domain'),
                resume_data.get('experience_level', 'Unknown'),
                resume_data.get('experience_years', 0),
                resume_data.get('education', 'Not Found'),
                resume_data.get('current_company', 'Not Found'),
                resume_data.get('current_role', 'Not Found'),
                resume_data.get('location', 'Not Found'),
                resume_data.get('resume_score', 0),
                resume_data.get('skills', 'Not Found'),
                resume_data.get('certifications', 'Not Found'),
                resume_data.get('projects', 'Not Found'),
                email_metadata.get('filename', 'Unknown'),
                email_metadata.get('drive_file_id', ''),
                email_metadata.get('sender', 'Unknown'),
                'Processed'
            ]
            
            # Write to Resume Summary sheet
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.main_spreadsheet_id,
                range='Resume Summary!A:T',
                valueInputOption='USER_ENTERED',
                body={'values': [resume_row]}
            ).execute()
            
            # Write to Contact Details sheet
            contact_row = [
                resume_id,
                resume_data.get('name', 'Not Found'),
                resume_data.get('email', 'Not Found'),
                '',  # Secondary Email
                resume_data.get('phone', 'Not Found'),
                '',  # Phone 2
                resume_data.get('linkedin', 'Not Found'),
                resume_data.get('github', 'Not Found'),
                '',  # Portfolio
                resume_data.get('location', 'Not Found'),
                '',  # City
                '',  # State
                '',  # Country
                '',  # Postal Code
                timestamp
            ]
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.main_spreadsheet_id,
                range='Contact Details!A:O',
                valueInputOption='USER_ENTERED',
                body={'values': [contact_row]}
            ).execute()
            
            # Write to Skills Matrix sheet
            skills_row = [
                resume_id,
                resume_data.get('name', 'Not Found'),
                resume_data.get('domain', 'Unknown Domain'),
                resume_data.get('programming_languages', 'Not Found'),
                resume_data.get('tools_software', 'Not Found'),
                '',  # Methodologies
                '',  # Protocols
                '',  # Operating Systems
                '',  # Databases
                '',  # Cloud Platforms
                resume_data.get('certifications', 'Not Found'),
                resume_data.get('experience_years', 0),
                self._extract_domain_specific_skills(resume_data, 'Physical Design'),
                self._extract_domain_specific_skills(resume_data, 'Design Verification'),
                self._extract_domain_specific_skills(resume_data, 'DFT'),
                self._extract_domain_specific_skills(resume_data, 'RTL Design'),
                self._extract_domain_specific_skills(resume_data, 'Analog Design'),
                self._extract_domain_specific_skills(resume_data, 'FPGA'),
                self._extract_domain_specific_skills(resume_data, 'Silicon Validation'),
                self._extract_domain_specific_skills(resume_data, 'Mixed Signal'),
                '',  # Management Skills
                resume_data.get('skills', 'Not Found'),
                self._calculate_skill_level(resume_data),
                timestamp
            ]
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.main_spreadsheet_id,
                range='Skills Matrix!A:X',
                valueInputOption='USER_ENTERED',
                body={'values': [skills_row]}
            ).execute()
            
            # Write experience details if available
            experience_details = resume_data.get('experience_details', [])
            for exp in experience_details[:3]:  # Limit to 3 most recent
                exp_row = [
                    resume_id,
                    resume_data.get('name', 'Not Found'),
                    exp.get('company', 'Not Found'),
                    exp.get('role', 'Not Found'),
                    exp.get('start_year', ''),
                    exp.get('end_year', ''),
                    self._calculate_duration(exp.get('start_year', ''), exp.get('end_year', '')),
                    '',  # Description
                    '',  # Key Achievements
                    resume_data.get('tools_software', 'Not Found'),
                    resume_data.get('domain', 'Unknown Domain'),
                    '',  # Team Size
                    '',  # Reporting Manager
                    '',  # Employment Type
                    resume_data.get('location', 'Not Found'),
                    '',  # Salary Range
                    '',  # Industry
                    '',  # Company Size
                    '',  # Notable Projects
                    timestamp
                ]
                
                self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.main_spreadsheet_id,
                    range='Experience Details!A:T',
                    valueInputOption='USER_ENTERED',
                    body={'values': [exp_row]}
                ).execute()
            
            self.add_log(f"📊 Resume data written to sheets: {resume_data.get('name', 'Unknown')}", 'success')
            return True
            
        except Exception as e:
            self.add_log(f"❌ Failed to write to sheets: {e}", 'error')
            return False

    def _extract_domain_specific_skills(self, resume_data: Dict, domain: str) -> str:
        """Extract domain-specific skills"""
        skills_text = resume_data.get('skills', '').lower()
        
        domain_skills = {
            'Physical Design': ['place and route', 'floorplanning', 'sta', 'timing closure', 'cts', 'power planning'],
            'Design Verification': ['uvm', 'systemverilog', 'testbench', 'coverage', 'assertion', 'scoreboard'],
            'DFT': ['scan', 'atpg', 'bist', 'mbist', 'jtag', 'boundary scan'],
            'RTL Design': ['verilog', 'vhdl', 'synthesis', 'fsm', 'microarchitecture'],
            'Analog Design': ['spice', 'spectre', 'opamp', 'pll', 'adc', 'dac'],
            'FPGA': ['xilinx', 'altera', 'vivado', 'quartus', 'zynq'],
            'Silicon Validation': ['bring up', 'characterization', 'lab', 'debug'],
            'Mixed Signal': ['serdes', 'high speed', 'signal integrity', 'jitter']
        }
        
        found_skills = []
        for skill in domain_skills.get(domain, []):
            if skill in skills_text:
                found_skills.append(skill.title())
        
        return ', '.join(found_skills) if found_skills else ''

    def _calculate_skill_level(self, resume_data: Dict) -> str:
        """Calculate overall skill level based on experience and skills"""
        experience_years = resume_data.get('experience_years', 0)
        skills_count = len(resume_data.get('skills', '').split(','))
        
        if experience_years >= 8 or skills_count >= 15:
            return 'Expert'
        elif experience_years >= 5 or skills_count >= 10:
            return 'Advanced'
        elif experience_years >= 2 or skills_count >= 5:
            return 'Intermediate'
        else:
            return 'Beginner'

    def _calculate_duration(self, start_year: str, end_year: str) -> str:
        """Calculate duration between start and end years"""
        try:
            if start_year and start_year.isdigit():
                start = int(start_year)
                if end_year and end_year.isdigit():
                    end = int(end_year)
                elif end_year.lower() in ['present', 'current']:
                    end = datetime.now().year
                else:
                    return ''
                
                duration = end - start
                if duration == 0:
                    return '< 1 year'
                elif duration == 1:
                    return '1 year'
                else:
                    return f'{duration} years'
            return ''
        except:
            return ''

    def process_email_with_sheets(self, message_id: str) -> Dict[str, Any]:
        """Enhanced email processing with sheets integration"""
        try:
            # Get basic email processing result
            result = self.process_email(message_id)
            
            if result.get('has_resume', False):
                # For each processed attachment, write to sheets
                for attachment in result.get('attachments', []):
                    if attachment.get('drive_file_id'):
                        # Get the analysis result from the attachment processing
                        resume_data = {
                            'domain': attachment.get('domain', 'Unknown Domain'),
                            'experience_level': attachment.get('experience', 'Unknown'),
                            'resume_score': attachment.get('score', 0),
                            'name': 'Extracted from file',  # This would be enhanced in real implementation
                            'email': 'Not Found',
                            'phone': 'Not Found'
                        }
                        
                        email_metadata = {
                            'filename': attachment.get('filename', 'Unknown'),
                            'drive_file_id': attachment.get('drive_file_id', ''),
                            'sender': result.get('sender', 'Unknown'),
                            'subject': result.get('subject', 'No Subject'),
                            'date': result.get('date', '')
                        }
                        
                        # Write to sheets
                        self.write_to_sheets(resume_data, email_metadata)
            
            return result
            
        except Exception as e:
            self.add_log(f"❌ Error in enhanced email processing: {e}", 'error')
            return {'message_id': message_id, 'error': str(e)}

    def scan_emails_with_sheets(self, max_results: int = None) -> Dict[str, Any]:
        """Enhanced email scanning with sheets integration"""
        try:
            if not self.gmail_service:
                return {'success': False, 'error': 'Gmail service not available'}
            
            # Ensure sheets are set up
            if not self.main_spreadsheet_id:
                if not self.setup_sheets_integration():
                    return {'success': False, 'error': 'Failed to setup sheets integration'}
            
            self.add_log(f"🔍 Starting enhanced Gmail scan with sheets integration", 'info')
            
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
            sheets_entries = 0
            
            for i, message in enumerate(messages, 1):
                try:
                    self.add_log(f"📨 Processing email {i}/{len(messages)}", 'info')
                    
                    # Use enhanced processing
                    result = self.process_email_with_sheets(message['id'])
                    
                    if result.get('has_resume'):
                        resumes_found += 1
                        sheets_entries += len(result.get('attachments', []))
                    
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
            
            self.add_log(f"✅ Enhanced scan completed: {processed_count} emails, {resumes_found} resumes, {sheets_entries} sheet entries", 'success')
            
            return {
                'success': True,
                'processed': processed_count,
                'resumes_found': resumes_found,
                'sheets_entries': sheets_entries,
                'spreadsheet_id': self.main_spreadsheet_id,
                'stats': self.stats
            }
            
        except Exception as e:
            self.add_log(f"❌ Enhanced email scan failed: {e}", 'error')
            return {'success': False, 'error': str(e)}

    def bulk_process_existing_resumes(self) -> Dict[str, Any]:
        """Process existing resumes in Drive and add to sheets"""
        try:
            if not self.drive_service or not self.sheets_service:
                return {'success': False, 'error': 'Services not available'}
            
            if not self.main_spreadsheet_id:
                if not self.setup_sheets_integration():
                    return {'success': False, 'error': 'Failed to setup sheets'}
            
            self.add_log("🔄 Starting bulk processing of existing resumes", 'info')
            
            processed_count = 0
            
            # Process files in each domain folder
            for domain, folder_id in self.domain_folders.items():
                if not folder_id:
                    continue
                
                self.add_log(f"📁 Processing {domain} folder", 'info')
                
                # Get all files in domain folder (including subfolders)
                query = f"parents in '{folder_id}' and (name contains '.pdf' or name contains '.doc')"
                files_result = self.drive_service.files().list(
                    q=query,
                    fields="files(id, name, parents, description)"
                ).execute()
                
                files = files_result.get('files', [])
                
                for file_info in files:
                    try:
                        # Download and analyze file
                        file_content = self.drive_service.files().get_media(fileId=file_info['id']).execute()
                        
                        # Enhanced analysis
                        analysis_result = self.enhanced_analyze_content(file_content, file_info['name'])
                        
                        if analysis_result.get('is_resume', False):
                            # Prepare metadata
                            email_metadata = {
                                'filename': file_info['name'],
                                'drive_file_id': file_info['id'],
                                'sender': 'Bulk Processing',
                                'subject': f'Existing Resume - {domain}',
                                'date': datetime.now().strftime('%Y-%m-%d')
                            }
                            
                            # Write to sheets
                            if self.write_to_sheets(analysis_result, email_metadata):
                                processed_count += 1
                        
                    except Exception as e:
                        self.add_log(f"❌ Error processing {file_info['name']}: {e}", 'error')
                        continue
            
            self.add_log(f"✅ Bulk processing completed: {processed_count} resumes processed", 'success')
            
            return {
                'success': True,
                'processed': processed_count,
                'spreadsheet_id': self.main_spreadsheet_id
            }
            
        except Exception as e:
            self.add_log(f"❌ Bulk processing failed: {e}", 'error')
            return {'success': False, 'error': str(e)}

# Replace the original scanner instance
scanner = EnhancedVLSIResumeScanner()

# Add new API endpoints

@app.route('/api/setup-sheets', methods=['POST'])
@admin_required
def api_setup_sheets():
    """Setup Google Sheets integration"""
    try:
        if scanner.setup_sheets_integration():
            return jsonify({
                'status': 'success', 
                'message': 'Sheets integration setup completed',
                'spreadsheet_id': scanner.main_spreadsheet_id
            })
        else:
            return jsonify({'status': 'error', 'message': 'Sheets setup failed'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Sheets setup failed: {str(e)}'})

@app.route('/api/scan-with-sheets', methods=['POST'])
@admin_required
def api_scan_with_sheets():
    """Enhanced Gmail scan with sheets integration"""
    data = request.get_json() or {}
    max_results = data.get('max_results')
    
    result = scanner.scan_emails_with_sheets(max_results)
    return jsonify(result)

@app.route('/api/bulk-process', methods=['POST'])
@admin_required
def api_bulk_process():
    """Bulk process existing resumes"""
    result = scanner.bulk_process_existing_resumes()
    return jsonify(result)

@app.route('/api/sheets-info')
@admin_required
def api_sheets_info():
    """Get sheets information"""
    try:
        if scanner.main_spreadsheet_id:
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{scanner.main_spreadsheet_id}"
            return jsonify({
                'success': True,
                'spreadsheet_id': scanner.main_spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'sheets_service_active': scanner.sheets_service is not None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Sheets not set up yet'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

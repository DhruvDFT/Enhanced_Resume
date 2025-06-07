# Add this import at the top of app.py
from enhanced_resume_analyzer import EnhancedResumeAnalyzer, integrate_enhanced_analyzer

# Modify the VLSIResumeScanner class __init__ method to include the enhanced analyzer
class VLSIResumeScanner:
    def __init__(self):
        # ... existing initialization code ...
        
        # Initialize enhanced analyzer
        self.enhanced_analyzer = EnhancedResumeAnalyzer()
        
        # Add new statistics tracking
        self.classification_stats = {
            'total_analyzed': 0,
            'correctly_classified': 0,
            'false_positives': 0,
            'domains': {}
        }

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
            
            # Update analyzer's extract_text to return the extracted text
            self.enhanced_analyzer.extract_text = lambda data, name: text
            
            # Use enhanced analysis
            result = self.enhanced_analyzer.analyze_content(file_data, filename)
            
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
            
            # Add contact info if available
            if enhanced.get('contact_info'):
                contact = enhanced['contact_info']
                description_parts.extend([
                    f"",
                    f"=== CONTACT INFO ===",
                    f"Email: {contact.get('email', 'Not found')}",
                    f"Phone: {contact.get('phone', 'Not found')}",
                    f"Location: {contact.get('location', 'Not found')}"
                ])
            
            # Add education if available
            if enhanced.get('education'):
                description_parts.extend([f"", f"=== EDUCATION ==="])
                for edu in enhanced['education'][:2]:
                    description_parts.append(f"{edu.get('degree', '')} in {edu.get('field', '')}")
            
            # Add top skills
            if enhanced.get('skills'):
                description_parts.extend([
                    f"",
                    f"=== TOP SKILLS ===",
                    f"{', '.join(enhanced['skills'][:10])}"
                ])
            
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
                'description': '\n'.join(description_parts),
                'properties': {
                    'vlsi_domain': domain,
                    'experience_years': str(experience_years),
                    'quality_score': str(quality_score),
                    'analysis_confidence': str(enhanced.get('confidence', 0))
                }
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

# Add new API endpoints for enhanced features

@app.route('/api/reanalyze', methods=['POST'])
@admin_required
def api_reanalyze():
    """Reanalyze a specific file with enhanced analyzer"""
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        attachment_id = data.get('attachment_id')
        
        if not message_id or not attachment_id:
            return jsonify({'status': 'error', 'message': 'message_id and attachment_id required'})
        
        # Download and analyze
        result = scanner.get_detailed_analysis(message_id, attachment_id)
        
        return jsonify({
            'status': 'success',
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/classification-report')
@admin_required
def api_classification_report():
    """Get classification statistics report"""
    report = scanner.get_classification_report()
    return jsonify(report)

@app.route('/api/validate-classification', methods=['POST'])
@admin_required
def api_validate_classification():
    """Mark a classification as correct or incorrect for learning"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        is_correct = data.get('is_correct', True)
        correct_domain = data.get('correct_domain')
        
        if is_correct:
            scanner.classification_stats['correctly_classified'] += 1
            scanner.add_log(f"✅ Classification validated for file {file_id}", 'info')
        else:
            scanner.add_log(
                f"❌ Misclassification reported for file {file_id}. "
                f"Correct domain: {correct_domain}",
                'warning'
            )
        
        return jsonify({'status': 'success', 'message': 'Feedback recorded'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Update the HTML template to include new features
# Add this to the controls section in the index() function template:
"""
<button onclick="showClassificationReport()" style="background: #9c27b0;">
    📊 Classification Report
</button>

<div id="classification-report" style="display: none; background: #f3e5f5; 
     border: 1px solid #9c27b0; border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h3 style="color: #7b1fa2;">📊 Classification Analytics</h3>
    <div id="report-content">Loading...</div>
    <button onclick="hideClassificationReport()" 
            style="margin-top: 10px; padding: 8px 16px; background: #666; 
                   color: white; border: none; border-radius: 4px; cursor: pointer;">
        Close
    </button>
</div>
"""

# Add these JavaScript functions:
"""
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
"""

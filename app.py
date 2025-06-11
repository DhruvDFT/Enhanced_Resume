<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                            </svg>
                            Processing Errors
                        </div>
                        <div class="stat-value" id="errors-count">0</div>
                    </div>
                </div>

                <div class="controls-section">
                    <div class="controls-header">
                        <h2>Scanner Controls</h2>
                        <div id="scan-status"></div>
                    </div>
                    <div class="controls-grid">
                        <button onclick="setupGmail()" class="btn btn-info">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
                            </svg>
                            Setup Gmail
                        </button>
                        <button id="scan-btn" onclick="handleScan()" class="btn btn-primary">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
                            </svg>
                            Full Scan
                        </button>
                        <button onclick="quickScan()" class="btn btn-success">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                            </svg>
                            Quick Scan
                        </button>
                        <button onclick="testSystem()" class="btn btn-secondary">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>
                            </svg>
                            Test System
                        </button>
                        <button onclick="showUserManager()" class="btn btn-warning">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>
                            </svg>
                            Team Access
                        </button>
                        <button onclick="exportLogs()" class="btn btn-outline">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Export Logs
                        </button>
                    </div>
                </div>

                <div class="status-grid">
                    <div class="status-card">
                        <h3>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                            </svg>
                            System Status
                        </h3>
                        <div id="system-status">
                            <div class="status-item">
                                <span>Loading...</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="10" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
                            </svg>
                            Authentication Status
                        </h3>
                        <div id="auth-status">
                            <div class="status-item">
                                <span>Loading...</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="logs-container">
                    <div class="logs-header">
                        <h3>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                            </svg>
                            Activity Logs
                        </h3>
                        <div class="logs-controls">
                            <button class="log-filter active" onclick="filterLogs('all')">All</button>
                            <button class="log-filter" onclick="filterLogs('error')">Errors</button>
                            <button class="log-filter" onclick="filterLogs('warning')">Warnings</button>
                            <button class="log-filter" onclick="filterLogs('success')">Success</button>
                            <button class="btn btn-outline" onclick="toggleLogPause()" id="pause-btn">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
                                </svg>
                                Pause
                            </button>
                            <button class="btn btn-outline" onclick="clearLogs()">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 6h18"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                                </svg>
                                Clear
                            </button>
                        </div>
                    </div>
                    <div class="logs-section" id="logs-container">
                        <div class="log-entry info">
                            <span class="log-timestamp">00:00:00</span>
                            <span class="log-level">Info</span>
                            <span class="log-message">System initialized. Ready to scan resumes...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- User Manager Modal -->
        <div id="user-manager-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>👥 Team Member Management</h3>
                    <button class="close-btn" onclick="hideUserManager()">&times;</button>
                </div>
                <div class="modal-body">
                    <p style="color: var(--text-secondary); margin-bottom: 20px;">
                        Add team members to allow them to authenticate with their Gmail accounts.
                    </p>
                    <div class="input-group">
                        <label for="user-email-input">Email Address</label>
                        <input type="email" id="user-email-input" placeholder="team-member@gmail.com">
                    </div>
                    <button onclick="authenticateUser()" class="btn btn-primary btn-full">
                        Add Team Member
                    </button>
                    <div style="margin-top: 24px;">
                        <h4 style="margin-bottom: 12px;">Authenticated Users</h4>
                        <div id="user-list" style="background: var(--light); border-radius: 8px; padding: 16px;">
                            Loading...
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button onclick="hideUserManager()" class="btn btn-outline">Close</button>
                </div>
            </div>
        </div>

        <!-- OAuth Input Modal -->
        <div id="oauth-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>🔑 OAuth Authorization Required</h3>
                    <button class="close-btn" onclick="hideOAuthInput()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="oauth-notice">
                        <strong>⚠️ Action Required:</strong> Please complete the Google authorization process by following the URL in the logs above, then enter the authorization code below.
                    </div>
                    <div class="input-group">
                        <label for="oauth-code-input">Authorization Code</label>
                        <input type="text" id="oauth-code-input" placeholder="4/1AUJR-x7uuwO5w4uilFkKhvWFzrd99..." style="font-family: monospace;">
                    </div>
                    <button onclick="submitOAuthCode()" class="btn btn-success btn-full">
                        Submit Authorization Code
                    </button>
                </div>
                <div class="modal-footer">
                    <button onclick="hideOAuthInput()" class="btn btn-outline">Cancel</button>
                </div>
            </div>
        </div>

        <script>
        let isAdmin = false;
        let logCount = 0;
        let isScanning = false;
        let scanAbortController = null;
        let logsPaused = false;
        let currentLogFilter = 'all';
        let allLogs = [];

        function authenticate(event) {
            event.preventDefault();
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
                    showNotification('Invalid password', 'error');
                }
            });
        }

        function setupGmail() {
            if (!isAdmin) return;
            addLogToDisplay('Starting Gmail API setup...', 'info');
            
            fetch('/api/setup-gmail', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        addLogToDisplay(data.message, 'success');
                        hideOAuthInput();
                    } else {
                        addLogToDisplay(data.message, 'error');
                        if (data.message.includes('authentication failed')) {
                            setTimeout(showOAuthInput, 1000);
                        }
                    }
                })
                .catch(e => {
                    addLogToDisplay('Setup failed: ' + e.message, 'error');
                });
        }

        function showOAuthInput() {
            document.getElementById('oauth-modal').style.display = 'block';
        }

        function hideOAuthInput() {
            document.getElementById('oauth-modal').style.display = 'none';
            document.getElementById('oauth-code-input').value = '';
        }

        function submitOAuthCode() {
            const code = document.getElementById('oauth-code-input').value.trim();
            
            if (!code) {
                showNotification('Please enter the authorization code', 'error');
                return;
            }
            
            addLogToDisplay('Submitting authorization code...', 'info');
            
            fetch('/api/oauth-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLogToDisplay(data.message, 'success');
                    hideOAuthInput();
                } else {
                    addLogToDisplay(data.message, 'error');
                }
            })
            .catch(e => {
                addLogToDisplay('Code submission failed: ' + e.message, 'error');
            });
        }

        function showUserManager() {
            document.getElementById('user-manager-modal').style.display = 'block';
            loadAuthenticatedUsers();
        }

        function hideUserManager() {
            document.getElementById('user-manager-modal').style.display = 'none';
        }

        function authenticateUser() {
            const email = document.getElementById('user-email-input').value.trim();
            
            if (!email || !email.includes('@')) {
                showNotification('Please enter a valid email address', 'error');
                return;
            }
            
            addLogToDisplay(`Starting authentication for ${email}...`, 'info');
            
            fetch('/api/setup-gmail', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: email })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    addLogToDisplay(data.message, 'success');
                    hideOAuthInput();
                    hideUserManager();
                } else {
                    addLogToDisplay(data.message, 'error');
                    if (data.message.includes('authentication failed')) {
                        setTimeout(showOAuthInput, 1000);
                    }
                }
            })
            .catch(e => {
                addLogToDisplay('Authentication failed: ' + e.message, 'error');
            });
        }

        function loadAuthenticatedUsers() {
            fetch('/api/users')
            .then(r => r.json())
            .then(data => {
                const userList = document.getElementById('user-list');
                if (data.users && data.users.length > 0) {
                    userList.innerHTML = data.users.map(user => 
                        `<div style="padding: 8px 0; border-bottom: 1px solid var(--border);">
                            <span style="color: var(--success);">✓</span> ${user}
                        </div>`
                    ).join('');
                } else {
                    userList.innerHTML = '<div style="color: var(--text-secondary); font-style: italic;">No authenticated users yet</div>';
                }
            })
            .catch(e => {
                document.getElementById('user-list').innerHTML = '<div style="color: var(--danger);">Error loading users</div>';
            });
        }

        function handleScan() {
            if (isScanning) {
                stopScan();
            } else {
                scanGmail();
            }
        }

        function scanGmail() {
            if (!isAdmin) return;
            
            isScanning = true;
            updateScanButton();
            addLogToDisplay('Starting full Gmail scan...', 'info');
            
            scanAbortController = new AbortController();
            
            fetch('/api/scan-gmail', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
                signal: scanAbortController.signal
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        addLogToDisplay(`Scan completed: ${data.processed} emails processed, ${data.resumes_found} resumes found`, 'success');
                        updateStats(data.stats);
                    } else {
                        addLogToDisplay(data.error, 'error');
                    }
                })
                .catch(e => {
                    if (e.name !== 'AbortError') {
                        addLogToDisplay('Scan failed: ' + e.message, 'error');
                    }
                })
                .finally(() => {
                    isScanning = false;
                    updateScanButton();
                });
        }

        function stopScan() {
            if (scanAbortController) {
                scanAbortController.abort();
                addLogToDisplay('Scan stopped by user', 'warning');
            }
            isScanning = false;
            updateScanButton();
        }

        function updateScanButton() {
            const btn = document.getElementById('scan-btn');
            if (isScanning) {
                btn.innerHTML = `
                    <div class="scanning">
                        <div class="spinner"></div>
                        Stop Scan
                    </div>
                `;
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-danger');
            } else {
                btn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
                    </svg>
                    Full Scan
                `;
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-primary');
            }
        }

        function quickScan() {
            if (!isAdmin) return;
            addLogToDisplay('Starting quick scan (last 50 emails)...', 'info');
            
            fetch('/api/quick-scan', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        addLogToDisplay(`Quick scan completed: ${data.processed} emails processed, ${data.resumes_found} resumes found`, 'success');
                        updateStats(data.stats);
                    } else {
                        addLogToDisplay(data.error, 'error');
                    }
                })
                .catch(e => {
                    addLogToDisplay('Quick scan failed: ' + e.message, 'error');
                });
        }

        function testSystem() {
            if (!isAdmin) return;
            addLogToDisplay('Running system diagnostics...', 'info');
            
            fetch('/api/test-system', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
                .then(r => r.json())
                .then(data => {
                    addLogToDisplay('System diagnostics completed', 'info');
                    loadSystemStatus();
                })
                .catch(e => {
                    addLogToDisplay('System test failed: ' + e.message, 'error');
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
                    <span>Google APIs</span>
                    <span class="status-value ${data.google_apis_available ? 'success' : 'error'}">
                        ${data.google_apis_available ? '✅ Available' : '❌ Missing'}
                    </span>
                </div>
                <div class="status-item">
                    <span>PDF Processing</span>
                    <span class="status-value ${data.pdf_processing_available ? 'success' : 'error'}">
                        ${data.pdf_processing_available ? '✅ Available' : '❌ Missing'}
                    </span>
                </div>
                <div class="status-item">
                    <span>DOC Processing</span>
                    <span class="status-value ${data.docx_processing_available || data.doc_processing_available ? 'success' : 'error'}">
                        ${data.docx_processing_available || data.doc_processing_available ? '✅ Available' : '❌ Missing'}
                    </span>
                </div>
            `;
            
            authStatus.innerHTML = `
                <div class="status-item">
                    <span>Gmail Service</span>
                    <span class="status-value ${data.gmail_service_active ? 'success' : 'error'}">
                        ${data.gmail_service_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Drive Service</span>
                    <span class="status-value ${data.drive_service_active ? 'success' : 'error'}">
                        ${data.drive_service_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                </div>
                <div class="status-item">
                    <span>Current User</span>
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
                    const lastScan = new Date(stats.last_scan_time);
                    document.getElementById('last-scan').textContent = formatDate(lastScan);
                }
            }
        }

        function formatDate(date) {
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) return 'Just now';
            if (diff < 3600000) return Math.floor(diff / 60000) + ' mins ago';
            if (diff < 86400000) return Math.floor(diff / 3600000) + ' hours ago';
            
            return date.toLocaleDateString();
        }

        function addLogToDisplay(message, level = 'info') {
            const timestamp = new Date().toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            
            const logEntry = {
                timestamp,
                level,
                message
            };
            
            allLogs.push(logEntry);
            
            if (!logsPaused && (currentLogFilter === 'all' || currentLogFilter === level)) {
                appendLogEntry(logEntry);
            }
        }

        function appendLogEntry(log) {
            const logsContainer = document.getElementById('logs-container');
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry ${log.level}`;
            
            logDiv.innerHTML = `
                <span class="log-timestamp">${log.timestamp}</span>
                <span class="log-level">${log.level}</span>
                <span class="log-message">${log.message}</span>
            `;
            
            logsContainer.appendChild(logDiv);
            
            if (!logsPaused) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
            
            while (logsContainer.children.length > 200) {
                logsContainer.removeChild(logsContainer.firstChild);
            }
        }

        function toggleLogPause() {
            logsPaused = !logsPaused;
            const pauseBtn = document.getElementById('pause-btn');
            const logsContainer = document.getElementById('logs-container');
            
            if (logsPaused) {
                pauseBtn.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Resume
                `;
                logsContainer.classList.add('paused');
            } else {
                pauseBtn.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
                    </svg>
                    Pause
                `;
                logsContainer.classList.remove('paused');
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        }

        function filterLogs(filter) {
            currentLogFilter = filter;
            const logsContainer = document.getElementById('logs-container');
            
            // Update filter buttons
            document.querySelectorAll('.log-filter').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Clear and re-render logs
            logsContainer.innerHTML = '';
            
            const filteredLogs = filter === 'all' 
                ? allLogs 
                : allLogs.filter(log => log.level === filter);
            
            filteredLogs.forEach(log => appendLogEntry(log));
        }

        function clearLogs() {
            if (confirm('Clear all logs?')) {
                allLogs = [];
                document.getElementById('logs-container').innerHTML = '';
                addLogToDisplay('Logs cleared', 'info');
            }
        }

        function exportLogs() {
            const logText = allLogs.map(log => 
                `[${log.timestamp}] ${log.level.toUpperCase()}: ${log.message}`
            ).join('\n');
            
            const blob = new Blob([logText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vlsi-scanner-logs-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            addLogToDisplay('Logs exported successfully', 'success');
        }

        function showNotification(message, type = 'info') {
            // Simple notification implementation
            alert(message);
        }

        function startLogPolling() {
            setInterval(() => {
                if (isAdmin && !logsPaused) {
                    fetch('/api/logs')
                        .then(r => r.json())
                        .then(logs => {
                            const newLogs = logs.slice(logCount);
                            newLogs.forEach(log => {
                                const formattedLog = {
                                    timestamp: log.timestamp.split(' ')[1],
                                    level: log.level,
                                    message: log.message
                                };
                                allLogs.push(formattedLog);
                                
                                if (currentLogFilter === 'all' || currentLogFilter === log.level) {
                                    appendLogEntry(formattedLog);
                                }
                            });
                            
                            logCount = logs.length;
                        })
                        .catch(e => console.error('Log polling failed:', e));
                }
            }, 2000);
        }

        // Close modals when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                clearLogs();
            }
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                toggleLogPause();
            }
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                exportLogs();
            }
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

@app.route('/api/stop-scan', methods=['POST'])
@admin_required
def api_stop_scan():
    """Stop ongoing scan"""
    # This would need implementation in the scanner class
    # For now, return success
    return jsonify({'status': 'success', 'message': 'Scan stop requested'})

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
    app.run(host='0.0.0.0', port=port, debug=False)                temp_file.write(doc_data)
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
        <title>VLSI Resume Scanner - Professional Edition</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            :root {
                --primary: #6366f1;
                --primary-dark: #4f46e5;
                --secondary: #8b5cf6;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --info: #3b82f6;
                --dark: #1f2937;
                --light: #f9fafb;
                --border: #e5e7eb;
                --text-primary: #111827;
                --text-secondary: #6b7280;
                --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            }
            
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f3f4f6;
                min-height: 100vh;
                color: var(--text-primary);
                line-height: 1.6;
            }
            
            .container { 
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: white;
                border-radius: 12px;
                padding: 32px;
                margin-bottom: 24px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
            }
            
            .header h1 { 
                font-size: 2rem;
                font-weight: 700;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 8px;
            }
            
            .header .subtitle { 
                color: var(--text-secondary);
                font-size: 1rem;
            }
            
            .version-badge {
                display: inline-flex;
                align-items: center;
                background: var(--primary);
                color: white;
                font-size: 0.75rem;
                padding: 4px 12px;
                border-radius: 20px;
                font-weight: 500;
            }
            
            .auth-card {
                max-width: 400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 32px;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--border);
            }
            
            .auth-card h2 {
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 24px;
                text-align: center;
            }
            
            .input-group {
                margin-bottom: 16px;
            }
            
            .input-group label {
                display: block;
                font-size: 0.875rem;
                font-weight: 500;
                color: var(--text-primary);
                margin-bottom: 6px;
            }
            
            .input-group input {
                width: 100%;
                padding: 10px 14px;
                border: 1px solid var(--border);
                border-radius: 8px;
                font-size: 0.875rem;
                transition: all 0.2s;
                font-family: inherit;
            }
            
            .input-group input:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }
            
            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                font-family: inherit;
                text-decoration: none;
                line-height: 1;
            }
            
            .btn:hover:not(:disabled) {
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }
            
            .btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none !important;
            }
            
            .btn-primary {
                background: var(--primary);
                color: white;
            }
            
            .btn-primary:hover:not(:disabled) {
                background: var(--primary-dark);
            }
            
            .btn-success {
                background: var(--success);
                color: white;
            }
            
            .btn-info {
                background: var(--info);
                color: white;
            }
            
            .btn-warning {
                background: var(--warning);
                color: white;
            }
            
            .btn-danger {
                background: var(--danger);
                color: white;
            }
            
            .btn-secondary {
                background: var(--text-secondary);
                color: white;
            }
            
            .btn-outline {
                background: white;
                color: var(--text-primary);
                border: 1px solid var(--border);
            }
            
            .btn-outline:hover:not(:disabled) {
                background: var(--light);
            }
            
            .btn-full {
                width: 100%;
            }
            
            .dashboard-grid {
                display: grid;
                gap: 24px;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: white;
                border-radius: 12px;
                padding: 24px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
                position: relative;
                overflow: hidden;
            }
            
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
            }
            
            .stat-label {
                font-size: 0.875rem;
                color: var(--text-secondary);
                font-weight: 500;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .stat-value {
                font-size: 2rem;
                font-weight: 700;
                color: var(--text-primary);
            }
            
            .controls-section {
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
            }
            
            .controls-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .controls-header h2 {
                font-size: 1.25rem;
                font-weight: 600;
            }
            
            .controls-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 12px;
            }
            
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }
            
            .status-card {
                background: white;
                border-radius: 12px;
                padding: 24px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
            }
            
            .status-card h3 {
                font-size: 1rem;
                font-weight: 600;
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid var(--light);
                font-size: 0.875rem;
            }
            
            .status-item:last-child {
                border-bottom: none;
            }
            
            .status-value {
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .status-value.success { color: var(--success); }
            .status-value.error { color: var(--danger); }
            .status-value.warning { color: var(--warning); }
            
            .logs-container {
                background: white;
                border-radius: 12px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
                overflow: hidden;
            }
            
            .logs-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px 24px;
                background: var(--light);
                border-bottom: 1px solid var(--border);
            }
            
            .logs-header h3 {
                font-size: 1rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .logs-controls {
                display: flex;
                gap: 8px;
            }
            
            .log-filter {
                padding: 6px 12px;
                border: 1px solid var(--border);
                border-radius: 6px;
                font-size: 0.75rem;
                background: white;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .log-filter:hover {
                background: var(--light);
            }
            
            .log-filter.active {
                background: var(--primary);
                color: white;
                border-color: var(--primary);
            }
            
            .logs-section {
                background: #0f172a;
                padding: 20px;
                max-height: 500px;
                overflow-y: auto;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 0.8125rem;
                line-height: 1.6;
            }
            
            .logs-section.paused {
                opacity: 0.7;
            }
            
            .logs-section.paused::after {
                content: 'PAUSED';
                position: sticky;
                top: 10px;
                float: right;
                background: var(--warning);
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            .log-entry {
                margin-bottom: 8px;
                padding: 8px 12px;
                border-radius: 4px;
                display: flex;
                align-items: flex-start;
                gap: 12px;
                transition: all 0.2s;
                opacity: 0;
                animation: slideIn 0.3s ease forwards;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            .log-entry:hover {
                background: rgba(255, 255, 255, 0.05);
            }
            
            .log-timestamp {
                color: #64748b;
                font-size: 0.75rem;
                min-width: 80px;
            }
            
            .log-level {
                min-width: 60px;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.75rem;
                padding: 2px 8px;
                border-radius: 4px;
                text-align: center;
            }
            
            .log-message {
                flex: 1;
                color: #e2e8f0;
            }
            
            .log-entry.info .log-level {
                background: rgba(59, 130, 246, 0.2);
                color: #60a5fa;
            }
            
            .log-entry.success .log-level {
                background: rgba(16, 185, 129, 0.2);
                color: #34d399;
            }
            
            .log-entry.warning .log-level {
                background: rgba(245, 158, 11, 0.2);
                color: #fbbf24;
            }
            
            .log-entry.error .log-level {
                background: rgba(239, 68, 68, 0.2);
                color: #f87171;
            }
            
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                z-index: 1000;
                backdrop-filter: blur(4px);
            }
            
            .modal-content {
                background: white;
                max-width: 600px;
                margin: 50px auto;
                border-radius: 12px;
                box-shadow: var(--shadow-lg);
                overflow: hidden;
                animation: modalSlideIn 0.3s ease;
            }
            
            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .modal-header {
                padding: 24px;
                background: var(--light);
                border-bottom: 1px solid var(--border);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .modal-header h3 {
                font-size: 1.25rem;
                font-weight: 600;
            }
            
            .modal-body {
                padding: 24px;
            }
            
            .modal-footer {
                padding: 16px 24px;
                background: var(--light);
                border-top: 1px solid var(--border);
                display: flex;
                justify-content: flex-end;
                gap: 12px;
            }
            
            .close-btn {
                background: none;
                border: none;
                font-size: 1.5rem;
                color: var(--text-secondary);
                cursor: pointer;
                line-height: 1;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s;
            }
            
            .close-btn:hover {
                background: var(--border);
                color: var(--text-primary);
            }
            
            .oauth-notice {
                background: #fef3c7;
                border: 1px solid #fcd34d;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
                font-size: 0.875rem;
                color: #92400e;
            }
            
            .spinner {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 0.8s linear infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .scanning {
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            
            .tooltip {
                position: relative;
                cursor: help;
            }
            
            .tooltip::after {
                content: attr(data-tooltip);
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: var(--dark);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                white-space: nowrap;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.2s;
            }
            
            .tooltip:hover::after {
                opacity: 1;
            }
            
            /* Scrollbar styling */
            .logs-section::-webkit-scrollbar {
                width: 8px;
            }
            
            .logs-section::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.05);
            }
            
            .logs-section::-webkit-scrollbar-thumb {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
            
            .logs-section::-webkit-scrollbar-thumb:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .container {
                    padding: 12px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .controls-grid {
                    grid-template-columns: 1fr;
                }
                
                .status-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 11H3v10h6V11zm5-7H8v17h6V4zm5 3h-6v14h6V7z"/>
                    </svg>
                    VLSI Resume Scanner
                    <span class="version-badge">v2.1 Pro</span>
                </h1>
                <p class="subtitle">AI-Powered Domain Classification & Resume Management System</p>
            </div>
            
            <div id="auth-section">
                <div class="auth-card">
                    <h2>🔐 Admin Authentication</h2>
                    <form onsubmit="authenticate(event)">
                        <div class="input-group">
                            <label for="admin-password">Password</label>
                            <input type="password" id="admin-password" placeholder="Enter admin password" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-full">
                            Sign In
                        </button>
                    </form>
                </div>
            </div>

            <div id="main-content" style="display: none;">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                            </svg>
                            Total Emails Scanned
                        </div>
                        <div class="stat-value" id="total-emails">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/>
                            </svg>
                            Resumes Found
                        </div>
                        <div class="stat-value" id="resumes-found">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                            </svg>
                            Last Scan
                        </div>
                        <div class="stat-value" id="last-scan" style="font-size: 1.2rem;">Never</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VLSI Resume Scanner v2.1 - Professional Edition"""

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
    'https://www.googleapis.com/auth/drive.file'
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
            # Use raw strings for all regex patterns
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
                        if len(match) == 2:
                            try:
                                years = float(match[0]) + float(match[1]) / 12
                                experience_years = max(experience_years, years)
                            except (ValueError, TypeError):
                                pass
                    else:
                        try:
                            years = float(match)
                            if 0 < years < 50:  # Sanity check
                                experience_years = max(experience_years, years)
                        except (ValueError, TypeError):
                            pass
            
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
                temp_file.write(doc_

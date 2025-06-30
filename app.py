# 1. CREATE: railway.toml (in your project root)
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 4 --worker-class sync --max-requests 1000 --max-requests-jitter 100 --preload"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"

# 2. CREATE: Procfile (alternative to railway.toml)
# web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 4

# 3. CREATE: requirements.txt (update your existing one)
Flask==2.3.3
gunicorn==21.2.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
PyPDF2==3.0.1
python-docx==0.8.11

# 4. CREATE: .railway (folder) with nixpacks.toml inside
[phases.build]
cmds = ["pip install -r requirements.txt"]

[phases.install] 
cmds = ["pip install gunicorn"]

[start]
cmd = "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 4"

# 5. CREATE: gunicorn.conf.py (optional but recommended)
import os
import multiprocessing

# Railway-optimized configuration
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1
threads = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Performance
worker_tmp_dir = "/dev/shm"
graceful_timeout = 30

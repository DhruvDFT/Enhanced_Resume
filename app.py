# app.py - Physical Design Interview System (3 Questions Version, Optimized)
import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pd-secret-2024')

# In-memory storage with improved structure
data_store = {
    'users': {},
    'assignments': {},
    'notifications': {}
}
assignment_counter = 0

# Initialize default users
def init_users():
    data_store['users']['admin'] = {
        'id': 'admin',
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'is_admin': True,
        'experience_years': 3
    }
    
    for i in range(1, 4):
        user_id = f'eng00{i}'
        data_store['users'][user_id] = {
            'id': user_id,
            'username': user_id,
            'password': generate_password_hash('password123'),
            'is_admin': False,
            'experience_years': 3
        }

# 3 Questions per topic (3+ Years Experience)
QUESTIONS = {
    "floorplanning": [
        "You have a 5mm x 5mm die with 4 hard macros (each 1mm x 0.8mm) and need to achieve 70% utilization. Describe your macro placement strategy considering timing and power delivery.",
        "Your design has setup timing violations on paths crossing from left to right. The floorplan has macros placed randomly. How would you reorganize the floorplan to improve timing?",
        "During floorplan, you notice routing congestion in the center region. What are 3 specific techniques you would use to reduce congestion without major timing impact?"
    ],
    "placement": [
        "Your placement run shows timing violations on 20 critical paths with negative slack up to -50ps. Describe your systematic approach to fix these violations.",
        "You're seeing routing congestion hotspots after placement in 2-3 regions. What placement adjustments would you make to improve routability?",
        "Your design has high-fanout nets (>500 fanout) causing placement issues. How would you handle these nets during placement optimization?"
    ],
    "routing": [
        "After global routing, you have 500 DRC violations (spacing, via, width). Describe your systematic approach to resolve these violations efficiently.",
        "Your design has 10 differential pairs for high-speed signals. Explain your routing strategy to maintain 100-ohm impedance and minimize skew.",
        "You're seeing timing degradation after detailed routing compared to placement timing. What causes this and how would you recover the timing?"
    ]
}

# Keywords for auto-scoring (2 points per keyword, max 10 per question)
ANSWER_KEYWORDS = {
    "floorplanning": {
        0: ["macro placement", "timing", "power", "utilization", "power delivery", "IR drop", "blockage", "pins", "orientation", "dataflow"],
        1: ["setup violations", "timing paths", "floorplan", "critical paths", "placement", "buffers", "repeaters", "pipeline", "hierarchy", "partition"],
        2: ["congestion", "routing", "density", "spreading", "blockages", "channels", "utilization", "cell density", "padding", "keep-out"]
    },
    "placement": {
        0: ["timing violations", "negative slack", "optimization", "critical paths", "placement", "setup", "hold", "clock", "incremental", "ECO"],
        1: ["congestion", "hotspots", "spreading", "density", "padding", "blockages", "magnet placement", "guides", "regions", "utilization"],
        2: ["high-fanout", "buffer tree", "cloning", "load splitting", "placement", "clustering", "net weights", "timing", "physical synthesis", "optimization"]
    },
    "routing": {
        0: ["DRC violations", "spacing", "via", "width", "metal", "tracks", "reroute", "ECO", "search repair", "manual fixes"],
        1: ["differential pairs", "impedance", "matching", "shielding", "spacing", "length matching", "skew", "routing", "symmetry", "guard rings"],
        2: ["timing degradation", "parasitics", "RC delay", "crosstalk", "coupling", "optimization", "layer assignment", "via optimization", "buffer", "sizing"]
    }
}

# Scoring rubric
SCORING_RUBRIC = {
    10: "Excellent - Comprehensive answer with deep understanding",
    8: "Very Good - Covers most key points with good detail",
    6: "Good - Basic understanding with some key points",
    4: "Fair - Limited understanding, missing key concepts",
    2: "Poor - Minimal understanding shown",
    0: "No answer or completely incorrect"
}

# Helper functions
def calculate_auto_score(answer, topic, question_index):
    if not answer:
        return 0
    
    answer_lower = answer.lower()
    keywords_found = 0
    
    if topic in ANSWER_KEYWORDS and question_index < len(ANSWER_KEYWORDS[topic]):
        keywords = ANSWER_KEYWORDS[topic][question_index]
        for keyword in keywords:
            if keyword.lower() in answer_lower:
                keywords_found += 1
    
    return min(keywords_found * 2, 10)

def create_assignment(engineer_id, topic):
    global assignment_counter
    
    if engineer_id not in data_store['users'] or topic not in QUESTIONS:
        return None
    
    assignment_counter += 1
    assignment_id = f"PD_{topic.upper()}_{engineer_id}_{assignment_counter}"
    
    assignment = {
        'id': assignment_id,
        'engineer_id': engineer_id,
        'topic': topic,
        'questions': QUESTIONS[topic],
        'submission': {
            'answers': {},
            'auto_scores': {},
            'submitted_at': None
        },
        'review': {
            'final_scores': {},
            'total_score': None,
            'scored_by': None,
            'scored_at': None
        },
        'status': 'pending',  # pending -> submitted -> under_review -> published
        'created_at': datetime.now().isoformat(),
        'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
        'published_at': None
    }
    
    data_store['assignments'][assignment_id] = assignment
    
    if engineer_id not in data_store['notifications']:
        data_store['notifications'][engineer_id] = []
    
    data_store['notifications'][engineer_id].append({
        'id': str(uuid4()),
        'title': f'New {topic.title()} Assignment',
        'message': f'3 questions for 3+ years experience, due in 3 days',
        'created_at': datetime.now().isoformat(),
        'read': False
    })
    
    return assignment

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/admin' if session.get('is_admin') else '/student')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = data_store['users'].get(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            return redirect('/admin' if user.get('is_admin') else '/student')
        error = 'Invalid credentials'
    
    return f'''
        <html>
            <head>
                <title>Physical Design Interview System</title>
                <style>
                    body {{ font-family: Arial; margin: 40px; }}
                    .container {{ max-width: 400px; margin: auto; }}
                    .error {{ color: red; }}
                    input {{ width: 100%; padding: 8px; margin: 10px 0; }}
                    button {{ padding: 10px; width: 100%; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Physical Design Interview System</h2>
                    <p>3 Questions per Topic (3+ Years)</p>
                    <p>Demo Credentials:<br>Admin: admin / admin123<br>Student: eng001 / password123</p>
                    {f'<p class="error">{error}</p>' if error else ''}
                    <form method="POST">
                        <label>Username</label>
                        <input type="text" name="username" required>
                        <label>Password</label>
                        <input type="password" name="password" required>
                        <button type="submit">Login</button>
                    </form>
                </div>
            </body>
        </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    engineers = [u for u in data_store['users'].values() if not u.get('is_admin')]
    all_assignments = list(data_store['assignments'].values())
    
    submitted = [a for a in all_assignments if a['status'] == 'submitted']
    under_review = [a for a in all_assignments if a['status'] == 'under_review']
    published = [a for a in all_assignments if a['status'] == 'published']
    
    return f'''
        <html>
            <head>
                <title>Admin Dashboard</title>
                <style>
                    body {{ font-family: Arial; margin: 40px; }}
                    .container {{ max-width: 800px; margin: auto; }}
                    .stats {{ display: flex; gap: 20px; }}
                    .stat {{ border: 1px solid #ccc; padding: 10px; flex: 1; text-align: center; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                    a {{ color: blue; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Admin Dashboard - {session["username"]} <a href="/logout">Logout</a></h2>
                    <div class="stats">
                        <div class="stat"><h3>{len(engineers)}</h3><p>Engineers</p></div>
                        <div class="stat"><h3>{len(submitted)}</h3><p>Submitted</p></div>
                        <div class="stat"><h3>{len(under_review)}</h3><p>Under Review</p></div>
                        <div class="stat"><h3>{len(published)}</h3><p>Published</p></div>
                    </div>
                    <h3>Create Assignment</h3>
                    <form method="POST" action="/admin/create">
                        <label>Engineer</label>
                        <select name="engineer_id" required>
                            <option value="">Select...</option>
                            {"".join(f'<option value="{eng["username"]}">{eng["username"]}</option>' for eng in engineers)}
                        </select>
                        <label>Topic</label>
                        <select name="topic" required>
                            <option value="">Select...</option>
                            <option value="floorplanning">Floorplanning</option>
                            <option value="placement">Placement</option>
                            <option value="routing">Routing</option>
                        </select>
                        <button type="submit">Create Assignment</button>
                    </form>
                    <h3>Submitted Assignments (Ready for Review)</h3>
                    {"".join(f'<p><b>{a["id"]} - {a["engineer_id"]} - {a["topic"].title()}</b><br>Submitted: All 3 answers | Auto-score calculated<br><a href="/admin/review/{a["id"]}">Review & Score</a></p>' for a in submitted) or '<p>No assignments ready for review</p>'}
                    <h3>All Assignments</h3>
                    <table>
                        <tr><th>ID</th><th>Engineer</th><th>Topic</th><th>Status</th><th>Score</th><th>Action</th></tr>
                        {"".join(f'<tr><td>{a["id"]}</td><td>{a["engineer_id"]}</td><td>{a["topic"]}</td><td>{a["status"]}</td><td>{a["review"].get("total_score", "-")}/30</td><td>{"<a href=/admin/publish/"+a["id"]+">Publish</a>" if a["status"] == "under_review" else "Published ✓" if a["status"] == "published" else ""}</td></tr>' for a in all_assignments[-10:])}
                    </table>
                </div>
            </body>
        </html>
    '''

@app.route('/admin/create', methods=['POST'])
def admin_create():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    engineer_id = request.form.get('engineer_id')
    topic = request.form.get('topic').lower()
    
    if engineer_id and topic:
        create_assignment(engineer_id, topic)
    
    return redirect('/admin')

@app.route('/admin/review/<assignment_id>', methods=['GET', 'POST'])
def admin_review(assignment_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    assignment = data_store['assignments'].get(assignment_id)
    if not assignment or assignment['status'] != 'submitted':
        return redirect('/admin')
    
    if request.method == 'POST':
        total_score = 0
        for i in range(3):
            score = request.form.get(f'score_{i}', '0')
            try:
                final_score = int(score)
                if 0 <= final_score <= 10:
                    assignment['review']['final_scores'][str(i)] = final_score
                    total_score += final_score
            except ValueError:
                pass
        
        if len(assignment['review']['final_scores']) == 3:
            assignment['review']['total_score'] = total_score
            assignment['review']['scored_by'] = session['username']
            assignment['review']['scored_at'] = datetime.now().isoformat()
            assignment['status'] = 'under_review'
        
        return redirect('/admin')
    
    if not assignment['submission']['auto_scores']:
        for i, question in enumerate(assignment['questions']):
            answer = assignment['submission']['answers'].get(str(i), '')
            assignment['submission']['auto_scores'][str(i)] = calculate_auto_score(answer, assignment['topic'], i)
    
    return f'''
        <html>
            <head>
                <title>Review Assignment</title>
                <style>
                    body {{ font-family: Arial; margin: 40px; }}
                    .container {{ max-width: 800px; margin: auto; }}
                    .question {{ margin: 20px 0; }}
                    textarea {{ width: 100%; height: 100px; }}
                    select {{ width: 100px; }}
                    a {{ color: blue; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Review Assignment - {assignment_id}</h2>
                    <p>Engineer: {assignment["engineer_id"]} | Topic: {assignment["topic"].title()}</p>
                    <p><b>Scoring Rubric:</b><br>{"<br>".join(f"{score}: {desc}" for score, desc in SCORING_RUBRIC.items())}</p>
                    <form method="POST">
                        {"".join(f'<div class="question"><p><b>Q{i+1}: {question}</b></p><p><b>Student\'s Answer:</b><br>{assignment["submission"]["answers"].get(str(i), "No answer provided")}</p><p><b>Auto-score (Keywords): {assignment["submission"]["auto_scores"].get(str(i), 0)}/10</b></p><label>Final Score (0-10):</label><select name="score_{i}" required><option value="">Select...</option>{"".join(f'<option value="{s}">{s}</option>' for s in range(11))}</select></div>' for i, question in enumerate(assignment["questions"]))}
                        <button type="submit">Save Scores (Next: Publish)</button>
                        <a href="/admin">Cancel</a>
                    </form>
                </div>
            </body>
        </html>
    '''

@app.route('/admin/publish/<assignment_id>')
def admin_publish(assignment_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    assignment = data_store['assignments'].get(assignment_id)
    if not assignment or assignment['status'] != 'under_review':
        return redirect('/admin')
    
    assignment['status'] = 'published'
    assignment['published_at'] = datetime.now().isoformat()
    
    engineer_id = assignment['engineer_id']
    if engineer_id not in data_store['notifications']:
        data_store['notifications'][engineer_id] = []
    
    data_store['notifications'][engineer_id].append({
        'id': str(uuid4()),
        'title': f'{assignment["topic"].title()} Assignment Scored',
        'message': f'Your assignment has been evaluated. Score: {assignment["review"]["total_score"]}/30',
        'created_at': datetime.now().isoformat(),
        'read': False
    })
    
    return redirect('/admin')

@app.route('/student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    my_assignments = [a for a in data_store['assignments'].values() if a['engineer_id'] == user_id]
    my_notifications = [n for n in data_store['notifications'].get(user_id, []) if not n['read']][-5:]
    
    return f'''
        <html>
            <head>
                <title>Student Dashboard</title>
                <style>
                    body {{ font-family: Arial; margin: 40px; }}
                    .container {{ max-width: 800px; margin: auto; }}
                    .notification {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
                    .assignment {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
                    a {{ color: blue; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Student Dashboard - {session["username"]} <a href="/logout">Logout</a></h2>
                    {f'<h3>Notifications</h3>{"".join(f'<div class="notification"><b>{n["title"]}</b><p>{n["message"]}<br>{n["created_at"][:16]}</p></div>' for n in my_notifications)}' if my_notifications else ''},
                    <h3>My Assignments</h3>,
                    {"".join(f'<div class="assignment"><p><b>{a["topic"].title()} Assignment</b> <span>{a["status"]}</span></p><p>Due: {a["due_date"][:10]}</p>{"<p>Score: "+str(a["review"]["total_score"])+"/30 (Scored by: "+a["review"].get("scored_by", "Admin")+")</p><a href=/student/assignment/"+a["id"]+">View Results</a>" if a["status"] == "published" else "<p>Your submission is being reviewed...</p>" if a["status"] in ["submitted", "under_review"] else f"<a href=/student/assignment/{a['id']}>Answer Questions</a>"}</div>' for a in my_assignments) or '<p>No assignments yet.</p>'}
                </div>
            </body>
        </html>
    '''

@app.route('/student/assignment/<assignment_id>', methods=['GET', 'POST'])
def student_assignment(assignment_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    assignment = data_store['assignments'].get(assignment_id)
    if not assignment or assignment['engineer_id'] != session['user_id']:
        return redirect('/student')
    
    if request.method == 'POST' and assignment['status'] == 'pending':
        answers = {}
        for i in range(3):
            answer = request.form.get(f'answer_{i}', '').strip()
            if answer:
                answers[str(i)] = answer
        
        if len(answers) == 3:
            assignment['submission']['answers'] = answers
            assignment['submission']['submitted_at'] = datetime.now().isoformat()
            assignment['status'] = 'submitted'
            
            for i in range(3):
                answer = answers.get(str(i), '')
                assignment['submission']['auto_scores'][str(i)] = calculate_auto_score(answer, assignment['topic'], i)
        
        return redirect('/student')
    
    return f'''
        <html>
            <head>
                <title>{assignment["topic"].title()} Assignment</title>
                <style>
                    body {{ font-family: Arial; margin: 40px; }}
                    .container {{ max-width: 800px; margin: auto; }}
                    .question {{ margin: 20px 0; }}
                    textarea {{ width: 100%; height: 100px; }}
                    a {{ color: blue; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>{assignment["topic"].title()} Assignment</h2>
                    <p>Status: {assignment["status"]} | Due: {assignment["due_date"][:10]}</p>
                    {f'<p><b>Total Score: {assignment["review"]["total_score"]}/30</b></p>' if assignment["status"] == "published" else ''}
                    <form method="POST">
                        {"".join(f'<div class="question"><p><b>Q{i+1}: {question}</b></p>{"<textarea name=answer_"+str(i)+" required></textarea>" if assignment["status"] == "pending" else f"<p><b>Your Answer:</b><br>{assignment['submission']['answers'].get(str(i), 'No answer provided')}</p>{'<p>Score: '+str(assignment['review']['final_scores'].get(str(i), 0))+'/10</p>' if assignment['status'] == 'published' else ''}"} </div>' for i, question in enumerate(assignment["questions"]))}
                        {f'<button type="submit">Submit All Answers</button>' if assignment["status"] == "pending" else ''}
                        <a href="/student">Back to Dashboard</a>
                    </form>
                </div>
            </body>
        </html>
    '''

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'users': len(data_store['users']),
        'assignments': len(data_store['assignments'])
    })

# Initialize
init_users()
if not data_store['assignments']:
    create_assignment('eng001', 'floorplanning')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

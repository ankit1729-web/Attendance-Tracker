from flask import Flask, request, jsonify, Response
import requests
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime
from pymongo import MongoClient
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adamas Attendence Tracker</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body>
    <div id="app">
        <!-- Login View -->
        <div id="login-view" class="view active">
            <div class="glass-panel login-panel">
                <div class="login-header">
                    <i data-lucide="graduation-cap" class="icon-large"></i>
                    <h1>Attendance Tracker</h1>
                    <p>Login with your college portal credentials</p>
                </div>
                <form id="login-form">
                    <div class="input-group">
                        <i data-lucide="user"></i>
                        <input type="text" id="username" placeholder="Username (Try 'test')" required>
                    </div>
                    <div class="input-group">
                        <i data-lucide="lock"></i>
                        <input type="password" id="password" placeholder="Password" required>
                    </div>
                    <button type="submit" class="btn-primary" id="login-btn">
                        <span>Authenticate</span>
                        <i data-lucide="arrow-right"></i>
                    </button>
                    <div id="login-error" class="error-msg"></div>
                </form>
            </div>
            
            <div class="animated-bg">
                <div class="blob blob-1"></div>
                <div class="blob blob-2"></div>
                <div class="blob blob-3"></div>
            </div>
        </div>

        <!-- Dashboard View -->
        <div id="dashboard-view" class="view">
            <nav class="navbar glass-panel">
                <div class="nav-brand">
                    <i data-lucide="graduation-cap"></i>
                    <h2>Adamas Attendence Tracker</h2>
                </div>
                <div class="nav-user">
                    <img id="user-avatar" src="" alt="Profile" style="display: none; width: 36px; height: 36px; border-radius: 50%; object-fit: cover; margin-right: 10px; border: 2px solid rgba(255,255,255,0.2);">
                    <span id="user-greeting">Hello, Student</span>
                    <button class="btn-icon" id="logout-btn" title="Logout">
                        <i data-lucide="log-out"></i>
                    </button>
                </div>
            </nav>

            <main class="dashboard-content">
                <header class="dashboard-header">
                    <div>
                        <h1>Your Attendance</h1>
                        <p>Analyze your progress and plan your leaves.</p>
                    </div>
                    <div class="target-selector glass-panel">
                        <label>Target:</label>
                        <button class="btn-target" data-target="75">75%</button>
                        <button class="btn-target active" data-target="85">85%</button>
                        <button class="btn-target" data-target="95">95%</button>
                    </div>
                </header>

                <div class="stats-grid" id="subjects-container">
                    <!-- Subjects will be injected here via JS -->
                </div>
                
                <div id="scraper-warning" class="warning-msg" style="display: none;">
                    <i data-lucide="alert-triangle"></i>
                    <span>Currently using mock data. You must update app.py with your college's specific HTML structure to fetch real data.</span>
                </div>
                
                <footer style="text-align: center; margin-top: 2rem; padding-bottom: 1rem; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
                    Created by Ankit
                </footer>
            </main>
        </div>
    </div>

    <!-- Template for a subject card -->
    <template id="subject-card-template">
        <div class="subject-card glass-panel">
            <h3 class="subject-name"></h3>
            <div class="progress-circle-container">
                <svg class="progress-circle" viewBox="0 0 36 36">
                    <path class="circle-bg"
                        d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path class="circle"
                        stroke-dasharray="0, 100"
                        d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                </svg>
                <div class="percentage-text">0%</div>
            </div>
            
            <div class="attendance-details">
                <div class="detail">
                    <span class="label">Attended</span>
                    <span class="value attended-val">0</span>
                </div>
                <div class="detail">
                    <span class="label">Total</span>
                    <span class="value total-val">0</span>
                </div>
            </div>
            
            <div class="action-box">
                <div class="status-icon"></div>
                <p class="action-text"></p>
            </div>
        </div>
    </template>

    <script src="script.js"></script>
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
"""
CSS_CONTENT = """:root {
    --bg-dark: #0f172a;
    --bg-card: rgba(30, 41, 59, 0.7);
    --primary: #8b5cf6;
    --primary-hover: #7c3aed;
    --accent: #06b6d4;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --glass-border: rgba(255, 255, 255, 0.1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Outfit', sans-serif;
}

body {
    background-color: var(--bg-dark);
    color: var(--text-main);
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
}

/* Animated Background */
.animated-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
    overflow: hidden;
    background: radial-gradient(circle at top right, #1e1b4b, #0f172a);
}

.blob {
    position: absolute;
    filter: blur(80px);
    border-radius: 50%;
    opacity: 0.5;
    animation: float 20s infinite ease-in-out alternate;
}

.blob-1 {
    width: 400px;
    height: 400px;
    background: var(--primary);
    top: -100px;
    left: -100px;
}

.blob-2 {
    width: 500px;
    height: 500px;
    background: var(--accent);
    bottom: -200px;
    right: -100px;
    animation-delay: -5s;
}

.blob-3 {
    width: 300px;
    height: 300px;
    background: #ec4899;
    top: 40%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation-delay: -10s;
}

@keyframes float {
    0% { transform: translate(0, 0) scale(1); }
    100% { transform: translate(50px, 50px) scale(1.1); }
}

/* Glassmorphism utility */
.glass-panel {
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    border-radius: 24px;
}

/* Views */
.view {
    display: none;
    opacity: 0;
    transition: opacity 0.4s ease;
    min-height: 100vh;
    padding: 2rem;
}

.view.active {
    display: flex;
    flex-direction: column;
    opacity: 1;
}

/* Login View */
#login-view {
    justify-content: center;
    align-items: center;
}

.login-panel {
    width: 100%;
    max-width: 420px;
    padding: 3rem 2.5rem;
    position: relative;
    z-index: 10;
}

.login-header {
    text-align: center;
    margin-bottom: 2.5rem;
}

.login-header .icon-large {
    width: 64px;
    height: 64px;
    color: var(--primary);
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.5));
}

.login-header h1 {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #fff, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.login-header p {
    color: var(--text-muted);
    font-size: 0.95rem;
}

.input-group {
    position: relative;
    margin-bottom: 1.5rem;
}

.input-group i {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    width: 20px;
    height: 20px;
}

.input-group input {
    width: 100%;
    padding: 1rem 1rem 1rem 3rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    color: var(--text-main);
    font-size: 1rem;
    outline: none;
    transition: all 0.3s ease;
}

.input-group input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.15);
}

.btn-primary {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.3s ease;
    margin-top: 1rem;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px -10px rgba(139, 92, 246, 0.6);
}

.btn-primary:active {
    transform: translateY(0);
}

.error-msg {
    color: var(--danger);
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
    min-height: 20px;
}

/* Dashboard View */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    margin-bottom: 2rem;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.nav-brand i {
    color: var(--primary);
}

.nav-user {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.btn-icon {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    transition: color 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    border-radius: 8px;
}

.btn-icon:hover {
    color: var(--danger);
    background: rgba(239, 68, 68, 0.1);
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 2.5rem;
    flex-wrap: wrap;
    gap: 1.5rem;
}

.dashboard-header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.25rem;
}

.dashboard-header p {
    color: var(--text-muted);
}

.target-selector {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem 1rem;
    border-radius: 100px;
}

.target-selector label {
    color: var(--text-muted);
    font-weight: 600;
}

.btn-target {
    background: transparent;
    border: none;
    color: var(--text-muted);
    padding: 0.5rem 1rem;
    border-radius: 100px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s;
}

.btn-target.active {
    background: var(--primary);
    color: white;
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
}

.subject-card {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: transform 0.3s ease;
}

.subject-card:hover {
    transform: translateY(-5px);
}

.subject-name {
    font-size: 1.2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    color: var(--text-main);
    width: 100%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Circular Progress */
.progress-circle-container {
    position: relative;
    width: 120px;
    height: 120px;
    margin-bottom: 1.5rem;
}

.progress-circle {
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);
}

.circle-bg {
    fill: none;
    stroke: rgba(255, 255, 255, 0.05);
    stroke-width: 3;
}

.circle {
    fill: none;
    stroke: var(--primary);
    stroke-width: 3;
    stroke-linecap: round;
    transition: stroke-dasharray 1s ease-out, stroke 0.3s;
}

.percentage-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.75rem;
    font-weight: 800;
}

.attendance-details {
    display: flex;
    width: 100%;
    justify-content: space-around;
    margin-bottom: 1.5rem;
    padding: 1rem 0;
    border-top: 1px solid var(--glass-border);
    border-bottom: 1px solid var(--glass-border);
}

.detail {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.detail .label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.detail .value {
    font-size: 1.25rem;
    font-weight: 600;
}

.action-box {
    width: 100%;
    padding: 1rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: rgba(0, 0, 0, 0.2);
}

.action-box i {
    flex-shrink: 0;
}

.action-text {
    font-size: 0.9rem;
    line-height: 1.4;
}

/* Colors for different states */
.status-good { stroke: var(--success); }
.status-warn { stroke: var(--warning); }
.status-bad { stroke: var(--danger); }

.bg-good { background: rgba(16, 185, 129, 0.1); color: var(--success); }
.bg-warn { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
.bg-bad { background: rgba(239, 68, 68, 0.1); color: var(--danger); }

.warning-msg {
    margin-top: 2rem;
    padding: 1rem;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 12px;
    color: var(--warning);
    display: flex;
    align-items: center;
    gap: 1rem;
}

/* Responsive */
@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .view {
        padding: 1rem;
    }
}
"""
JS_CONTENT = """document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loginView = document.getElementById('login-view');
    const dashboardView = document.getElementById('dashboard-view');
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const errorMsg = document.getElementById('login-error');
    const logoutBtn = document.getElementById('logout-btn');
    const userGreeting = document.getElementById('user-greeting');
    const subjectsContainer = document.getElementById('subjects-container');
    const targetBtns = document.querySelectorAll('.btn-target');
    const scraperWarning = document.getElementById('scraper-warning');

    // State
    let currentData = null;
    let targetPercentage = 0.85;

    // Check if already logged in (using sessionStorage for demo)
    const storedData = sessionStorage.getItem('attendanceData');
    if (storedData) {
        currentData = JSON.parse(storedData);
        showDashboard();
    }

    // Login Handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<i data-lucide="loader" class="spin"></i><span>Authenticating...</span>';
        lucide.createIcons();
        errorMsg.textContent = '';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (result.success) {
                currentData = result.data;
                sessionStorage.setItem('attendanceData', JSON.stringify(currentData));
                
                if (result.message) {
                    scraperWarning.style.display = 'flex';
                } else {
                    scraperWarning.style.display = 'none';
                }

                showDashboard();
            } else {
                errorMsg.textContent = result.error || 'Login failed';
            }
        } catch (err) {
            errorMsg.textContent = 'Server error. Is the backend running?';
        } finally {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<span>Authenticate</span><i data-lucide="arrow-right"></i>';
            lucide.createIcons();
        }
    });

    // Logout
    logoutBtn.addEventListener('click', () => {
        sessionStorage.removeItem('attendanceData');
        currentData = null;
        dashboardView.classList.remove('active');
        setTimeout(() => {
            loginView.classList.add('active');
            loginForm.reset();
        }, 400);
    });

    // Target Selection
    targetBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            targetBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            targetPercentage = parseInt(e.target.dataset.target) / 100;
            renderSubjects();
        });
    });

    function showDashboard() {
        loginView.classList.remove('active');
        userGreeting.textContent = `Hello, ${currentData.studentName}`;
        
        const userAvatar = document.getElementById('user-avatar');
        if (currentData.profilePhoto) {
            userAvatar.src = currentData.profilePhoto;
            userAvatar.onerror = function() {
                this.style.display = 'none';
            };
            userAvatar.style.display = 'block';
        } else {
            userAvatar.style.display = 'none';
        }

        setTimeout(() => {
            dashboardView.classList.add('active');
            renderSubjects();
        }, 400);
    }

    function calculateAction(attended, total, target) {
        const currentPerc = total === 0 ? 0 : attended / total;
        
        if (currentPerc >= target) {
            // Can skip classes
            // Formula: attended / (total + y) = target => y = (attended - target*total) / target
            const y = Math.floor((attended - target * total) / target);
            return {
                type: 'skip',
                count: y,
                message: y > 0 ? `You can safely bunk ${y} class${y > 1 ? 'es' : ''}.` : `On track. Don't skip next class.`,
                statusClass: 'status-good',
                bgClass: 'bg-good',
                icon: 'check-circle'
            };
        } else {
            // Need to attend classes
            // Formula: (attended + x) / (total + x) = target => x = (target*total - attended) / (1 - target)
            const x = Math.ceil((target * total - attended) / (1 - target));
            
            // If it's mathematically impossible (e.g., target is 100%), handle it
            if (x === Infinity) {
                return {
                    type: 'attend',
                    count: x,
                    message: `Impossible to reach ${target*100}%.`,
                    statusClass: 'status-bad',
                    bgClass: 'bg-bad',
                    icon: 'alert-octagon'
                };
            }

            return {
                type: 'attend',
                count: x,
                message: `Attend next ${x} class${x > 1 ? 'es' : ''} to reach ${target*100}%.`,
                statusClass: 'status-warn',
                bgClass: 'bg-warn',
                icon: 'alert-triangle'
            };
        }
    }

    function renderSubjects() {
        subjectsContainer.innerHTML = '';
        const template = document.getElementById('subject-card-template');

        currentData.subjects.forEach((subject, index) => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.subject-card');
            
            // Set basic info
            card.querySelector('.subject-name').textContent = subject.name;
            card.querySelector('.subject-name').title = subject.name; // Tooltip for long names
            card.querySelector('.attended-val').textContent = subject.attended;
            card.querySelector('.total-val').textContent = subject.total;

            const percentage = subject.total === 0 ? 0 : Math.round((subject.attended / subject.total) * 100);
            card.querySelector('.percentage-text').textContent = `${percentage}%`;

            // Calculate action
            const action = calculateAction(subject.attended, subject.total, targetPercentage);
            
            const actionBox = card.querySelector('.action-box');
            actionBox.classList.add(action.bgClass);
            actionBox.querySelector('.action-text').textContent = action.message;
            actionBox.querySelector('.status-icon').innerHTML = `<i data-lucide="${action.icon}" class="${action.statusClass}"></i>`;

            // Set progress circle
            const circle = card.querySelector('.circle');
            circle.classList.add(action.statusClass);
            
            // Need a slight delay for the CSS transition to work on first render
            setTimeout(() => {
                circle.setAttribute('stroke-dasharray', `${percentage}, 100`);
            }, 50 * index);

            subjectsContainer.appendChild(clone);
        });

        lucide.createIcons();
    }
});
"""

MOCK_DATA = {
    "studentName": "John Doe",
    "subjects": [
        {"name": "Data Structures", "total": 40, "attended": 30},
        {"name": "Algorithms", "total": 35, "attended": 20}
    ]
}

@app.route('/')
def index():
    return Response(HTML_CONTENT, mimetype='text/html')

@app.route('/style.css')
def style():
    return Response(CSS_CONTENT, mimetype='text/css')

@app.route('/script.js')
def script():
    return Response(JS_CONTENT, mimetype='application/javascript')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if username == 'test':
        return jsonify({"success": True, "data": MOCK_DATA})

    try:
        session = requests.Session()
        
        login_url = "https://adamasknowledgecity.ac.in/student/login"
        login_page = session.get(login_url, verify=False)
        soup_login = BeautifulSoup(login_page.text, 'html.parser')
        
        token_input = soup_login.find('input', {'name': '_token'})
        if not token_input:
            return jsonify({"success": True, "data": MOCK_DATA, "message": "Portal structure changed."})
            
        token = token_input['value']
        
        login_payload = {
            "_token": token,
            "registration_no": username,
            "password": password,
            "login": "login"
        }
        
        login_response = session.post(login_url, data=login_payload, verify=False, allow_redirects=True)
        
        if 'login' in login_response.url and 'dashboard' not in login_response.url:
            return jsonify({"success": False, "error": "Invalid credentials or login failed"}), 401

        attendance_url = "https://adamasknowledgecity.ac.in/student/attendance"
        attendance_response = session.get(attendance_url, verify=False)
        
        soup = BeautifulSoup(attendance_response.text, 'html.parser')
        
        subjects = []
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = [td.text.strip() for td in row.find_all('td')]
                if len(cols) >= 3:
                    try:
                        total_classes = int(cols[1])
                        attended_classes = int(cols[2])
                    except ValueError:
                        continue
                        
                    subjects.append({
                        "name": cols[0],
                        "total": total_classes,
                        "attended": attended_classes
                    })
        soup_dashboard = BeautifulSoup(login_response.text, 'html.parser')
        student_name = username.split('/')[-1] if '/' in username else username
        name_span = soup_dashboard.find('span', class_='username')
        if name_span and name_span.text.strip():
            student_name = name_span.text.strip()
        else:
            # Aggressive fallback to profile page
            try:
                profile_resp = session.get("https://adamasknowledgecity.ac.in/student/account/personal-info", verify=False)
                profile_soup = BeautifulSoup(profile_resp.text, 'html.parser')
                
                # 1. Try username span
                profile_name_span = profile_soup.find('span', class_='username')
                if profile_name_span and profile_name_span.text.strip():
                    student_name = profile_name_span.text.strip()
                else:
                    # 2. Try input fields (like first_name, name, student_name)
                    found = False
                    for inp in profile_soup.find_all('input'):
                        if inp.get('name') and 'name' in inp.get('name').lower() and inp.get('value'):
                            val = inp.get('value').strip()
                            # avoid picking up weird hidden inputs
                            if len(val) > 2 and len(val) < 50:
                                student_name = val
                                found = True
                                break
                                
                    if not found:
                        # 3. Text Heuristic: Find label "Name" or "Student Name" and get the next text or td
                        all_text_elements = profile_soup.find_all(['th', 'td', 'label', 'div', 'span'])
                        for i, el in enumerate(all_text_elements):
                            text = el.get_text(strip=True).lower()
                            if text in ['name', 'name:', 'student name', 'student name:']:
                                # Try to find the next element that has text
                                for next_el in all_text_elements[i+1:]:
                                    next_text = next_el.get_text(strip=True)
                                    if next_text and next_text.lower() not in ['name', 'name:', 'student name']:
                                        if len(next_text) > 2 and len(next_text) < 50:
                                            student_name = next_text
                                            found = True
                                            break
                                if found:
                                    break
            except Exception as e:
                print(f"Failed to fetch profile: {e}")

        # Extract profile photo
        profile_photo = ""
        try:
            img = soup_dashboard.find('img', alt='User Pic') or soup_dashboard.find('img', class_='img-circle')
            if img and img.get('src'):
                profile_photo = img.get('src')
            elif 'profile_soup' in locals():
                img = profile_soup.find('img', alt='User Pic') or profile_soup.find('img', class_='img-circle')
                if img and img.get('src'):
                    profile_photo = img.get('src')
                    
            if profile_photo.startswith('/'):
                profile_photo = 'https://adamasknowledgecity.ac.in' + profile_photo
        except Exception:
            pass

        # Track login in database
        try:
            mongo_uri = os.environ.get("MONGO_URI")
            if mongo_uri:
                client = MongoClient(mongo_uri)
                db = client.get_database("attendance_tracker")
                logins = db.get_collection("logins")
                logins.insert_one({
                    "username": username,
                    "studentName": student_name,
                    "timestamp": datetime.utcnow()
                })
        except Exception as db_err:
            print(f"Database error: {db_err}")

        if not subjects:
             return jsonify({"success": True, "data": MOCK_DATA, "message": "No attendance records found."})
             
        return jsonify({
            "success": True,
            "data": {
                "studentName": student_name,
                "profilePhoto": profile_photo,
                "subjects": subjects
            }
        })
        
    except Exception as e:
        print(f"Error scraping: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

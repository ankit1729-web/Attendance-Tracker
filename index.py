from flask import Flask, request, jsonify, Response
import requests
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime
from pymongo import MongoClient
import concurrent.futures
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
                    <div class="dropdown">
                        <button class="dropbtn" id="academics-btn">Academics <i data-lucide="chevron-down"></i></button>
                        <div class="dropdown-content" id="academics-dropdown">
                            <a href="#" id="nav-info"><i data-lucide="info"></i> Info</a>
                            <a href="#" id="nav-cr-dashboard" style="display: none;"><i data-lucide="shield"></i> CR Dashboard</a>
                        </div>
                    </div>
                    <img id="user-avatar" src="" alt="Profile" style="display: none; width: 36px; height: 36px; border-radius: 50%; object-fit: cover; margin-right: 10px; border: 2px solid rgba(255,255,255,0.2);">
                    <span id="user-greeting">Hello, Student</span>
                    <span id="user-section" style="font-size: 0.9rem; margin-left: 10px; color: var(--primary);"></span>
                    <button class="btn-icon" id="logout-btn" title="Logout">
                        <i data-lucide="log-out"></i>
                    </button>
                </div>
            </nav>

            <main class="dashboard-content">
                <div class="tabs-container" style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <button class="btn-tab active" data-tab="attendance-tab" style="padding: 10px 20px; border-radius: 8px; border: none; background: rgba(255,255,255,0.1); color: white; cursor: pointer; transition: all 0.3s; font-weight: 600;">Attendance</button>
                    <button class="btn-tab" data-tab="routine-tab" style="padding: 10px 20px; border-radius: 8px; border: none; background: transparent; color: rgba(255,255,255,0.7); cursor: pointer; transition: all 0.3s; font-weight: 600;">Class Routine</button>
                </div>

                <div id="attendance-tab" class="tab-content active">
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
                </div> <!-- End attendance tab -->

                <div id="routine-tab" class="tab-content" style="display: none;">
                    <header class="dashboard-header">
                        <div>
                            <h1>Class Routine</h1>
                            <p>Your schedule for the week.</p>
                        </div>
                    </header>
                    <div class="routine-container glass-panel" style="overflow-x: auto; padding: 20px; margin-top: 1rem;">
                        <table class="routine-table" style="width: 100%; border-collapse: separate; border-spacing: 4px;">
                            <thead>
                                <tr>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Day</th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 1<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">09:30 - 10:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 2<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">10:30 - 11:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 3<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">11:30 - 12:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 4<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">12:30 - 13:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 5<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">13:30 - 14:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 6<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">14:30 - 15:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 7<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">15:30 - 16:25</small></th>
                                    <th style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; color: white;">Period 8<br><small style="font-weight: normal; color: rgba(255,255,255,0.7);">16:30 - 17:25</small></th>
                                </tr>
                            </thead>
                            <tbody id="routine-tbody">
                                <!-- Routine rows injected via JS -->
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <footer style="text-align: center; margin-top: 2rem; padding-bottom: 1rem; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
                    Created by Ankit
                </footer>
            </main>
        </div>

        <!-- CR Dashboard View -->
        <div id="cr-dashboard-view" class="view">
            <nav class="navbar glass-panel">
                <div class="nav-brand">
                    <i data-lucide="shield"></i>
                    <h2>CR Dashboard</h2>
                </div>
                <div class="nav-user">
                    <button class="btn-icon" id="back-to-dashboard-btn" title="Back to Main Dashboard">
                        <i data-lucide="arrow-left"></i>
                    </button>
                </div>
            </nav>

            <main class="dashboard-content">
                <div class="glass-panel" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div>
                        <h3>Attendance Register</h3>
                        <p style="color: var(--text-muted); margin-top: 5px; font-size: 0.9rem;"><span id="cr-section-label">Section</span> | Custom List</p>
                    </div>
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <input type="date" id="cr-date-picker" style="padding: 8px 12px; border-radius: 8px; border: 1px solid var(--glass-border); background: rgba(15, 23, 42, 0.6); color: white; outline: none; font-family: inherit;">
                        <button id="cr-export-btn" class="btn-primary" style="margin-top: 0; padding: 10px 20px; font-size: 0.95rem; width: auto;">
                            <i data-lucide="download"></i> Export PDF
                        </button>
                    </div>
                </div>

                <!-- Add Student Form -->
                <div class="glass-panel" style="margin-bottom: 20px;">
                    <form id="add-student-form" style="display: flex; gap: 15px; align-items: flex-end;">
                        <div style="flex: 1;">
                            <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 5px;">Roll Number</label>
                            <input type="text" id="add-roll" required placeholder="e.g. 351" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--glass-border); background: rgba(15, 23, 42, 0.6); color: white; outline: none; font-family: inherit;">
                        </div>
                        <div style="flex: 2;">
                            <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 5px;">Student Name</label>
                            <input type="text" id="add-name" required placeholder="e.g. John Doe" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--glass-border); background: rgba(15, 23, 42, 0.6); color: white; outline: none; font-family: inherit;">
                        </div>
                        <button type="submit" class="btn-primary" style="margin-top: 0; padding: 10px 20px; font-size: 0.95rem; width: auto; height: 42px;">
                            <i data-lucide="plus"></i> Add
                        </button>
                    </form>
                </div>

                <div class="glass-panel">
                    <div style="display: grid; grid-template-columns: 60px 220px 1fr 100px 80px; padding: 10px 15px; border-bottom: 1px solid var(--glass-border); font-weight: 600; color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase;">
                        <div>Sl No</div>
                        <div>Roll No</div>
                        <div>Name</div>
                        <div style="text-align: center;">Status</div>
                        <div></div>
                    </div>
                    <div id="cr-attendance-list" style="max-height: 500px; overflow-y: auto;">
                        <!-- Student rows injected via JS -->
                    </div>
                </div>
                
                <footer style="text-align: center; margin-top: 2rem; padding-bottom: 1rem; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
                    Created by Ankit
                </footer>
            </main>
        </div>
    </div>

    <!-- Info Modal -->
    <div id="info-modal" class="modal">
        <div class="modal-content glass-panel">
            <div class="modal-header">
                <h2><i data-lucide="user"></i> Personal Info</h2>
                <button class="close-modal"><i data-lucide="x"></i></button>
            </div>
            <div class="modal-body" id="info-modal-body">
                <!-- Info injected here via JS -->
            </div>
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

    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>
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
    position: relative;
    z-index: 1000;
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

/* Dropdown Menu */
.dropdown {
    position: relative;
    display: inline-block;
    margin-right: 1.5rem;
}

.dropbtn {
    background-color: transparent;
    color: var(--text-main);
    padding: 0.5rem 1rem;
    font-size: 1rem;
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.dropbtn:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

.dropdown-content {
    display: none;
    position: absolute;
    background-color: var(--bg-dark);
    min-width: 220px;
    box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.5);
    z-index: 100;
    border-radius: 12px;
    border: 1px solid var(--glass-border);
    top: 110%;
    right: 0;
    overflow: hidden;
}

.dropdown-content a {
    color: var(--text-main);
    padding: 12px 16px;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.9rem;
    transition: background 0.2s;
}

.dropdown-content a:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: var(--primary);
}

.dropdown.show .dropdown-content {
    display: block;
}

/* Modal CSS */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    justify-content: center;
    align-items: center;
}

.modal.active {
    display: flex;
}

.modal-content {
    background: var(--bg-card);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
    padding: 0;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--glass-border);
}

.modal-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.25rem;
}

.close-modal {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    transition: color 0.3s;
}

.close-modal:hover {
    color: var(--danger);
}

.modal-body {
    padding: 1.5rem;
}

.info-item {
    display: flex;
    flex-direction: column;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.info-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}

.info-value {
    font-size: 1.1rem;
    color: var(--text-light);
}

/* Toast Notifications */
.toast-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.toast {
    background: var(--bg-card);
    border-left: 4px solid var(--danger);
    border-radius: 8px;
    padding: 15px 20px;
    color: var(--text-light);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    gap: 12px;
    transform: translateX(120%);
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    max-width: 350px;
}

.toast.show {
    transform: translateX(0);
}

.toast.hiding {
    transform: translateX(120%);
    opacity: 0;
    transition: all 0.3s ease;
}

.toast-icon {
    color: var(--danger);
    flex-shrink: 0;
}

.toast-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.toast-title {
    font-weight: 600;
    font-size: 0.95rem;
}

.toast-message {
    font-size: 0.85rem;
    color: var(--text-muted);
}

/* CR Dashboard Attendance List */
.cr-student-row {
    display: grid;
    grid-template-columns: 60px 220px 1fr 100px 80px;
    padding: 12px 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    align-items: center;
    transition: background 0.2s;
}

.cr-student-row:hover {
    background: rgba(255, 255, 255, 0.02);
}

.cr-student-row:last-child {
    border-bottom: none;
}

/* Toggle Switch Styles */
.status-toggle {
    display: flex;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 20px;
    padding: 2px;
    width: 80px;
    position: relative;
    cursor: pointer;
    margin: 0 auto;
}

.status-toggle .toggle-option {
    flex: 1;
    text-align: center;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 4px 0;
    z-index: 1;
    color: var(--text-muted);
    transition: color 0.3s;
}

.status-toggle.present .toggle-option.opt-p {
    color: white;
}

.status-toggle.absent .toggle-option.opt-a {
    color: white;
}

.status-toggle .toggle-slider {
    position: absolute;
    top: 2px;
    left: 2px;
    width: calc(50% - 2px);
    height: calc(100% - 4px);
    border-radius: 18px;
    transition: transform 0.3s, background-color 0.3s;
    background-color: var(--good); /* Default to present green */
    z-index: 0;
}

.status-toggle.absent .toggle-slider {
    transform: translateX(100%);
    background-color: var(--danger);
}

.remove-student-btn, .edit-student-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 5px;
    border-radius: 4px;
    transition: all 0.2s;
    display: flex;
    justify-content: center;
    align-items: center;
}

.remove-student-btn:hover {
    background: rgba(239, 68, 68, 0.2);
    color: var(--danger);
}

.edit-student-btn:hover {
    background: rgba(139, 92, 246, 0.2);
    color: var(--primary);
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
    const tabBtns = document.querySelectorAll('.btn-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const routineTbody = document.getElementById('routine-tbody');
    const academicsBtn = document.getElementById('academics-btn');
    const academicsDropdown = document.getElementById('academics-dropdown');
    const navInfo = document.getElementById('nav-info');
    const infoModal = document.getElementById('info-modal');
    const closeModalBtn = infoModal.querySelector('.close-modal');
    const infoModalBody = document.getElementById('info-modal-body');
    const navCrDashboard = document.getElementById('nav-cr-dashboard');
    const crDashboardView = document.getElementById('cr-dashboard-view');
    const backToDashboardBtn = document.getElementById('back-to-dashboard-btn');
    const crDatePicker = document.getElementById('cr-date-picker');
    const crExportBtn = document.getElementById('cr-export-btn');
    const crAttendanceList = document.getElementById('cr-attendance-list');
    const addStudentForm = document.getElementById('add-student-form');
    const addRollInput = document.getElementById('add-roll');
    const addNameInput = document.getElementById('add-name');
    const crSectionLabel = document.getElementById('cr-section-label');
    const userSection = document.getElementById('user-section');

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

    // Tab Selection
    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update buttons
            tabBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = 'transparent';
                b.style.color = 'rgba(255,255,255,0.7)';
            });
            const clickedBtn = e.target;
            clickedBtn.classList.add('active');
            clickedBtn.style.background = 'rgba(255,255,255,0.1)';
            clickedBtn.style.color = 'white';

            // Update content
            tabContents.forEach(content => {
                content.style.display = 'none';
                content.classList.remove('active');
            });
            const targetTab = document.getElementById(clickedBtn.dataset.tab);
            targetTab.style.display = 'block';
            setTimeout(() => targetTab.classList.add('active'), 10);
        });
    });

    // Dropdown Toggle
    academicsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        academicsBtn.parentElement.classList.toggle('show');
    });

    // Close dropdown on outside click
    document.addEventListener('click', () => {
        academicsBtn.parentElement.classList.remove('show');
    });

    academicsDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // Modal Logic
    navInfo.addEventListener('click', (e) => {
        e.preventDefault();
        academicsBtn.parentElement.classList.remove('show');
        renderPersonalInfo();
        infoModal.classList.add('active');
    });

    if (navCrDashboard) {
        navCrDashboard.addEventListener('click', (e) => {
            e.preventDefault();
            academicsBtn.parentElement.classList.remove('show');
            dashboardView.classList.remove('active');
            setTimeout(() => {
                crDashboardView.classList.add('active');
                if (crStudentsData.length === 0) {
                    initCRDashboard();
                }
            }, 400);
        });
    }

    if (backToDashboardBtn) {
        backToDashboardBtn.addEventListener('click', () => {
            crDashboardView.classList.remove('active');
            setTimeout(() => {
                dashboardView.classList.add('active');
            }, 400);
        });
    }

    closeModalBtn.addEventListener('click', () => {
        infoModal.classList.remove('active');
    });

    infoModal.addEventListener('click', (e) => {
        if (e.target === infoModal) {
            infoModal.classList.remove('active');
        }
    });

    function renderPersonalInfo() {
        infoModalBody.innerHTML = '';
        if (!currentData || !currentData.personalInfo || Object.keys(currentData.personalInfo).length === 0) {
            infoModalBody.innerHTML = '<p style="text-align:center; color: var(--text-muted);">No personal information available.</p>';
            return;
        }

        // Recursive function to render nested objects
        function renderNode(node, container, level = 0) {
            if (Array.isArray(node)) {
                // Render array of objects (like Educational Details)
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.style.marginTop = '10px';
                table.style.marginBottom = '15px';
                
                if (node.length > 0) {
                    const thead = document.createElement('thead');
                    const trHead = document.createElement('tr');
                    Object.keys(node[0]).forEach(key => {
                        const th = document.createElement('th');
                        th.textContent = key;
                        th.style.padding = '8px';
                        th.style.background = 'rgba(255,255,255,0.1)';
                        th.style.textAlign = 'left';
                        th.style.fontSize = '0.85rem';
                        trHead.appendChild(th);
                    });
                    thead.appendChild(trHead);
                    table.appendChild(thead);
                    
                    const tbody = document.createElement('tbody');
                    node.forEach(rowObj => {
                        const tr = document.createElement('tr');
                        Object.values(rowObj).forEach(val => {
                            const td = document.createElement('td');
                            td.textContent = val;
                            td.style.padding = '8px';
                            td.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                            td.style.fontSize = '0.9rem';
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    });
                    table.appendChild(tbody);
                }
                container.appendChild(table);
            } else if (typeof node === 'object' && node !== null) {
                // Render object (key-value pairs or nested categories)
                Object.entries(node).forEach(([key, value]) => {
                    // Check if value is a string (or empty object meaning no subdata)
                    if (typeof value === 'string') {
                        const item = document.createElement('div');
                        item.className = 'info-item';
                        item.style.paddingLeft = `${level * 15}px`;
                        
                        // Check if value looks like an image URL
                        if (value.startsWith('http') && (value.includes('.jpeg') || value.includes('.jpg') || value.includes('.png') || value.includes('.gif'))) {
                            item.innerHTML = `
                                <span class="info-label">${key}</span>
                                <span class="info-value"><img src="${value}" alt="${key}" style="max-width: 150px; border-radius: 8px; margin-top: 5px;"></span>
                            `;
                        } else {
                            item.innerHTML = `
                                <span class="info-label">${key}</span>
                                <span class="info-value">${value}</span>
                            `;
                        }
                        container.appendChild(item);
                    } else if (Object.keys(value).length > 0) {
                        // It's a nested category
                        const header = document.createElement('h4');
                        header.textContent = key;
                        header.style.color = 'var(--primary)';
                        header.style.marginTop = '1.5rem';
                        header.style.marginBottom = '1rem';
                        header.style.paddingBottom = '0.5rem';
                        header.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
                        header.style.fontSize = level === 0 ? '1.1rem' : '0.95rem';
                        header.style.marginLeft = `${level * 15}px`;
                        container.appendChild(header);
                        
                        renderNode(value, container, level + 1);
                    }
                });
            }
        }

        renderNode(currentData.personalInfo, infoModalBody, 0);
    }

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
            renderRoutine();
            
            // Check CR status and show link if true
            if (currentData.is_cr) {
                navCrDashboard.style.display = 'block';
            } else {
                navCrDashboard.style.display = 'none';
            }

            if (currentData.section && userSection) {
                userSection.innerText = `| ${currentData.section}`;
            } else if (userSection) {
                userSection.innerText = '';
            }

            if (currentData.subjects && currentData.subjects.length > 0) {
                // Initial CR Dashboard rendering logic placeholder
            }
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

    // Toast Notification System
    function showToast(title, message, isWarning = false) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        if (!isWarning) {
            toast.style.borderLeftColor = 'var(--good)';
        }

        const iconColorClass = isWarning ? 'var(--danger)' : 'var(--good)';
        const iconName = isWarning ? 'alert-triangle' : 'check-circle';

        toast.innerHTML = `
            <div class="toast-icon" style="color: ${iconColorClass}">
                <i data-lucide="${iconName}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
        `;

        container.appendChild(toast);
        lucide.createIcons({ root: toast });

        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('hiding');
            toast.addEventListener('transitionend', () => {
                toast.remove();
            });
        }, 5000);
    }

    function renderSubjects() {
        subjectsContainer.innerHTML = '';
        const template = document.getElementById('subject-card-template');
        let lowSubjectsCount = 0;

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

            if (percentage < (targetPercentage * 100)) {
                lowSubjectsCount++;
            }

            subjectsContainer.appendChild(clone);
        });

        lucide.createIcons();

        // Trigger real-time low attendance notification
        if (lowSubjectsCount > 0) {
            showToast(
                'Low Attendance Alert', 
                `You have ${lowSubjectsCount} subject${lowSubjectsCount > 1 ? 's' : ''} below your ${Math.round(targetPercentage * 100)}% target!`, 
                true
            );
        } else if (currentData.subjects.length > 0) {
            showToast(
                'Attendance Looks Good', 
                `All your subjects meet the ${Math.round(targetPercentage * 100)}% target!`, 
                false
            );
        }
    }

    function renderRoutine() {
        routineTbody.innerHTML = '';
        if (!currentData || !currentData.routine) {
            routineTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">No routine data available.</td></tr>';
            return;
        }

        currentData.routine.forEach(day => {
            const tr = document.createElement('tr');
            
            // Day column
            const tdDay = document.createElement('td');
            tdDay.innerHTML = `<strong>${day.day}</strong>`;
            tdDay.style.padding = '10px';
            tdDay.style.background = 'rgba(255,255,255,0.05)';
            tdDay.style.borderRadius = '8px';
            tr.appendChild(tdDay);

            let expectedPeriod = 1;
            day.schedule.forEach(slot => {
                const td = document.createElement('td');
                td.colSpan = slot.colspan;
                td.style.padding = '10px';
                td.style.background = 'rgba(255,255,255,0.02)';
                td.style.borderRadius = '8px';
                td.style.textAlign = 'center';
                
                if (slot.subject) {
                    td.innerHTML = `
                        <div style="font-weight: 600; font-size: 0.9rem; color: #a5b4fc; text-transform: capitalize;">${slot.subject}</div>
                        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7); margin-top: 4px; text-transform: capitalize;">${slot.teacher}</div>
                        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px;">${slot.room}</div>
                    `;
                    td.style.border = '1px solid rgba(255,255,255,0.1)';
                } else {
                    td.innerHTML = '<span style="color: rgba(255,255,255,0.2);">-</span>';
                }
                tr.appendChild(td);
                expectedPeriod += slot.colspan;
            });

            // Fill any remaining empty slots if schedule array didn't go up to 8
            while (expectedPeriod <= 8) {
                const td = document.createElement('td');
                td.style.padding = '10px';
                td.style.background = 'rgba(255,255,255,0.02)';
                td.style.borderRadius = '8px';
                td.style.textAlign = 'center';
                td.innerHTML = '<span style="color: rgba(255,255,255,0.2);">-</span>';
                tr.appendChild(td);
                expectedPeriod++;
            }

            routineTbody.appendChild(tr);
        });
    }

    // CR Dashboard Logic
    let crStudentsData = [];
    
    async function saveCRStudents() {
        try {
            await fetch('/api/cr_students', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ students: crStudentsData })
            });
        } catch (e) {
            console.error("Failed to save CR students to server", e);
        }
    }

    async function loadCRStudents() {
        try {
            const resp = await fetch('/api/cr_students');
            const result = await resp.json();
            if (result.success && result.data && result.data.length > 0) {
                crStudentsData = result.data;
            } else {
                crStudentsData = [];
                // Auto-populate 351 to 384 for CRs on first load
                for (let i = 351; i <= 384; i++) {
                    crStudentsData.push({
                        rollNo: `UG/04/BTCSE/2025/${i}`,
                        name: '-',
                        status: 'Present'
                    });
                }
                saveCRStudents();
            }
        } catch (e) {
            console.error("Failed to load CR students from server", e);
        }
    }

    function renderCRStudents() {
        if (!crAttendanceList) return;
        crAttendanceList.innerHTML = '';
        
        crStudentsData.forEach((student, index) => {
            // Ensure status defaults to Present on fresh render if missing
            if (!student.status) student.status = 'Present';

            const row = document.createElement('div');
            row.className = 'cr-student-row';
            
            const isPresent = student.status === 'Present';
            const toggleClass = isPresent ? 'present' : 'absent';
            
            row.innerHTML = `
                <div>${index + 1}</div>
                <div>${student.rollNo}</div>
                <div style="text-transform: capitalize; font-size: 0.9rem;">${student.name}</div>
                <div>
                    <div class="status-toggle ${toggleClass}" data-index="${index}">
                        <div class="toggle-slider"></div>
                        <div class="toggle-option opt-p">P</div>
                        <div class="toggle-option opt-a">A</div>
                    </div>
                </div>
                <div style="display: flex; gap: 5px; justify-content: flex-end;">
                    <button class="edit-student-btn" data-index="${index}" title="Edit Name">
                        <i data-lucide="edit-2" style="width: 16px; height: 16px;"></i>
                    </button>
                    <button class="remove-student-btn" data-index="${index}" title="Remove Student">
                        <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>
                    </button>
                </div>
            `;
            
            crAttendanceList.appendChild(row);
        });

        lucide.createIcons();

        // Add event listeners to toggles
        const toggles = crAttendanceList.querySelectorAll('.status-toggle');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                if (this.classList.contains('present')) {
                    this.classList.remove('present');
                    this.classList.add('absent');
                    crStudentsData[index].status = 'Absent';
                } else {
                    this.classList.remove('absent');
                    this.classList.add('present');
                    crStudentsData[index].status = 'Present';
                }
            });
        });

        // Add event listeners to remove buttons
        const removeBtns = crAttendanceList.querySelectorAll('.remove-student-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                crStudentsData.splice(index, 1);
                saveCRStudents();
                renderCRStudents();
            });
        });

        // Add event listeners to edit buttons
        const editBtns = crAttendanceList.querySelectorAll('.edit-student-btn');
        editBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                const student = crStudentsData[index];
                const currentName = student.name !== '-' ? student.name : '';
                const newName = prompt(`Enter new name for Roll ${student.rollNo}:`, currentName);
                
                if (newName !== null && newName.trim() !== '') {
                    student.name = newName.trim();
                    saveCRStudents();
                    renderCRStudents();
                }
            });
        });
    }

    async function initCRDashboard() {
        if (!crAttendanceList) return;
        
        if (crSectionLabel && currentData && currentData.section) {
            crSectionLabel.innerText = currentData.section;
        }

        // Initialize date picker to today (local timezone)
        if (crDatePicker) {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            crDatePicker.value = `${yyyy}-${mm}-${dd}`;
        }

        await loadCRStudents();
        renderCRStudents();
    }

    if (addStudentForm) {
        addStudentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const rollNo = addRollInput.value.trim();
            const name = addNameInput.value.trim();
            
            if (rollNo && name) {
                crStudentsData.push({
                    rollNo: rollNo,
                    name: name,
                    status: 'Present'
                });
                saveCRStudents();
                renderCRStudents();
                
                addRollInput.value = '';
                addNameInput.value = '';
                addRollInput.focus();
            }
        });
    }

    if (crExportBtn) {
        crExportBtn.addEventListener('click', () => {
            const dateVal = crDatePicker.value;
            if (!dateVal) {
                alert("Please select a date first.");
                return;
            }

            if (crStudentsData.length === 0) {
                alert("No students in the list. Add some students first.");
                return;
            }

            try {
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF();
                
                // Add Header
                doc.setFontSize(18);
                doc.setTextColor(30, 41, 59);
                doc.text("Batch Attendance Register", 14, 22);
                
                doc.setFontSize(11);
                doc.setTextColor(100, 116, 139);
                doc.text(`Date: ${dateVal}`, 14, 30);
                
                const sectionText = (currentData && currentData.section) ? currentData.section : "Custom List";
                doc.text(`${sectionText} | Total Students: ${crStudentsData.length}`, 14, 36);

                // Calculate summary
                const presentCount = crStudentsData.filter(s => s.status === 'Present').length;
                const absentCount = crStudentsData.filter(s => s.status === 'Absent').length;
                doc.text(`Summary: ${presentCount} Present, ${absentCount} Absent`, 14, 42);

                // Prepare table data
                const tableColumn = ["Sl No", "Roll Number", "Name", "Status"];
                const tableRows = [];

                crStudentsData.forEach((student, index) => {
                    tableRows.push([
                        index + 1,
                        student.rollNo,
                        student.name,
                        student.status
                    ]);
                });

                // Generate table using autoTable plugin
                doc.autoTable({
                    head: [tableColumn],
                    body: tableRows,
                    startY: 50,
                    theme: 'grid',
                    headStyles: { fillColor: [139, 92, 246] },
                    styles: { fontSize: 10, cellPadding: 3 },
                    didParseCell: function (data) {
                        // Color the status column based on value
                        if (data.section === 'body' && data.column.index === 3) {
                            if (data.cell.raw === 'Present') {
                                data.cell.styles.textColor = [16, 185, 129];
                                data.cell.styles.fontStyle = 'bold';
                            } else if (data.cell.raw === 'Absent') {
                                data.cell.styles.textColor = [239, 68, 68];
                                data.cell.styles.fontStyle = 'bold';
                            }
                        }
                    }
                });

                // Save PDF
                doc.save(`Attendance_${dateVal}.pdf`);
            } catch (err) {
                console.error("PDF generation failed:", err);
                alert("Could not generate PDF. Check console for errors.");
            }
        });
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

    # Check for CR authorization early
    authorized_crs = ["AU/2025/0004141", "AU/2025/0004167", "AU/2025/0004182"]
    is_cr = username in authorized_crs

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

        def fetch_url(url):
            return session.get(url, verify=False, timeout=10)
            
        attendance_response = fetch_url("https://adamasknowledgecity.ac.in/student/attendance")
        r_routine = fetch_url("https://adamasknowledgecity.ac.in/student/routine")
        
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

        # Extract all personal info (Form data and Table data)
        personal_info = {}
        if 'profile_soup' in locals():
            try:
                # Iterate over panels to preserve hierarchy
                for panel in profile_soup.find_all('div', class_='panel-default'):
                    panel_title_tag = panel.find('h5', class_='panel-title')
                    if not panel_title_tag: continue
                    main_category = panel_title_tag.get_text(strip=True).replace('+', '').replace('-', '').strip()
                    personal_info[main_category] = {}
                    
                    # (Image extraction removed as per user request)
                                
                    tables = panel.find_all('table', class_='table-user-information')
                    for table in tables:
                        sub_category = None
                        prev_h5 = table.find_previous_sibling('h5')
                        if prev_h5:
                            sub_category = prev_h5.get_text(strip=True)
                            
                        target_dict = personal_info[main_category]
                        if sub_category:
                            if sub_category not in target_dict:
                                target_dict[sub_category] = {}
                            target_dict = target_dict[sub_category]
                            
                        # Extract table rows
                        for tr in table.find_all('tr'):
                            tds = tr.find_all('td')
                            if len(tds) == 2:
                                key = tds[0].get_text(strip=True).strip(':')
                                val = tds[1].get_text(strip=True)
                                if key:
                                    target_dict[key] = val
                            elif len(tds) == 1:
                                text = tds[0].get_text(strip=True)
                                if ':' in text:
                                    parts = text.split(':', 1)
                                    if len(parts) == 2 and parts[0].strip():
                                        target_dict[parts[0].strip()] = parts[1].strip()
                                    
                        # Handle grids (like educational details)
                        thead = table.find('thead')
                        if thead and len(table.find_all('tr')) > 1:
                            headers = [th.get_text(strip=True) for th in thead.find_all('th')]
                            tbody = table.find('tbody')
                            if headers and tbody:
                                grid_data = []
                                for tr in tbody.find_all('tr'):
                                    tds = [td.get_text(strip=True) for td in tr.find_all('td')]
                                    if len(tds) == len(headers):
                                        row_data = {headers[i]: tds[i] for i in range(len(headers))}
                                        grid_data.append(row_data)
                                if grid_data:
                                    if sub_category:
                                        personal_info[main_category][sub_category] = grid_data
                                    else:
                                        personal_info[main_category]['List'] = grid_data
            except Exception as e:
                print(f"Failed to extract personal info details: {e}")
                
        # Find Section
        student_section = ""
        def find_section(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if "section" in k.lower():
                        return str(v).strip()
                    res = find_section(v)
                    if res:
                        return res
            elif isinstance(d, list):
                for item in d:
                    res = find_section(item)
                    if res:
                        return res
            return None
            
        found_sec = find_section(personal_info)
        
        # Fallback to searching the dashboard HTML text if not found
        if not found_sec and 'soup_dashboard' in locals():
            # Sometimes section is written like "Section : F" or "Section: F" anywhere in the dashboard
            dash_text = soup_dashboard.get_text(separator=' ')
            import re
            sec_match = re.search(r'Section\s*[:\-]?\s*([A-Za-z0-9]+)', dash_text, re.IGNORECASE)
            if sec_match:
                found_sec = sec_match.group(1).strip()

        if is_cr:
            student_section = "SEC- F"
        elif found_sec:
            student_section = f"SEC- {found_sec.upper()}"

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

        # Extract Class Routine
        routine = []
        try:
            if r_routine and r_routine.status_code == 200:
                soup_routine = BeautifulSoup(r_routine.text, 'html.parser')
                table = soup_routine.find('table', class_='table-bordered')
                if table:
                    tbody = table.find('tbody')
                    for tr in tbody.find_all('tr', recursive=False):
                        day_td = tr.find('td', class_='week-day')
                        if not day_td:
                            continue
                            
                        day_text = day_td.get_text(separator='|', strip=True).split('|')[0]
                        
                        day_schedule = []
                        period_idx = 1
                        
                        for td in tr.find_all('td', recursive=False)[1:]:
                            colspan = int(td.get('colspan', 1))
                            subject_span = td.find('span', class_='class-subject')
                            if subject_span:
                                subject = subject_span.get_text(strip=True)
                                teacher_span = td.find('span', class_='class-teacher')
                                room_span = td.find('span', class_='bulding-room')
                                day_schedule.append({
                                    "period": period_idx,
                                    "colspan": colspan,
                                    "subject": subject,
                                    "teacher": teacher_span.get_text(strip=True) if teacher_span else "",
                                    "room": room_span.get_text(strip=True) if room_span else ""
                                })
                            else:
                                day_schedule.append({
                                    "period": period_idx,
                                    "colspan": colspan,
                                    "subject": None
                                })
                            period_idx += colspan
                            
                        routine.append({
                            "day": day_text,
                            "schedule": day_schedule
                        })
        except Exception as e:
            print(f"Failed to fetch routine: {e}")

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

        # Check for CR authorization
        # (moved to top of function)

        if not subjects:
             return jsonify({"success": True, "data": MOCK_DATA, "message": "No attendance records found."})
             
        return jsonify({
            "success": True,
            "data": {
                "is_cr": is_cr,
                "section": student_section,
                "studentName": student_name,
                "profilePhoto": profile_photo,
                "subjects": subjects,
                "routine": routine,
                "personalInfo": personal_info
            }
        })
        
    except Exception as e:
        print(f"Error scraping: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cr_students', methods=['GET'])
def get_cr_students():
    try:
        mongo_uri = os.environ.get("MONGO_URI")
        if mongo_uri:
            client = MongoClient(mongo_uri)
            db = client.get_database("attendance_tracker")
            doc = db.cr_students.find_one({"_id": "shared_list"})
            if doc:
                return jsonify({"success": True, "data": doc.get("students", [])})
    except Exception as e:
        print("Mongo error:", e)
        
    import json
    if os.path.exists('cr_students.json'):
        with open('cr_students.json', 'r') as f:
            return jsonify({"success": True, "data": json.load(f)})
            
    return jsonify({"success": True, "data": []})

@app.route('/api/cr_students', methods=['POST'])
def save_cr_students():
    data = request.json
    students = data.get('students', [])
    
    try:
        mongo_uri = os.environ.get("MONGO_URI")
        if mongo_uri:
            client = MongoClient(mongo_uri)
            db = client.get_database("attendance_tracker")
            db.cr_students.update_one(
                {"_id": "shared_list"},
                {"$set": {"students": students}},
                upsert=True
            )
    except Exception as e:
        print("Mongo error:", e)

    import json
    with open('cr_students.json', 'w') as f:
        json.dump(students, f)
        
    return jsonify({"success": True})

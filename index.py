import os
from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup

# Get absolute paths to templates and static
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# Mock data for demonstration
MOCK_DATA = {
    "studentName": "John Doe",
    "subjects": [
        {"name": "Data Structures", "total": 40, "attended": 30},
        {"name": "Algorithms", "total": 35, "attended": 20},
        {"name": "Database Systems", "total": 38, "attended": 36},
        {"name": "Operating Systems", "total": 42, "attended": 30}
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

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
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        session = requests.Session()
        
        # 1. GET Login Page to extract CSRF token
        login_url = "https://adamasknowledgecity.ac.in/student/login"
        login_page = session.get(login_url, verify=False)
        soup_login = BeautifulSoup(login_page.text, 'html.parser')
        
        token_input = soup_login.find('input', {'name': '_token'})
        if not token_input:
            return jsonify({"success": True, "data": MOCK_DATA, "message": "Portal structure changed. Using mock data."})
            
        token = token_input['value']
        
        # 2. POST Login Data
        login_payload = {
            "_token": token,
            "registration_no": username,
            "password": password,
            "login": "login"
        }
        
        login_response = session.post(login_url, data=login_payload, verify=False, allow_redirects=True)
        
        if 'login' in login_response.url and 'dashboard' not in login_response.url:
            return jsonify({"success": False, "error": "Invalid credentials or login failed"}), 401

        # 3. Fetch Attendance
        attendance_url = "https://adamasknowledgecity.ac.in/student/attendance"
        attendance_response = session.get(attendance_url, verify=False)
        
        soup = BeautifulSoup(attendance_response.text, 'html.parser')
        
        # 4. Parse Attendance Data
        subjects = []
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')[1:] # Skip header
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
        
        if not subjects:
             return jsonify({"success": True, "data": MOCK_DATA, "message": "No attendance records found. Using mock data."})
             
        return jsonify({
            "success": True,
            "data": {
                "studentName": username.split('/')[-1] if '/' in username else username,
                "subjects": subjects
            }
        })
        
    except Exception as e:
        print(f"Error scraping: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

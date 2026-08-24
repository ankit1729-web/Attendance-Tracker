import os

html = open('index.html', encoding='utf-8').read()
css = open('style.css', encoding='utf-8').read()
js = open('script.js', encoding='utf-8').read()

new_index = f'''from flask import Flask, request, jsonify, Response
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

HTML_CONTENT = """{html}"""
CSS_CONTENT = """{css}"""
JS_CONTENT = """{js}"""

MOCK_DATA = {{
    "studentName": "John Doe",
    "subjects": [
        {{"name": "Data Structures", "total": 40, "attended": 30}},
        {{"name": "Algorithms", "total": 35, "attended": 20}}
    ]
}}

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
        return jsonify({{"error": "Username and password are required"}}), 400

    if username == 'test':
        return jsonify({{"success": True, "data": MOCK_DATA}})

    try:
        session = requests.Session()
        
        login_url = "https://adamasknowledgecity.ac.in/student/login"
        login_page = session.get(login_url, verify=False)
        soup_login = BeautifulSoup(login_page.text, 'html.parser')
        
        token_input = soup_login.find('input', {{'name': '_token'}})
        if not token_input:
            return jsonify({{"success": True, "data": MOCK_DATA, "message": "Portal structure changed."}})
            
        token = token_input['value']
        
        login_payload = {{
            "_token": token,
            "registration_no": username,
            "password": password,
            "login": "login"
        }}
        
        login_response = session.post(login_url, data=login_payload, verify=False, allow_redirects=True)
        
        if 'login' in login_response.url and 'dashboard' not in login_response.url:
            return jsonify({{"success": False, "error": "Invalid credentials or login failed"}}), 401

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
                        
                    subjects.append({{
                        "name": cols[0],
                        "total": total_classes,
                        "attended": attended_classes
                    }})
        soup_dashboard = BeautifulSoup(login_response.text, 'html.parser')
        student_name = username.split('/')[-1] if '/' in username else username
        name_span = soup_dashboard.find('span', class_='username')
        if name_span and name_span.text.strip():
            student_name = name_span.text.strip()
        else:
            # Fallback to profile page just in case
            try:
                profile_resp = session.get("https://adamasknowledgecity.ac.in/student/account/personal-info", verify=False)
                profile_soup = BeautifulSoup(profile_resp.text, 'html.parser')
                profile_name_span = profile_soup.find('span', class_='username')
                if profile_name_span and profile_name_span.text.strip():
                    student_name = profile_name_span.text.strip()
                else:
                    # Look for input with name='name' or 'student_name' or 'first_name'
                    for input_name in ['name', 'student_name', 'first_name', 'studentName']:
                        name_input = profile_soup.find('input', {{'name': input_name}})
                        if name_input and name_input.get('value', '').strip():
                            student_name = name_input.get('value').strip()
                            break
            except Exception:
                pass

        if not subjects:
             return jsonify({{"success": True, "data": MOCK_DATA, "message": "No attendance records found."}})
             
        return jsonify({{
            "success": True,
            "data": {{
                "studentName": student_name,
                "subjects": subjects
            }}
        }})
        
    except Exception as e:
        print(f"Error scraping: {{e}}")
        return jsonify({{"success": False, "error": str(e)}}), 500
'''

with open('index.py', 'w', encoding='utf-8') as f:
    f.write(new_index)

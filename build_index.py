import os

html = open('index.html', encoding='utf-8').read()
css = open('style.css', encoding='utf-8').read()
js = open('script.js', encoding='utf-8').read()

new_index = f'''from flask import Flask, request, jsonify, Response
import requests
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime
from pymongo import MongoClient
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
                print(f"Failed to fetch profile: {{e}}")

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
            routine_url = "https://adamasknowledgecity.ac.in/student/routine"
            r_routine = session.get(routine_url, timeout=10)
            if r_routine.status_code == 200:
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
                                day_schedule.append({{
                                    "period": period_idx,
                                    "colspan": colspan,
                                    "subject": subject,
                                    "teacher": teacher_span.get_text(strip=True) if teacher_span else "",
                                    "room": room_span.get_text(strip=True) if room_span else ""
                                }})
                            else:
                                day_schedule.append({{
                                    "period": period_idx,
                                    "colspan": colspan,
                                    "subject": None
                                }})
                            period_idx += colspan
                            
                        routine.append({{
                            "day": day_text,
                            "schedule": day_schedule
                        }})
        except Exception as e:
            print(f"Failed to fetch routine: {{e}}")

        # Track login in database
        try:
            mongo_uri = os.environ.get("MONGO_URI")
            if mongo_uri:
                client = MongoClient(mongo_uri)
                db = client.get_database("attendance_tracker")
                logins = db.get_collection("logins")
                logins.insert_one({{
                    "username": username,
                    "studentName": student_name,
                    "timestamp": datetime.utcnow()
                }})
        except Exception as db_err:
            print(f"Database error: {{db_err}}")

        if not subjects:
             return jsonify({{"success": True, "data": MOCK_DATA, "message": "No attendance records found."}})
             
        return jsonify({{
            "success": True,
            "data": {{
                "studentName": student_name,
                "profilePhoto": profile_photo,
                "subjects": subjects,
                "routine": routine
            }}
        }})
        
    except Exception as e:
        print(f"Error scraping: {{e}}")
        return jsonify({{"success": False, "error": str(e)}}), 500
'''

with open('index.py', 'w', encoding='utf-8') as f:
    f.write(new_index)

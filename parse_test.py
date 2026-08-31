from bs4 import BeautifulSoup

with open('routine.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup_routine = BeautifulSoup(html, 'html.parser')
table = soup_routine.find('table', class_='table-bordered')
routine = []
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

print(routine)

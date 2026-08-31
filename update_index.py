import sys

with open('script.js', 'r', encoding='utf-8') as f:
    js_data = f.read()

with open('index.py', 'r', encoding='utf-8') as f:
    index_data = f.read()

start_str = 'JS_CONTENT = """'
end_str = '"""\n\nMOCK_DATA ='

start_idx = index_data.find(start_str)
end_idx = index_data.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_index_data = index_data[:start_idx] + start_str + js_data + "\n" + end_str + index_data[end_idx + len(end_str):]
    with open('index.py', 'w', encoding='utf-8') as f:
        f.write(new_index_data)
    print('Updated index.py with new JS_CONTENT')
else:
    print('Could not find JS_CONTENT block:', start_idx, end_idx)

import sys
sys.path.append('c:/Users/Admin/OneDrive/Desktop/ScrapMachine_Project/backend')
import requests
with open('send_report.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('yoyokingguys1143@gmail.com', 'yoyokingguys143@gmail.com, yoyokingguys1143@gmail.com')
with open('send_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

import send_report

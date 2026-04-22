import sys
sys.path.append('c:/Users/Admin/OneDrive/Desktop/ScrapMachine_Project/backend')
from app import app
from flask_jwt_extended import create_access_token

with app.app_context():
    token = create_access_token(identity='1', additional_claims={'role': 'Admin', 'full_name': 'Test'})
    client = app.test_client()
    resp = client.post('/api/reports/send-assignments', headers={'Authorization': f'Bearer {token}'})
    print(resp.json)

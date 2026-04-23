import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.database import test_mysql_connection, MYSQL_CONFIG

print("Current MYSQL_CONFIG:")
print({k: ('***' if k == 'password' else v) for k, v in MYSQL_CONFIG.items()})
print(f"Password being used: {MYSQL_CONFIG.get('password')}")

ok, msg = test_mysql_connection()
print(f"Connection OK: {ok}")
print(f"Message: {msg}")

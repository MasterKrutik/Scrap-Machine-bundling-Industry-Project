import sqlite3
from werkzeug.security import generate_password_hash
conn = sqlite3.connect('scrap_machine.db')
hash_pw = generate_password_hash('admin123')
conn.execute("UPDATE users SET password_hash=? WHERE username='admin'", (hash_pw,))
conn.commit()

import sqlite3
conn = sqlite3.connect('scrap_machine.db')
conn.execute("UPDATE users SET Operator_ID=NULL WHERE username='admin'")
conn.commit()

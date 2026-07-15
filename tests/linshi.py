import sqlite3
c = sqlite3.connect("data/oj.db")
print("Tables:")
for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    print(" ", r[0])
print("Admins:")
for r in c.execute("SELECT id, username, role, is_active FROM users WHERE role='admin'").fetchall():
    print(" ", r)
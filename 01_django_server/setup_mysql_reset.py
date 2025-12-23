import MySQLdb
import sys

def reset_db(user, password, host='127.0.0.1', port=3306):
    print(f"Connecting as {user}@{host}:{port} to RESET database...")
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=password, port=port)
        cursor = conn.cursor()
        
        # 1. Drop Database
        cursor.execute("DROP DATABASE IF EXISTS cdss_db;")
        print("Database 'cdss_db' dropped.")
        
        # 2. Create Database
        cursor.execute("CREATE DATABASE cdss_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print("Database 'cdss_db' created.")
        
        # 3. Create User & Grant (Ensure user exists with correct privileges)
        try:
            cursor.execute("CREATE USER IF NOT EXISTS 'cdss_user'@'localhost' IDENTIFIED BY 'cdss_password';")
        except Exception:
            pass # User might exist
            
        cursor.execute("GRANT ALL PRIVILEGES ON cdss_db.* TO 'cdss_user'@'localhost';")
        cursor.execute("FLUSH PRIVILEGES;")
        print("Privileges granted.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Failed with {user}: {e}")
        return False

# Try credentials (root preferred for DROP/CREATE)
credentials = [
    ('root', 'acorn1234'),
    ('acorn', 'acorn1234'),
    ('root', 'root'), 
]

success = False
for user, pwd in credentials:
    if reset_db(user, pwd):
        print("Database reset successful!")
        success = True
        break
    if reset_db(user, pwd, host='localhost'):
        print("Database reset successful via localhost!")
        success = True
        break

if not success:
    sys.exit(1)

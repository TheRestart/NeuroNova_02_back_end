import MySQLdb
import sys

def try_setup(user, password, host='127.0.0.1', port=3306):
    print(f"Trying connection as {user}@{host}:{port}...")
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=password, port=port)
        cursor = conn.cursor()
        
        # 1. Create Database
        cursor.execute("CREATE DATABASE IF NOT EXISTS cdss_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print("Database 'cdss_db' created or exists.")
        
        # 2. Create User
        try:
            cursor.execute("CREATE USER IF NOT EXISTS 'cdss_user'@'localhost' IDENTIFIED BY 'cdss_password';")
            print("User 'cdss_user'@'localhost' created or exists.")
        except Exception as e:
            print(f"User creation warning: {e}")

        # 3. Grant Privileges
        cursor.execute("GRANT ALL PRIVILEGES ON cdss_db.* TO 'cdss_user'@'localhost';")
        print("Privileges granted to 'cdss_user'.")
        
        # 4. Flush
        cursor.execute("FLUSH PRIVILEGES;")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Failed with {user}: {e}")
        return False

# Try credentials
credentials = [
    ('acorn', 'acorn1234'),
    ('root', 'acorn1234'),
    ('acorn', 'acorn'),
    ('root', 'root'), 
]

success = False
for user, pwd in credentials:
    if try_setup(user, pwd):
        print(f"Successfully set up database using {user}!")
        success = True
        break
    # Try localhost socket if 127.0.0.1 failed
    if try_setup(user, pwd, host='localhost'):
        print(f"Successfully set up database using {user} via localhost!")
        success = True
        break

if not success:
    sys.exit(1)

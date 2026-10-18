import re
import string
import secrets
import sqlite3
import hashlib

# ==========================================
# Database Setup & Cryptography (Hashing)
# ==========================================

def init_db():
    """Initializes a local SQLite database to store password hashes."""
    conn = sqlite3.connect('password_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_hash TEXT UNIQUE
        )
    ''')
    conn.commit()
    return conn

def hash_password(password):
    """
    Hashes the password using SHA-256.
    Note: For production, use bcrypt or Argon2 with unique salts.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def is_password_used_before(conn, password):
    """Checks the database to see if the password hash already exists."""
    pwd_hash = hash_password(password)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM password_history WHERE password_hash = ?', (pwd_hash,))
    return cursor.fetchone() is not None

def save_password(conn, password):
    """Saves a new password hash to the database."""
    pwd_hash = hash_password(password)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO password_history (password_hash) VALUES (?)', (pwd_hash,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Hash already exists

# ==========================================
# Password Strength & Generation
# ==========================================

def evaluate_password(password):
    """Evaluates password strength based on length and character sets."""
    score = 0
    feedback = []

    if len(password) >= 12:
        score += 1
    else:
        feedback.append("Increase length to at least 12 characters.")

    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Add uppercase letters.")

    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Add lowercase letters.")

    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("Add numbers.")

    if re.search(r'[\W_]', password):
        score += 1
    else:
        feedback.append("Add special characters (e.g., !@#$%).")

    return score, feedback

def generate_strong_password(length=16):
    """
    Generates a cryptographically secure password.
    Uses the 'secrets' module, which is designed for managing secrets, 
    unlike the standard 'random' module which is predictable.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Ensure the generated password meets all complexity requirements
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 2
                and any(c in string.punctuation for c in password)):
            return password

# ==========================================
# Main CLI Application
# ==========================================

def main():
    conn = init_db()
    print("=== Password Strength Analyzer ===")
    
    while True:
        user_pwd = input("\nEnter a password to evaluate (or 'q' to quit): ")
        if user_pwd.lower() == 'q':
            break

        # 1. Check History
        if is_password_used_before(conn, user_pwd):
            print("\n[!] SECURITY WARNING: You have used this password before.")
            print("[!] Password reuse makes you vulnerable to credential stuffing attacks.")
        else:
            # 2. Evaluate Strength
            score, feedback = evaluate_password(user_pwd)
            
            print(f"\nStrength Score: {score}/5")
            if score == 5:
                print("[+] Excellent password! It is strong and complex.")
                save_option = input("Do you want to save this to your history to prevent future reuse? (y/n): ")
                if save_option.lower() == 'y':
                    save_password(conn, user_pwd)
                    print("Password hash saved to database.")
            else:
                print("[-] Weak password. See feedback below:")
                for item in feedback:
                    print(f"    - {item}")
                
                # 3. Suggest Alternative
                suggestion = generate_strong_password()
                print(f"\n[?] Consider using a generated secure password instead:")
                print(f"    {suggestion}")

    conn.close()
    print("Exiting Analyzer.")

if __name__ == "__main__":
    main()
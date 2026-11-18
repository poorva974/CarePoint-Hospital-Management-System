"""
create_admin.py - Secure Initial Administrator Account Creation
Hospital Management System (CarePoint)

Allows the system operator to initialize or update an administrative account.
Uses Werkzeug password hashing (scrypt/pbkdf2) so plaintext passwords are never stored.
Accepts credentials interactively via getpass or command-line arguments.
"""

import argparse
import getpass
import re
import sys
from werkzeug.security import generate_password_hash
from database import init_users_table, execute_one, execute_write

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def create_or_update_admin(name=None, email=None, password=None, role="Administrator"):
    """Create or update an administrative/staff user account with secure password hashing."""
    init_users_table()

    if not name:
        name = input("Enter Full Name [Default: System Administrator]: ").strip() or "System Administrator"

    if not email:
        while True:
            email = input("Enter Admin Email: ").strip()
            if EMAIL_REGEX.match(email):
                break
            print("Invalid email format. Please try again.")

    if not password:
        while True:
            p1 = getpass.getpass("Enter Password (min 6 characters): ")
            if len(p1) < 6:
                print("Password must be at least 6 characters long.")
                continue
            p2 = getpass.getpass("Confirm Password: ")
            if p1 != p2:
                print("Passwords do not match. Please try again.")
                continue
            password = p1
            break

    email = email.strip().lower()
    name = name.strip()

    # Hash the password securely using Werkzeug (default method uses scrypt with salt)
    password_hash = generate_password_hash(password)

    # Check if user already exists
    existing = execute_one("SELECT user_id, name, email, role, status FROM users WHERE email = %s", (email,))
    if existing:
        execute_write("""
            UPDATE users 
            SET name = %s, password_hash = %s, role = %s, status = 'Approved'
            WHERE user_id = %s
        """, (name, password_hash, role, existing["user_id"]))
        print(f"User '{email}' ({role}) updated successfully with status 'Approved' and new password hash.")
        return existing["user_id"]
    else:
        res = execute_write("""
            INSERT INTO users (name, email, password_hash, role, status)
            VALUES (%s, %s, %s, %s, 'Approved')
        """, (name, email, password_hash, role))
        print(f"User '{name}' <{email}> created successfully with role '{role}' and status 'Approved' (ID: #{res['lastrowid']}).")
        return res["lastrowid"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or update CarePoint admin user account.")
    parser.add_argument("--name", help="Full name of user", default=None)
    parser.add_argument("--email", help="User email address", default=None)
    parser.add_argument("--password", help="User password", default=None)
    parser.add_argument("--role", help="User role (Administrator or Staff)", default="Administrator")

    args = parser.parse_args()
    create_or_update_admin(name=args.name, email=args.email, password=args.password, role=args.role)


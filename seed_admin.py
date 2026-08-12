"""
Secure Admin Seeder for Valam Platform.
Reads admin credentials from environment variables or command-line arguments.
Credentials are NEVER hardcoded in source files.

Usage:
  python seed_admin.py
  python seed_admin.py --email admin@valam.lk --password YourSecurePassword123! --name "System Administrator"
"""

import os
import sys
import argparse
from app import create_app
from app.extensions import db
from app.models.user import User

def seed_admin(email=None, password=None, name=None, phone=None, role="super_admin"):
    app = create_app(os.getenv("FLASK_CONFIG", "development"))
    
    admin_email = email or os.getenv("ADMIN_EMAIL", "admin@valam.lk")
    admin_password = password or os.getenv("ADMIN_PASSWORD", "ValamAdmin@2026")
    admin_name = name or os.getenv("ADMIN_NAME", "Valam Administrator")
    admin_phone = phone or os.getenv("ADMIN_PHONE", "+94770000000")

    with app.app_context():
        db.create_all()

        user = User.query.filter_by(email=admin_email).first()
        if not user:
            user = User(
                full_name=admin_name,
                email=admin_email,
                phone=admin_phone,
                role=role,
                status="active",
                farming_category="Administrator",
                district="Vavuniya",
                ds_division="Vavuniya Town",
                preferred_language="en",
                onboarding_completed=True,
            )
            user.set_password(admin_password)
            db.session.add(user)
            db.session.commit()
            print(f"[SUCCESS] Admin account created successfully for: {admin_email} (Role: {role})")
        else:
            user.full_name = admin_name
            user.role = role
            user.status = "active"
            user.onboarding_completed = True
            user.set_password(admin_password)
            db.session.commit()
            print(f"[SUCCESS] Admin account updated successfully for: {admin_email} (Role: {role})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Administrator Account without exposing credentials")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password")
    parser.add_argument("--name", help="Admin full name")
    parser.add_argument("--phone", help="Admin phone number")
    parser.add_argument("--role", default="super_admin", help="Admin role (admin or super_admin)")

    args = parser.parse_args()
    seed_admin(
        email=args.email,
        password=args.password,
        name=args.name,
        phone=args.phone,
        role=args.role
    )

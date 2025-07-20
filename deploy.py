#!/usr/bin/env python3
"""
Deployment script for the eCommerce backend
Run this script on your production server after deployment
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Starting deployment process...")
    
    # List of commands to run
    commands = [
        ("python manage.py collectstatic --noinput", "Collecting static files"),
        ("python manage.py migrate", "Running database migrations"),
        ("python manage.py check", "Running system checks"),
    ]
    
    # Run each command
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n❌ Deployment failed at: {description}")
            sys.exit(1)
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📝 Next steps:")
    print("1. Set DEBUG=False in your environment variables")
    print("2. Restart your web server")
    print("3. Test your endpoints:")
    print("   - Admin: https://backend.okpuja.in/admin/")
    print("   - Swagger: https://backend.okpuja.in/swagger/")

if __name__ == "__main__":
    main()

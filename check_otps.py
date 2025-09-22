#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = "db.sqlite3"
EMAIL = "princekumar205086@gmail.com"

def check_otps():
    if not os.path.exists(DB_PATH):
        print("Database not found")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user ID
    cursor.execute("SELECT id FROM accounts_user WHERE email = ?", (EMAIL,))
    user_result = cursor.fetchone()
    
    if not user_result:
        print(f"User not found: {EMAIL}")
        return
    
    user_id = user_result[0]
    print(f"User ID: {user_id}")
    
    # Get recent OTPs
    cursor.execute("""
        SELECT otp_code, otp_type, created_at, is_verified, email
        FROM accounts_otp 
        WHERE user_id = ?
        ORDER BY created_at DESC 
        LIMIT 5
    """, (user_id,))
    
    otps = cursor.fetchall()
    print("\nRecent OTPs:")
    for otp in otps:
        print(f"OTP: {otp[0]}, Type: {otp[1]}, Created: {otp[2]}, Verified: {otp[3]}, Email: {otp[4]}")
    
    conn.close()

if __name__ == "__main__":
    check_otps()
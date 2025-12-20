#!/usr/bin/env python3
"""
Email configuration test script
Run this to test your email setup before using the main system
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email_configuration():
    """Test email configuration"""
    
    # Load environment variables
    load_dotenv()
    
    # Get email configuration
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    print("Testing Email Configuration...")
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"Sender Email: {sender_email}")
    print(f"Password: {'*' * len(sender_password) if sender_password else 'NOT SET'}")
    print("-" * 50)
    
    # Check if all required fields are set
    if not all([smtp_server, sender_email, sender_password]):
        print("❌ ERROR: Missing email configuration!")
        print("Please check your .env file and ensure all fields are set:")
        print("- SMTP_SERVER")
        print("- SENDER_EMAIL") 
        print("- SENDER_PASSWORD")
        return False
    
    # Test SMTP connection
    try:
        print("Testing SMTP connection...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print("✅ TLS connection established")
        
        print("Testing authentication...")
        server.login(sender_email, sender_password)
        print("✅ Authentication successful")
        
        server.quit()
        print("✅ Email configuration is working correctly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("Please check your email and password/app-password")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("Please check your SMTP server and port settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def send_test_email():
    """Send a test email to verify everything works"""
    
    # Load environment variables
    load_dotenv()
    
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    # Get test recipient email
    test_email = input("Enter test recipient email address: ").strip()
    
    if not test_email:
        print("No email provided. Skipping test email.")
        return
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = test_email
        msg['Subject'] = "Test Email - Test Management System"
        
        body = """
This is a test email from the Test Management System.

If you receive this email, your email configuration is working correctly!

Best regards,
Test Management System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print(f"Sending test email to {test_email}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, test_email, text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    if test_email_configuration():
        print("\n" + "=" * 60)
        send_test_email()
    
    print("\n" + "=" * 60)
    print("Test completed!")

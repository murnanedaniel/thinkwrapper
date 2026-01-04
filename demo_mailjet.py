#!/usr/bin/env python3
"""
Demo script to test Mailjet email integration.

This script tests the email sending functionality with a real Mailjet API.
Set MAILJET_API_KEY, MAILJET_API_SECRET and MAILJET_TEST_EMAIL environment variables before running.

Usage:
    export MAILJET_API_KEY="your-mailjet-api-key"
    export MAILJET_API_SECRET="your-mailjet-api-secret"
    export MAILJET_TEST_EMAIL="your-email@example.com"
    python demo_mailjet.py
"""

import os
import sys
from app import create_app
from app.services import send_email
from app.email_templates import (
    get_test_template,
    get_welcome_template,
    get_newsletter_template
)


def test_mailjet_integration():
    """Test Mailjet email delivery with real API."""
    
    # Check environment variables
    api_key = os.environ.get("MAILJET_API_KEY")
    api_secret = os.environ.get("MAILJET_API_SECRET")
    test_email = os.environ.get("MAILJET_TEST_EMAIL")
    
    if not api_key:
        print("❌ Error: MAILJET_API_KEY not configured")
        print("   Please set a valid Mailjet API key:")
        print("   export MAILJET_API_KEY='your-api-key'")
        return False
    
    if not api_secret:
        print("❌ Error: MAILJET_API_SECRET not configured")
        print("   Please set a valid Mailjet API secret:")
        print("   export MAILJET_API_SECRET='your-api-secret'")
        return False
    
    if not test_email or test_email == "test@example.com":
        print("⚠️  Warning: MAILJET_TEST_EMAIL not set")
        print("   Using default: test@example.com")
        print("   Set your email to receive test emails:")
        print("   export MAILJET_TEST_EMAIL='your-email@example.com'")
        test_email = "test@example.com"
    
    print("=" * 60)
    print("Mailjet Email Integration Test")
    print("=" * 60)
    print(f"📧 Test email: {test_email}")
    print(f"🔑 API Key: {api_key[:10]}..." if len(api_key) > 10 else "🔑 API Key: [hidden]")
    print()
    
    # Create Flask app context
    app = create_app({"TESTING": False})
    
    with app.app_context():
        # Test 1: Simple test email
        print("Test 1: Sending test email...")
        html_content = get_test_template()
        result = send_email(
            test_email,
            "Test Email - Mailjet Integration",
            html_content
        )
        
        if result:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email")
            return False
        
        print()
        
        # Test 2: Welcome email with template
        print("Test 2: Sending welcome email...")
        html_content = get_welcome_template("Test User")
        result = send_email(
            test_email,
            "Welcome to ThinkWrapper Newsletter",
            html_content
        )
        
        if result:
            print("✅ Welcome email sent successfully!")
        else:
            print("❌ Failed to send welcome email")
            return False
        
        print()
        
        # Test 3: Newsletter email with custom content
        print("Test 3: Sending newsletter email...")
        newsletter_content = """
            <h2>Weekly Tech Update</h2>
            <p>Here are this week's top stories:</p>
            <ul>
                <li><strong>AI Breakthrough:</strong> New language model achieves human-level performance</li>
                <li><strong>Cloud Computing:</strong> Latest trends in serverless architecture</li>
                <li><strong>Security:</strong> Best practices for API authentication</li>
            </ul>
            <p>Stay tuned for more updates!</p>
        """
        html_content = get_newsletter_template(
            "Weekly Tech Update",
            newsletter_content,
            preheader="Your weekly tech digest is here!"
        )
        result = send_email(
            test_email,
            "Weekly Tech Update - ThinkWrapper",
            html_content
        )
        
        if result:
            print("✅ Newsletter email sent successfully!")
        else:
            print("❌ Failed to send newsletter email")
            return False
    
    print()
    print("=" * 60)
    print("✅ All email tests passed!")
    print("=" * 60)
    print(f"📬 Check {test_email} for 3 test emails")
    print()
    
    return True


def main():
    """Main function."""
    try:
        success = test_mailjet_integration()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

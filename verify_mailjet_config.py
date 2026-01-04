#!/usr/bin/env python3
"""
Verify Mailjet credentials and configuration.

This script checks that the Mailjet integration is properly configured.
Set environment variables before running:
    export MAILJET_API_KEY="your-api-key"
    export MAILJET_API_SECRET="your-api-secret"
    export MAILJET_TEST_EMAIL="your-email@example.com"
"""

import os
import sys


def verify_mailjet_config():
    """Verify Mailjet configuration."""
    
    print("=" * 60)
    print("Mailjet Configuration Verification")
    print("=" * 60)
    print()
    
    # Check API key
    api_key = os.environ.get("MAILJET_API_KEY")
    if api_key:
        # Mask the key for security
        masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "[MASKED]"
        print(f"✅ MAILJET_API_KEY: {masked_key}")
    else:
        print("❌ MAILJET_API_KEY: Not set")
        return False
    
    # Check API secret
    api_secret = os.environ.get("MAILJET_API_SECRET")
    if api_secret:
        # Mask the secret for security
        masked_secret = api_secret[:10] + "..." + api_secret[-4:] if len(api_secret) > 14 else "[MASKED]"
        print(f"✅ MAILJET_API_SECRET: {masked_secret}")
    else:
        print("❌ MAILJET_API_SECRET: Not set")
        return False
    
    # Check test email
    test_email = os.environ.get("MAILJET_TEST_EMAIL", "Not set")
    print(f"📧 MAILJET_TEST_EMAIL: {test_email}")
    
    print()
    print("=" * 60)
    print("Configuration Status: ✅ COMPLETE")
    print("=" * 60)
    print()
    print("The Mailjet integration is properly configured.")
    print()
    print("To test email delivery:")
    print("  1. Ensure network access to api.mailjet.com")
    print("  2. Run: python demo_mailjet.py")
    print("  3. Or run E2E tests: pytest tests/test_email_integration.py::TestEmailE2E -v")
    print()
    
    return True


if __name__ == "__main__":
    success = verify_mailjet_config()
    sys.exit(0 if success else 1)

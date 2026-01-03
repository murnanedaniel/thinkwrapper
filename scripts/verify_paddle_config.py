#!/usr/bin/env python
"""
Paddle Configuration Verification Script

This script verifies that Paddle is properly configured by:
1. Checking all required environment variables are set
2. Verifying the payment service can initialize
3. Testing the configuration values

Usage:
    python scripts/verify_paddle_config.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print colored header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")


def check_env_var(name, required=True):
    """Check if environment variable is set."""
    value = os.getenv(name)
    if value:
        # Mask sensitive values
        if len(value) > 8:
            masked = f"{value[:4]}...{value[-4:]}"
        else:
            masked = "*" * len(value)
        print_success(f"{name}: {masked}")
        return True
    else:
        if required:
            print_error(f"{name}: Not set (REQUIRED)")
        else:
            print_warning(f"{name}: Not set (optional)")
        return not required


def main():
    """Run configuration verification."""
    print_header("Paddle Configuration Verification")
    
    all_ok = True
    
    # Check required environment variables
    print_info("Checking environment variables...")
    print()
    
    required_vars = [
        'PADDLE_VENDOR_ID',
        'PADDLE_API_KEY',
        'PADDLE_WEBHOOK_SECRET',
    ]
    
    optional_vars = [
        'PADDLE_SANDBOX',
    ]
    
    for var in required_vars:
        if not check_env_var(var, required=True):
            all_ok = False
    
    for var in optional_vars:
        check_env_var(var, required=False)
    
    # Check PADDLE_SANDBOX value
    sandbox_mode = os.getenv('PADDLE_SANDBOX', 'true').lower()
    print()
    if sandbox_mode == 'true':
        print_info("Mode: SANDBOX (testing)")
        print_info("API URL: https://sandbox-api.paddle.com")
    else:
        print_warning("Mode: PRODUCTION (live payments)")
        print_info("API URL: https://api.paddle.com")
    
    if not all_ok:
        print()
        print_error("Configuration incomplete!")
        print()
        print_info("To fix:")
        print_info("1. Copy .env.example to .env")
        print_info("2. Fill in your Paddle credentials")
        print_info("3. See docs/guides/PADDLE_SETUP.md for help")
        return 1
    
    # Try to import and initialize the service
    print()
    print_info("Testing service initialization...")
    print()
    
    try:
        from app import create_app
        from app.payment_service import PaddlePaymentService
        
        app = create_app({'TESTING': True})
        
        with app.app_context():
            service = PaddlePaymentService()
            
            # Check service attributes
            if service.vendor_id:
                print_success(f"Vendor ID configured")
            else:
                print_error("Vendor ID not loaded")
                all_ok = False
            
            if service.api_key:
                print_success(f"API Key configured")
            else:
                print_error("API Key not loaded")
                all_ok = False
            
            if service.webhook_secret:
                print_success(f"Webhook Secret configured")
            else:
                print_error("Webhook Secret not loaded")
                all_ok = False
            
            print_success(f"Service initialized successfully")
            
    except Exception as e:
        print_error(f"Service initialization failed: {str(e)}")
        all_ok = False
    
    # Print summary
    print()
    print_header("Summary")
    
    if all_ok:
        print_success("✨ Paddle is properly configured!")
        print()
        print_info("Next steps:")
        print_info("1. Run tests: python -m pytest tests/test_payment*.py")
        print_info("2. Test webhooks: python scripts/test_paddle_webhook.py")
        print_info("3. See docs/guides/PADDLE_SETUP.md for usage examples")
        return 0
    else:
        print_error("Configuration has issues")
        print()
        print_info("See docs/guides/PADDLE_SETUP.md for setup instructions")
        return 1


if __name__ == '__main__':
    sys.exit(main())

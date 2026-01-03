#!/usr/bin/env python
"""
Paddle Webhook Test Script

This script helps test Paddle webhook integration by:
1. Generating valid webhook signatures
2. Sending test webhooks to your local endpoint
3. Verifying webhook processing

Usage:
    python scripts/test_paddle_webhook.py

Requirements:
    - Flask app running locally on port 5000
    - PADDLE_WEBHOOK_SECRET set in .env file
"""

import os
import sys
import json
import hmac
import hashlib
import requests
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WEBHOOK_URL = os.getenv('WEBHOOK_TEST_URL', 'http://localhost:5000/api/payment/webhook')
WEBHOOK_SECRET = os.getenv('PADDLE_WEBHOOK_SECRET')

# ANSI color codes for pretty output
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


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")


def generate_webhook_signature(payload: str, secret: str) -> str:
    """Generate a valid Paddle webhook signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def send_webhook(event_type: str, event_data: dict) -> tuple:
    """
    Send a test webhook to the local endpoint.
    
    Returns:
        tuple: (success: bool, status_code: int, response_data: dict)
    """
    webhook_payload = {
        'event_type': event_type,
        'event_id': f'evt_test_{uuid.uuid4().hex[:16]}',
        'occurred_at': datetime.now().isoformat() + 'Z',
        'data': event_data
    }
    
    payload_str = json.dumps(webhook_payload)
    signature = generate_webhook_signature(payload_str, WEBHOOK_SECRET)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=payload_str,
            headers={
                'Content-Type': 'application/json',
                'Paddle-Signature': signature
            },
            timeout=5
        )
        
        return (
            response.status_code == 200,
            response.status_code,
            response.json() if response.text else {}
        )
    except requests.exceptions.ConnectionError:
        return False, 0, {'error': 'Connection failed - is the server running?'}
    except Exception as e:
        return False, 0, {'error': str(e)}


def test_transaction_completed():
    """Test transaction.completed webhook."""
    print_header("Test 1: Transaction Completed")
    
    event_data = {
        'id': 'txn_test_12345',
        'customer_id': 'cus_test_67890',
        'amount': '29.99',
        'currency_code': 'USD',
        'status': 'completed',
        'custom_data': {
            'user_id': 'test_user_123',
            'plan': 'premium'
        }
    }
    
    success, status_code, response = send_webhook('transaction.completed', event_data)
    
    if success:
        print_success(f"Webhook accepted (Status: {status_code})")
        print_info(f"Response: {json.dumps(response, indent=2)}")
        return True
    else:
        print_error(f"Webhook failed (Status: {status_code})")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return False


def test_subscription_created():
    """Test subscription.created webhook."""
    print_header("Test 2: Subscription Created")
    
    event_data = {
        'id': 'sub_test_12345',
        'customer_id': 'cus_test_67890',
        'status': 'active',
        'items': [
            {
                'price_id': 'pri_test_monthly',
                'quantity': 1
            }
        ],
        'next_billed_at': '2024-02-15T00:00:00.000Z'
    }
    
    success, status_code, response = send_webhook('subscription.created', event_data)
    
    if success:
        print_success(f"Webhook accepted (Status: {status_code})")
        print_info(f"Response: {json.dumps(response, indent=2)}")
        return True
    else:
        print_error(f"Webhook failed (Status: {status_code})")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return False


def test_subscription_cancelled():
    """Test subscription.cancelled webhook."""
    print_header("Test 3: Subscription Cancelled")
    
    event_data = {
        'id': 'sub_test_12345',
        'customer_id': 'cus_test_67890',
        'status': 'cancelled',
        'cancelled_at': datetime.now().isoformat() + 'Z'
    }
    
    success, status_code, response = send_webhook('subscription.cancelled', event_data)
    
    if success:
        print_success(f"Webhook accepted (Status: {status_code})")
        print_info(f"Response: {json.dumps(response, indent=2)}")
        return True
    else:
        print_error(f"Webhook failed (Status: {status_code})")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return False


def test_invalid_signature():
    """Test webhook with invalid signature (should be rejected)."""
    print_header("Test 4: Invalid Signature (Should Fail)")
    
    event_data = {'id': 'txn_test_invalid'}
    webhook_payload = {
        'event_type': 'transaction.completed',
        'data': event_data
    }
    
    payload_str = json.dumps(webhook_payload)
    invalid_signature = 'this_is_not_a_valid_signature'
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=payload_str,
            headers={
                'Content-Type': 'application/json',
                'Paddle-Signature': invalid_signature
            },
            timeout=5
        )
        
        if response.status_code == 401:
            print_success("Invalid signature correctly rejected (Status: 401)")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Security issue: Invalid signatures should be rejected!")
            return False
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def test_subscription_past_due():
    """Test subscription.past_due webhook."""
    print_header("Test 5: Subscription Past Due")
    
    event_data = {
        'id': 'sub_test_12345',
        'customer_id': 'cus_test_67890',
        'status': 'past_due',
        'next_billing_date': '2024-01-20T00:00:00.000Z'
    }
    
    success, status_code, response = send_webhook('subscription.past_due', event_data)
    
    if success:
        print_success(f"Webhook accepted (Status: {status_code})")
        print_info(f"Response: {json.dumps(response, indent=2)}")
        return True
    else:
        print_error(f"Webhook failed (Status: {status_code})")
        print_error(f"Response: {json.dumps(response, indent=2)}")
        return False


def main():
    """Run all webhook tests."""
    print_header("Paddle Webhook Integration Test")
    
    # Check configuration
    if not WEBHOOK_SECRET:
        print_error("PADDLE_WEBHOOK_SECRET not set in environment!")
        print_info("Please set it in your .env file")
        sys.exit(1)
    
    print_info(f"Webhook URL: {WEBHOOK_URL}")
    print_info(f"Webhook Secret: {'*' * (len(WEBHOOK_SECRET) - 4)}{WEBHOOK_SECRET[-4:]}")
    print_info("Make sure your Flask app is running on the configured port")
    
    # Run tests
    tests = [
        ("Transaction Completed", test_transaction_completed),
        ("Subscription Created", test_subscription_created),
        ("Subscription Cancelled", test_subscription_cancelled),
        ("Invalid Signature", test_invalid_signature),
        ("Subscription Past Due", test_subscription_past_due),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print_success("All tests passed! ✨")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

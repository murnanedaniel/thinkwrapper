#!/usr/bin/env python3
"""Validate environment configuration for ThinkWrapper."""
import os
import sys

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_env_var(name, required=True, for_env="all"):
    """Check if environment variable is set."""
    value = os.environ.get(name)
    env = os.environ.get("FLASK_ENV", "development")

    # Skip non-required vars in development
    if not required and env == "development":
        if value:
            print(f"{GREEN}✓{RESET} {name} (optional, set)")
        else:
            print(f"{YELLOW}○{RESET} {name} (optional, not set)")
        return True

    # Check if required only for specific environment
    if for_env != "all" and env != for_env:
        if value:
            print(f"{GREEN}✓{RESET} {name} (set)")
        else:
            print(f"{YELLOW}○{RESET} {name} (not required for {env})")
        return True

    if value:
        # Mask sensitive values
        if len(value) > 10:
            display_value = f"{value[:4]}...{value[-4:]}"
        else:
            display_value = "***"
        print(f"{GREEN}✓{RESET} {name} = {display_value}")
        return True
    else:
        print(f"{RED}✗{RESET} {name} (missing)")
        return False


def main():
    """Run environment validation."""
    print("=" * 60)
    print("ThinkWrapper Environment Validation")
    print("=" * 60)

    env = os.environ.get("FLASK_ENV", "development")
    print(f"\nEnvironment: {env}\n")

    all_valid = True

    # Flask Configuration
    print("Flask Configuration:")
    all_valid = all_valid and check_env_var("FLASK_ENV", required=False)
    all_valid = all_valid and check_env_var(
        "SECRET_KEY", required=True, for_env="production"
    )

    # Database
    print("\nDatabase:")
    all_valid = all_valid and check_env_var("DATABASE_URL", required=True)

    # Redis (for Celery)
    print("\nRedis:")
    all_valid = all_valid and check_env_var("REDIS_URL", required=False)

    # API Keys
    print("\nAPI Keys:")
    all_valid = all_valid and check_env_var("ANTHROPIC_API_KEY", required=False)
    all_valid = all_valid and check_env_var("BRAVE_SEARCH_API_KEY", required=False)
    all_valid = all_valid and check_env_var("SENDGRID_API_KEY", required=False)

    # Paddle
    print("\nPaddle (Payment Processing):")
    all_valid = all_valid and check_env_var("PADDLE_VENDOR_ID", required=False)
    all_valid = all_valid and check_env_var("PADDLE_API_KEY", required=False)
    all_valid = all_valid and check_env_var("PADDLE_PUBLIC_KEY", required=False)
    all_valid = all_valid and check_env_var("PADDLE_WEBHOOK_SECRET", required=False)

    # Google OAuth
    print("\nGoogle OAuth:")
    all_valid = all_valid and check_env_var("GOOGLE_CLIENT_ID", required=False)
    all_valid = all_valid and check_env_var("GOOGLE_CLIENT_SECRET", required=False)

    # CORS
    print("\nSecurity:")
    all_valid = all_valid and check_env_var("CORS_ORIGINS", required=False)

    print("\n" + "=" * 60)

    if all_valid:
        print(f"{GREEN}✓ All required environment variables are set!{RESET}")
        return 0
    else:
        print(f"{RED}✗ Some required environment variables are missing.{RESET}")
        print(f"\nCopy .env.template to .env and fill in the values:")
        print(f"  cp .env.template .env")
        return 1


if __name__ == "__main__":
    sys.exit(main())

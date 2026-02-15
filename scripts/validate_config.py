#!/usr/bin/env python3
"""
Configuration Validator and Health Check Script

This script validates the application configuration and checks
if all required services are accessible.

Usage:
    python scripts/validate_config.py
    python scripts/validate_config.py --env production
    doppler run -- python scripts/validate_config.py
"""

import argparse
import os
import sys

from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


def _supports_unicode_output():
    """Return True if current stdout encoding can print common unicode symbols."""
    encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    try:
        "✓✗⚠ℹ".encode(encoding)
        return True
    except Exception:
        return False


UNICODE_OK = _supports_unicode_output()
SUCCESS_ICON = "✓" if UNICODE_OK else "[OK]"
ERROR_ICON = "✗" if UNICODE_OK else "[ERROR]"
WARNING_ICON = "⚠" if UNICODE_OK else "[WARN]"
INFO_ICON = "ℹ" if UNICODE_OK else "[INFO]"


def safe_print(text=""):
    """Print text without crashing on limited console encodings."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        fallback = text.encode(encoding, errors='replace').decode(encoding)
        print(fallback)


def print_header(text):
    """Print a formatted header."""
    safe_print(f"\n{Fore.CYAN}{'=' * 70}")
    safe_print(f"{Fore.CYAN}{text.center(70)}")
    safe_print(f"{Fore.CYAN}{'=' * 70}\n")


def print_success(text):
    """Print success message."""
    safe_print(f"{Fore.GREEN}{SUCCESS_ICON} {text}")


def print_error(text):
    """Print error message."""
    safe_print(f"{Fore.RED}{ERROR_ICON} {text}")


def print_warning(text):
    """Print warning message."""
    safe_print(f"{Fore.YELLOW}{WARNING_ICON} {text}")


def print_info(text):
    """Print info message."""
    safe_print(f"{Fore.BLUE}{INFO_ICON} {text}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Flask portfolio configuration and service connectivity."
    )
    parser.add_argument(
        '--env',
        choices=['development', 'production', 'testing', 'doppler'],
        help='Target environment to validate. Defaults to current environment settings.',
    )
    return parser.parse_args()


def apply_environment_override(target_env):
    """Apply --env override before config modules are imported."""
    if not target_env:
        return

    if target_env == 'doppler':
        # Mark as Doppler mode for configuration detection.
        os.environ.setdefault('DOPPLER_ENVIRONMENT', 'manual')
    else:
        os.environ['FLASK_ENV'] = target_env


def check_python_version():
    """Check Python version."""
    print_header("Python Version Check")
    major, minor = sys.version_info[:2]
    version = f"{major}.{minor}"

    if major >= 3 and minor >= 8:
        print_success(f"Python {version} (Supported)")
        return True

    print_error(f"Python {version} (Requires Python 3.8+)")
    return False


def check_config_source():
    """Check configuration source (Doppler or .env)."""
    print_header("Configuration Source")

    from config import DopplerConfig

    if DopplerConfig.is_doppler_active():
        doppler_info = DopplerConfig.get_doppler_info() or {}
        print_success("Doppler configuration active")
        print_info(f"  Project: {doppler_info.get('project', 'N/A')}")
        print_info(f"  Config: {doppler_info.get('config', 'N/A')}")
        print_info(f"  Environment: {doppler_info.get('environment', 'N/A')}")
        return True

    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        print_success(f".env file found: {env_file}")
        return True

    print_warning("No .env file found and Doppler is not active")
    print_info("Create .env from .env.example or use Doppler")
    return False


def check_required_config():
    """Check required configuration values."""
    print_header("Required Configuration")

    from config import Config

    is_valid, missing = Config.validate_required_config()

    if is_valid:
        print_success("All required configuration values are set")
        return True

    print_error("Missing required configuration:")
    for key in missing:
        safe_print(f"  - {key}")
    return False


def check_database_connection():
    """Check database connectivity."""
    print_header("Database Connection")

    try:
        from app import app, db
        with app.app_context():
            db.engine.connect()
            driver = app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]
            print_success(f"Database connected: {driver}")
        return True
    except Exception as exc:
        print_error(f"Database connection failed: {exc}")
        return False


def check_redis_connection():
    """Check Redis connectivity."""
    print_header("Redis Connection")

    try:
        import redis
        from config import Config

        redis_url = Config.REDIS_URL
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        safe_endpoint = redis_url.split('@')[-1] if '@' in redis_url else redis_url
        print_success(f"Redis connected: {safe_endpoint}")
        return True
    except ImportError:
        print_warning("Redis library not installed (pip install redis)")
        print_info("Redis is optional but recommended for production")
        return True
    except Exception as exc:
        print_warning(f"Redis connection failed: {exc}")
        print_info("Redis is optional but recommended for production")
        return True


def check_email_config():
    """Check email configuration."""
    print_header("Email Configuration")

    from config import Config

    if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
        print_success(f"Email configured: {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
        print_info(f"  Username: {Config.MAIL_USERNAME}")
        print_info(f"  TLS: {Config.MAIL_USE_TLS}")
        return True

    print_warning("Email not fully configured")
    print_info("Set MAIL_USERNAME and MAIL_PASSWORD in environment configuration")
    return False


def check_admin_credentials():
    """Check admin credentials."""
    print_header("Admin Credentials")

    from config import Config

    if Config.ADMIN_USERNAME and Config.ADMIN_PASSWORD_HASH:
        if (
            'dev-secret' in Config.ADMIN_PASSWORD_HASH
            or Config.ADMIN_PASSWORD_HASH.startswith('scrypt:32768:8:1$zQX8')
        ):
            print_warning("Using default admin credentials")
            print_info("Generate secure password hash:")
            print_info(
                "  python -c \"from werkzeug.security import generate_password_hash; "
                "print(generate_password_hash('your-password'))\""
            )
        else:
            print_success(f"Admin configured: {Config.ADMIN_USERNAME}")
        return True

    print_error("Admin credentials not configured")
    return False


def check_security_settings():
    """Check security settings."""
    print_header("Security Settings")

    from config import Config

    issues = []

    # Check SECRET_KEY
    if 'dev-secret' in Config.SECRET_KEY or len(Config.SECRET_KEY) < 32:
        issues.append("Weak SECRET_KEY detected")
        print_error("SECRET_KEY is using default or is too short")
        print_info("Generate: python -c \"import secrets; print(secrets.token_hex(32))\"")
    else:
        print_success("SECRET_KEY configured")

    # Check HTTPS settings
    if Config.FLASK_ENV == 'production':
        if not Config.SESSION_COOKIE_SECURE:
            issues.append("SESSION_COOKIE_SECURE should be True in production")
            print_warning("SESSION_COOKIE_SECURE is False (not suitable for production)")
        else:
            print_success("Secure cookies enabled")

    return len(issues) == 0


def display_config_summary():
    """Display non-sensitive configuration summary."""
    print_header("Configuration Summary")

    from config import Config

    config_dict = Config.get_all_config()
    for key, value in sorted(config_dict.items()):
        if isinstance(value, (str, int, bool, float)):
            safe_print(f"{Fore.WHITE}{key}: {Fore.YELLOW}{value}")


def main(target_env=None):
    """Main validation routine."""
    apply_environment_override(target_env)

    safe_print(f"{Fore.MAGENTA}")
    safe_print("  ____             __ _         __     __    _ _     _       _             ")
    safe_print(" / ___|___  _ __  / _(_) __ _   \\ \\   / /_ _| (_) __| | __ _| |_ ___  _ __ ")
    safe_print("| |   / _ \\| '_ \\| |_| |/ _` |   \\ \\ / / _` | | |/ _` |/ _` | __/ _ \\| '__|")
    safe_print("| |__| (_) | | | |  _| | (_| |    \\ V / (_| | | | (_| | (_| | || (_) | |   ")
    safe_print(" \\____\\___/|_| |_|_| |_|\\__, |     \\_/ \\__,_|_|_|\\__,_|\\__,_|\\__\\___/|_|   ")
    safe_print("                        |___/                                               ")
    safe_print(Style.RESET_ALL)

    if target_env:
        print_info(f"Environment override active: {target_env}")

    checks = [
        ("Python Version", check_python_version),
        ("Configuration Source", check_config_source),
        ("Required Config", check_required_config),
        ("Database", check_database_connection),
        ("Redis", check_redis_connection),
        ("Email", check_email_config),
        ("Admin Credentials", check_admin_credentials),
        ("Security", check_security_settings),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as exc:
            print_error(f"{name} check failed with exception: {exc}")
            results[name] = False

    display_config_summary()
    print_header("Validation Summary")

    passed = sum(1 for result in results.values() if result)
    total = len(results)
    status_color = Fore.GREEN if passed == total else Fore.YELLOW
    safe_print(f"\n{Fore.WHITE}Checks passed: {status_color}{passed}/{total}")

    if passed == total:
        safe_print(f"\n{Fore.GREEN}{'=' * 70}")
        print_success("All checks passed! Your configuration is ready.")
        safe_print(f"{Fore.GREEN}{'=' * 70}\n")
        return 0

    safe_print(f"\n{Fore.YELLOW}{'=' * 70}")
    print_warning("Some checks failed. Review the output above.")
    safe_print(f"{Fore.YELLOW}{'=' * 70}\n")
    print_info("See docs/CONFIG.md for configuration help")
    return 1


if __name__ == "__main__":
    args = parse_args()
    try:
        sys.exit(main(args.env))
    except KeyboardInterrupt:
        safe_print(f"\n{Fore.YELLOW}Validation interrupted by user")
        sys.exit(130)
    except Exception as exc:
        safe_print(f"\n{Fore.RED}Validation failed with unexpected error:")
        safe_print(f"{Fore.RED}{exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

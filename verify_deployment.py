#!/usr/bin/env python3
"""
Pre-Deployment Verification Script
Checks all configuration files for Railway deployment
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_file_exists(filepath):
    """Check if file exists"""
    return Path(filepath).exists()

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return None

def check_in_file(filepath, search_text, description):
    """Check if text exists in file"""
    content = read_file(filepath)
    if content is None:
        print_error(f"{description} - File not readable: {filepath}")
        return False
    
    if search_text in content:
        print_success(f"{description}")
        return True
    else:
        print_error(f"{description}")
        return False

def main():
    print_header("RAILWAY DEPLOYMENT VERIFICATION SCRIPT")
    
    # Track overall status
    all_checks_passed = True
    
    # ========================================
    # CHECK 1: .ENV FILE
    # ========================================
    print_header("CHECK 1: .env FILE (Local Development)")
    
    env_file = '.env'
    if not check_file_exists(env_file):
        print_error(f"{env_file} not found!")
        all_checks_passed = False
    else:
        print_success(f"{env_file} exists")
        
        # Check Gmail SMTP settings
        env_content = read_file(env_file)
        
        checks = [
            ('EMAIL_HOST=smtp.gmail.com', 'Gmail SMTP host configured'),
            ('EMAIL_PORT=587', 'Gmail SMTP port configured'),
            ('EMAIL_USE_TLS=True', 'TLS enabled for Gmail'),
            ('EMAIL_HOST_USER=', 'Email host user defined'),
            ('EMAIL_HOST_PASSWORD=', 'Email password/app password defined'),
            ('DEFAULT_FROM_EMAIL=', 'Default from email defined'),
        ]
        
        for search, desc in checks:
            if search in env_content:
                print_success(desc)
            else:
                print_error(desc)
                all_checks_passed = False
        
        # Extract actual email
        for line in env_content.split('\n'):
            if 'EMAIL_HOST_USER=' in line and not line.startswith('#'):
                email = line.split('=')[1].strip()
                print_info(f"Email account: {email}")
                break
    
    # ========================================
    # CHECK 2: BASE.PY
    # ========================================
    print_header("CHECK 2: config/settings/base.py")
    
    base_file = 'config/settings/base.py'
    if not check_file_exists(base_file):
        print_error(f"{base_file} not found!")
        all_checks_passed = False
    else:
        print_success(f"{base_file} exists")
        
        base_content = read_file(base_file)
        
        # Check for defaults in config() calls
        checks = [
            ("config('SECRET_KEY'", 'SECRET_KEY uses config()'),
            ("config('DB_PASSWORD'", 'DB_PASSWORD uses config()'),
            ("default=", 'Has default values (CRITICAL for Railway)'),
        ]
        
        for search, desc in checks:
            if search in base_content:
                print_success(desc)
            else:
                print_warning(f"{desc} - May cause Railway build errors")
                
        # Check email settings in base.py
        if 'EMAIL_HOST' in base_content:
            print_info("Email settings found in base.py")
            if 'smtp.gmail.com' in base_content:
                print_success("Gmail SMTP configured in base.py")
            else:
                print_warning("Gmail SMTP not explicitly set in base.py (might be in other settings)")
        else:
            print_info("Email settings not in base.py (likely in production.py)")
    
    # ========================================
    # CHECK 3: PRODUCTION.PY
    # ========================================
    print_header("CHECK 3: config/settings/production.py")
    
    prod_file = 'config/settings/production.py'
    if not check_file_exists(prod_file):
        print_error(f"{prod_file} not found!")
        all_checks_passed = False
    else:
        print_success(f"{prod_file} exists")
        
        prod_content = read_file(prod_file)
        
        # Critical checks for Railway
        critical_checks = [
            ("from .base import *", "Imports from base.py"),
            ("import dj_database_url", "dj_database_url imported"),
            ("DATABASE_URL", "Uses DATABASE_URL for Railway"),
            ("DATABASES = {", "DATABASES setting defined"),
            ("dj_database_url.config", "Uses dj_database_url parser"),
        ]
        
        for search, desc in critical_checks:
            if check_in_file(prod_file, search, desc):
                pass
            else:
                all_checks_passed = False
        
        # Check email settings
        print("\n--- Email Settings in production.py ---")
        email_checks = [
            ('EMAIL_HOST', 'EMAIL_HOST defined'),
            ('EMAIL_PORT', 'EMAIL_PORT defined'),
            ('EMAIL_USE_TLS', 'EMAIL_USE_TLS defined'),
            ('EMAIL_HOST_USER', 'EMAIL_HOST_USER defined'),
            ('EMAIL_HOST_PASSWORD', 'EMAIL_HOST_PASSWORD defined'),
        ]
        
        for search, desc in email_checks:
            if search in prod_content:
                print_success(desc)
                # Check if it's hardcoded or using config()
                for line in prod_content.split('\n'):
                    if search in line and '=' in line:
                        if 'config(' in line or 'environ' in line:
                            print_info(f"  → Uses environment variable ✓")
                        elif 'smtp.gmail.com' in line:
                            print_success(f"  → Gmail SMTP hardcoded (OK for testing)")
                        break
            else:
                print_warning(f"{desc} - Not found")
        
        # Security settings
        print("\n--- Security Settings ---")
        security_checks = [
            ('DEBUG = False', 'DEBUG disabled'),
            ('ALLOWED_HOSTS', 'ALLOWED_HOSTS configured'),
            ('.railway.app', 'Railway domain in ALLOWED_HOSTS'),
            ('SECURE_SSL_REDIRECT', 'SSL redirect enabled'),
        ]
        
        for search, desc in security_checks:
            check_in_file(prod_file, search, desc)
    
    # ========================================
    # CHECK 4: DEVELOPMENT.PY
    # ========================================
    print_header("CHECK 4: config/settings/development.py")
    
    dev_file = 'config/settings/development.py'
    if not check_file_exists(dev_file):
        print_warning(f"{dev_file} not found (optional)")
    else:
        print_success(f"{dev_file} exists")
        
        dev_content = read_file(dev_file)
        
        checks = [
            ("from .base import *", "Imports from base.py"),
            ("DEBUG = True", "DEBUG enabled for development"),
        ]
        
        for search, desc in checks:
            check_in_file(dev_file, search, desc)
    
    # ========================================
    # CHECK 5: REQUIREMENTS.TXT
    # ========================================
    print_header("CHECK 5: requirements.txt")
    
    req_file = 'requirements.txt'
    if not check_file_exists(req_file):
        print_error(f"{req_file} not found!")
        all_checks_passed = False
    else:
        print_success(f"{req_file} exists")
        
        req_content = read_file(req_file)
        
        # Check deployment packages
        deployment_packages = [
            ('gunicorn', 'Web server for Railway'),
            ('dj-database-url', 'Database URL parser'),
            ('whitenoise', 'Static files serving'),
            ('psycopg2', 'PostgreSQL adapter'),
        ]
        
        for package, desc in deployment_packages:
            if package in req_content.lower():
                print_success(f"{desc} ({package})")
            else:
                print_error(f"{desc} ({package}) - REQUIRED for Railway!")
                all_checks_passed = False
    
    # ========================================
    # CHECK 6: WSGI.PY
    # ========================================
    print_header("CHECK 6: config/wsgi.py")
    
    wsgi_file = 'config/wsgi.py'
    if not check_file_exists(wsgi_file):
        print_error(f"{wsgi_file} not found!")
        all_checks_passed = False
    else:
        print_success(f"{wsgi_file} exists")
        
        wsgi_content = read_file(wsgi_file)
        
        if 'config.settings' in wsgi_content:
            print_success("Uses config.settings module")
        else:
            print_warning("Check DJANGO_SETTINGS_MODULE path")
    
    # ========================================
    # CHECK 7: RAILWAY CONFIGURATION FILES
    # ========================================
    print_header("CHECK 7: Railway Configuration Files")
    
    # Check for optional Railway files
    railway_files = [
        ('railway.json', 'Railway build configuration'),
        ('Procfile', 'Process configuration'),
        ('runtime.txt', 'Python version specification'),
    ]
    
    for filename, desc in railway_files:
        if check_file_exists(filename):
            print_success(f"{desc} ({filename})")
        else:
            print_info(f"{desc} ({filename}) - Optional, Railway auto-detects")
    
    # ========================================
    # SUMMARY
    # ========================================
    print_header("VERIFICATION SUMMARY")
    
    if all_checks_passed:
        print_success("ALL CRITICAL CHECKS PASSED! ✓")
        print_info("\nYou're ready to deploy to Railway!")
        print_info("\nNext steps:")
        print_info("1. Commit and push to GitHub")
        print_info("2. Follow RAILWAY_PROPER_FLOW_GUIDE.md")
        print_info("3. Add environment variables in Railway dashboard:")
        print_info("   - SECRET_KEY")
        print_info("   - DJANGO_SETTINGS_MODULE=config.settings.production")
        print_info("   - EMAIL_HOST=smtp.gmail.com")
        print_info("   - EMAIL_PORT=587")
        print_info("   - EMAIL_HOST_USER=erecyclo.web@gmail.com")
        print_info("   - EMAIL_HOST_PASSWORD=ceid uaaj ifso monb")
        print_info("   - DEFAULT_FROM_EMAIL=E-RECYCLO <noreply@erecyclo.in>")
        return 0
    else:
        print_error("\nSOME CHECKS FAILED!")
        print_warning("\nPlease fix the errors above before deploying.")
        print_info("\nCommon fixes:")
        print_info("1. Add default='' to config() calls in base.py")
        print_info("2. Update production.py with correct Gmail settings")
        print_info("3. Add missing packages to requirements.txt")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error running verification: {e}{Colors.END}")
        sys.exit(1)
import os
from dotenv import load_dotenv

load_dotenv()


def get_tenant_config():
    """
    Multi-tenant configuration for Flask application.
    Returns configuration dictionary for secure subdomain routing.
    """
    environment = os.getenv('ENVIRONMENT', 'development')
    
    config = {
        'SERVER_NAME': os.getenv('SERVER_NAME', 'schooldigify.local:5000'),
        'SESSION_COOKIE_DOMAIN': os.getenv('SESSION_COOKIE_DOMAIN', '.schooldigify.local'),
        'SESSION_COOKIE_SECURE': environment == 'production',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'PREFERRED_URL_SCHEME': 'https' if environment == 'production' else 'http',
        'PERMANENT_SESSION_LIFETIME': 60 * 60 * 24 * 7,
    }
    
    return config


def validate_school_subdomain(school_id):
    """
    Validate school subdomain format.
    Prevents injection attacks and ensures valid subdomain naming.
    """
    if not school_id:
        return False
    
    if not isinstance(school_id, str):
        return False
    
    if len(school_id) < 2 or len(school_id) > 63:
        return False
    
    if not school_id.replace('-', '').replace('_', '').isalnum():
        return False
    
    if school_id.startswith('-') or school_id.endswith('-'):
        return False
    
    if school_id in ['www', 'mail', 'ftp', 'admin', 'api', 'login', 'auth']:
        return False
    
    return True

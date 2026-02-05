from flask import request, session, url_for as flask_url_for
from src.model.Schools import Schools
from sqlalchemy import or_


def get_school_from_subdomain(subdomain):
    """Extract school from subdomain. Returns Schools object or None."""
    if not subdomain:
        return None
    
    return Schools.query.filter_by(id=subdomain).first()



def extract_school_id_from_request():
    """
    Extract school_id from request subdomain.
    Returns school_id string or None.
    """
    if not request.host:
        return None
    
    host = request.host.split(':')[0]
    
    if '.' not in host:
        return None
    
    parts = host.split('.')
    potential_subdomain = parts[0]
    
    if potential_subdomain in ['www', 'mail', 'api', 'admin']:
        return None
    
    return potential_subdomain


def get_current_school_id():
    """
    Get current school_id from session or request subdomain.
    Session takes priority.
    """
    if 'school_id' in session:
        return session.get('school_id')
    
    return extract_school_id_from_request()


def is_subdomain_access():
    """Check if user is accessing via subdomain."""
    return extract_school_id_from_request() is not None


def is_authenticated_for_subdomain(school_id):
    """
    Verify user is authenticated and authorized for the subdomain.
    """
    if 'user_id' not in session or 'school_id' not in session:
        return False
    
    school = get_school_from_subdomain(school_id)
    if not school:
        return False
    
    return session.get('school_id') == school.id


def url_for_school(endpoint, school_id=None, **kwargs):
    if not school_id:
        school_id = get_current_school_id()

    if school_id:
        kwargs['school_id'] = school_id

    return flask_url_for(endpoint, **kwargs)

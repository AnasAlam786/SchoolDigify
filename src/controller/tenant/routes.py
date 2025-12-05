from flask import Blueprint, request, render_template
from sqlalchemy import or_
from src.model.Schools import Schools

# Keep the blueprint subdomain option (Flask still needs SERVER_NAME configured
# to route by subdomain). Routes will also accept a school identifier from the
# URL/host so this works even without subdomain configuration.
tenant_bp = Blueprint('tenant', __name__, subdomain='<school_subdomain>')


def _extract_subdomain_from_request():
    host = request.host.split(':')[0]
    # If host looks like "sub.domain.tld", assume the first segment is subdomain
    if '.' in host:
        return host.split('.')[0]
    return None


@tenant_bp.route('/')
def tenant_home(school_subdomain=None):
    # Allow school identifier from either the routed subdomain or fallback to host
    if not school_subdomain:
        school_subdomain = _extract_subdomain_from_request()

    if not school_subdomain:
        return "School identifier not provided", 404

    # Try to find by id (primary key) or by School_Name as a fallback
    school = Schools.query.filter(
        or_(Schools.id == school_subdomain, Schools.School_Name == school_subdomain)
    ).first()

    if not school:
        return "School not found", 404

    display_name = getattr(school, 'School_Name', None) or getattr(school, 'School_Name', '')
    if not display_name:
        display_name = school.id

    return f"Welcome to {display_name}!"


@tenant_bp.route('/about')
def tenant_about(school_subdomain=None):
    if not school_subdomain:
        school_subdomain = _extract_subdomain_from_request()

    if not school_subdomain:
        return "School identifier not provided", 404

    school = Schools.query.filter(
        or_(Schools.id == school_subdomain, Schools.School_Name == school_subdomain)
    ).first()

    if not school:
        return "School not found", 404

    display_name = getattr(school, 'School_Name', None) or school.id
    return f"This is the about page of {display_name}."
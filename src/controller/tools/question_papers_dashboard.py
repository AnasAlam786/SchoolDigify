# src/controller/tools/question_papers_dashboard.py

from flask import session, render_template, Blueprint, jsonify
from src import db
from src.controller.permissions.has_permission import has_permission
from src.model.Papers import Papers
from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required

question_papers_dashboard_bp = Blueprint('question_papers_dashboard_bp', __name__)


@question_papers_dashboard_bp.route('/question-papers', methods=["GET"])
@login_required
@permission_required('create_paper')
def question_papers_dashboard():
    """Render the question papers dashboard.

    No data is fetched on the server side any more since the page uses
    an API call to load papers. The previous `papers` variable was never
    used in the template.
    """
    return render_template('question_paper/question_papers_dashboard.html')


@question_papers_dashboard_bp.route('/question-papers/api/list', methods=["GET"])
@login_required
@permission_required('create_paper')
def get_papers_list():
    """API endpoint to fetch question papers.

    The response now distinguishes between papers created by the current
    user and (when permitted) other papers in the same school/session.

    * If the caller has `view_all_papers`, the JSON payload contains two
      lists: ``user_papers`` and ``session_papers`` (other teachers').
    * Otherwise only ``user_papers`` is returned (``session_papers`` will
      be an empty list).
    """
    user_id = session.get('user_id')
    school_id = session.get('school_id')
    session_id = session.get('session_id')

    # always provide the current user's own papers
    user_papers = Papers.query.filter_by(user_id=user_id).order_by(Papers.created_at.desc()).all()
    user_data = [{
        'id': p.id,
        'event': p.event,
        'subject': p.subject,
        'class_name': p.class_name,
        'marks': p.marks,
        'duration': p.duration,
        'created_at': p.created_at.strftime('%d %b %Y, %I:%M %p'),
        'updated_at': p.updated_at.strftime('%d %b %Y, %I:%M %p'),
        'teacher_name': p.staff_data.Name if p.staff_data else 'Unknown',
    } for p in user_papers]

    session_data = []
    if has_permission('view_all_papers'):
        # include all other papers in the same school/session
        others = Papers.query.filter(
            Papers.school_id == school_id,
            Papers.session_id == session_id,
            Papers.user_id != user_id
        ).order_by(Papers.created_at.desc()).all()
        for p in others:
            session_data.append({
                'id': p.id,
                'event': p.event,
                'subject': p.subject,
                'class_name': p.class_name,
                'marks': p.marks,
                'duration': p.duration,
                'created_at': p.created_at.strftime('%d %b %Y, %I:%M %p'),
                'updated_at': p.updated_at.strftime('%d %b %Y, %I:%M %p'),
                'teacher_name': p.staff_data.Name if p.staff_data else 'Unknown',
                "sections": 45,
                "question_count": 23
            })

    return jsonify({
        'user_papers': user_data,
        'session_papers': session_data
    })





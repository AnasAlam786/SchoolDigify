# src/controller/tools/question_papers_dashboard.py

from flask import session, render_template, request, Blueprint, jsonify
from src import db
from src.model.Papers import Papers
from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required

question_papers_dashboard_bp = Blueprint('question_papers_dashboard_bp', __name__)


@question_papers_dashboard_bp.route('/question-papers', methods=["GET"])
@login_required
@permission_required('create_paper')
def question_papers_dashboard():
    """Render the question papers dashboard with all created papers"""
    
    user_id = session.get('user_id')
    school_id = session.get('school_id')
    
    # Get all papers for this user
    papers = Papers.query.filter_by(user_id=user_id).order_by(Papers.created_at.desc()).all()
    
    return render_template('question_paper/question_papers_dashboard.html', papers=papers)


@question_papers_dashboard_bp.route('/question-papers/api/list', methods=["GET"])
@login_required
@permission_required('create_paper')
def get_papers_list():
    """API endpoint to fetch all question papers for the user"""
    
    user_id = session.get('user_id')
    
    papers = Papers.query.filter_by(user_id=user_id).order_by(Papers.created_at.desc()).all()
    
    papers_data = [{
        'id': p.id,
        'event': p.event,
        'subject': p.subject,
        'class_name': p.class_name,
        'marks': p.marks,
        'duration': p.duration,
        'created_at': p.created_at.strftime('%d %b %Y, %I:%M %p'),
        'updated_at': p.updated_at.strftime('%d %b %Y, %I:%M %p'),
    } for p in papers]
    
    return jsonify({'papers': papers_data})

# src/controller/tools/question_paper_api.py

from flask import session, render_template, request, jsonify, Blueprint
from bs4 import BeautifulSoup
from src.model.Papers import Papers

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required

question_paper_api_bp = Blueprint('question_paper_api_bp', __name__)


@question_paper_api_bp.route('/question_paper_api', methods=["POST"])
@login_required
@permission_required('create_paper')
def question_paper_api():
    """Generate PDF content for question papers"""
    
    payload = request.json

    questions = payload.get('questions')
    event = payload.get('eventName')
    subject = payload.get('subject')
    std = payload.get('std')
    MM = payload.get('MM')
    hrs = payload.get('hrs')

    try:
        school = session["school_name"]
    except Exception as e:
        print(e)
        school = "School Name"

    # Render the paper template
    html = render_template('paper_elements.html', questions=questions, school=school, 
                            event=event, subject=subject, std=std, MM=MM, hrs=hrs)
    return jsonify({"html": str(html)})




    


@question_paper_api_bp.route('/question-papers/api/<int:paper_id>/preview', methods=["GET"])
@login_required
@permission_required('create_paper')
def preview_paper_pdf(paper_id):
    """Generate PDF preview HTML for a question paper"""
    
    user_id = session.get('user_id')
    
    paper = Papers.query.filter_by(id=paper_id, user_id=user_id).first()
    
    if not paper:
        return jsonify({'error': 'Paper not found'}), 404
    
    try:
        school = session.get("school_name", "School Name")
        questions = paper.paper_data.get('questions', [])
        
        html = render_template('paper_elements.html', 
                             questions=questions, 
                             school=school,
                             event=paper.event,
                             subject=paper.subject,
                             std=paper.class_name,
                             MM=paper.marks,
                             hrs=paper.duration)
        
        soup = BeautifulSoup(html, "lxml")
        content = soup.find('div', id="a4PDF").decode_contents()
        
        return jsonify({"html": str(content)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        

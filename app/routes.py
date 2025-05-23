from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory
from flask_login import login_required, current_user # Import login_required and current_user
from .services import generate_newsletter_content, send_email # Added send_email for later use
from .models import db, User, Newsletter, Issue # Import models
from datetime import datetime, timezone
import os # ensure os is imported for path checks

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Serve the SPA index page."""
    # In a real app, ensure static_folder exists and index.html is present
    if not os.path.exists(os.path.join(current_app.static_folder, 'index.html')):
        # Fallback or error for missing index.html if needed, for now will let send_from_directory handle it
        pass 
    return send_from_directory(current_app.static_folder, 'index.html')

@bp.route('/api/generate', methods=['POST'])
@login_required # Protect this route
def generate_newsletter_route():
    """Generate a newsletter, save it, (optionally) send it, and return status."""
    data = request.json
    topic = data.get('topic')
    name = data.get('name')
    # user_email_to_send_to = data.get('user_email') # Or get from User object

    if not topic or not name:
        return jsonify({'error': 'Missing topic or newsletter name'}), 400
    
    # Use the currently logged-in user
    user = current_user 
    # user = User.query.filter_by(email='default_user@example.com').first()
    # if not user:
    #     user = User(email='default_user@example.com', subscription_id='test_sub_id') # Added dummy sub_id for user
    #     db.session.add(user)
    #     db.session.commit()
    
    user_email_to_send_to = user.email # Use the user's email

    newsletter_obj = Newsletter.query.filter_by(name=name, user_id=user.id).first()
    if not newsletter_obj:
        newsletter_obj = Newsletter(name=name, topic=topic, user_id=user.id, schedule=data.get('schedule'))
        db.session.add(newsletter_obj)
        db.session.commit()

    generated_data = generate_newsletter_content(topic)
    
    if generated_data:
        new_issue = Issue(
            newsletter_id=newsletter_obj.id,
            subject=generated_data['subject'],
            content=generated_data['content'],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_issue)
        newsletter_obj.last_sent_at = datetime.now(timezone.utc)
        db.session.commit()
        
        email_sent_successfully = False
        if user_email_to_send_to: # Only attempt send if email is available
            email_sent_successfully = send_email(
                to_email_address=user_email_to_send_to,
                subject=new_issue.subject,
                html_content=new_issue.content # Assuming content is HTML suitable for email
            )
            if email_sent_successfully:
                new_issue.sent_at = datetime.now(timezone.utc)
                db.session.commit()
            else:
                current_app.logger.warning(f"Failed to send newsletter issue {new_issue.id} to {user_email_to_send_to}")
        
        return jsonify({
            'status': 'success',
            'message': 'Newsletter issue generated and saved.' + (' Email sent.' if email_sent_successfully else ' Email sending failed or skipped.'),
            'issue_id': new_issue.id,
            'subject': new_issue.subject,
            'email_status': 'sent' if email_sent_successfully else ('skipped' if not user_email_to_send_to else 'failed')
        }), 201
    else:
        return jsonify({'error': 'Failed to generate newsletter content'}), 500

@bp.route('/api/newsletters', methods=['GET'])
@login_required
def get_newsletters_route():
    """Fetch all newsletters for the currently logged-in user."""
    user_newsletters = Newsletter.query.filter_by(user_id=current_user.id).order_by(Newsletter.created_at.desc()).all()
    
    output = []
    for newsletter in user_newsletters:
        issues_count = Issue.query.filter_by(newsletter_id=newsletter.id).count()
        output.append({
            'id': newsletter.id,
            'name': newsletter.name,
            'topic': newsletter.topic,
            'schedule': newsletter.schedule,
            'last_sent_at': newsletter.last_sent_at.isoformat() if newsletter.last_sent_at else None,
            'created_at': newsletter.created_at.isoformat(),
            'issue_count': issues_count,
            # 'paused': newsletter.paused # Assuming a 'paused' attribute exists or will be added
        })
    return jsonify(output), 200

# Catch-all to support client-side routing (but exclude auth routes)
@bp.route('/<path:path>')
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    # Don't catch auth routes - let them go to the auth blueprint
    if path.startswith('auth/'):
        from flask import abort
        abort(404)  # This will let other blueprints handle it
    
    try:
        return send_from_directory(current_app.static_folder, path)
    except:
        return send_from_directory(current_app.static_folder, 'index.html') 
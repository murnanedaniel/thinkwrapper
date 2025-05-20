from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Serve the SPA index page."""
    return send_from_directory(current_app.static_folder, 'index.html')

@bp.route('/api/generate', methods=['POST'])
def generate_newsletter():
    """Generate a newsletter based on the provided topic."""
    data = request.json
    topic = data.get('topic', '')
    
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    # In MVP, generate synchronously; later move to Celery
    # from .services import generate_newsletter_content
    # content = generate_newsletter_content(topic)
    
    return jsonify({'status': 'processing', 'topic': topic}), 202

# Catch-all to support client-side routing
@bp.route('/<path:path>')
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    try:
        return send_from_directory(current_app.static_folder, path)
    except:
        return send_from_directory(current_app.static_folder, 'index.html') 
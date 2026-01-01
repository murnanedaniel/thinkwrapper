from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory
from app.tasks import generate_newsletter_async, send_email_async

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
    style = data.get('style', 'concise')
    
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    # Queue the task asynchronously
    task = generate_newsletter_async.delay(topic, style)
    
    return jsonify({
        'status': 'processing',
        'topic': topic,
        'task_id': task.id
    }), 202

@bp.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get the status of a Celery task."""
    from app.celery_config import celery
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed'
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'status': str(task.info),
        }
    else:
        response = {
            'state': task.state,
            'result': task.result if task.state == 'SUCCESS' else None
        }
    
    return jsonify(response)

# Catch-all to support client-side routing
@bp.route('/<path:path>')
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    try:
        return send_from_directory(current_app.static_folder, path)
    except:
        return send_from_directory(current_app.static_folder, 'index.html') 
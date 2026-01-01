from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory
from . import claude_service

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

@bp.route('/api/claude/generate', methods=['POST'])
def claude_generate():
    """
    Generate text using Claude API (demo endpoint).
    
    Request body:
        {
            "prompt": "Your prompt text",
            "model": "claude-3-5-sonnet-20241022" (optional),
            "max_tokens": 1024 (optional),
            "temperature": 1.0 (optional),
            "system_prompt": "System prompt" (optional)
        }
    
    Response:
        {
            "success": true,
            "text": "Generated text...",
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 10, "output_tokens": 100}
        }
    """
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    # Optional parameters
    model = data.get('model', 'claude-3-5-sonnet-20241022')
    max_tokens = data.get('max_tokens', 1024)
    temperature = data.get('temperature', 1.0)
    system_prompt = data.get('system_prompt')
    
    # Generate text using Claude
    result = claude_service.generate_text(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt
    )
    
    if result is None:
        return jsonify({
            'error': 'Failed to generate text. Check API key configuration.'
        }), 500
    
    return jsonify({
        'success': True,
        'text': result['text'],
        'model': result['model'],
        'usage': result['usage'],
        'stop_reason': result['stop_reason']
    }), 200

@bp.route('/api/claude/newsletter', methods=['POST'])
def claude_newsletter():
    """
    Generate newsletter content using Claude API (demo endpoint).
    
    Request body:
        {
            "topic": "Newsletter topic",
            "style": "professional" (optional),
            "max_tokens": 2000 (optional)
        }
    
    Response:
        {
            "success": true,
            "subject": "Newsletter subject",
            "content": "Newsletter body...",
            "model": "claude-3-5-sonnet-20241022",
            "usage": {"input_tokens": 50, "output_tokens": 500}
        }
    """
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    topic = data.get('topic', '')
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    # Optional parameters
    style = data.get('style', 'professional')
    max_tokens = data.get('max_tokens', 2000)
    
    # Generate newsletter using Claude
    result = claude_service.generate_newsletter_content_claude(
        topic=topic,
        style=style,
        max_tokens=max_tokens
    )
    
    if result is None:
        return jsonify({
            'error': 'Failed to generate newsletter. Check API key configuration.'
        }), 500
    
    return jsonify({
        'success': True,
        'subject': result['subject'],
        'content': result['content'],
        'model': result['model'],
        'usage': result['usage']
    }), 200

# Catch-all to support client-side routing
@bp.route('/<path:path>')
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    try:
        return send_from_directory(current_app.static_folder, path)
    except:
        return send_from_directory(current_app.static_folder, 'index.html') 
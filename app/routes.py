from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory
from datetime import datetime
from .newsletter_synthesis import NewsletterSynthesizer, NewsletterRenderer, NewsletterConfig
from .services import send_email

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


@bp.route('/api/admin/synthesize', methods=['POST'])
def synthesize_newsletter():
    """
    Admin endpoint to trigger newsletter synthesis on demand.
    
    Expected JSON payload:
    {
        "newsletter_id": 1,
        "topic": "AI Weekly",
        "style": "professional",  // optional
        "format": "html",  // optional: html, text, both
        "send_email": false,  // optional
        "email_to": "admin@example.com"  // optional, required if send_email is true
    }
    """
    data = request.json
    
    # Validate required fields
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    newsletter_id = data.get('newsletter_id')
    topic = data.get('topic')
    
    if not newsletter_id:
        return jsonify({'error': 'newsletter_id is required'}), 400
    if not topic:
        return jsonify({'error': 'topic is required'}), 400
    
    # Optional parameters
    style = data.get('style', 'professional')
    output_format = data.get('format', 'html')
    send_email_flag = data.get('send_email', False)
    email_to = data.get('email_to')
    
    # Validate send_email requirements
    if send_email_flag and not email_to:
        return jsonify({'error': 'email_to is required when send_email is true'}), 400
    
    # Initialize synthesizer and renderer
    synthesizer = NewsletterSynthesizer()
    renderer = NewsletterRenderer()
    
    try:
        # Generate newsletter on demand
        result = synthesizer.generate_on_demand(
            newsletter_id=newsletter_id,
            topic=topic,
            style=style
        )
        
        if not result.get('success'):
            return jsonify({
                'error': 'Newsletter synthesis failed',
                'details': result.get('error')
            }), 500
        
        # Prepare content for rendering
        content = {
            'subject': result['subject'],
            'content': result['content']
        }
        
        # Render in requested format(s)
        rendered_output = {}
        
        if output_format == 'both':
            rendered_output['html'] = renderer.render_html(content)
            rendered_output['text'] = renderer.render_plain_text(content)
        elif output_format == 'text':
            rendered_output['text'] = renderer.render_plain_text(content)
        else:  # default to html
            rendered_output['html'] = renderer.render_html(content)
        
        # Send email if requested
        email_sent = False
        if send_email_flag:
            email_content = rendered_output.get('html') or rendered_output.get('text')
            email_sent = send_email(email_to, result['subject'], email_content)
        
        return jsonify({
            'success': True,
            'subject': result['subject'],
            'content': result['content'],
            'rendered': rendered_output,
            'metadata': {
                'content_items_count': result['content_items_count'],
                'generated_at': result['generated_at'],
                'style': result['style'],
                'format': output_format,
                'email_sent': email_sent
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Newsletter synthesis error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@bp.route('/api/admin/newsletter/config', methods=['GET', 'POST'])
def newsletter_config():
    """
    Get or update newsletter configuration settings.
    
    GET: Returns current configuration
    POST: Updates configuration with provided settings
    """
    config = NewsletterConfig()
    
    if request.method == 'GET':
        return jsonify(config.to_dict()), 200
    
    # POST - update configuration
    data = request.json
    if not data:
        return jsonify({'error': 'No configuration data provided'}), 400
    
    try:
        config.from_dict(data)
        is_valid, error_message = config.validate()
        
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # In a real implementation, save config to database
        return jsonify({
            'success': True,
            'config': config.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Failed to update configuration',
            'details': str(e)
        }), 500


@bp.route('/api/admin/newsletter/preview', methods=['POST'])
def preview_newsletter():
    """
    Preview newsletter in different formats without sending.
    
    Expected JSON payload:
    {
        "subject": "Newsletter Subject",
        "content": "Newsletter content...",
        "format": "html"  // html, text, or both
    }
    """
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    subject = data.get('subject')
    content = data.get('content')
    output_format = data.get('format', 'html')
    
    if not subject or not content:
        return jsonify({'error': 'subject and content are required'}), 400
    
    renderer = NewsletterRenderer()
    content_dict = {'subject': subject, 'content': content}
    
    try:
        rendered_output = {}
        
        if output_format == 'both':
            rendered_output['html'] = renderer.render_html(content_dict)
            rendered_output['text'] = renderer.render_plain_text(content_dict)
        elif output_format == 'text':
            rendered_output['text'] = renderer.render_plain_text(content_dict)
        else:
            rendered_output['html'] = renderer.render_html(content_dict)
        
        return jsonify({
            'success': True,
            'rendered': rendered_output
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Preview generation failed',
            'details': str(e)
        }), 500

# Catch-all to support client-side routing
@bp.route('/<path:path>')
def catch_all(path):
    """Serve static files or return index.html for client-side routing."""
    try:
        return send_from_directory(current_app.static_folder, path)
    except:
        return send_from_directory(current_app.static_folder, 'index.html') 
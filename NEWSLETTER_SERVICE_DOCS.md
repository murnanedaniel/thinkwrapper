# Newsletter Synthesis Service Documentation

## Overview

The Newsletter Synthesis Service is a backend feature that enables the automatic generation and customization of periodic newsletters. It collects content from various sources, synthesizes it using AI, and delivers newsletters in multiple formats.

## Features

- **Content Collection**: Automatically collect and organize source content for newsletter generation
- **AI-Powered Synthesis**: Use OpenAI to generate engaging newsletter content
- **Pluggable Rendering**: Support for multiple output formats (HTML, plain text)
- **On-Demand Generation**: Admin users can trigger newsletter synthesis manually
- **Flexible Configuration**: Customizable settings for schedule, format, and style
- **Email Distribution**: Built-in integration with SendGrid for email delivery

## Architecture

### Core Components

1. **NewsletterSynthesizer** (`app/newsletter_synthesis.py`)
   - Collects source content
   - Synthesizes newsletter content using OpenAI
   - Provides fallback content generation when AI is unavailable
   - Supports on-demand generation

2. **NewsletterRenderer** (`app/newsletter_synthesis.py`)
   - Converts newsletter content to different formats
   - Supports HTML and plain text rendering
   - Basic markdown-to-HTML conversion

3. **NewsletterConfig** (`app/newsletter_synthesis.py`)
   - Manages configuration settings
   - Validates configuration values
   - Supports multiple delivery formats and schedules

### API Endpoints

#### 1. Synthesize Newsletter (Admin Only)

**Endpoint**: `POST /api/admin/synthesize`

**Purpose**: Trigger newsletter synthesis on demand

**Request Body**:
```json
{
  "newsletter_id": 1,
  "topic": "AI Weekly Update",
  "style": "professional",
  "format": "html",
  "send_email": false,
  "email_to": "admin@example.com"
}
```

**Required Fields**:
- `newsletter_id`: Integer - The newsletter ID
- `topic`: String - Newsletter topic

**Optional Fields**:
- `style`: String - Writing style (professional, casual, technical). Default: "professional"
- `format`: String - Output format (html, text, both). Default: "html"
- `send_email`: Boolean - Whether to send email. Default: false
- `email_to`: String - Email recipient (required if send_email is true)

**Response** (Success):
```json
{
  "success": true,
  "subject": "AI Weekly Update - January 1, 2024",
  "content": "Newsletter content here...",
  "rendered": {
    "html": "<html>...</html>"
  },
  "metadata": {
    "content_items_count": 5,
    "generated_at": "2024-01-01T00:00:00",
    "style": "professional",
    "format": "html",
    "email_sent": false
  }
}
```

**Example Usage**:
```bash
curl -X POST http://localhost:5000/api/admin/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "newsletter_id": 1,
    "topic": "Weekly Tech Update",
    "style": "professional",
    "format": "both",
    "send_email": true,
    "email_to": "admin@example.com"
  }'
```

#### 2. Get/Update Newsletter Configuration

**Endpoint**: `GET /api/admin/newsletter/config`

**Purpose**: Retrieve current newsletter configuration

**Response**:
```json
{
  "schedule": "weekly",
  "delivery_format": "html",
  "max_content_items": 10,
  "style": "professional",
  "send_time": "09:00",
  "timezone": "UTC"
}
```

**Endpoint**: `POST /api/admin/newsletter/config`

**Purpose**: Update newsletter configuration

**Request Body**:
```json
{
  "schedule": "daily",
  "delivery_format": "both",
  "style": "casual",
  "max_content_items": 15
}
```

**Valid Values**:
- `schedule`: "daily", "weekly", "monthly"
- `delivery_format`: "html", "text", "both"
- `style`: "professional", "casual", "technical"
- `max_content_items`: 1-50

**Example Usage**:
```bash
# Get configuration
curl http://localhost:5000/api/admin/newsletter/config

# Update configuration
curl -X POST http://localhost:5000/api/admin/newsletter/config \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": "daily",
    "delivery_format": "html",
    "style": "technical"
  }'
```

#### 3. Preview Newsletter

**Endpoint**: `POST /api/admin/newsletter/preview`

**Purpose**: Preview newsletter rendering without sending

**Request Body**:
```json
{
  "subject": "Test Newsletter",
  "content": "# Main Title\n\nNewsletter content...",
  "format": "html"
}
```

**Response**:
```json
{
  "success": true,
  "rendered": {
    "html": "<!DOCTYPE html>..."
  }
}
```

**Example Usage**:
```bash
curl -X POST http://localhost:5000/api/admin/newsletter/preview \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Newsletter",
    "content": "# Hello World\n\nThis is a test.",
    "format": "both"
  }'
```

## Running the Service

### Prerequisites

1. Python 3.12+
2. Required environment variables:
   - `OPENAI_API_KEY` (required for AI synthesis)
   - `SENDGRID_API_KEY` (required for email sending)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Flask server
flask --app app run --debug
```

### Configuration

Create a `.env` file in the project root:

```env
FLASK_ENV=development
OPENAI_API_KEY=your-openai-api-key
SENDGRID_API_KEY=your-sendgrid-api-key
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

## Testing

### Run All Tests

```bash
# Run newsletter synthesis tests
python -m pytest tests/test_newsletter_synthesis.py -v

# Run API route tests
python -m pytest tests/test_synthesis_routes.py -v

# Run all tests
python -m pytest tests/ -v
```

### Test Coverage

The test suite includes:
- Unit tests for content collection and synthesis
- Tests for all rendering formats (HTML, text)
- Configuration validation tests
- API endpoint tests with various scenarios
- Error handling and fallback tests

## Customization Guide

### Adding a New Rendering Format

To add a new rendering format (e.g., PDF):

1. Add a new method to `NewsletterRenderer`:
```python
def render_pdf(self, content: Dict[str, str]) -> bytes:
    """Render newsletter as PDF."""
    # PDF generation logic here
    pass
```

2. Update the `render()` method to support the new format:
```python
def render(self, content: Dict[str, str], format: str = "html"):
    if format.lower() == "pdf":
        return self.render_pdf(content)
    # ... existing code
```

3. Update `NewsletterConfig` validation to allow the new format.

### Customizing Content Collection

To customize how content is collected:

1. Override or extend `collect_source_content()` in `NewsletterSynthesizer`:
```python
def collect_source_content(self, newsletter_id: int, since: Optional[datetime] = None):
    # Add custom data source integration
    # Query your database, APIs, etc.
    return content_items
```

### Changing AI Model

To use a different OpenAI model:

1. Modify the `synthesize_newsletter()` method:
```python
response = client.completions.create(
    model="gpt-4",  # Change model here
    prompt=prompt,
    max_tokens=1000,  # Adjust parameters as needed
    temperature=0.7
)
```

## Proof-of-Concept Demo

### Generate and Email a Newsletter

Here's a complete example of generating and emailing a newsletter:

```python
from app.newsletter_synthesis import NewsletterSynthesizer, NewsletterRenderer
from app.services import send_email

# Initialize services
synthesizer = NewsletterSynthesizer()
renderer = NewsletterRenderer()

# Generate newsletter
result = synthesizer.generate_on_demand(
    newsletter_id=1,
    topic="Weekly Tech News",
    style="professional"
)

if result['success']:
    # Render as HTML
    content = {
        'subject': result['subject'],
        'content': result['content']
    }
    html_newsletter = renderer.render_html(content)
    
    # Send email
    send_email(
        to_email="subscriber@example.com",
        subject=result['subject'],
        content=html_newsletter
    )
    
    print(f"Newsletter sent: {result['subject']}")
else:
    print(f"Generation failed: {result['error']}")
```

### Using the API

```bash
# Generate and send newsletter via API
curl -X POST http://localhost:5000/api/admin/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "newsletter_id": 1,
    "topic": "AI Developments This Week",
    "style": "professional",
    "format": "html",
    "send_email": true,
    "email_to": "admin@example.com"
  }'
```

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Issue: Newsletter generation fails
   - Solution: Check that `OPENAI_API_KEY` is set correctly
   - Fallback: The service will automatically use fallback content generation

2. **Email Not Sending**
   - Issue: Email delivery fails
   - Solution: Verify `SENDGRID_API_KEY` is configured
   - Check: Review Flask logs for specific error messages

3. **Import Errors**
   - Issue: Module not found errors
   - Solution: Ensure all dependencies are installed: `pip install -r requirements.txt`

### Logging

The service logs errors using Flask's logger. Enable debug logging:

```python
app = create_app()
app.logger.setLevel(logging.DEBUG)
```

Or via environment variable:
```bash
export FLASK_DEBUG=1
```

## Production Deployment

### Recommended Setup

1. **Use Celery for Async Processing**: Move newsletter generation to background tasks
2. **Configure Rate Limiting**: Protect API endpoints from abuse
3. **Set Up Monitoring**: Track newsletter generation success rates
4. **Database Integration**: Store generated newsletters for archival
5. **Implement Authentication**: Secure admin endpoints properly

### Environment Variables for Production

```env
FLASK_ENV=production
OPENAI_API_KEY=prod-openai-key
SENDGRID_API_KEY=prod-sendgrid-key
DATABASE_URL=postgresql://prod-db-url
REDIS_URL=redis://prod-redis-url  # For Celery
```

## Future Enhancements

- [ ] Schedule automated newsletter generation (using Celery)
- [ ] Support for custom templates
- [ ] Analytics and tracking
- [ ] A/B testing for subject lines
- [ ] Multi-language support
- [ ] RSS feed integration
- [ ] Social media integration
- [ ] Subscriber management interface

## Support

For issues or questions:
- Review the test files for usage examples
- Check Flask logs for error details
- Consult the API documentation above

## License

MIT License - See LICENSE file for details

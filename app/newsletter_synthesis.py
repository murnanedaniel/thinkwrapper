"""
Newsletter Synthesis Service

This module provides functionality to synthesize and generate periodic newsletters
by collecting and transforming source content into newsletter summaries.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

# Try to import Flask current_app, but make it optional for testing
try:
    from flask import current_app
    _has_flask = True
except ImportError:
    _has_flask = False
    current_app = None


class NewsletterSynthesizer:
    """
    Service for synthesizing newsletter content from multiple sources.
    """
    
    def __init__(self):
        """Initialize the newsletter synthesizer."""
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    def collect_source_content(
        self, 
        newsletter_id: int, 
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect source content for newsletter synthesis.
        
        Args:
            newsletter_id: The newsletter ID to collect content for
            since: Optional datetime to collect content since (defaults to last 7 days)
            
        Returns:
            List of content items with metadata
        """
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)
        
        # In a real implementation, this would query a database or external APIs
        # For now, return mock data structure
        return [
            {
                'title': 'Sample Content Item 1',
                'summary': 'This is a sample content summary',
                'source': 'Platform Data',
                'created_at': datetime.utcnow().isoformat(),
                'url': 'https://example.com/item1'
            },
            {
                'title': 'Sample Content Item 2',
                'summary': 'Another interesting piece of content',
                'source': 'Saved Content',
                'created_at': datetime.utcnow().isoformat(),
                'url': 'https://example.com/item2'
            }
        ]
    
    def synthesize_newsletter(
        self,
        topic: str,
        content_items: List[Dict[str, Any]],
        style: str = "professional"
    ) -> Dict[str, str]:
        """
        Synthesize newsletter content from collected items.
        
        Args:
            topic: The newsletter topic
            content_items: List of content items to synthesize
            style: Writing style (professional, casual, technical)
            
        Returns:
            Dictionary with 'subject' and 'content' keys
        """
        if not self.openai_api_key:
            self._log_error("OpenAI API key not configured")
            return self._generate_fallback_content(topic, content_items)
        
        # Build context from content items
        content_summary = "\n".join([
            f"- {item['title']}: {item['summary']}"
            for item in content_items
        ])
        
        prompt = f"""
        Create a {style} newsletter about {topic}.
        
        Based on the following content items:
        {content_summary}
        
        Generate:
        1. An engaging subject line (first line)
        2. A brief introduction
        3. Summaries of key highlights from the content
        4. A closing paragraph with call-to-action
        
        Keep the tone {style} and the length moderate (300-500 words).
        """
        
        try:
            # Using OpenAI's v1.0+ API structure
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            content = response.choices[0].text.strip()
            
            # Extract subject and body
            lines = content.split('\n', 1)
            subject = lines[0].replace('Subject:', '').strip()
            body = lines[1].strip() if len(lines) > 1 else content
            
            return {
                'subject': subject,
                'content': body
            }
        except Exception as e:
            self._log_error(f"Newsletter synthesis error: {str(e)}")
            return self._generate_fallback_content(topic, content_items)
    
    def _generate_fallback_content(
        self, 
        topic: str, 
        content_items: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate fallback content when AI synthesis is unavailable.
        
        Args:
            topic: The newsletter topic
            content_items: List of content items
            
        Returns:
            Dictionary with 'subject' and 'content' keys
        """
        subject = f"{topic} Newsletter - {datetime.utcnow().strftime('%B %d, %Y')}"
        
        content_sections = []
        content_sections.append(f"# {topic} Newsletter\n")
        content_sections.append(f"Welcome to this week's {topic} update.\n")
        
        if content_items:
            content_sections.append("\n## Highlights\n")
            for item in content_items:
                content_sections.append(f"### {item['title']}\n")
                content_sections.append(f"{item['summary']}\n")
                if 'url' in item:
                    content_sections.append(f"[Read more]({item['url']})\n")
        
        content_sections.append("\n---\n")
        content_sections.append("Thank you for reading!\n")
        
        return {
            'subject': subject,
            'content': '\n'.join(content_sections)
        }
    
    def generate_on_demand(
        self,
        newsletter_id: int,
        topic: str,
        style: str = "professional",
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate newsletter on demand for admin users.
        
        Args:
            newsletter_id: The newsletter ID
            topic: Newsletter topic
            style: Writing style
            since: Optional datetime to collect content since
            
        Returns:
            Dictionary with synthesis results including metadata
        """
        try:
            # Collect source content
            content_items = self.collect_source_content(newsletter_id, since)
            
            # Synthesize newsletter
            synthesized = self.synthesize_newsletter(topic, content_items, style)
            
            return {
                'success': True,
                'subject': synthesized['subject'],
                'content': synthesized['content'],
                'content_items_count': len(content_items),
                'generated_at': datetime.utcnow().isoformat(),
                'style': style
            }
        except Exception as e:
            self._log_error(f"On-demand generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _log_error(self, message: str):
        """
        Log error message, using Flask's logger if available.
        
        Args:
            message: Error message to log
        """
        if _has_flask and current_app:
            try:
                current_app.logger.error(message)
            except RuntimeError:
                # Outside application context, use print as fallback
                print(f"ERROR: {message}")
        else:
            print(f"ERROR: {message}")


class NewsletterRenderer:
    """
    Pluggable rendering system for newsletters.
    Supports multiple output formats (plain text, HTML).
    """
    
    def render_plain_text(self, content: Dict[str, str]) -> str:
        """
        Render newsletter content as plain text.
        
        Args:
            content: Dictionary with 'subject' and 'content' keys
            
        Returns:
            Plain text formatted newsletter
        """
        subject = content.get('subject', 'Newsletter')
        body = content.get('content', '')
        
        # Convert basic markdown to plain text
        plain_content = body.replace('# ', '').replace('## ', '').replace('### ', '')
        plain_content = plain_content.replace('**', '').replace('__', '')
        plain_content = plain_content.replace('[', '').replace(']', '')
        
        output = f"Subject: {subject}\n"
        output += "=" * 70 + "\n\n"
        output += plain_content
        output += "\n\n" + "=" * 70 + "\n"
        
        return output
    
    def render_html(self, content: Dict[str, str]) -> str:
        """
        Render newsletter content as HTML.
        
        Args:
            content: Dictionary with 'subject' and 'content' keys
            
        Returns:
            HTML formatted newsletter
        """
        subject = content.get('subject', 'Newsletter')
        body = content.get('content', '')
        
        # Convert basic markdown to HTML
        html_content = self._markdown_to_html(body)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 25px;
        }}
        h3 {{
            color: #666;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #777;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{subject}</h1>
        {html_content}
        <div class="footer">
            <p>Thank you for reading!</p>
        </div>
    </div>
</body>
</html>
"""
        return html_template
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert basic markdown to HTML.
        
        Args:
            markdown_text: Markdown formatted text
            
        Returns:
            HTML formatted text
        """
        # Split into lines for processing
        lines = markdown_text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Process headers
            if line.startswith('### '):
                processed_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('## '):
                processed_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('# '):
                processed_lines.append(f'<h1>{line[2:]}</h1>')
            else:
                processed_lines.append(line)
        
        html = '\n'.join(processed_lines)
        
        # Convert bold
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
        
        # Convert line breaks to paragraphs
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and not any(para.startswith(f'<h{i}>') for i in range(1, 7)):
                html_paragraphs.append(f'<p>{para}</p>')
            elif para:
                html_paragraphs.append(para)
        
        html = '\n'.join(html_paragraphs)
        
        return html
    
    def render(self, content: Dict[str, str], format: str = "html") -> str:
        """
        Render newsletter in the specified format.
        
        Args:
            content: Dictionary with newsletter content
            format: Output format ('html' or 'text')
            
        Returns:
            Rendered newsletter content
        """
        if format.lower() == "text":
            return self.render_plain_text(content)
        else:
            return self.render_html(content)


class NewsletterConfig:
    """
    Configuration settings for newsletter synthesis and delivery.
    """
    
    def __init__(self):
        """Initialize with default configuration."""
        self.schedule = "weekly"  # weekly, monthly, daily
        self.delivery_format = "html"  # html, text, both
        self.max_content_items = 10
        self.style = "professional"  # professional, casual, technical
        self.send_time = "09:00"  # Time to send newsletters
        self.timezone = "UTC"
    
    def from_dict(self, config_dict: Dict[str, Any]) -> 'NewsletterConfig':
        """
        Load configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            Self for chaining
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary with configuration values
        """
        return {
            'schedule': self.schedule,
            'delivery_format': self.delivery_format,
            'max_content_items': self.max_content_items,
            'style': self.style,
            'send_time': self.send_time,
            'timezone': self.timezone
        }
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration settings.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_schedules = ['daily', 'weekly', 'monthly']
        if self.schedule not in valid_schedules:
            return False, f"Invalid schedule: {self.schedule}"
        
        valid_formats = ['html', 'text', 'both']
        if self.delivery_format not in valid_formats:
            return False, f"Invalid delivery format: {self.delivery_format}"
        
        valid_styles = ['professional', 'casual', 'technical']
        if self.style not in valid_styles:
            return False, f"Invalid style: {self.style}"
        
        if self.max_content_items < 1 or self.max_content_items > 50:
            return False, f"Invalid max_content_items: {self.max_content_items}"
        
        return True, None
